import 'package:freezed_annotation/freezed_annotation.dart';

part 'video_upload_result_model.freezed.dart';
part 'video_upload_result_model.g.dart';

@freezed
class VideoUploadResultModel with _$VideoUploadResultModel {
  const factory VideoUploadResultModel({
    @JsonKey(name: 'asset_id') required String assetId,
    required String filename,
    @JsonKey(name: 'original_filename') required String originalFilename,
    @JsonKey(name: 'size_bytes') required int sizeBytes,
    @JsonKey(name: 'project_id') required String projectId,
    required String status,
    String? message,
  }) = _VideoUploadResultModel;

  factory VideoUploadResultModel.fromJson(Map<String, dynamic> json) =>
      _$VideoUploadResultModelFromJson(json);
}
