import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../core/utils/duration_formatter.dart';
import '../../../data/models/timeline_models.dart';
import 'clip_score_indicator.dart';

class TimelineClipTile extends StatefulWidget {
  const TimelineClipTile({
    super.key,
    required this.clip,
    required this.isSaving,
    required this.isPending,
    required this.onTrim,
    required this.onRemove,
    required this.onMerge,
    required this.onSplit,
    required this.dragHandle,
  });

  final TimelineClip clip;
  final bool isSaving;
  final bool isPending;
  final void Function(Duration start, Duration end) onTrim;
  final VoidCallback onRemove;
  final VoidCallback onMerge;
  final VoidCallback onSplit;
  final Widget dragHandle;

  @override
  State<TimelineClipTile> createState() => _TimelineClipTileState();
}

class _TimelineClipTileState extends State<TimelineClipTile> {
  late RangeValues _rangeValues;
  late double _min;
  late double _max;

  @override
  void initState() {
    super.initState();
    _syncFromClip();
  }

  @override
  void didUpdateWidget(TimelineClipTile oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.clip.id != widget.clip.id ||
        oldWidget.clip.start != widget.clip.start ||
        oldWidget.clip.end != widget.clip.end ||
        oldWidget.clip.originalStart != widget.clip.originalStart ||
        oldWidget.clip.originalEnd != widget.clip.originalEnd) {
      _syncFromClip();
    }
  }

  void _syncFromClip() {
    _min = widget.clip.originalStart.inMilliseconds.toDouble();
    _max = widget.clip.originalEnd.inMilliseconds.toDouble();
    if (_max <= _min) {
      _max = widget.clip.end.inMilliseconds.toDouble();
      _min = widget.clip.start.inMilliseconds.toDouble();
    }
    final start = widget.clip.start.inMilliseconds.toDouble().clamp(_min, _max);
    final end = widget.clip.end.inMilliseconds.toDouble().clamp(_min, _max);
    _rangeValues = RangeValues(start, end);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final clip = widget.clip;
    final theme = Theme.of(context);
    final backgroundColor = widget.isPending
        ? theme.colorScheme.primary.withOpacity(0.06)
        : theme.colorScheme.surfaceVariant.withOpacity(0.12);
    final borderColor = widget.isPending
        ? theme.colorScheme.primary
        : theme.colorScheme.outlineVariant;

    final showSlider = _max > _min;
    final durationText = DurationFormatter.format(clip.duration);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeInOut,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor, width: widget.isPending ? 2 : 1),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      clip.name,
                      style: theme.textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Chip(
                          label: Text(_sourceLabel(l10n, clip.source)),
                          backgroundColor: theme.colorScheme.secondaryContainer,
                          labelStyle: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSecondaryContainer,
                          ),
                          visualDensity: VisualDensity.compact,
                        ),
                        Text(
                          l10n.timelineDurationLabel(durationText),
                          style: theme.textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              widget.dragHandle,
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              ClipScoreIndicator(
                label: l10n.timelineQualityLabel,
                value: clip.qualityScore,
                icon: Icons.auto_awesome,
              ),
              ClipScoreIndicator(
                label: l10n.timelineConfidenceLabel,
                value: clip.confidence,
                icon: Icons.assessment,
              ),
              if (clip.transcriptPreview != null &&
                  clip.transcriptPreview!.trim().isNotEmpty)
                Chip(
                  avatar: const Icon(Icons.notes, size: 16),
                  label: Text(
                    clip.transcriptPreview!.trim(),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          if (showSlider)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.timelineTrimLabel(
                    DurationFormatter.format(
                      Duration(milliseconds: _rangeValues.start.round()),
                    ),
                    DurationFormatter.format(
                      Duration(milliseconds: _rangeValues.end.round()),
                    ),
                  ),
                  style: theme.textTheme.bodySmall,
                ),
                SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    showValueIndicator: ShowValueIndicator.never,
                  ),
                  child: RangeSlider(
                    values: _rangeValues,
                    min: _min,
                    max: _max,
                    divisions: ((_max - _min) / 1000).clamp(1, 600).round(),
                    labels: RangeLabels(
                      DurationFormatter.format(
                        Duration(milliseconds: _rangeValues.start.round()),
                      ),
                      DurationFormatter.format(
                        Duration(milliseconds: _rangeValues.end.round()),
                      ),
                    ),
                    onChanged: (values) {
                      setState(() {
                        _rangeValues = values;
                      });
                    },
                    onChangeEnd: (values) {
                      final start =
                          Duration(milliseconds: values.start.round());
                      final end = Duration(milliseconds: values.end.round());
                      widget.onTrim(start, end);
                    },
                  ),
                ),
              ],
            )
          else
            Text(
              l10n.timelineTrimUnavailable,
              style: theme.textTheme.bodySmall,
            ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              IconButton(
                icon: const Icon(Icons.call_split),
                tooltip: l10n.timelineSplitClip,
                onPressed: widget.onSplit,
              ),
              IconButton(
                icon: const Icon(Icons.merge_type),
                tooltip: l10n.timelineMergeClip,
                onPressed: widget.onMerge,
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline),
                tooltip: l10n.timelineRemoveClip,
                onPressed: widget.onRemove,
              ),
            ],
          ),
          if (widget.isSaving)
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  l10n.timelineSaving,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.primary,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  String _sourceLabel(AppLocalizations l10n, ClipSourceType source) {
    switch (source) {
      case ClipSourceType.ai:
        return l10n.timelineSourceAi;
      case ClipSourceType.transcript:
        return l10n.timelineSourceTranscript;
      case ClipSourceType.manual:
        return l10n.timelineSourceManual;
    }
  }
}
