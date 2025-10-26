import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/constants/app_constants.dart';
import 'upload_controller.dart';

class UploadPage extends ConsumerWidget {
  const UploadPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final uploads = ref.watch(uploadControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.upload),
      ),
      floatingActionButton: FloatingActionButton(
        key: const Key('upload_add_button'),
        tooltip: l10n.addMedia,
        onPressed: () => ref
            .read(uploadControllerProvider.notifier)
            .addMockUpload(),
        child: const Icon(Icons.add),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.uploadDescription,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: uploads.isEmpty
                  ? Center(
                      child: Text(
                        l10n.uploadEmpty,
                        key: const Key('upload_empty_state'),
                        textAlign: TextAlign.center,
                      ),
                    )
                  : ListView.builder(
                      key: const Key('upload_list'),
                      itemCount: uploads.length,
                      itemBuilder: (context, index) {
                        final item = uploads[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          child: ListTile(
                            leading: Icon(
                              item.completed
                                  ? Icons.check_circle
                                  : Icons.cloud_upload_outlined,
                              color: item.completed
                                  ? Colors.green
                                  : Theme.of(context).colorScheme.primary,
                            ),
                            title: Text(item.name),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(l10n.uploadDuration(
                                  item.duration.inSeconds,
                                )),
                                const SizedBox(height: 4),
                                LinearProgressIndicator(
                                  value: item.progress,
                                ),
                              ],
                            ),
                            trailing: IconButton(
                              key: Key('upload_progress_${item.id}'),
                              icon: const Icon(Icons.play_arrow),
                              tooltip: l10n.advanceUpload,
                              onPressed: () => ref
                                  .read(uploadControllerProvider.notifier)
                                  .incrementProgress(item.id),
                            ),
                          ),
                        );
                      },
                    ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              key: const Key('upload_go_to_timeline'),
              onPressed: uploads.isEmpty
                  ? null
                  : () => context.push(AppConstants.timelineRoute),
              icon: const Icon(Icons.timeline),
              label: Text(l10n.goToTimeline),
            ),
          ],
        ),
      ),
    );
  }
}
