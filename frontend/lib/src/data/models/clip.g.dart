// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'clip.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Clip _$ClipFromJson(Map<String, dynamic> json) => Clip(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      projectId: json['project_id'] as String,
      sourceAssetId: json['source_asset_id'] as String?,
      title: json['title'] as String,
      description: json['description'] as String?,
      status: ClipStatus.fromString(json['status'] as String),
      startTime: (json['start_time'] as num?)?.toDouble(),
      endTime: (json['end_time'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$ClipToJson(Clip instance) => <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'project_id': instance.projectId,
      'source_asset_id': instance.sourceAssetId,
      'title': instance.title,
      'description': instance.description,
      'status': instance.status.value,
      'start_time': instance.startTime,
      'end_time': instance.endTime,
    };

ClipVersion _$ClipVersionFromJson(Map<String, dynamic> json) => ClipVersion(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      clipId: json['clip_id'] as String,
      outputAssetId: json['output_asset_id'] as String?,
      presetId: json['preset_id'] as String?,
      versionNumber: json['version_number'] as int,
      status: ClipVersionStatus.fromString(json['status'] as String),
      notes: json['notes'] as String?,
      qualityMetrics: json['quality_metrics'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$ClipVersionToJson(ClipVersion instance) =>
    <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'clip_id': instance.clipId,
      'output_asset_id': instance.outputAssetId,
      'preset_id': instance.presetId,
      'version_number': instance.versionNumber,
      'status': instance.status.value,
      'notes': instance.notes,
      'quality_metrics': instance.qualityMetrics,
    };