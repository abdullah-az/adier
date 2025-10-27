import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../l10n/app_localizations.dart';
import 'upload_controller.dart';

class UploadFlow extends ConsumerWidget {
  const UploadFlow({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final uploadState = ref.watch(uploadControllerProvider);
    final controller = ref.read(uploadControllerProvider.notifier);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              l10n.upload,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              key: const Key('upload_button'),
              onPressed: uploadState.isUploading
                  ? null
                  : () async {
                      await controller.uploadDemoFile();
                    },
              icon: const Icon(Icons.cloud_upload),
              label: Text(uploadState.isComplete ? l10n.uploadCompleted : l10n.selectFile),
            ),
            const SizedBox(height: 12),
            if (uploadState.isUploading) ...[
              LinearProgressIndicator(
                key: const Key('upload_progress'),
                value: uploadState.progress,
              ),
              const SizedBox(height: 8),
              Text(l10n.uploadInProgress),
            ] else if (uploadState.isComplete) ...[
              Text(
                l10n.uploadCompleted,
                key: const Key('upload_complete'),
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: Theme.of(context).colorScheme.primary),
              ),
            ] else if (uploadState.hasError) ...[
              Text(
                l10n.uploadFailed,
                key: const Key('upload_error'),
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: Theme.of(context).colorScheme.error),
              ),
            ],
            if (uploadState.fileName != null) ...[
              const SizedBox(height: 8),
              Text('${l10n.selectedFile}: ${uploadState.fileName}'),
            ],
          ],
        ),
      ),
    );
  }
}
