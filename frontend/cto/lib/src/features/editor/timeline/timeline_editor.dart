import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../core/utils/timeline_utils.dart';
import '../../../data/models/timeline_segment.dart';
import 'timeline_controller.dart';
import 'timeline_thumbnail.dart';

class TimelineEditor extends ConsumerWidget {
  const TimelineEditor({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final timelineState = ref.watch(timelineControllerProvider);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              l10n.timeline,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            timelineState.when(
              loading: () => const Expanded(
                child: Center(
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (error, __) => Expanded(
                child: Center(
                  child: Text(
                    l10n.timelineError,
                    key: const Key('timeline_error'),
                  ),
                ),
              ),
              data: (summary) {
                if (summary.segments.isEmpty) {
                  return Expanded(
                    child: Center(
                      child: Text(
                        l10n.timelineEmpty,
                        key: const Key('timeline_empty'),
                      ),
                    ),
                  );
                }

                return Expanded(
                  child: Column(
                    children: [
                      TimelineThumbnail(
                        segments: summary.segments,
                      ),
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          l10n.timelineTotalDuration(_formatDuration(summary.totalDuration)),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Expanded(
                        child: ListView.builder(
                          key: const Key('timeline_list'),
                          itemCount: summary.segments.length,
                          itemBuilder: (context, index) {
                            final segment = summary.segments[index];
                            return _TimelineTile(segment: segment);
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

class _TimelineTile extends StatelessWidget {
  const _TimelineTile({required this.segment});

  final TimelineSegment segment;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      key: Key('timeline_tile_${segment.id}'),
      leading: CircleAvatar(
        backgroundColor: segment.color ?? Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
        child: Text(
          segment.label.isNotEmpty ? segment.label[0].toUpperCase() : '?',
        ),
      ),
      title: Text(segment.label),
      subtitle: Text(
        '${segment.startMs}ms → ${segment.endMs}ms',
      ),
      trailing: Text(
        '${segment.duration.inSeconds}s',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    );
  }
}
