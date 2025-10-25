import 'package:flutter/material.dart';

import '../../../data/models/timeline_models.dart';
import '../state/project_timeline_state.dart';
import 'metadata_overview_panel.dart';
import 'scene_suggestions_panel.dart';
import 'timeline_builder_panel.dart';

class ProjectTimelineWorkspace extends StatelessWidget {
  const ProjectTimelineWorkspace({
    super.key,
    required this.state,
    required this.projectId,
    required this.errorMessage,
    required this.searchController,
    required this.onSelectSource,
    required this.onToggleSuggestion,
    required this.onDropSuggestion,
    required this.onReorderClip,
    required this.onTrimClip,
    required this.onRemoveClip,
    required this.onMergeClip,
    required this.onSplitClip,
    required this.onAddTranscriptSegment,
    required this.onSearchTranscript,
    required this.onRefreshRequested,
  });

  final ProjectTimelineState state;
  final String projectId;
  final String? errorMessage;
  final TextEditingController searchController;
  final ValueChanged<SegmentSource> onSelectSource;
  final ValueChanged<String> onToggleSuggestion;
  final ValueChanged<String> onDropSuggestion;
  final void Function(int oldIndex, int newIndex) onReorderClip;
  final void Function(String clipId, Duration start, Duration end) onTrimClip;
  final ValueChanged<String> onRemoveClip;
  final ValueChanged<String> onMergeClip;
  final Future<void> Function(String clipId, Duration position) onSplitClip;
  final ValueChanged<String> onAddTranscriptSegment;
  final ValueChanged<String> onSearchTranscript;
  final VoidCallback onRefreshRequested;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final width = constraints.maxWidth;

          if (width >= 1200) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 320,
                  child: SizedBox(
                    height: 640,
                    child: SceneSuggestionsPanel(
                      state: state,
                      searchController: searchController,
                      onSourceChanged: onSelectSource,
                      onToggleSuggestion: onToggleSuggestion,
                      onAddTranscriptSegment: onAddTranscriptSegment,
                      onSearchTranscript: onSearchTranscript,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  flex: 5,
                  child: SizedBox(
                    height: 640,
                    child: TimelineBuilderPanel(
                      state: state,
                      errorMessage: errorMessage,
                      onDropSuggestion: onDropSuggestion,
                      onReorderClip: onReorderClip,
                      onTrimClip: onTrimClip,
                      onRemoveClip: onRemoveClip,
                      onMergeClip: onMergeClip,
                      onSplitClip: onSplitClip,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                SizedBox(
                  width: 320,
                  child: TimelineMetadataPanel(
                    metadata: state.metadata,
                    totalDuration: state.totalDuration,
                    hasUnsavedChanges: state.hasUnsavedChanges,
                    isSaving: state.isSaving,
                    onRefresh: onRefreshRequested,
                    isOverLimit: state.isOverMaxDuration,
                  ),
                ),
              ],
            );
          }

          if (width >= 800) {
            return Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 480,
                        child: SceneSuggestionsPanel(
                          state: state,
                          searchController: searchController,
                          onSourceChanged: onSelectSource,
                          onToggleSuggestion: onToggleSuggestion,
                          onAddTranscriptSegment: onAddTranscriptSegment,
                          onSearchTranscript: onSearchTranscript,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      flex: 2,
                      child: SizedBox(
                        height: 480,
                        child: TimelineBuilderPanel(
                          state: state,
                          errorMessage: errorMessage,
                          onDropSuggestion: onDropSuggestion,
                          onReorderClip: onReorderClip,
                          onTrimClip: onTrimClip,
                          onRemoveClip: onRemoveClip,
                          onMergeClip: onMergeClip,
                          onSplitClip: onSplitClip,
                        ),
                      ),
                    ),
                  ],
                  ),
                  const SizedBox(height: 16),
                  TimelineMetadataPanel(
                  metadata: state.metadata,
                  totalDuration: state.totalDuration,
                  hasUnsavedChanges: state.hasUnsavedChanges,
                  isSaving: state.isSaving,
                  onRefresh: onRefreshRequested,
                  isOverLimit: state.isOverMaxDuration,
                  ),

            );
          }

          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  height: 420,
                  child: SceneSuggestionsPanel(
                    state: state,
                    searchController: searchController,
                    onSourceChanged: onSelectSource,
                    onToggleSuggestion: onToggleSuggestion,
                    onAddTranscriptSegment: onAddTranscriptSegment,
                    onSearchTranscript: onSearchTranscript,
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  height: 420,
                  child: TimelineBuilderPanel(
                    state: state,
                    errorMessage: errorMessage,
                    onDropSuggestion: onDropSuggestion,
                    onReorderClip: onReorderClip,
                    onTrimClip: onTrimClip,
                    onRemoveClip: onRemoveClip,
                    onMergeClip: onMergeClip,
                    onSplitClip: onSplitClip,
                  ),
                ),
                const SizedBox(height: 16),
                TimelineMetadataPanel(
                  metadata: state.metadata.copyWith(projectId: projectId),
                  totalDuration: state.totalDuration,
                  hasUnsavedChanges: state.hasUnsavedChanges,
                  isSaving: state.isSaving,
                  onRefresh: onRefreshRequested,
                  isOverLimit: state.isOverMaxDuration,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
