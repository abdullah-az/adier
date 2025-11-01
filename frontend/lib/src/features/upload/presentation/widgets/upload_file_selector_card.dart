import 'dart:async';

import 'package:desktop_drop/desktop_drop.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

import '../../application/upload_workflow_controller.dart';
import '../../domain/selected_upload_file.dart';

class UploadFileSelectorCard extends StatefulWidget {
  const UploadFileSelectorCard({
    super.key,
    required this.state,
    required this.l10n,
    required this.onFileSelected,
    required this.onClearSelection,
    required this.onUpload,
  });

  final UploadWorkflowState state;
  final AppLocalizations l10n;
  final ValueChanged<SelectedUploadFile> onFileSelected;
  final VoidCallback onClearSelection;
  final FutureOr<void> Function() onUpload;

  @override
  State<UploadFileSelectorCard> createState() => _UploadFileSelectorCardState();
}

class _UploadFileSelectorCardState extends State<UploadFileSelectorCard> {
  bool _dragging = false;
  bool _picking = false;

  bool get _supportsDrop {
    if (kIsWeb) {
      return true;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.macOS:
      case TargetPlatform.linux:
      case TargetPlatform.windows:
        return true;
      default:
        return false;
    }
  }

  UploadWorkflowState get _state => widget.state;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = widget.l10n;
    final selectedFile = _state.selectedFile;

    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.uploadFileSectionTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: 12),
            Text(
              l10n.uploadFileSectionSubtitle,
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            _buildDropArea(context, theme, l10n),
            if (selectedFile != null) ...<Widget>[
              const SizedBox(height: 16),
              _SelectedFileTile(
                file: selectedFile,
                l10n: l10n,
                onClear: widget.onClearSelection,
                isBusy: _state.isBusy,
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: <Widget>[
                FilledButton.icon(
                  onPressed: _state.canStartUpload ? _handleUpload : null,
                  icon: _state.isUploading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.cloud_upload_rounded),
                  label: Text(l10n.uploadFileUploadButton),
                ),
                const SizedBox(width: 12),
                if (_state.isOffline)
                  Flexible(
                    child: Text(
                      l10n.uploadFileOfflineRestriction,
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDropArea(BuildContext context, ThemeData theme, AppLocalizations l10n) {
    final supportsDrop = _supportsDrop;
    final isDisabled = _state.isBusy;

    Widget child = AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeInOut,
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 32),
      decoration: BoxDecoration(
        border: Border.all(
          color: _dragging ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
          style: _dragging ? BorderStyle.solid : BorderStyle.solid,
          width: 1.5,
        ),
        borderRadius: BorderRadius.circular(16),
        color: _dragging ? theme.colorScheme.primary.withOpacity(0.08) : theme.colorScheme.surfaceVariant,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(Icons.cloud_upload_outlined, size: 40, color: theme.colorScheme.primary),
          const SizedBox(height: 12),
          Text(
            supportsDrop ? l10n.uploadFileDropInstructions : l10n.uploadFileTapInstructions,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: isDisabled ? null : _pickFile,
            icon: _picking
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.folder_open_rounded),
            label: Text(l10n.uploadFileBrowseButton),
          ),
        ],
      ),
    );

    if (supportsDrop) {
      child = DropTarget(
        onDragEntered: (_) {
          if (isDisabled) {
            return;
          }
          setState(() => _dragging = true);
        },
        onDragExited: (_) {
          if (!mounted) {
            return;
          }
          setState(() => _dragging = false);
        },
        onDragDone: (details) async {
          if (isDisabled) {
            return;
          }
          setState(() => _dragging = false);
          await _handleDroppedFiles(details.files);
        },
        child: child,
      );
    } else {
      child = InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: isDisabled ? null : _pickFile,
        child: child,
      );
    }

    return child;
  }

  Future<void> _pickFile() async {
    if (_picking) {
      return;
    }
    setState(() => _picking = true);
    try {
      final result = await openFile(
        acceptedTypeGroups: <XTypeGroup>[
          const XTypeGroup(
            label: 'videos',
            mimeTypes: <String>['video/*'],
            extensions: <String>['mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'],
          ),
        ],
      );
      if (result == null) {
        return;
      }
      final selected = await _toSelectedFile(result);
      if (selected != null && mounted) {
        widget.onFileSelected(selected);
      }
    } catch (error) {
      _showError(error);
    } finally {
      if (mounted) {
        setState(() => _picking = false);
      }
    }
  }

  Future<void> _handleDroppedFiles(List<XFile> files) async {
    if (files.isEmpty) {
      return;
    }
    final file = files.first;
    if (!_isVideo(file.name)) {
      _showUnsupportedType();
      return;
    }
    try {
      final selected = await _toSelectedFile(file);
      if (selected != null && mounted) {
        widget.onFileSelected(selected);
      }
    } catch (error) {
      _showError(error);
    }
  }

  Future<SelectedUploadFile?> _toSelectedFile(XFile file) async {
    try {
      final size = await file.length();
      final mimeType = file.mimeType ?? _inferMimeType(file.name);
      return SelectedUploadFile(
        name: file.name,
        mimeType: mimeType,
        sizeBytes: size,
      );
    } catch (error) {
      _showError(error);
      return null;
    }
  }

  Future<void> _handleUpload() async {
    await widget.onUpload();
  }

  void _showError(Object error) {
    if (!mounted) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    messenger.showSnackBar(
      SnackBar(
        content: Text(widget.l10n.uploadFileGenericError(error.toString())),
        backgroundColor: Theme.of(context).colorScheme.errorContainer,
      ),
    );
  }

  void _showUnsupportedType() {
    if (!mounted) {
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    messenger.showSnackBar(
      SnackBar(
        content: Text(widget.l10n.uploadFileUnsupportedType),
        backgroundColor: Theme.of(context).colorScheme.errorContainer,
      ),
    );
  }

  bool _isVideo(String name) {
    final extension = name.split('.').lastOrNull?.toLowerCase() ?? '';
    return <String>{'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'}.contains(extension);
  }

  String _inferMimeType(String name) {
    final extension = name.split('.').lastOrNull?.toLowerCase();
    switch (extension) {
      case 'mp4':
        return 'video/mp4';
      case 'mov':
        return 'video/quicktime';
      case 'mkv':
        return 'video/x-matroska';
      case 'avi':
        return 'video/x-msvideo';
      case 'webm':
        return 'video/webm';
      case 'm4v':
        return 'video/x-m4v';
      default:
        return 'application/octet-stream';
    }
  }
}

class _SelectedFileTile extends StatelessWidget {
  const _SelectedFileTile({
    required this.file,
    required this.l10n,
    required this.onClear,
    required this.isBusy,
  });

  final SelectedUploadFile file;
  final AppLocalizations l10n;
  final VoidCallback onClear;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        leading: const Icon(Icons.movie_creation_outlined),
        title: Text(file.name, maxLines: 2, overflow: TextOverflow.ellipsis),
        subtitle: Text(l10n.uploadFileSelectedLabel(file.sizeLabel)),
        trailing: IconButton(
          icon: const Icon(Icons.clear_rounded),
          tooltip: l10n.uploadFileRemoveButton,
          onPressed: isBusy ? null : onClear,
        ),
      ),
    );
  }
}

extension _IterableStringLastOrNull on Iterable<String> {
  String? get lastOrNull => isEmpty ? null : last;
}
