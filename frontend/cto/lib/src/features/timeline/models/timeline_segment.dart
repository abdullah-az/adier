class TimelineSegment {
  const TimelineSegment({
    required this.id,
    required this.label,
    required this.duration,
  });

  final String id;
  final String label;
  final Duration duration;

  TimelineSegment copyWith({
    String? id,
    String? label,
    Duration? duration,
  }) {
    return TimelineSegment(
      id: id ?? this.id,
      label: label ?? this.label,
      duration: duration ?? this.duration,
    );
  }
}
