import 'dart:math';

import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../core/utils/duration_formatter.dart';
import '../../../data/models/timeline_models.dart';

class SplitClipDialog extends StatefulWidget {
  const SplitClipDialog({super.key, required this.clip});

  final TimelineClip clip;

  static Future<Duration?> show(
    BuildContext context,
    TimelineClip clip,
  ) {
    return showDialog<Duration>(
      context: context,
      builder: (context) => SplitClipDialog(clip: clip),
    );
  }

  @override
  State<SplitClipDialog> createState() => _SplitClipDialogState();
}

class _SplitClipDialogState extends State<SplitClipDialog> {
  late double _currentValue;

  @override
  void initState() {
    super.initState();
    final clip = widget.clip;
    final startMs = clip.start.inMilliseconds;
    final endMs = clip.end.inMilliseconds;
    _currentValue = (startMs + (endMs - startMs) / 2).toDouble();
  }

  @override
  Widget build(BuildContext context) {
    final clip = widget.clip;
    final l10n = AppLocalizations.of(context)!;
    final startMs = clip.start.inMilliseconds.toDouble();
    final endMs = clip.end.inMilliseconds.toDouble();
    final divisions = max(1, min(240, clip.duration.inSeconds));

    return AlertDialog(
      title: Text(l10n.timelineSplitClip),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            l10n.timelineSplitInstruction(
              DurationFormatter.format(clip.start),
              DurationFormatter.format(clip.end),
            ),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Slider(
            value: _currentValue.clamp(startMs, endMs),
            min: startMs,
            max: endMs,
            divisions: divisions,
            onChanged: (value) {
              setState(() {
                _currentValue = value;
              });
            },
          ),
          const SizedBox(height: 8),
          Text(
            l10n.timelineSplitSelected(
              DurationFormatter.format(
                Duration(milliseconds: _currentValue.round()),
              ),
            ),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l10n.timelineSplitCancel),
        ),
        FilledButton(
          onPressed: () {
            final duration = Duration(milliseconds: _currentValue.round());
            Navigator.of(context).pop(duration);
          },
          child: Text(l10n.timelineSplitConfirm),
        ),
      ],
    );
  }
}
