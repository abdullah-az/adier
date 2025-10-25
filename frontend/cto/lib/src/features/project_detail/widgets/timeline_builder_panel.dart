import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../data/models/timeline_models.dart';
import '../state/project_timeline_state.dart';
import 'timeline_clip_tile.dart';
import 'split_clip_dialog.dart';

class TimelineBuilderPanel extends StatelessWidget {
  const TimelineBuilderPanel({
    super.key,
    required this.state,
    required this.errorMessage,
    required this.onDropSuggestion,
    required this.onReorderClip,
    required this.onTrimClip,
    required this.onRemoveClip,
    required this.onMergeClip,
    required this.onSplitClip,
  });

  final ProjectTimelineState state;
  final String? errorMessage;
  final ValueChanged<String> onDropSuggestion;
  final void Function(int oldIndex, int newIndex) onReorderClip;
  final void Function(String clipId, Duration start, Duration end) onTrimClip;
  final ValueChanged<String> onRemoveClip;
  final ValueChanged<String> onMergeClip;
  final Future<void> Function(String clipId, Duration position) onSplitClip;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    l10n.timelineBuilderTitle,
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                if (state.isSaving)
                  Row(
                    children: [
                      const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        l10n.timelineSaving,
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
              ],
            ),
            if (errorMessage != null) ...[
              const SizedBox(height: 12),
              DecoratedBox(
                decoration: BoxDecoration(
                  color: theme.colorScheme.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(Icons.warning,
                          color: theme.colorScheme.error, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          errorMessage!,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.error,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: 16),
            Expanded(
              child: DragTarget<SceneSuggestion>(
                onWillAccept: (_) => true,
                onAccept: (suggestion) => onDropSuggestion(suggestion.id),
                builder: (context, candidateData, rejectedData) {
                  final highlight = candidateData.isNotEmpty;
                  final borderColor = highlight
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outlineVariant;

                  if (state.timeline.isEmpty) {
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      decoration: BoxDecoration(
                        border: Border.all(color: borderColor, width: 2),
                        borderRadius: BorderRadius.circular(16),
                        color: highlight
                            ? theme.colorScheme.primary.withOpacity(0.05)
                            : theme.colorScheme.surfaceVariant.withOpacity(0.14),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        highlight
                            ? l10n.timelineDropHere
                            : l10n.timelineEmptyState,
                        style: theme.textTheme.titleMedium,
                        textAlign: TextAlign.center,
                      ),
                    );
                  }

                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    decoration: BoxDecoration(
                      border: Border.all(color: borderColor),
                      borderRadius: BorderRadius.circular(16),
                      color: highlight
                          ? theme.colorScheme.primary.withOpacity(0.05)
                          : null,
                    ),
                    padding: const EdgeInsets.all(8),
                    child: _TimelineList(
                      state: state,
                      onReorderClip: onReorderClip,
                      onTrimClip: onTrimClip,
                      onRemoveClip: onRemoveClip,
                      onMergeClip: onMergeClip,
                      onSplitClip: onSplitClip,
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

class _TimelineList extends StatelessWidget {
  const _TimelineList({
    required this.state,
    required this.onReorderClip,
    required this.onTrimClip,
    required this.onRemoveClip,
    required this.onMergeClip,
    required this.onSplitClip,
  });

  final ProjectTimelineState state;
  final void Function(int oldIndex, int newIndex) onReorderClip;
  final void Function(String clipId, Duration start, Duration end) onTrimClip;
  final ValueChanged<String> onRemoveClip;
  final ValueChanged<String> onMergeClip;
  final Future<void> Function(String clipId, Duration position) onSplitClip;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return ReorderableListView.builder(
      buildDefaultDragHandles: false,
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: state.timeline.length,
      proxyDecorator: (child, index, animation) {
        return AnimatedBuilder(
          animation: animation,
          builder: (context, _) {
            return Transform.scale(
              scale: Tween<double>(begin: 1, end: 1.03).evaluate(animation),
              child: Material(
                elevation: 6,
                borderRadius: BorderRadius.circular(12),
                child: child,
              ),
            );
          },
        );
      },
      onReorder: onReorderClip,
      itemBuilder: (context, index) {
        final clip = state.timeline[index];
        final pending = state.pendingClipIds.contains(clip.id);
        return Padding(
          key: ValueKey(clip.id),
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
          child: TimelineClipTile(
            clip: clip,
            isSaving: state.isSaving && pending,
            isPending: pending,
            onTrim: (start, end) => onTrimClip(clip.id, start, end),
            onRemove: () => onRemoveClip(clip.id),
            onMerge: () => onMergeClip(clip.id),
            onSplit: () async {
              final splitPoint = await SplitClipDialog.show(context, clip);
              if (splitPoint != null) {
                await onSplitClip(clip.id, splitPoint);
              }
            },
            dragHandle: ReorderableDragStartListener(
              index: index,
              child: Tooltip(
                message: l10n.timelineReorderTooltip,
                child: const Icon(Icons.drag_indicator),
              ),
            ),
          ),
        );
      },
    );
  }
}
