import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/constants/app_constants.dart';
import '../../core/utils/timeline_math.dart';
import '../export/export_dialog.dart';
import 'models/timeline_segment.dart';
import 'timeline_controller.dart';

class TimelineEditorPage extends ConsumerWidget {
  const TimelineEditorPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final segments = ref.watch(timelineControllerProvider);
    final total = TimelineMath.totalDuration(segments);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.timelineEditor),
        actions: [
          IconButton(
            key: const Key('timeline_add_segment'),
            icon: const Icon(Icons.add),
            tooltip: l10n.addSegment,
            onPressed: () {
              ref
                  .read(timelineControllerProvider.notifier)
                  .addSegment(const Duration(seconds: 3));
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        key: const Key('timeline_export_button'),
        tooltip: l10n.export,
        onPressed: () async {
          final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => const ExportDialog(),
          );
          if (confirmed == true && context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(l10n.exportSuccess)),
            );
          }
        },
        child: const Icon(Icons.ios_share),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.timelineSummary(
                    segments.length,
                    TimelineMath.formatDuration(total),
                  ),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  l10n.timelineHint,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Expanded(
            child: ReorderableListView.builder(
              key: const Key('timeline_list'),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: segments.length,
              onReorder: (oldIndex, newIndex) {
                ref
                    .read(timelineControllerProvider.notifier)
                    .reorderSegments(oldIndex, newIndex);
              },
              itemBuilder: (context, index) {
                final segment = segments[index];
                final start = TimelineMath.startForSegment(segments, segment.id);
                final progress = TimelineMath.progressAt(start, total);
                final normalized = TimelineMath.progressAt(
                  segment.duration,
                  total,
                );
                return Card(
                  key: ValueKey(segment.id),
                  margin: const EdgeInsets.symmetric(vertical: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text('${index + 1}'),
                    ),
                    title: Text(segment.label),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(l10n.segmentDuration(
                          TimelineMath.formatDuration(segment.duration),
                          (normalized * 100).toStringAsFixed(0),
                        )),
                        Text(l10n.segmentStart(
                          TimelineMath.formatDuration(start),
                          (progress * 100).toStringAsFixed(0),
                        )),
                      ],
                    ),
                    trailing: const Icon(Icons.drag_indicator),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: FilledButton.icon(
                key: const Key('open_subtitle_editor'),
                onPressed: () => context.push(AppConstants.subtitlesRoute),
                icon: const Icon(Icons.subtitles_outlined),
                label: Text(l10n.openSubtitles),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
