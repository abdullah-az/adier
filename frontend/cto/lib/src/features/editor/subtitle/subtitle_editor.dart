import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../l10n/app_localizations.dart';
import '../timeline/timeline_controller.dart';

class SubtitleEditor extends ConsumerWidget {
  const SubtitleEditor({super.key});

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
              l10n.subtitles,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Expanded(
              child: timelineState.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, __) => Center(
                  child: Text(
                    l10n.subtitleError,
                    key: const Key('subtitle_error'),
                  ),
                ),
                data: (summary) {
                  final cues = summary.cues;
                  if (cues.isEmpty) {
                    return Center(
                      child: Text(
                        l10n.subtitlesEmpty,
                        key: const Key('subtitle_empty'),
                      ),
                    );
                  }

                  return ListView.builder(
                    key: const Key('subtitle_list'),
                    itemCount: cues.length,
                    itemBuilder: (context, index) {
                      final cue = cues[index];
                      return ListTile(
                        key: Key('subtitle_tile_${cue.id}'),
                        leading: Text('#${index + 1}'),
                        title: Text(cue.text),
                        subtitle: Text('${cue.startMs}ms → ${cue.endMs}ms'),
                        trailing: Text('${cue.duration.inSeconds}s'),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
