import 'package:freezed_annotation/freezed_annotation.dart';

part 'video_asset_model.freezed.dart';
part 'video_asset_model.g.dart';

@freezed
class VideoAssetModel with _$VideoAssetModel {
  const factory VideoAssetModel({
    required String id,
    @JsonKey(name: 'project_id') required String projectId,
    required String filename,
    @JsonKey(name: 'original_filename') required String originalFilename,
    @JsonKey(name: 'relative_path') required String relativePath,
    required String checksum,
    @JsonKey(name: 'size_bytes') required int sizeBytes,
    @JsonKey(name: 'mime_type') required String mimeType,
    required String status,
    @JsonKey(name: 'thumbnail_path') String? thumbnailPath,
    @Default({}) Map<String, dynamic> metadata,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
  }) = _VideoAssetModel;

  factory VideoAssetModel.fromJson(Map<String, dynamic> json) =>
      _$VideoAssetModelFromJson(json);
}
