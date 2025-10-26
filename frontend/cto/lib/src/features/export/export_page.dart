import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/utils/timeline_math.dart';
import '../timeline/timeline_controller.dart';
import 'export_dialog.dart';

class ExportPage extends ConsumerWidget {
  const ExportPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final timeline = ref.watch(timelineControllerProvider);
    final totalDuration = TimelineMath.totalDuration(timeline);
    final steps = [
      l10n.exportStepReview,
      l10n.exportStepQuality,
      l10n.exportStepSubtitles,
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.export),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.exportSummary(
                timeline.length,
                TimelineMath.formatDuration(totalDuration),
              ),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.separated(
                key: const Key('export_steps_list'),
                itemBuilder: (context, index) {
                  final step = steps[index];
                  return ListTile(
                    leading: CircleAvatar(
                      child: Text('${index + 1}'),
                    ),
                    title: Text(step),
                  );
                },
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemCount: steps.length,
              ),
            ),
            FilledButton.icon(
              key: const Key('export_page_open_dialog'),
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
              icon: const Icon(Icons.ios_share),
              label: Text(l10n.exportProjectAction),
            ),
          ],
        ),
      ),
    );
  }
}
