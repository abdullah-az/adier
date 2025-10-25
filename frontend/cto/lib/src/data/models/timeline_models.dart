import 'package:flutter/foundation.dart';

const _unset = Object();

int _durationToMilliseconds(Duration duration) => duration.inMilliseconds;

Duration _durationFromJson(dynamic value) {
  if (value is Duration) {
    return value;
  }
  if (value is int) {
    return Duration(milliseconds: value);
  }
  if (value is double) {
    return Duration(milliseconds: (value * 1000).round());
  }
  if (value is String) {
    final parsed = int.tryParse(value);
    if (parsed != null) {
      return Duration(milliseconds: parsed);
    }
  }
  return Duration.zero;
}

DateTime? _dateTimeFromJson(dynamic value) {
  if (value is DateTime) {
    return value;
  }
  if (value is String) {
    return DateTime.tryParse(value);
  }
  return null;
}

String _dateTimeToJson(DateTime? value) => value?.toIso8601String() ?? '';

enum ClipSourceType { ai, transcript, manual }

ClipSourceType clipSourceTypeFromJson(String value) {
  switch (value) {
    case 'ai':
    case 'ai_suggestion':
      return ClipSourceType.ai;
    case 'transcript':
    case 'transcript_search':
      return ClipSourceType.transcript;
    case 'manual':
    case 'editor':
      return ClipSourceType.manual;
    default:
      return ClipSourceType.manual;
  }
}

String clipSourceTypeToJson(ClipSourceType source) {
  switch (source) {
    case ClipSourceType.ai:
      return 'ai';
    case ClipSourceType.transcript:
      return 'transcript';
    case ClipSourceType.manual:
      return 'manual';
  }
}

@immutable
class TimelineClip {
  const TimelineClip({
    required this.id,
    required this.projectId,
    required this.sourceId,
    required this.name,
    required this.source,
    required this.start,
    required this.end,
    required this.originalStart,
    required this.originalEnd,
    required this.qualityScore,
    required this.confidence,
    this.originSuggestionId,
    this.transcriptPreview,
    this.isLocked = false,
    this.notes,
  });

  final String id;
  final String projectId;
  final String sourceId;
  final String name;
  final ClipSourceType source;
  final Duration start;
  final Duration end;
  final Duration originalStart;
  final Duration originalEnd;
  final double qualityScore;
  final double confidence;
  final String? originSuggestionId;
  final String? transcriptPreview;
  final bool isLocked;
  final String? notes;

  Duration get duration => end - start;

  bool get isTrimmed => start != originalStart || end != originalEnd;

  TimelineClip copyWith({
    String? id,
    String? projectId,
    String? sourceId,
    String? name,
    ClipSourceType? source,
    Duration? start,
    Duration? end,
    Duration? originalStart,
    Duration? originalEnd,
    double? qualityScore,
    double? confidence,
    Object? originSuggestionId = _unset,
    Object? transcriptPreview = _unset,
    bool? isLocked,
    Object? notes = _unset,
  }) {
    return TimelineClip(
      id: id ?? this.id,
      projectId: projectId ?? this.projectId,
      sourceId: sourceId ?? this.sourceId,
      name: name ?? this.name,
      source: source ?? this.source,
      start: start ?? this.start,
      end: end ?? this.end,
      originalStart: originalStart ?? this.originalStart,
      originalEnd: originalEnd ?? this.originalEnd,
      qualityScore: qualityScore ?? this.qualityScore,
      confidence: confidence ?? this.confidence,
      originSuggestionId: originSuggestionId == _unset
          ? this.originSuggestionId
          : originSuggestionId as String?,
      transcriptPreview: transcriptPreview == _unset
          ? this.transcriptPreview
          : transcriptPreview as String?,
      isLocked: isLocked ?? this.isLocked,
      notes: notes == _unset ? this.notes : notes as String?,
    );
  }

