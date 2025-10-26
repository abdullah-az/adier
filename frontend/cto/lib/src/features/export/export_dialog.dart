import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';

class ExportDialog extends StatefulWidget {
  const ExportDialog({super.key});

  @override
  State<ExportDialog> createState() => _ExportDialogState();
}

class _ExportDialogState extends State<ExportDialog> {
  String _format = 'mp4';
  String _resolution = '1080p';
  bool _includeSubtitles = true;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return AlertDialog(
      key: const Key('export_dialog'),
      title: Text(l10n.exportProjectTitle),
      content: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              key: const Key('export_format_dropdown'),
              decoration: InputDecoration(labelText: l10n.exportFormat),
              value: _format,
              items: const [
                DropdownMenuItem(value: 'mp4', child: Text('MP4')),
                DropdownMenuItem(value: 'mov', child: Text('MOV')),
                DropdownMenuItem(value: 'gif', child: Text('GIF')),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _format = value;
                  });
                }
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: const Key('export_resolution_dropdown'),
              decoration: InputDecoration(labelText: l10n.exportResolution),
              value: _resolution,
              items: const [
                DropdownMenuItem(value: '720p', child: Text('720p')),
                DropdownMenuItem(value: '1080p', child: Text('1080p')),
                DropdownMenuItem(value: '4k', child: Text('4K')),
              ],
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _resolution = value;
                  });
                }
              },
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              key: const Key('export_subtitles_switch'),
              title: Text(l10n.exportIncludeSubtitles),
              value: _includeSubtitles,
              onChanged: (value) {
                setState(() {
                  _includeSubtitles = value;
                });
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          key: const Key('export_cancel_button'),
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(l10n.cancel),
        ),
        FilledButton(
          key: const Key('export_confirm_button'),
          onPressed: () {
            Navigator.of(context).pop(true);
          },
          child: Text(l10n.export),
        ),
      ],
    );
  }
}
