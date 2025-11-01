// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'media_asset.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MediaAsset _$MediaAssetFromJson(Map<String, dynamic> json) => MediaAsset(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      projectId: json['project_id'] as String,
      type: MediaAssetType.fromString(json['type'] as String),
      filename: json['filename'] as String,
      filePath: json['file_path'] as String,
      mimeType: json['mime_type'] as String?,
      sizeBytes: json['size_bytes'] as int?,
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble(),
      checksum: json['checksum'] as String?,
      analysisCache: json['analysis_cache'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$MediaAssetToJson(MediaAsset instance) =>
    <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'project_id': instance.projectId,
      'type': instance.type.value,
      'filename': instance.filename,
      'file_path': instance.filePath,
      'mime_type': instance.mimeType,
      'size_bytes': instance.sizeBytes,
      'duration_seconds': instance.durationSeconds,
      'checksum': instance.checksum,
      'analysis_cache': instance.analysisCache,
    };