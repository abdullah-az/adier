import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import 'export/export_controller.dart';
import 'export/export_dialog.dart';
import 'subtitle/subtitle_editor.dart';
import 'timeline/timeline_controller.dart';
import 'timeline/timeline_editor.dart';
import 'upload/upload_controller.dart';
import 'upload/upload_flow.dart';

class EditorScreen extends ConsumerWidget {
  const EditorScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen<UploadState>(uploadControllerProvider, (previous, next) {
      if (next.isComplete && previous?.uploadId != next.uploadId) {
        ref.read(timelineControllerProvider.notifier).loadTimeline(next.uploadId!);
      }
    });

    final l10n = AppLocalizations.of(context)!;
    final uploadState = ref.watch(uploadControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.editorTitle),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const UploadFlow(),
            const SizedBox(height: 16),
            Expanded(
              child: Row(
                children: const [
                  Expanded(child: TimelineEditor()),
                  SizedBox(width: 16),
                  Expanded(child: SubtitleEditor()),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Align(
              alignment: Alignment.centerRight,
              child: ElevatedButton.icon(
                key: const Key('open_export_dialog'),
                onPressed: uploadState.uploadId == null
                    ? null
                    : () {
                        ref.read(exportControllerProvider.notifier).reset();
                        showDialog<void>(
                          context: context,
                          builder: (context) => ExportDialog(uploadId: uploadState.uploadId!),
                        );
                      },
                icon: const Icon(Icons.outbox),
                label: Text(l10n.export),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
