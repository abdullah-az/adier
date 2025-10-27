import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/utils/timeline_utils.dart';
import '../../../data/models/timeline_segment.dart';
import '../../../data/providers/editor_providers.dart';
import '../../../data/repositories/editor_repository.dart';

class TimelineController extends StateNotifier<AsyncValue<TimelineSummary>> {
  TimelineController({
    required EditorRepository repository,
    required TimelineCache cache,
    required TimelineProfiler profiler,
  })  : _repository = repository,
        _cache = cache,
        _profiler = profiler,
        super(const AsyncValue.loading());

  final EditorRepository _repository;
  final TimelineCache _cache;
  final TimelineProfiler _profiler;

  Future<void> loadTimeline(String uploadId) async {
    final stopwatch = Stopwatch()..start();
    final cached = _cache.read(uploadId);
    if (cached != null) {
      state = AsyncValue.data(cached);
      stopwatch.stop();
      _profiler.record('timelineCacheHit', stopwatch.elapsed);
      return;
    }

    state = const AsyncValue.loading();
    try {
      final segments = await _repository.fetchTimeline(uploadId);
      final summary = buildTimelineSummary(segments);
      _cache.write(uploadId, summary);
      state = AsyncValue.data(summary);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    } finally {
      stopwatch.stop();
      _profiler.record('fetchTimeline', stopwatch.elapsed);
    }
  }

  void clear() {
    state = const AsyncValue.loading();
  }

  void updateSegment(TimelineSegment segment) {
    final current = state;
    if (!current.hasValue) {
      return;
    }
    final summary = current.value!;
    final updatedSegments = summary.segments.map((existing) {
      return existing.id == segment.id ? segment : existing;
    }).toList(growable: false);
    final updatedSummary = buildTimelineSummary(updatedSegments);
    state = AsyncValue.data(updatedSummary);
  }
}

final timelineControllerProvider =
    StateNotifierProvider<TimelineController, AsyncValue<TimelineSummary>>((ref) {
  final repository = ref.watch(editorRepositoryProvider);
  final cache = ref.watch(timelineCacheProvider);
  final profiler = ref.watch(timelineProfilerProvider);
  return TimelineController(repository: repository, cache: cache, profiler: profiler);
});
