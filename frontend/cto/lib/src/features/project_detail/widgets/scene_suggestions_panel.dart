import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../core/utils/duration_formatter.dart';
import '../../../data/models/timeline_models.dart';
import '../state/project_timeline_state.dart';
import 'clip_score_indicator.dart';

class SceneSuggestionsPanel extends StatelessWidget {
  const SceneSuggestionsPanel({
    super.key,
    required this.state,
    required this.searchController,
    required this.onSourceChanged,
    required this.onToggleSuggestion,
    required this.onAddTranscriptSegment,
    required this.onSearchTranscript,
  });

  final ProjectTimelineState state;
  final TextEditingController searchController;
  final ValueChanged<SegmentSource> onSourceChanged;
  final ValueChanged<String> onToggleSuggestion;
  final ValueChanged<String> onAddTranscriptSegment;
  final ValueChanged<String> onSearchTranscript;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final isTranscript = state.activeSource == SegmentSource.transcriptSearch;

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
                    l10n.timelineSuggestionsTitle,
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                if (state.isSearchingTranscript)
                  const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            SegmentedButton<SegmentSource>(
              segments: <ButtonSegment<SegmentSource>>[
                ButtonSegment<SegmentSource>(
                  value: SegmentSource.aiSuggestions,
                  label: Text(l10n.timelineSegmentSourceAi),
                  icon: const Icon(Icons.auto_awesome),
                ),
                ButtonSegment<SegmentSource>(
                  value: SegmentSource.transcriptSearch,
                  label: Text(l10n.timelineSegmentSourceTranscript),
                  icon: const Icon(Icons.search),
                ),
              ],
              selected: <SegmentSource>{state.activeSource},
              onSelectionChanged: (selection) {
                if (selection.isNotEmpty) {
                  onSourceChanged(selection.first);
                }
              },
            ),
            const SizedBox(height: 16),
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 250),
                switchInCurve: Curves.easeIn,
                switchOutCurve: Curves.easeOut,
                child: isTranscript
                    ? _TranscriptSearchView(
                        key: const ValueKey('transcript'),
                        state: state,
                        controller: searchController,
                        onSearch: onSearchTranscript,
                        onAdd: onAddTranscriptSegment,
                      )
                    : _AiSuggestionsList(
                        key: const ValueKey('ai'),
                        suggestions: state.suggestions,
                        onToggleSuggestion: onToggleSuggestion,
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AiSuggestionsList extends StatelessWidget {
  const _AiSuggestionsList({
    super.key,
    required this.suggestions,
    required this.onToggleSuggestion,
  });

  final List<SceneSuggestion> suggestions;
  final ValueChanged<String> onToggleSuggestion;

  @override
  Widget build(BuildContext context) {
    if (suggestions.isEmpty) {
      return Center(
        child: Text(AppLocalizations.of(context)!.timelineNoSuggestions),
      );
    }
    return ListView.separated(
      physics: const BouncingScrollPhysics(),
      itemCount: suggestions.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final suggestion = suggestions[index];
        return _SceneSuggestionCard(
          suggestion: suggestion,
          onToggle: () => onToggleSuggestion(suggestion.id),
        );
      },
    );
  }
}

class _SceneSuggestionCard extends StatelessWidget {
  const _SceneSuggestionCard({
    required this.suggestion,
    required this.onToggle,
  });

  final SceneSuggestion suggestion;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final isSelected = suggestion.isSelected;
    final duration = suggestion.end - suggestion.start;
    final borderColor = isSelected
        ? theme.colorScheme.primary
        : theme.colorScheme.outlineVariant;
    final background = isSelected
        ? theme.colorScheme.primary.withOpacity(0.08)
        : theme.colorScheme.surface;

