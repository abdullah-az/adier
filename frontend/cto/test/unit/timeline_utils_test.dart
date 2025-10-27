import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/models/timeline_segment.dart';

void main() {
  group('Timeline utilities', () {
    final segments = [
      const TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 2000, color: Colors.blue),
      const TimelineSegment(id: 'b', label: 'Main', startMs: 1500, endMs: 4000, color: Colors.red),
    ];

    test('calculateTimelineDuration sums segment duration', () {
      final duration = calculateTimelineDuration(segments);

      expect(duration.inMilliseconds, 4500);
    });

    test('normalizeTimelineSegments removes overlaps', () {
      final normalized = normalizeTimelineSegments(segments);

      expect(normalized.first.startMs, 0);
      expect(normalized.first.endMs, 2000);
      expect(normalized.last.startMs, 2000);
      expect(normalized.last.endMs, 4000);
    });

    test('mergeAdjacentSegments merges matching labels within gap', () {
      final merged = mergeAdjacentSegments([
        const TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1000),
        const TimelineSegment(id: 'b', label: 'Intro', startMs: 1020, endMs: 2000),
        const TimelineSegment(id: 'c', label: 'Outro', startMs: 4000, endMs: 5000),
      ]);

      expect(merged.length, 2);
      expect(merged.first.startMs, 0);
      expect(merged.first.endMs, 2000);
    });

    test('generateSubtitleCues splits lengthy segments', () {
      final cues = generateSubtitleCues([
        const TimelineSegment(id: 'main', label: 'Main', startMs: 0, endMs: 20000),
      ], maxSegmentDuration: const Duration(seconds: 5));

      expect(cues.length, greaterThan(1));
      expect(cues.first.startMs, 0);
      expect(cues.last.endMs, 20000);
    });

    test('buildTimelineSummary composes normalized segments and cues', () {
      final summary = buildTimelineSummary(segments);

      expect(summary.segments.first.endMs, 2000);
      expect(summary.cues, isNotEmpty);
      expect(summary.totalDuration.inMilliseconds, 4500);
    });
  });

  test('TimelineCache stores and retrieves summaries', () {
    final cache = TimelineCache();
    final summary = buildTimelineSummary([
      const TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1000),
    ]);

    expect(cache.read('key'), isNull);

    cache.write('key', summary);

    expect(cache.read('key'), same(summary));

    cache.clear();
    expect(cache.read('key'), isNull);
  });
}
