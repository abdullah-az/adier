import 'dart:async';
import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/subtitle_segment.dart';
import '../../../data/providers/subtitle_provider.dart';
import '../../../data/repositories/subtitle_repository.dart';

const Duration _minimumSegmentDuration = Duration(milliseconds: 300);

Duration _clampDuration(Duration value, Duration min, Duration max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

const Object _noChange = Object();

class SubtitleEditorState {
  const SubtitleEditorState({
    required this.isLoading,
    required this.isSaving,
    required this.segments,
    required this.selectedSegmentId,
    required this.previewPosition,
    required this.hasChanges,
    this.errorMessage,
  });

  factory SubtitleEditorState.initial() {
    return const SubtitleEditorState(
      isLoading: true,
      isSaving: false,
      segments: <SubtitleSegment>[],
      selectedSegmentId: null,
      previewPosition: Duration.zero,
      hasChanges: false,
      errorMessage: null,
    );
  }

  final bool isLoading;
  final bool isSaving;
  final List<SubtitleSegment> segments;
  final String? selectedSegmentId;
  final Duration previewPosition;
  final bool hasChanges;
  final String? errorMessage;

  SubtitleSegment? get selectedSegment {
    if (segments.isEmpty) {
      return null;
    }
    if (selectedSegmentId == null) {
      return segments.first;
    }
    for (final segment in segments) {
      if (segment.id == selectedSegmentId) {
        return segment;
      }
    }
    return segments.first;
  }

  Duration get totalDuration {
    return segments.fold<Duration>(
      Duration.zero,
      (previous, segment) => segment.end > previous ? segment.end : previous,
    );
  }

  SubtitleEditorState copyWith({
    bool? isLoading,
    bool? isSaving,
    List<SubtitleSegment>? segments,
    String? selectedSegmentId,
    Duration? previewPosition,
    bool? hasChanges,
    Object? errorMessage = _noChange,
  }) {
    return SubtitleEditorState(
      isLoading: isLoading ?? this.isLoading,
      isSaving: isSaving ?? this.isSaving,
      segments: segments ?? this.segments,
      selectedSegmentId: selectedSegmentId ?? this.selectedSegmentId,
      previewPosition: previewPosition ?? this.previewPosition,
      hasChanges: hasChanges ?? this.hasChanges,
      errorMessage: identical(errorMessage, _noChange) ? this.errorMessage : errorMessage as String?,
    );
  }
}

class SubtitleEditorController extends StateNotifier<SubtitleEditorState> {
  SubtitleEditorController({
    required SubtitleRepository repository,
    required this.videoId,
  })  : _repository = repository,
        super(SubtitleEditorState.initial());

  final SubtitleRepository _repository;
  final String videoId;

  bool _initialized = false;
  Completer<void>? _loadingCompleter;

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    await _loadSegments();
  }

  Future<void> refresh() async {
    await _loadSegments();
  }

  Future<void> _loadSegments() async {
    if (_loadingCompleter != null && !_loadingCompleter!.isCompleted) {
      return _loadingCompleter!.future;
    }
    final completer = Completer<void>();
    _loadingCompleter = completer;

    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final segments = await _repository.fetchSubtitles(videoId);
      segments.sort((a, b) => a.start.compareTo(b.start));
      state = state.copyWith(
        isLoading: false,
        segments: List<SubtitleSegment>.unmodifiable(segments),
        selectedSegmentId: segments.isNotEmpty ? segments.first.id : null,
        previewPosition: Duration.zero,
        hasChanges: false,
        errorMessage: null,
      );
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
      );
    } finally {
      completer.complete();
      _loadingCompleter = null;
    }
  }

  void selectSegment(String segmentId) {
    if (state.selectedSegmentId == segmentId) {
      return;
    }
    if (state.segments.any((segment) => segment.id == segmentId)) {
      state = state.copyWith(selectedSegmentId: segmentId);
    }
  }

  void updateSegmentText(String segmentId, String text) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) {
      return;
    }
    final updated = segments[index].copyWith(text: text);
    segments[index] = updated;
    _publishSegments(segments);
  }

  void toggleVisibility(String segmentId) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;
    final segment = segments[index];
    segments[index] = segment.copyWith(isVisible: !segment.isVisible);
    _publishSegments(segments);
  }

  void adjustStart(String segmentId, Duration adjustment) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;
    final segment = segments[index];

    final previousEnd = index == 0 ? Duration.zero : segments[index - 1].end;
    final maxStart = segment.end - _minimumSegmentDuration;
    final newStart = _clampDuration(
      segment.start + adjustment,
      previousEnd,
      maxStart > previousEnd ? maxStart : previousEnd,
    );

    segments[index] = segment.copyWith(start: newStart);
    _publishSegments(segments, maintainSelection: true);
  }

  void setStart(String segmentId, Duration newStart) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;

    final previousEnd = index == 0 ? Duration.zero : segments[index - 1].end;
    final segment = segments[index];
    final maxStart = segment.end - _minimumSegmentDuration;
    final clamped = _clampDuration(newStart, previousEnd, maxStart > previousEnd ? maxStart : previousEnd);
    segments[index] = segment.copyWith(start: clamped);
    _publishSegments(segments, maintainSelection: true);
  }

  void adjustEnd(String segmentId, Duration adjustment) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;

    final segment = segments[index];
    final isLastSegment = index == segments.length - 1;
    final nextStart = isLastSegment ? segment.end + adjustment : segments[index + 1].start;
    final minEnd = segment.start + _minimumSegmentDuration;
    final target = segment.end + adjustment;
    final maxEndCandidate = nextStart - _minimumSegmentDuration;
    final maxEnd = isLastSegment
        ? (target > minEnd ? target : minEnd)
        : (maxEndCandidate > minEnd ? maxEndCandidate : minEnd);
    final clamped = _clampDuration(target, minEnd, maxEnd);

    segments[index] = segment.copyWith(end: clamped);
    if (index < segments.length - 1 && clamped > segments[index + 1].start) {
      final next = segments[index + 1];
      segments[index + 1] = next.copyWith(start: clamped);
    }
    _publishSegments(segments, maintainSelection: true);
  }

  void setEnd(String segmentId, Duration newEnd) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;

    final segment = segments[index];
    final isLastSegment = index == segments.length - 1;
    final nextStart = isLastSegment ? newEnd : segments[index + 1].start;
    final minEnd = segment.start + _minimumSegmentDuration;
    final maxEndCandidate = nextStart - _minimumSegmentDuration;
    final maxEnd = isLastSegment
        ? (newEnd > minEnd ? newEnd : minEnd)
        : (maxEndCandidate > minEnd ? maxEndCandidate : minEnd);
    final clamped = _clampDuration(newEnd, minEnd, maxEnd);

    segments[index] = segment.copyWith(end: clamped);
    if (index < segments.length - 1 && clamped > segments[index + 1].start) {
      final next = segments[index + 1];
      segments[index + 1] = next.copyWith(start: clamped);
    }
    _publishSegments(segments, maintainSelection: true);
  }

  void splitSegment(String segmentId) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1) return;

    final segment = segments[index];
    final currentDuration = segment.duration;
    if (currentDuration <= _minimumSegmentDuration * 2) {
      return;
    }

    final halfMs = (currentDuration.inMilliseconds / 2).round();
    final midPoint = segment.start + Duration(milliseconds: halfMs);

    final text = segment.text.trim();
    final splitIndex = _nearestSplitIndex(text);
    final firstText = text.substring(0, splitIndex).trim();
    final secondText = text.substring(splitIndex).trim();

    final firstSegment = segment.copyWith(end: midPoint, text: firstText.isEmpty ? segment.text : firstText);
    final newSegment = SubtitleSegment(
      id: _generateId(),
      start: midPoint,
      end: segment.end,
      text: secondText.isEmpty ? segment.text : secondText,
      isVisible: segment.isVisible,
    );

    segments[index] = firstSegment;
    segments.insert(index + 1, newSegment);
    _publishSegments(segments, maintainSelection: false, newSelectedId: newSegment.id);
  }

  void mergeWithNext(String segmentId) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final index = segments.indexWhere((segment) => segment.id == segmentId);
    if (index == -1 || index == segments.length - 1) {
      return;
    }

    final current = segments[index];
    final next = segments[index + 1];

    final merged = current.copyWith(
      end: max(current.end, next.end),
      text: '${current.text.trim()} ${next.text.trim()}'.trim(),
      isVisible: current.isVisible || next.isVisible,
    );

    segments[index] = merged;
    segments.removeAt(index + 1);
    _publishSegments(segments, maintainSelection: true, newSelectedId: merged.id);
  }

  void addSegmentAfter(String? segmentId) {
    final segments = List<SubtitleSegment>.from(state.segments);
    final insertIndex = segmentId == null
        ? segments.length
        : max(0, segments.indexWhere((segment) => segment.id == segmentId) + 1);

    final start = insertIndex == 0
        ? Duration.zero
        : segments[insertIndex - 1].end;

    final nextStart = insertIndex >= segments.length
        ? start + const Duration(seconds: 2)
        : segments[insertIndex].start;
    var end = start + const Duration(seconds: 2);
    if (nextStart > start) {
      final candidate = nextStart - const Duration(milliseconds: 100);
      if (candidate > start + _minimumSegmentDuration) {
        end = candidate;
      }
    }
    if (end <= start) {
      end = start + const Duration(seconds: 2);
    }

    final newSegment = SubtitleSegment(
      id: _generateId(),
      start: start,
      end: end,
      text: '',
      isVisible: true,
    );

    segments.insert(insertIndex, newSegment);
    _publishSegments(segments, maintainSelection: false, newSelectedId: newSegment.id);
  }

  Future<bool> saveChanges() async {
    if (!state.hasChanges) {
      return true;
    }
    final completer = Completer<bool>();
    state = state.copyWith(isSaving: true, errorMessage: null);
    try {
      await _repository.updateSubtitles(videoId, state.segments);
      state = state.copyWith(isSaving: false, hasChanges: false, errorMessage: null);
      completer.complete(true);
    } catch (error) {
      state = state.copyWith(isSaving: false, errorMessage: error.toString());
      completer.complete(false);
    }
    return completer.future;
  }

  void updatePreviewPosition(Duration position) {
    final timeline = state.totalDuration;
    final maxTimeline = timeline > Duration.zero ? timeline : Duration.zero;
    final clamped = _clampDuration(position, Duration.zero, maxTimeline);
    state = state.copyWith(previewPosition: clamped);
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(errorMessage: null);
    }
  }

  void _publishSegments(
    List<SubtitleSegment> segments, {
    bool maintainSelection = true,
    String? newSelectedId,
  }) {
    segments.sort((a, b) => a.start.compareTo(b.start));
    final selectedId = maintainSelection
        ? (newSelectedId ?? state.selectedSegmentId)
        : newSelectedId;
    final immutableSegments = List<SubtitleSegment>.unmodifiable(segments);
    final totalDuration = immutableSegments.fold<Duration>(
      Duration.zero,
      (previous, segment) => segment.end > previous ? segment.end : previous,
    );
    final previewPosition = state.previewPosition > totalDuration ? totalDuration : state.previewPosition;

    state = state.copyWith(
      segments: immutableSegments,
      selectedSegmentId: selectedId ?? (immutableSegments.isNotEmpty ? immutableSegments.first.id : null),
      hasChanges: true,
      previewPosition: previewPosition,
    );
  }

  int _nearestSplitIndex(String text) {
    if (text.isEmpty) {
      return 0;
    }
    final halfLength = text.length / 2;
    var splitIndex = text.indexOf(' ', halfLength.round());
    if (splitIndex == -1) {
      splitIndex = text.lastIndexOf(' ', halfLength.floor());
    }
    if (splitIndex == -1 || splitIndex == 0) {
      splitIndex = text.length ~/ 2;
    }
    return splitIndex;
  }

  String _generateId() => DateTime.now().microsecondsSinceEpoch.toString();
}

final subtitleEditorProvider = StateNotifierProvider.autoDispose
    .family<SubtitleEditorController, SubtitleEditorState, String>((ref, videoId) {
  final repository = ref.read(subtitleRepositoryProvider);
  final controller = SubtitleEditorController(
    repository: repository,
    videoId: videoId,
  );
  // Load data asynchronously without blocking provider creation.
  scheduleMicrotask(controller.init);
  return controller;
});
