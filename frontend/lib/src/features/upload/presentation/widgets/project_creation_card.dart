import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

import '../../application/upload_workflow_controller.dart';

class ProjectCreationCard extends StatefulWidget {
  const ProjectCreationCard({
    super.key,
    required this.state,
    required this.l10n,
    required this.onNameChanged,
    required this.onSubmit,
    required this.onReset,
  });

  final UploadWorkflowState state;
  final AppLocalizations l10n;
  final ValueChanged<String> onNameChanged;
  final VoidCallback onSubmit;
  final VoidCallback onReset;

  @override
  State<ProjectCreationCard> createState() => _ProjectCreationCardState();
}

class _ProjectCreationCardState extends State<ProjectCreationCard> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;

  UploadWorkflowState get _state => widget.state;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _state.projectName);
    _focusNode = FocusNode();
  }

  @override
  void didUpdateWidget(covariant ProjectCreationCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_state.projectName != _controller.text) {
      _controller.value = TextEditingValue(
        text: _state.projectName,
        selection: TextSelection.collapsed(offset: _state.projectName.length),
      );
    }
    if (oldWidget.state.project != _state.project && _state.project == null && mounted) {
      _focusNode.requestFocus();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = widget.l10n;
    final project = _state.project;

    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.uploadProjectSectionTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: 12),
            Text(
              l10n.uploadProjectSectionSubtitle,
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            if (project != null) ...<Widget>[
              _ActiveProjectSummary(projectName: project.name, projectId: project.id, l10n: l10n),
              const SizedBox(height: 20),
            ],
            TextField(
              controller: _controller,
              focusNode: _focusNode,
              enabled: !_state.isBusy && project == null,
              onChanged: widget.onNameChanged,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _triggerSubmit(),
              decoration: InputDecoration(
                labelText: l10n.uploadProjectNameLabel,
                hintText: l10n.uploadProjectNameHint,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: <Widget>[
                FilledButton.icon(
                  onPressed: project == null && _state.canCreateProject ? _triggerSubmit : null,
                  icon: _state.isBusy && _state.status == UploadWorkflowStatus.creatingProject
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.check_rounded),
                  label: Text(l10n.uploadProjectCreateButton),
                ),
                const SizedBox(width: 12),
                if (project != null)
                  OutlinedButton.icon(
                    onPressed: _state.isBusy ? null : widget.onReset,
                    icon: const Icon(Icons.refresh_rounded),
                    label: Text(l10n.uploadProjectCreateAnotherButton),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _triggerSubmit() {
    if (_state.canCreateProject) {
      widget.onSubmit();
    }
  }
}

class _ActiveProjectSummary extends StatelessWidget {
  const _ActiveProjectSummary({
    required this.projectName,
    required this.projectId,
    required this.l10n,
  });

  final String projectName;
  final String projectId;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(Icons.folder_open_rounded, size: 32, color: theme.colorScheme.primary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    projectName,
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    l10n.uploadProjectIdLabel(projectId),
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Chip(label: Text(l10n.uploadProjectActiveLabel)),
          ],
        ),
      ),
    );
  }
}
