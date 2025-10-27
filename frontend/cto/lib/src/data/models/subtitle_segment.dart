class SubtitleSegment {
  const SubtitleSegment({
    required this.id,
    required this.start,
    required this.end,
    required this.text,
    required this.isVisible,
  }) : assert(!end.isNegative, 'End time cannot be negative');

  factory SubtitleSegment.fromJson(Map<String, dynamic> json) {
    return SubtitleSegment(
      id: json['id'] as String,
      start: Duration(milliseconds: json['start'] as int),
      end: Duration(milliseconds: json['end'] as int),
      text: json['text'] as String,
      isVisible: json['isVisible'] as bool? ?? true,
    );
  }

  final String id;
  final Duration start;
  final Duration end;
  final String text;
  final bool isVisible;

  Duration get duration => end - start;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'start': start.inMilliseconds,
      'end': end.inMilliseconds,
      'text': text,
      'isVisible': isVisible,
    };
  }

  SubtitleSegment copyWith({
    String? id,
    Duration? start,
    Duration? end,
    String? text,
    bool? isVisible,
  }) {
    return SubtitleSegment(
      id: id ?? this.id,
      start: start ?? this.start,
      end: end ?? this.end,
      text: text ?? this.text,
      isVisible: isVisible ?? this.isVisible,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is SubtitleSegment &&
        other.id == id &&
        other.start == start &&
        other.end == end &&
        other.text == text &&
        other.isVisible == isVisible;
  }

  @override
  int get hashCode => Object.hash(id, start, end, text, isVisible);
}