  TimelineClip trim(Duration newStart, Duration newEnd) {
    final clampedStart = newStart < originalStart ? originalStart : newStart;
    final clampedEnd = newEnd > originalEnd ? originalEnd : newEnd;
    return copyWith(
      start: clampedStart,
      end: clampedEnd > clampedStart ? clampedEnd : clampedStart + const Duration(milliseconds: 500),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'project_id': projectId,
      'source_id': sourceId,
      'name': name,
      'source': clipSourceTypeToJson(source),
      'start_ms': _durationToMilliseconds(start),
      'end_ms': _durationToMilliseconds(end),
      'original_start_ms': _durationToMilliseconds(originalStart),
      'original_end_ms': _durationToMilliseconds(originalEnd),
      'quality_score': qualityScore,
      'confidence': confidence,
      'origin_suggestion_id': originSuggestionId,
      'transcript_preview': transcriptPreview,
      'is_locked': isLocked,
      'notes': notes,
    };
  }

  factory TimelineClip.fromJson(Map<String, dynamic> json) {
    return TimelineClip(
      id: json['id']?.toString() ?? '',
      projectId: json['project_id']?.toString() ?? '',
      sourceId: json['source_id']?.toString() ?? '',
      name: json['name']?.toString() ?? 'Clip',
      source: clipSourceTypeFromJson(json['source']?.toString() ?? 'manual'),
      start: _durationFromJson(json['start_ms'] ?? json['start']),
      end: _durationFromJson(json['end_ms'] ?? json['end']),
      originalStart: _durationFromJson(json['original_start_ms'] ?? json['available_start_ms'] ?? json['start_ms'] ?? 0),
      originalEnd: _durationFromJson(json['original_end_ms'] ?? json['available_end_ms'] ?? json['end_ms'] ?? 0),
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      originSuggestionId: json['origin_suggestion_id']?.toString(),
      transcriptPreview: json['transcript_preview']?.toString(),
      isLocked: json['is_locked'] == true,
      notes: json['notes']?.toString(),
    );
  }
}

@immutable
class SceneSuggestion {
  const SceneSuggestion({
    required this.id,
    required this.title,
    required this.description,
    required this.sourceId,
    required this.start,
    required this.end,
    required this.qualityScore,
    required this.confidence,
    this.isLocked = false,
    this.attachedClipId,
  });

  final String id;
  final String title;
  final String description;
  final String sourceId;
  final Duration start;
  final Duration end;
  final double qualityScore;
  final double confidence;
  final bool isLocked;
  final String? attachedClipId;

  bool get isSelected => attachedClipId != null;

  SceneSuggestion copyWith({
    String? id,
    String? title,
    String? description,
    String? sourceId,
    Duration? start,
    Duration? end,
    double? qualityScore,
    double? confidence,
    bool? isLocked,
    Object? attachedClipId = _unset,
  }) {
    return SceneSuggestion(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      sourceId: sourceId ?? this.sourceId,
      start: start ?? this.start,
      end: end ?? this.end,
      qualityScore: qualityScore ?? this.qualityScore,
      confidence: confidence ?? this.confidence,
      isLocked: isLocked ?? this.isLocked,
      attachedClipId: attachedClipId == _unset
          ? this.attachedClipId
          : attachedClipId as String?,
    );
  }

  TimelineClip toTimelineClip({
    required String projectId,
    required String clipId,
  }) {
    return TimelineClip(
      id: clipId,
      projectId: projectId,
      sourceId: sourceId,
      name: title,
      source: ClipSourceType.ai,
      start: start,
      end: end,
      originalStart: start,
      originalEnd: end,
      qualityScore: qualityScore,
      confidence: confidence,
      originSuggestionId: id,
      transcriptPreview: description,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'source_id': sourceId,
      'start_ms': _durationToMilliseconds(start),
      'end_ms': _durationToMilliseconds(end),
      'quality_score': qualityScore,
      'confidence': confidence,
      'is_locked': isLocked,
      'attached_clip_id': attachedClipId,
    };
  }

  factory SceneSuggestion.fromJson(Map<String, dynamic> json) {
    return SceneSuggestion(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Scene',
      description: json['description']?.toString() ?? '',
      sourceId: json['source_id']?.toString() ?? '',
      start: _durationFromJson(json['start_ms'] ?? json['start']),
      end: _durationFromJson(json['end_ms'] ?? json['end']),
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      isLocked: json['is_locked'] == true,
      attachedClipId: json['attached_clip_id']?.toString(),
    );
  }
}

@immutable
class TranscriptSegment {
  const TranscriptSegment({
    required this.id,
    required this.sourceId,
    required this.text,
    required this.start,
    required this.end,
    this.confidence = 0,
  });

