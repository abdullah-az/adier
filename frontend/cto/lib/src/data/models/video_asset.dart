import 'package:freezed_annotation/freezed_annotation.dart';

part 'video_asset.freezed.dart';
part 'video_asset.g.dart';

enum VideoAssetCategory {
  source,
  processed,
  proxy,
  export,
  thumbnail,
  music,
}

@freezed
class VideoAsset with _$VideoAsset {
  const factory VideoAsset({
    required String id,
    @JsonKey(name: 'project_id') required String projectId,
    required String filename,
    @JsonKey(name: 'original_filename') required String originalFilename,
    @JsonKey(name: 'relative_path') required String relativePath,
    required String checksum,
    @JsonKey(name: 'size_bytes') required int sizeBytes,
    @JsonKey(name: 'mime_type') required String mimeType,
    @Default(VideoAssetCategory.source) VideoAssetCategory category,
    @Default('uploaded') String status,
    @JsonKey(name: 'thumbnail_path') String? thumbnailPath,
    @JsonKey(name: 'source_asset_ids') @Default([]) List<String> sourceAssetIds,
    @Default({}) Map<String, dynamic> metadata,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
  }) = _VideoAsset;

  factory VideoAsset.fromJson(Map<String, dynamic> json) => _$VideoAssetFromJson(json);
}

@freezed
class VideoUploadResponse with _$VideoUploadResponse {
  const factory VideoUploadResponse({
    @JsonKey(name: 'asset_id') required String assetId,
    required String filename,
    @JsonKey(name: 'original_filename') required String originalFilename,
    @JsonKey(name: 'size_bytes') required int sizeBytes,
    @JsonKey(name: 'project_id') required String projectId,
    required String status,
    @Default('Upload successful') String message,
  }) = _VideoUploadResponse;

  factory VideoUploadResponse.fromJson(Map<String, dynamic> json) =>
      _$VideoUploadResponseFromJson(json);
}

@freezed
class StorageStats with _$StorageStats {
  const factory StorageStats({
    String? root,
    @JsonKey(name: 'project_id') String? projectId,
    required Map<String, Map<String, dynamic>> categories,
  }) = _StorageStats;

  factory StorageStats.fromJson(Map<String, dynamic> json) => _$StorageStatsFromJson(json);
}
