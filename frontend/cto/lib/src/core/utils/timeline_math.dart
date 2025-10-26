import '../../features/timeline/models/timeline_segment.dart';

class TimelineMath {
  const TimelineMath._();

  static Duration totalDuration(List<TimelineSegment> segments) {
    return segments.fold(Duration.zero, (total, segment) => total + segment.duration);
  }

  static Duration startForSegment(List<TimelineSegment> segments, String segmentId) {
    var elapsed = Duration.zero;
    for (final segment in segments) {
      if (segment.id == segmentId) {
        return elapsed;
      }
      elapsed += segment.duration;
    }
    throw ArgumentError.value(segmentId, 'segmentId', 'Segment not found');
  }

  static double progressAt(Duration position, Duration total) {
    if (total.inMilliseconds == 0) {
      return 0;
    }
    final ratio = position.inMilliseconds / total.inMilliseconds;
    if (ratio.isNaN || ratio.isInfinite) {
      return 0;
    }
    return ratio.clamp(0.0, 1.0);
  }

  static Duration clampToTimeline(Duration position, Duration total) {
    if (position < Duration.zero) {
      return Duration.zero;
    }
    if (position > total) {
      return total;
    }
    return position;
  }

  static Duration snapToGrid(Duration position, {Duration grid = const Duration(milliseconds: 100)}) {
    if (grid.inMilliseconds <= 0) {
      return position;
    }
    final remainder = position.inMilliseconds % grid.inMilliseconds;
    final lower = position - Duration(milliseconds: remainder);
    final upper = lower + grid;
    if (remainder >= grid.inMilliseconds / 2) {
      return upper;
    }
    return lower;
  }

  static List<Duration> cumulativeStarts(List<TimelineSegment> segments) {
    final starts = <Duration>[];
    var elapsed = Duration.zero;
    for (final segment in segments) {
      starts.add(elapsed);
      elapsed += segment.duration;
    }
    return starts;
  }

  static String formatDuration(Duration duration) {
    final minutes = duration.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = duration.inSeconds.remainder(60).toString().padLeft(2, '0');
    final milliseconds = (duration.inMilliseconds.remainder(1000) ~/ 10)
        .toString()
        .padLeft(2, '0');
    return '$minutes:$seconds.$milliseconds';
  }
}
