class MusicAssignment {
  const MusicAssignment({
    required this.trackId,
    required this.volume,
    required this.fadeIn,
    required this.fadeOut,
    required this.applyToFullTimeline,
    required this.start,
    required this.end,
  }) : assert(volume >= 0 && volume <= 1, 'Volume must be between 0 and 1.');

  factory MusicAssignment.fromJson(Map<String, dynamic> json) {
    return MusicAssignment(
      trackId: json['trackId'] as String,
      volume: (json['volume'] as num?)?.toDouble() ?? 1.0,
      fadeIn: Duration(milliseconds: (json['fadeIn'] as int?) ?? 0),
      fadeOut: Duration(milliseconds: (json['fadeOut'] as int?) ?? 0),
      applyToFullTimeline: json['applyToFullTimeline'] as bool? ?? true,
      start: Duration(milliseconds: (json['start'] as int?) ?? 0),
      end: Duration(milliseconds: (json['end'] as int?) ?? 0),
    );
  }

  final String trackId;
  final double volume;
  final Duration fadeIn;
  final Duration fadeOut;
  final bool applyToFullTimeline;
  final Duration start;
  final Duration end;

  MusicAssignment copyWith({
    String? trackId,
    double? volume,
    Duration? fadeIn,
    Duration? fadeOut,
    bool? applyToFullTimeline,
    Duration? start,
    Duration? end,
  }) {
    return MusicAssignment(
      trackId: trackId ?? this.trackId,
      volume: volume ?? this.volume,
      fadeIn: fadeIn ?? this.fadeIn,
      fadeOut: fadeOut ?? this.fadeOut,
      applyToFullTimeline: applyToFullTimeline ?? this.applyToFullTimeline,
      start: start ?? this.start,
      end: end ?? this.end,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'trackId': trackId,
      'volume': volume,
      'fadeIn': fadeIn.inMilliseconds,
      'fadeOut': fadeOut.inMilliseconds,
      'applyToFullTimeline': applyToFullTimeline,
      'start': start.inMilliseconds,
      'end': end.inMilliseconds,
    };
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is MusicAssignment &&
        other.trackId == trackId &&
        other.volume == volume &&
        other.fadeIn == fadeIn &&
        other.fadeOut == fadeOut &&
        other.applyToFullTimeline == applyToFullTimeline &&
        other.start == start &&
        other.end == end;
  }

  @override
  int get hashCode => Object.hash(trackId, volume, fadeIn, fadeOut, applyToFullTimeline, start, end);
}
