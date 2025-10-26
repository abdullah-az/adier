import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/utils/timeline_math.dart';
import 'subtitle_controller.dart';

class SubtitleEditorPage extends ConsumerStatefulWidget {
  const SubtitleEditorPage({super.key});

  @override
  ConsumerState<SubtitleEditorPage> createState() => _SubtitleEditorPageState();
}

class _SubtitleEditorPageState extends ConsumerState<SubtitleEditorPage> {
  late final TextEditingController _startController;
  late final TextEditingController _endController;
  late final TextEditingController _textController;

  @override
  void initState() {
    super.initState();
    _startController = TextEditingController();
    _endController = TextEditingController();
    _textController = TextEditingController();
  }

  @override
  void dispose() {
    _startController.dispose();
    _endController.dispose();
    _textController.dispose();
    super.dispose();
  }

  void _addSubtitle(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final startValue = double.tryParse(_startController.text);
    final endValue = double.tryParse(_endController.text);
    final text = _textController.text.trim();

    if (startValue == null || endValue == null || endValue <= startValue || text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.subtitleValidationError)),
      );
      return;
    }

    ref.read(subtitleControllerProvider.notifier).addEntry(
          start: Duration(milliseconds: (startValue * 1000).round()),
          end: Duration(milliseconds: (endValue * 1000).round()),
          text: text,
        );

    _startController.clear();
    _endController.clear();
    _textController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final subtitles = ref.watch(subtitleControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.subtitleEditor),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.subtitleEditorDescription,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    key: const Key('subtitle_start_field'),
                    controller: _startController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: l10n.subtitleStartLabel,
                      helperText: l10n.subtitleTimeHelper,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    key: const Key('subtitle_end_field'),
                    controller: _endController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: l10n.subtitleEndLabel,
                      helperText: l10n.subtitleTimeHelper,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('subtitle_text_field'),
              controller: _textController,
              decoration: InputDecoration(
                labelText: l10n.subtitleTextLabel,
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              key: const Key('subtitle_add_button'),
              onPressed: () => _addSubtitle(context),
              icon: const Icon(Icons.add),
              label: Text(l10n.addSubtitle),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                key: const Key('subtitle_list'),
                itemCount: subtitles.length,
                itemBuilder: (context, index) {
                  final subtitle = subtitles[index];
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        child: Text('${index + 1}'),
                      ),
                      title: Text(subtitle.text),
                      subtitle: Text(
                        l10n.subtitleTimeRange(
                          TimelineMath.formatDuration(subtitle.start),
                          TimelineMath.formatDuration(subtitle.end),
                        ),
                      ),
                    ),
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
