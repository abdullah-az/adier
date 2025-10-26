import 'package:cto/src/core/utils/timeline_math.dart';
import 'package:cto/src/features/timeline/models/timeline_segment.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final segments = [
    const TimelineSegment(id: 'a', label: 'Intro', duration: Duration(seconds: 4)),
    const TimelineSegment(id: 'b', label: 'Main', duration: Duration(seconds: 6)),
    const TimelineSegment(id: 'c', label: 'Outro', duration: Duration(seconds: 2)),
  ];

  test('totalDuration sums segment durations', () {
    expect(TimelineMath.totalDuration(segments), const Duration(seconds: 12));
  });

  test('startForSegment returns cumulative start time', () {
    expect(TimelineMath.startForSegment(segments, 'a'), Duration.zero);
    expect(TimelineMath.startForSegment(segments, 'b'), const Duration(seconds: 4));
    expect(TimelineMath.startForSegment(segments, 'c'), const Duration(seconds: 10));
  });

  test('progressAt calculates ratio and clamps to range', () {
    final total = const Duration(seconds: 12);
    expect(TimelineMath.progressAt(const Duration(seconds: 3), total), closeTo(0.25, 0.001));
    expect(TimelineMath.progressAt(const Duration(seconds: 20), total), 1.0);
    expect(TimelineMath.progressAt(const Duration(seconds: -2), total), 0.0);
  });

  test('clampToTimeline bounds values within total duration', () {
    final total = const Duration(seconds: 12);
    expect(TimelineMath.clampToTimeline(const Duration(seconds: -1), total), Duration.zero);
    expect(TimelineMath.clampToTimeline(const Duration(seconds: 4), total), const Duration(seconds: 4));
    expect(TimelineMath.clampToTimeline(const Duration(seconds: 20), total), total);
  });

  test('snapToGrid moves to nearest grid boundary', () {
    const grid = Duration(milliseconds: 500);
    expect(
      TimelineMath.snapToGrid(const Duration(milliseconds: 260), grid: grid),
      const Duration(milliseconds: 500),
    );
    expect(
      TimelineMath.snapToGrid(const Duration(milliseconds: 220), grid: grid),
      const Duration(milliseconds: 0),
    );
  });

  test('cumulativeStarts returns list of start positions', () {
    final starts = TimelineMath.cumulativeStarts(segments);
    expect(starts, [Duration.zero, const Duration(seconds: 4), const Duration(seconds: 10)]);
  });

  test('formatDuration outputs mm:ss.SS format', () {
    final formatted = TimelineMath.formatDuration(const Duration(milliseconds: 9050));
    expect(formatted, '00:09.05');
  });
}
