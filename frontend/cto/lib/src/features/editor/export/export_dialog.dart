import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../l10n/app_localizations.dart';
import 'export_controller.dart';

class ExportDialog extends ConsumerWidget {
  const ExportDialog({
    required this.uploadId,
    super.key,
  });

  final String uploadId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final exportState = ref.watch(exportControllerProvider);
    final controller = ref.read(exportControllerProvider.notifier);

    return AlertDialog(
      title: Text(l10n.exportTitle),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(l10n.exportSubtitle),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: const Key('export_format_dropdown'),
            value: exportState.format,
            decoration: InputDecoration(
              labelText: l10n.exportFormat,
            ),
            onChanged: exportState.isExporting
                ? null
                : (value) {
                    if (value != null) {
                      controller.updateFormat(value);
                    }
                  },
            items: const [
              DropdownMenuItem(value: 'mp4', child: Text('MP4')),
              DropdownMenuItem(value: 'mov', child: Text('MOV')),
              DropdownMenuItem(value: 'gif', child: Text('GIF')),
            ],
          ),
          const SizedBox(height: 12),
          if (exportState.isExporting) ...[
            const LinearProgressIndicator(),
            const SizedBox(height: 8),
            Text(
              l10n.exportInProgress,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ] else if (exportState.isComplete) ...[
            Text(
              l10n.exportSuccess(exportState.exportId!),
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.primary),
            ),
          ] else if (exportState.hasError) ...[
            Text(
              l10n.exportError,
              key: const Key('export_error'),
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.error),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l10n.cancel),
        ),
        ElevatedButton(
          key: const Key('confirm_export_button'),
          onPressed: exportState.isExporting
              ? null
              : () async {
                  await controller.exportProject(uploadId);
                },
          child: Text(l10n.export),
        ),
      ],
    );
  }
}