  final String id;
  final String sourceId;
  final String text;
  final Duration start;
  final Duration end;
  final double confidence;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'source_id': sourceId,
      'text': text,
      'start_ms': _durationToMilliseconds(start),
      'end_ms': _durationToMilliseconds(end),
      'confidence': confidence,
    };
  }

  factory TranscriptSegment.fromJson(Map<String, dynamic> json) {
    return TranscriptSegment(
      id: json['id']?.toString() ?? '',
      sourceId: json['source_id']?.toString() ?? '',
      text: json['text']?.toString() ?? '',
      start: _durationFromJson(json['start_ms'] ?? json['start']),
      end: _durationFromJson(json['end_ms'] ?? json['end']),
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
    );
  }
}

@immutable
class ProjectMetadata {
  const ProjectMetadata({
    required this.projectId,
    required this.title,
    required this.description,
    required this.maxDuration,
    required this.currentDuration,
    required this.clipCount,
    this.lastSavedAt,
    this.owner,
    this.status,
  });

  final String projectId;
  final String title;
  final String description;
  final Duration maxDuration;
  final Duration currentDuration;
  final int clipCount;
  final DateTime? lastSavedAt;
  final String? owner;
  final String? status;

  Duration get remainingDuration {
    final remaining = maxDuration - currentDuration;
    return remaining.isNegative ? Duration.zero : remaining;
  }

  ProjectMetadata copyWith({
    String? projectId,
    String? title,
    String? description,
    Duration? maxDuration,
    Duration? currentDuration,
    int? clipCount,
    Object? lastSavedAt = _unset,
    Object? owner = _unset,
    Object? status = _unset,
  }) {
    return ProjectMetadata(
      projectId: projectId ?? this.projectId,
      title: title ?? this.title,
      description: description ?? this.description,
      maxDuration: maxDuration ?? this.maxDuration,
      currentDuration: currentDuration ?? this.currentDuration,
      clipCount: clipCount ?? this.clipCount,
      lastSavedAt: lastSavedAt == _unset ? this.lastSavedAt : lastSavedAt as DateTime?,
      owner: owner == _unset ? this.owner : owner as String?,
      status: status == _unset ? this.status : status as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'project_id': projectId,
      'title': title,
      'description': description,
      'max_duration_ms': _durationToMilliseconds(maxDuration),
      'current_duration_ms': _durationToMilliseconds(currentDuration),
      'clip_count': clipCount,
      'last_saved_at': _dateTimeToJson(lastSavedAt),
      'owner': owner,
      'status': status,
    };
  }

  factory ProjectMetadata.fromJson(Map<String, dynamic> json) {
    return ProjectMetadata(
      projectId: json['project_id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Project',
      description: json['description']?.toString() ?? '',
      maxDuration: _durationFromJson(json['max_duration_ms'] ?? json['max_duration']),
      currentDuration: _durationFromJson(json['current_duration_ms'] ?? json['current_duration']),
      clipCount: json['clip_count'] is num ? (json['clip_count'] as num).round() : 0,
      lastSavedAt: _dateTimeFromJson(json['last_saved_at']),
      owner: json['owner']?.toString(),
      status: json['status']?.toString(),
    );
  }
}

@immutable
class ProjectTimelinePayload {
  const ProjectTimelinePayload({
    required this.timeline,
    required this.suggestions,
    required this.metadata,
  });

  final List<TimelineClip> timeline;
  final List<SceneSuggestion> suggestions;
  final ProjectMetadata metadata;

  Map<String, dynamic> toJson() {
    return {
      'timeline': timeline.map((clip) => clip.toJson()).toList(),
      'suggestions': suggestions.map((scene) => scene.toJson()).toList(),
      'metadata': metadata.toJson(),
    };
  }

  factory ProjectTimelinePayload.fromJson(Map<String, dynamic> json) {
    final timelineJson = json['timeline'] as List<dynamic>? ?? <dynamic>[];
    final suggestionsJson = json['suggestions'] as List<dynamic>? ?? <dynamic>[];
    return ProjectTimelinePayload(
      timeline: timelineJson.map((item) => TimelineClip.fromJson(item as Map<String, dynamic>)).toList(),
      suggestions: suggestionsJson.map((item) => SceneSuggestion.fromJson(item as Map<String, dynamic>)).toList(),
      metadata: ProjectMetadata.fromJson(json['metadata'] as Map<String, dynamic>),
    );
  }
}
