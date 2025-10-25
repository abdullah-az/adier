import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/timeline_models.dart';
import '../../../data/providers/timeline_provider.dart';
import '../../../data/repositories/timeline_repository.dart';
import '../state/project_timeline_state.dart';

final projectTimelineControllerProvider =
    AutoDisposeAsyncNotifierProviderFamily<ProjectTimelineController,
        ProjectTimelineState, String>(ProjectTimelineController.new);

class ProjectTimelineController
    extends AutoDisposeAsyncNotifier<ProjectTimelineState> {
  ProjectTimelineController() : _random = Random();

  late final TimelineRepository _repository;
  late String _projectId;
  final Random _random;

  static const Duration _minClipDuration = Duration(seconds: 2);

  @override
  Future<ProjectTimelineState> build(String projectId) async {
    _repository = ref.read(timelineRepositoryProvider);
    _projectId = projectId;
    final payload = await _repository.fetchProjectTimeline(projectId);
    return ProjectTimelineState.initial(payload);
  }

  void setActiveSource(SegmentSource source) {
    final current = state.valueOrNull;
    if (current == null || current.activeSource == source) {
      return;
    }
    state = AsyncData(current.copyWith(activeSource: source, errorMessage: null));
  }

  Future<void> refresh() async {
    final current = state.valueOrNull;
    if (current != null) {
      state = AsyncData(current.copyWith(isLoading: true));
    } else {
      state = const AsyncLoading();
    }
    try {
      final payload = await _repository.fetchProjectTimeline(_projectId);
      state = AsyncData(ProjectTimelineState.initial(payload));
    } on TimelineRepositoryException catch (error) {
      if (current != null) {
        state = AsyncData(
          current.copyWith(
            isLoading: false,
            errorMessage: TimelineErrorCodes.loadFailed,
          ),
        );
      } else {
        state = AsyncError(error, StackTrace.current);
      }
    } catch (error, stack) {
      if (current != null) {
        state = AsyncData(
          current.copyWith(
            isLoading: false,
            errorMessage: TimelineErrorCodes.loadFailed,
          ),
        );
      } else {
        state = AsyncError(error, stack);
      }
    }
  }

  Future<void> toggleSuggestionSelection(String suggestionId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final suggestionIndex =
        current.suggestions.indexWhere((s) => s.id == suggestionId);
    if (suggestionIndex == -1) {
      return;
    }

    final suggestion = current.suggestions[suggestionIndex];
    if (suggestion.isSelected && suggestion.attachedClipId != null) {
      await removeClip(suggestion.attachedClipId!);
      return;
    }

    await addSuggestionToTimeline(suggestionId);
  }

  Future<void> addSuggestionToTimeline(String suggestionId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final suggestionIndex =
        current.suggestions.indexWhere((s) => s.id == suggestionId);
    if (suggestionIndex == -1) {
      return;
    }

    final suggestion = current.suggestions[suggestionIndex];
    if (suggestion.isSelected) {
      return;
    }

    var newClip = suggestion.toTimelineClip(
      projectId: _projectId,
      clipId: _generateClipId(),
    );

    if (!_isClipLongEnough(newClip)) {
      _emitError(current, TimelineErrorCodes.clipTooShort);
      return;
    }

    if (_hasOverlap(current.timeline, newClip)) {
      _emitError(current, TimelineErrorCodes.clipOverlap);
      return;
    }

    if (current.metadata.maxDuration > Duration.zero) {
      final projected = current.totalDuration + newClip.duration;
      if (projected > current.metadata.maxDuration) {
        _emitError(current, TimelineErrorCodes.maxDurationExceeded);
        return;
      }
    }

    final newTimeline = List<TimelineClip>.from(current.timeline)..add(newClip);
    final updatedSuggestions = current.suggestions.map((scene) {
      if (scene.id == suggestion.id) {
        return scene.copyWith(attachedClipId: newClip.id);
      }
      return scene;
    }).toList();

    final updatedMetadata = _recalculateMetadata(
      current.metadata,
      newTimeline,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      suggestions: updatedSuggestions,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
      pendingClipIds: {
        ...current.pendingClipIds,
        newClip.id,
      },
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> removeClip(String clipId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final index = current.timeline.indexWhere((clip) => clip.id == clipId);
    if (index == -1) {
      return;
    }

    final newTimeline = List<TimelineClip>.from(current.timeline)
      ..removeAt(index);

    final updatedSuggestions = current.suggestions
        .map((scene) => scene.attachedClipId == clipId
            ? scene.copyWith(attachedClipId: null)
            : scene)
        .toList();

    final updatedMetadata = _recalculateMetadata(
      current.metadata,
      newTimeline,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      suggestions: updatedSuggestions,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> reorderClip(int oldIndex, int newIndex) async {
    final current = state.valueOrNull;
    if (current == null || oldIndex == newIndex) {
      return;
    }
    if (oldIndex < 0 || oldIndex >= current.timeline.length) {
      return;
    }

    var targetIndex = newIndex;
    if (targetIndex > oldIndex) {
      targetIndex -= 1;
    }
    if (targetIndex < 0 || targetIndex >= current.timeline.length) {
      return;
    }

    final newTimeline = List<TimelineClip>.from(current.timeline);
    final item = newTimeline.removeAt(oldIndex);
    newTimeline.insert(targetIndex, item);

    final updatedMetadata = _recalculateMetadata(
      current.metadata,
      newTimeline,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> trimClip(
    String clipId,
    Duration newStart,
    Duration newEnd,
  ) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final index = current.timeline.indexWhere((clip) => clip.id == clipId);
    if (index == -1) {
      return;
    }

    final clip = current.timeline[index];
    var trimmed = clip.trim(newStart, newEnd);
    if (!_isClipLongEnough(trimmed)) {
      trimmed = trimmed.copyWith(end: trimmed.start + _minClipDuration);
    }

    if (_hasOverlap(current.timeline, trimmed, excludeClipId: clipId)) {
      _emitError(current, TimelineErrorCodes.clipOverlap);
      return;
    }

    final newTimeline = List<TimelineClip>.from(current.timeline)
      ..[index] = trimmed;

    final updatedMetadata = _recalculateMetadata(
      current.metadata,
      newTimeline,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
      pendingClipIds: {
        ...current.pendingClipIds,
        clipId,
      },
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> mergeClipWithNext(String clipId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final index = current.timeline.indexWhere((clip) => clip.id == clipId);
    if (index == -1 || index == current.timeline.length - 1) {
      _emitError(current, TimelineErrorCodes.mergeIncompatible);
      return;
    }

    final first = current.timeline[index];
    final second = current.timeline[index + 1];
    if (first.sourceId != second.sourceId) {
      _emitError(current, TimelineErrorCodes.mergeIncompatible);
      return;
    }

    final newStart = first.start < second.start ? first.start : second.start;
    final newEnd = first.end > second.end ? first.end : second.end;
    final totalDuration = first.duration + second.duration;
    final mergedQuality =
        _weightedAverage(first.qualityScore, second.qualityScore, first.duration,
            second.duration);
    final mergedConfidence =
        _weightedAverage(first.confidence, second.confidence, first.duration,
            second.duration);

    final mergedClip = first.copyWith(
      start: newStart,
      end: newEnd,
      originalStart: newStart,
      originalEnd: newEnd,
      qualityScore: mergedQuality,
      confidence: mergedConfidence,
      originSuggestionId: null,
      transcriptPreview: null,
    );

    final newTimeline = List<TimelineClip>.from(current.timeline)
      ..[index] = mergedClip
      ..removeAt(index + 1);

    final updatedSuggestions = current.suggestions
        .map((scene) => scene.attachedClipId == first.id ||
                scene.attachedClipId == second.id
            ? scene.copyWith(attachedClipId: null)
            : scene)
        .toList();

    final updatedMetadata = current.metadata.copyWith(
      currentDuration: current.totalDuration,
      clipCount: newTimeline.length,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      suggestions: updatedSuggestions,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> splitClip(String clipId, Duration splitPoint) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final index = current.timeline.indexWhere((clip) => clip.id == clipId);
    if (index == -1) {
      _emitError(current, TimelineErrorCodes.invalidSplitPoint);
      return;
    }

    final clip = current.timeline[index];
    final splitFromStart = splitPoint - clip.start;
    if (splitFromStart <= Duration.zero || splitPoint >= clip.end) {
      _emitError(current, TimelineErrorCodes.invalidSplitPoint);
      return;
    }

    final leftDuration = splitPoint - clip.start;
    final rightDuration = clip.end - splitPoint;
    if (leftDuration < _minClipDuration || rightDuration < _minClipDuration) {
      _emitError(current, TimelineErrorCodes.clipTooShort);
      return;
    }

    final firstClip = clip.copyWith(
      end: splitPoint,
      originalEnd: splitPoint,
      originSuggestionId: clip.originSuggestionId,
    );
    final secondClip = clip.copyWith(
      id: _generateClipId(),
      start: splitPoint,
      end: clip.end,
      originalStart: splitPoint,
      originSuggestionId: null,
      transcriptPreview: clip.transcriptPreview,
    );

    final newTimeline = List<TimelineClip>.from(current.timeline)
      ..[index] = firstClip
      ..insert(index + 1, secondClip);

    final updatedMetadata = current.metadata.copyWith(
      currentDuration: current.totalDuration,
      clipCount: newTimeline.length,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> addTranscriptSegment(String segmentId) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    final segmentIndex =
        current.transcriptResults.indexWhere((item) => item.id == segmentId);
    if (segmentIndex == -1) {
      return;
    }

    final segment = current.transcriptResults[segmentIndex];

    var newClip = TimelineClip(
      id: _generateClipId(),
      projectId: _projectId,
      sourceId: segment.sourceId,
      name: segment.text.trim().isEmpty
          ? 'Transcript Clip'
          : segment.text.trim(),
      source: ClipSourceType.transcript,
      start: segment.start,
      end: segment.end,
      originalStart: segment.start,
      originalEnd: segment.end,
      qualityScore: max(0.6, segment.confidence),
      confidence: segment.confidence,
      originSuggestionId: null,
      transcriptPreview: segment.text,
    );

    if (!_isClipLongEnough(newClip)) {
      newClip = newClip.copyWith(end: newClip.start + _minClipDuration);
    }

    if (_hasOverlap(current.timeline, newClip)) {
      _emitError(current, TimelineErrorCodes.clipOverlap);
      return;
    }

    if (current.metadata.maxDuration > Duration.zero) {
      final projected = current.totalDuration + newClip.duration;
      if (projected > current.metadata.maxDuration) {
        _emitError(current, TimelineErrorCodes.maxDurationExceeded);
        return;
      }
    }

    final newTimeline = List<TimelineClip>.from(current.timeline)..add(newClip);
    final updatedMetadata = _recalculateMetadata(
      current.metadata,
      newTimeline,
      lastSavedAt: current.metadata.lastSavedAt,
    );

    final optimistic = current.copyWith(
      timeline: newTimeline,
      metadata: updatedMetadata,
      hasUnsavedChanges: true,
      errorMessage: null,
      pendingClipIds: {
        ...current.pendingClipIds,
        newClip.id,
      },
    );

    await _persistTimeline(optimistic, previousState: current);
  }

  Future<void> searchTranscript(String query) async {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }

    state = AsyncData(
      current.copyWith(
        isSearchingTranscript: true,
        searchQuery: query,
        errorMessage: null,
      ),
    );

    try {
      final results = await _repository.searchTranscript(_projectId, query);
      final updated = state.valueOrNull;
      if (updated == null) {
        return;
      }
      state = AsyncData(
        updated.copyWith(
          transcriptResults: results,
          isSearchingTranscript: false,
        ),
      );
    } on TimelineRepositoryException {
      final updated = state.valueOrNull;
      if (updated == null) {
        return;
      }
      state = AsyncData(
        updated.copyWith(
          isSearchingTranscript: false,
          errorMessage: TimelineErrorCodes.transcriptSearchFailed,
        ),
      );
    } catch (_) {
      final updated = state.valueOrNull;
      if (updated == null) {
        return;
      }
      state = AsyncData(
        updated.copyWith(
          isSearchingTranscript: false,
          errorMessage: TimelineErrorCodes.transcriptSearchFailed,
        ),
      );
    }
  }

  void clearError() {
    final current = state.valueOrNull;
    if (current == null) {
      return;
    }
    state = AsyncData(current.clearError());
  }

  Future<void> _persistTimeline(
    ProjectTimelineState optimisticState, {
    required ProjectTimelineState previousState,
  }) async {
    state = AsyncData(
      optimisticState.copyWith(
        isSaving: true,
        errorMessage: null,
      ),
    );

    try {
      final payload = await _repository.saveTimeline(
        _projectId,
        optimisticState.timeline.toList(),
        suggestions: optimisticState.suggestions.toList(),
      );

      final timeline = payload.timeline.isEmpty
          ? optimisticState.timeline.toList()
          : payload.timeline;
      final suggestions = payload.suggestions.isEmpty
          ? optimisticState.suggestions.toList()
          : payload.suggestions;

      final metadata = payload.metadata.maxDuration == Duration.zero
          ? optimisticState.metadata.copyWith(
              currentDuration: payload.metadata.currentDuration,
              clipCount: payload.metadata.clipCount,
              lastSavedAt:
                  payload.metadata.lastSavedAt ?? DateTime.now(),
            )
          : payload.metadata.copyWith(
              lastSavedAt:
                  payload.metadata.lastSavedAt ?? DateTime.now(),
            );

      final syncedState = optimisticState.copyWith(
        timeline: timeline,
        suggestions: suggestions,
        metadata: metadata,
        hasUnsavedChanges: false,
        isSaving: false,
        pendingClipIds: <String>{},
        errorMessage: null,
      );

      state = AsyncData(syncedState);
    } on TimelineRepositoryException {
      state = AsyncData(
        previousState.copyWith(
          isSaving: false,
          errorMessage: TimelineErrorCodes.saveFailed,
        ),
      );
    } catch (_) {
      state = AsyncData(
        previousState.copyWith(
          isSaving: false,
          errorMessage: TimelineErrorCodes.saveFailed,
        ),
      );
    }
  }

  void _emitError(ProjectTimelineState current, String code) {
    state = AsyncData(current.copyWith(errorMessage: code));
  }

  bool _isClipLongEnough(TimelineClip clip) {
    return clip.duration >= _minClipDuration;
  }

  bool _hasOverlap(
    List<TimelineClip> timeline,
    TimelineClip candidate, {
    String? excludeClipId,
  }) {
    for (final clip in timeline) {
      if (clip.sourceId != candidate.sourceId) {
        continue;
      }
      if (excludeClipId != null && clip.id == excludeClipId) {
        continue;
      }
      final candidateStart = candidate.start.inMilliseconds;
      final candidateEnd = candidate.end.inMilliseconds;
      final clipStart = clip.start.inMilliseconds;
      final clipEnd = clip.end.inMilliseconds;
      final overlaps = candidateStart < clipEnd && candidateEnd > clipStart;
      if (overlaps) {
        return true;
      }
    }
    return false;
  }

  ProjectMetadata _recalculateMetadata(
    ProjectMetadata base,
    List<TimelineClip> timeline, {
    DateTime? lastSavedAt,
  }) {
    final total = timeline.fold<Duration>(
      Duration.zero,
      (sum, clip) => sum + clip.duration,
    );

    return base.copyWith(
      currentDuration: total,
      clipCount: timeline.length,
      lastSavedAt: lastSavedAt ?? base.lastSavedAt,
    );
  }

  double _weightedAverage(
    double first,
    double second,
    Duration firstDuration,
    Duration secondDuration,
  ) {
    final firstMs = firstDuration.inMilliseconds.toDouble();
    final secondMs = secondDuration.inMilliseconds.toDouble();
    final total = firstMs + secondMs;
    if (total == 0) {
      return (first + second) / 2;
    }
    return ((first * firstMs) + (second * secondMs)) / total;
  }

  String _generateClipId() {
    final suffix = _random.nextInt(1 << 32).toRadixString(16);
    return 'clip-${DateTime.now().microsecondsSinceEpoch}-$suffix';
  }
}
