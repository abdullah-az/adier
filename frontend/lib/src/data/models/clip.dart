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
    this.inPointMs,
    this.outPointMs,
    this.transcriptSnippet,
    this.qualityScore,
    this.markers = const <int>[],
  });

  final String id;
  final String projectId;
  final int sequence;
  final Duration duration;
  final Uri playbackUrl;
  final DateTime createdAt;
  final String? description;

  // Optional trim points (milliseconds) relative to the clip media itself
  final int? inPointMs;
  final int? outPointMs;

  // Optional metadata for UI
  final String? transcriptSnippet;
  final double? qualityScore;
  final List<int> markers;

  Clip copyWith({
    int? sequence,
    Duration? duration,
    Uri? playbackUrl,
    DateTime? createdAt,
    String? description,
    int? inPointMs,
    int? outPointMs,
    String? transcriptSnippet,
    double? qualityScore,
    List<int>? markers,
  }) {
    return Clip(
      id: id,
      projectId: projectId,
      sequence: sequence ?? this.sequence,
      duration: duration ?? this.duration,
      playbackUrl: playbackUrl ?? this.playbackUrl,
      createdAt: createdAt ?? this.createdAt,
      description: description ?? this.description,
      inPointMs: inPointMs ?? this.inPointMs,
      outPointMs: outPointMs ?? this.outPointMs,
      transcriptSnippet: transcriptSnippet ?? this.transcriptSnippet,
      qualityScore: qualityScore ?? this.qualityScore,
      markers: markers ?? this.markers,
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
      inPointMs: json['inPointMs'] as int?,
      outPointMs: json['outPointMs'] as int?,
      transcriptSnippet: json['transcriptSnippet'] as String?,
      qualityScore: (json['qualityScore'] as num?)?.toDouble(),
      markers: (json['markers'] as List<dynamic>?)?.map((e) => e as int).toList(growable: false) ??
          const <int>[],
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
      if (inPointMs != null) 'inPointMs': inPointMs,
      if (outPointMs != null) 'outPointMs': outPointMs,
      if (transcriptSnippet != null) 'transcriptSnippet': transcriptSnippet,
      if (qualityScore != null) 'qualityScore': qualityScore,
      if (markers.isNotEmpty) 'markers': markers,
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
        inPointMs,
        outPointMs,
        transcriptSnippet,
        qualityScore,
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
        other.description == description &&
        other.inPointMs == inPointMs &&
        other.outPointMs == outPointMs &&
        other.transcriptSnippet == transcriptSnippet &&
        other.qualityScore == qualityScore;
  }

  @override
  String toString() => 'Clip(id: $id, sequence: $sequence)';
}
