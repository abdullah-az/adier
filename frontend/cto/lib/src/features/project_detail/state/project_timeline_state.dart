import 'dart:collection';

import 'package:flutter/foundation.dart';

import '../../../data/models/timeline_models.dart';

const _unset = Object();

class TimelineErrorCodes {
  static const String maxDurationExceeded = 'max_duration_exceeded';
  static const String clipOverlap = 'clip_overlap_error';
  static const String clipTooShort = 'clip_too_short';
  static const String mergeIncompatible = 'merge_incompatible';
  static const String invalidSplitPoint = 'invalid_split_point';
  static const String saveFailed = 'save_failed';
  static const String loadFailed = 'timeline_load_failed';
  static const String transcriptSearchFailed = 'transcript_search_failed';
}

enum SegmentSource {
  aiSuggestions,
  transcriptSearch,
}

@immutable
class ProjectTimelineState {
  const ProjectTimelineState({
    required List<TimelineClip> timeline,
    required List<SceneSuggestion> suggestions,
    required this.metadata,
    List<TranscriptSegment> transcriptResults = const <TranscriptSegment>[],
    this.activeSource = SegmentSource.aiSuggestions,
    this.isLoading = false,
    this.isSaving = false,
    this.isSearchingTranscript = false,
    this.hasUnsavedChanges = false,
    this.searchQuery = '',
    this.errorMessage,
    Set<String> pendingClipIds = const <String>{},
  })  : _timeline = List<TimelineClip>.unmodifiable(timeline),
        _suggestions = List<SceneSuggestion>.unmodifiable(suggestions),
        _transcriptResults =
            List<TranscriptSegment>.unmodifiable(transcriptResults),
        _pendingClipIds = Set<String>.unmodifiable(pendingClipIds);

  factory ProjectTimelineState.initial(ProjectTimelinePayload payload) {
    return ProjectTimelineState(
      timeline: payload.timeline,
      suggestions: payload.suggestions,
      metadata: payload.metadata,
    );
  }

  factory ProjectTimelineState.loading() {
    return ProjectTimelineState(
      timeline: const <TimelineClip>[],
      suggestions: const <SceneSuggestion>[],
      metadata: ProjectMetadata(
        projectId: '',
        title: 'Loading',
        description: '',
        maxDuration: Duration.zero,
        currentDuration: Duration.zero,
        clipCount: 0,
      ),
      isLoading: true,
    );
  }

  final List<TimelineClip> _timeline;
  final List<SceneSuggestion> _suggestions;
  final List<TranscriptSegment> _transcriptResults;
  final Set<String> _pendingClipIds;

  List<TimelineClip> get timeline => UnmodifiableListView(_timeline);
  List<SceneSuggestion> get suggestions => UnmodifiableListView(_suggestions);
  List<TranscriptSegment> get transcriptResults =>
      UnmodifiableListView(_transcriptResults);
  Set<String> get pendingClipIds => UnmodifiableSetView(_pendingClipIds);

  final ProjectMetadata metadata;
  final SegmentSource activeSource;
  final bool isLoading;
  final bool isSaving;
  final bool isSearchingTranscript;
  final bool hasUnsavedChanges;
  final String searchQuery;
  final String? errorMessage;

  Duration get totalDuration => _timeline.fold<Duration>(
        Duration.zero,
        (sum, clip) => sum + clip.duration,
      );

  bool get isOverMaxDuration => metadata.maxDuration > Duration.zero
      ? totalDuration > metadata.maxDuration
      : false;

  double get durationProgress => metadata.maxDuration.inMilliseconds <= 0
      ? 0
      : totalDuration.inMilliseconds /
          metadata.maxDuration.inMilliseconds;

  ProjectTimelineState copyWith({
    List<TimelineClip>? timeline,
    List<SceneSuggestion>? suggestions,
    ProjectMetadata? metadata,
    List<TranscriptSegment>? transcriptResults,
    SegmentSource? activeSource,
    bool? isLoading,
    bool? isSaving,
    bool? isSearchingTranscript,
    bool? hasUnsavedChanges,
    String? searchQuery,
    Object? errorMessage = _unset,
    Set<String>? pendingClipIds,
  }) {
    return ProjectTimelineState(
      timeline: timeline ?? _timeline,
      suggestions: suggestions ?? _suggestions,
      metadata: metadata ?? this.metadata,
      transcriptResults: transcriptResults ?? _transcriptResults,
      activeSource: activeSource ?? this.activeSource,
      isLoading: isLoading ?? this.isLoading,
      isSaving: isSaving ?? this.isSaving,
      isSearchingTranscript: isSearchingTranscript ?? this.isSearchingTranscript,
      hasUnsavedChanges: hasUnsavedChanges ?? this.hasUnsavedChanges,
      searchQuery: searchQuery ?? this.searchQuery,
      errorMessage: errorMessage == _unset
          ? this.errorMessage
          : errorMessage as String?,
      pendingClipIds: pendingClipIds ?? _pendingClipIds,
    );
  }

  ProjectTimelineState updateTimeline(List<TimelineClip> timeline) {
    return copyWith(
      timeline: List<TimelineClip>.unmodifiable(timeline),
    );
  }

  ProjectTimelineState updateSuggestions(List<SceneSuggestion> suggestions) {
    return copyWith(
      suggestions: List<SceneSuggestion>.unmodifiable(suggestions),
    );
  }

  ProjectTimelineState updateTranscriptResults(
    List<TranscriptSegment> results,
  ) {
    return copyWith(
      transcriptResults: List<TranscriptSegment>.unmodifiable(results),
    );
  }

  ProjectTimelineState clearError() {
    return copyWith(errorMessage: null);
  }
}
