class MusicTrack {
  const MusicTrack({
    required this.id,
    required this.title,
    required this.artist,
    required this.duration,
    required this.mood,
    required this.previewUrl,
    this.tags = const <String>[],
  });

  factory MusicTrack.fromJson(Map<String, dynamic> json) {
    final List<dynamic>? rawTags = json['tags'] as List<dynamic>?;
    return MusicTrack(
      id: json['id'] as String,
      title: json['title'] as String,
      artist: json['artist'] as String? ?? '',
      duration: Duration(milliseconds: json['duration'] as int),
      mood: json['mood'] as String? ?? '',
      previewUrl: json['previewUrl'] as String,
      tags: rawTags != null ? rawTags.cast<String>() : const <String>[],
    );
  }

  final String id;
  final String title;
  final String artist;
  final Duration duration;
  final String mood;
  final String previewUrl;
  final List<String> tags;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'title': title,
      'artist': artist,
      'duration': duration.inMilliseconds,
      'mood': mood,
      'previewUrl': previewUrl,
      'tags': tags,
    };
  }

  MusicTrack copyWith({
    String? id,
    String? title,
    String? artist,
    Duration? duration,
    String? mood,
    String? previewUrl,
    List<String>? tags,
  }) {
    return MusicTrack(
      id: id ?? this.id,
      title: title ?? this.title,
      artist: artist ?? this.artist,
      duration: duration ?? this.duration,
      mood: mood ?? this.mood,
      previewUrl: previewUrl ?? this.previewUrl,
      tags: tags ?? this.tags,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is MusicTrack &&
        other.id == id &&
        other.title == title &&
        other.artist == artist &&
        other.duration == duration &&
        other.mood == mood &&
        other.previewUrl == previewUrl &&
        _listEquals(other.tags, tags);
  }

  @override
  int get hashCode => Object.hash(id, title, artist, duration, mood, previewUrl, Object.hashAll(tags));

  static bool _listEquals(List<String> a, List<String> b) {
    if (identical(a, b)) return true;
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}
