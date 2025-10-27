import 'dart:ui';

class TimelineSegment {
  const TimelineSegment({
    required this.id,
    required this.label,
    required this.startMs,
    required this.endMs,
    this.color,
  }) : assert(startMs <= endMs, 'Segment start must be before end');

  final String id;
  final String label;
  final int startMs;
  final int endMs;
  final Color? color;

  Duration get duration => Duration(milliseconds: endMs - startMs);

  TimelineSegment copyWith({
    String? id,
    String? label,
    int? startMs,
    int? endMs,
    Color? color,
  }) {
    return TimelineSegment(
      id: id ?? this.id,
      label: label ?? this.label,
      startMs: startMs ?? this.startMs,
      endMs: endMs ?? this.endMs,
      color: color ?? this.color,
    );
  }
}