    final card = DecoratedBox(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
        boxShadow: [
          if (isSelected)
            BoxShadow(
              color: theme.colorScheme.primary.withOpacity(0.2),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onToggle,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      suggestion.title,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Icon(
                    isSelected ? Icons.check_circle : Icons.movie,
                    color: isSelected
                        ? theme.colorScheme.primary
                        : theme.colorScheme.secondary,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                suggestion.description,
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  Chip(
                    avatar: const Icon(Icons.schedule, size: 16),
                    label: Text(
                      DurationFormatter.formatRange(
                        suggestion.start,
                        suggestion.end,
                      ),
                    ),
                  ),
                  ClipScoreIndicator(
                    label: l10n.timelineQualityLabel,
                    value: suggestion.qualityScore,
                    icon: Icons.auto_fix_high,
                  ),
                  ClipScoreIndicator(
                    label: l10n.timelineConfidenceLabel,
                    value: suggestion.confidence,
                    icon: Icons.verified,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: isSelected
                    ? OutlinedButton.icon(
                        icon: const Icon(Icons.remove_circle_outline),
                        label: Text(l10n.timelineAiSuggestionRemove),
                        onPressed: onToggle,
                      )
                    : FilledButton.icon(
                        icon: const Icon(Icons.download),
                        label: Text(l10n.timelineAiSuggestionAdd),
                        onPressed: onToggle,
                      ),
              ),
            ],
          ),
        ),
      ),
    );

    return LongPressDraggable<SceneSuggestion>(
      data: suggestion,
      feedback: Material(
        borderRadius: BorderRadius.circular(12),
        elevation: 6,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 280),
          child: card,
        ),
      ),
      childWhenDragging: Opacity(opacity: 0.5, child: card),
      child: card,
    );
  }
}

class _TranscriptSearchView extends StatelessWidget {
  const _TranscriptSearchView({
    super.key,
    required this.state,
    required this.controller,
    required this.onSearch,
    required this.onAdd,
  });

  final ProjectTimelineState state;
  final TextEditingController controller;
  final ValueChanged<String> onSearch;
  final ValueChanged<String> onAdd;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final showResults = state.transcriptResults.isNotEmpty;

    return Column(
      children: [
        TextField(
          controller: controller,
          textInputAction: TextInputAction.search,
          onSubmitted: onSearch,
          decoration: InputDecoration(
            labelText: l10n.timelineTranscriptSearchPlaceholder,
            suffixIcon: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (controller.text.isNotEmpty)
                  IconButton(
                    tooltip: MaterialLocalizations.of(context).deleteButtonTooltip,
                    icon: const Icon(Icons.clear),
                    onPressed: () {
                      controller.clear();
                      onSearch('');
                    },
                  ),
                IconButton(
                  icon: const Icon(Icons.search),
                  tooltip: l10n.timelineTranscriptSearchButton,
                  onPressed: () => onSearch(controller.text),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: showResults
              ? ListView.separated(
                  itemCount: state.transcriptResults.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final segment = state.transcriptResults[index];
                    return _TranscriptResultTile(
                      segment: segment,
                      onAdd: () => onAdd(segment.id),
                    );
                  },
                )
              : Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      controller.text.isEmpty
                          ? l10n.timelineTranscriptSearchEmpty
                          : l10n.timelineTranscriptNoResults(controller.text),
                      style: theme.textTheme.bodyMedium,
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
        ),
      ],
    );
  }
}

class _TranscriptResultTile extends StatelessWidget {
  const _TranscriptResultTile({
    required this.segment,
    required this.onAdd,
  });

  final TranscriptSegment segment;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              segment.text.trim(),
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                Chip(
                  avatar: const Icon(Icons.schedule, size: 16),
                  label: Text(
                    DurationFormatter.formatRange(
                      segment.start,
                      segment.end,
                    ),
                  ),
                ),
                ClipScoreIndicator(
                  label: l10n.timelineConfidenceLabel,
                  value: segment.confidence,
                  icon: Icons.verified_user,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: FilledButton.icon(
                icon: const Icon(Icons.add_circle_outline),
                label: Text(l10n.timelineTranscriptAdd),
                onPressed: onAdd,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
