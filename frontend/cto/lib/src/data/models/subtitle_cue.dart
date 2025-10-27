class SubtitleCue {
  const SubtitleCue({
    required this.id,
    required this.text,
    required this.startMs,
    required this.endMs,
  }) : assert(startMs <= endMs, 'Subtitle start must be before end');

  final String id;
  final String text;
  final int startMs;
  final int endMs;

  Duration get duration => Duration(milliseconds: endMs - startMs);

  SubtitleCue copyWith({
    String? id,
    String? text,
    int? startMs,
    int? endMs,
  }) {
    return SubtitleCue(
      id: id ?? this.id,
      text: text ?? this.text,
      startMs: startMs ?? this.startMs,
      endMs: endMs ?? this.endMs,
    );
  }
}
