import 'package:flutter/foundation.dart';

import '../../data/models/subtitle_cue.dart';
import '../../data/models/timeline_segment.dart';

Duration calculateTimelineDuration(List<TimelineSegment> segments) {
  if (segments.isEmpty) {
    return Duration.zero;
  }
  return segments
      .map((segment) => segment.duration)
      .fold(Duration.zero, (value, element) => value + element);
}

List<TimelineSegment> normalizeTimelineSegments(List<TimelineSegment> segments) {
  if (segments.length <= 1) {
    return List.unmodifiable(segments);
  }

  final sorted = [...segments]
    ..sort((a, b) => a.startMs.compareTo(b.startMs));

  final normalized = <TimelineSegment>[];
  var previousEnd = sorted.first.startMs;

  for (final segment in sorted) {
    final start = segment.startMs < previousEnd ? previousEnd : segment.startMs;
    final end = segment.endMs <= start ? start + 1 : segment.endMs;
    normalized.add(segment.copyWith(startMs: start, endMs: end));
    previousEnd = end;
  }

  return List.unmodifiable(normalized);
}

List<TimelineSegment> mergeAdjacentSegments(List<TimelineSegment> segments, {int maxGapMs = 250}) {
  if (segments.isEmpty) {
    return const [];
  }

  final sorted = normalizeTimelineSegments(segments);
  final merged = <TimelineSegment>[];

  var current = sorted.first;
  for (final segment in sorted.skip(1)) {
    final gap = segment.startMs - current.endMs;
    if (gap.abs() <= maxGapMs && segment.label == current.label) {
      current = current.copyWith(endMs: segment.endMs);
    } else {
      merged.add(current);
      current = segment;
    }
  }
  merged.add(current);
  return merged;
}

List<SubtitleCue> generateSubtitleCues(List<TimelineSegment> segments, {Duration maxSegmentDuration = const Duration(seconds: 8)}) {
  if (segments.isEmpty) {
    return const [];
  }

  final normalized = normalizeTimelineSegments(segments);
  final cues = <SubtitleCue>[];

  for (final segment in normalized) {
    final duration = segment.duration;
    if (duration <= maxSegmentDuration) {
      cues.add(
        SubtitleCue(
          id: segment.id,
          text: segment.label,
          startMs: segment.startMs,
          endMs: segment.endMs,
        ),
      );
    } else {
      final splits = (duration.inMilliseconds / maxSegmentDuration.inMilliseconds).ceil();
      final splitDurationMs = duration.inMilliseconds ~/ splits;
      for (var index = 0; index < splits; index++) {
        final startMs = segment.startMs + (splitDurationMs * index);
        final endMs = index == splits - 1 ? segment.endMs : startMs + splitDurationMs;
        cues.add(
          SubtitleCue(
            id: '${segment.id}_$index',
            text: segment.label,
            startMs: startMs,
            endMs: endMs,
          ),
        );
      }
    }
  }

  return cues;
}

class TimelineSummary {
  const TimelineSummary({
    required this.totalDuration,
    required this.segments,
    required this.cues,
  });

  final Duration totalDuration;
  final List<TimelineSegment> segments;
  final List<SubtitleCue> cues;
}

class TimelineCache {
  final _summaryCache = <String, TimelineSummary>{};

  TimelineSummary? read(String key) => _summaryCache[key];

  void write(String key, TimelineSummary summary) {
    _summaryCache[key] = summary;
  }

  void clear() {
    _summaryCache.clear();
  }
}

class TimelineProfiler {
  void record(String label, Duration duration) {
    debugPrint('[TimelineProfiler] $label took ${duration.inMilliseconds}ms');
  }
}

TimelineSummary buildTimelineSummary(List<TimelineSegment> segments) {
  final normalized = normalizeTimelineSegments(segments);
  final cues = generateSubtitleCues(normalized);
  final duration = calculateTimelineDuration(normalized);
  return TimelineSummary(
    totalDuration: duration,
    segments: normalized,
    cues: cues,
  );
}
