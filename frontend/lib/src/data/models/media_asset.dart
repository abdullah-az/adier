import 'package:json_annotation/json_annotation.dart';
import 'base_model.dart';
import 'enums.dart';

part 'media_asset.g.dart';

@JsonSerializable()
class MediaAsset extends BaseModel {
  @JsonKey(name: 'project_id')
  final String projectId;
  
  @JsonKey(name: 'type')
  final MediaAssetType type;
  
  @JsonKey(name: 'filename')
  final String filename;
  
  @JsonKey(name: 'file_path')
  final String filePath;
  
  @JsonKey(name: 'mime_type')
  final String? mimeType;
  
  @JsonKey(name: 'size_bytes')
  final int? sizeBytes;
  
  @JsonKey(name: 'duration_seconds')
  final double? durationSeconds;
  
  @JsonKey(name: 'checksum')
  final String? checksum;
  
  @JsonKey(name: 'analysis_cache')
  final Map<String, dynamic>? analysisCache;

  const MediaAsset({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    required this.projectId,
    required this.type,
    required this.filename,
    required this.filePath,
    this.mimeType,
    this.sizeBytes,
    this.durationSeconds,
    this.checksum,
    this.analysisCache,
  });

  factory MediaAsset.fromJson(Map<String, dynamic> json) =>
      _$MediaAssetFromJson(json);

  Map<String, dynamic> toJson() => _$MediaAssetToJson(this);

  MediaAsset copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? projectId,
    MediaAssetType? type,
    String? filename,
    String? filePath,
    String? mimeType,
    int? sizeBytes,
    double? durationSeconds,
    String? checksum,
    Map<String, dynamic>? analysisCache,
  }) {
    return MediaAsset(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      projectId: projectId ?? this.projectId,
      type: type ?? this.type,
      filename: filename ?? this.filename,
      filePath: filePath ?? this.filePath,
      mimeType: mimeType ?? this.mimeType,
      sizeBytes: sizeBytes ?? this.sizeBytes,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      checksum: checksum ?? this.checksum,
      analysisCache: analysisCache ?? this.analysisCache,
    );
  }
}