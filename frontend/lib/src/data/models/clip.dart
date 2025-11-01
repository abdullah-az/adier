import 'package:flutter/foundation.dart';

@immutable
class Clip {
  const Clip({
    required this.id,
    required this.projectId,
    required this.sequence,
    required this.duration,
    required this.playbackUrl,
    required this.createdAt,
    this.description,
  });

  final String id;
  final String projectId;
  final int sequence;
  final Duration duration;
  final Uri playbackUrl;
  final DateTime createdAt;
  final String? description;

  Clip copyWith({
    int? sequence,
    Duration? duration,
    Uri? playbackUrl,
    DateTime? createdAt,
    String? description,
  }) {
    return Clip(
      id: id,
      projectId: projectId,
      sequence: sequence ?? this.sequence,
      duration: duration ?? this.duration,
      playbackUrl: playbackUrl ?? this.playbackUrl,
      createdAt: createdAt ?? this.createdAt,
      description: description ?? this.description,
    );
  }

  factory Clip.fromJson(Map<String, dynamic> json) {
    return Clip(
      id: json['id'] as String,
      projectId: json['projectId'] as String,
      sequence: json['sequence'] as int,
      duration: Duration(milliseconds: json['durationMs'] as int),
      playbackUrl: Uri.parse(json['playbackUrl'] as String),
      createdAt: DateTime.parse(json['createdAt'] as String),
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'projectId': projectId,
      'sequence': sequence,
      'durationMs': duration.inMilliseconds,
      'playbackUrl': playbackUrl.toString(),
      'createdAt': createdAt.toIso8601String(),
      if (description != null) 'description': description,
    };
  }

  @override
  int get hashCode => Object.hash(
        id,
        projectId,
        sequence,
        duration,
        playbackUrl,
        createdAt,
        description,
      );

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) {
      return true;
    }
    return other is Clip &&
        other.id == id &&
        other.projectId == projectId &&
        other.sequence == sequence &&
        other.duration == duration &&
        other.playbackUrl == playbackUrl &&
        other.createdAt == createdAt &&
        other.description == description;
  }

  @override
  String toString() => 'Clip(id: $id, sequence: $sequence)';
}
