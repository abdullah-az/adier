import 'package:freezed_annotation/freezed_annotation.dart';

import 'job_model.dart';

part 'project_summary_model.freezed.dart';
part 'project_summary_model.g.dart';

@JsonEnum(fieldRename: FieldRename.snake, unknownValue: ProjectStatus.uploaded)
enum ProjectStatus {
  ready,
  processing,
  failed,
  uploaded,
  completed,
}

@freezed
class ProjectAssetSummaryModel with _$ProjectAssetSummaryModel {
  const factory ProjectAssetSummaryModel({
    @JsonKey(name: 'asset_id') required String assetId,
    required String filename,
    @JsonKey(name: 'original_filename') required String originalFilename,
    @JsonKey(name: 'size_bytes') required int sizeBytes,
    required String status,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
  }) = _ProjectAssetSummaryModel;

  factory ProjectAssetSummaryModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectAssetSummaryModelFromJson(json);
}

@freezed
class ProjectJobSummaryModel with _$ProjectJobSummaryModel {
  const factory ProjectJobSummaryModel({
    required String id,
    @JsonKey(name: 'job_type') required String jobType,
    required JobStatusModel status,
    required double progress,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @JsonKey(name: 'error_message') String? errorMessage,
  }) = _ProjectJobSummaryModel;

  factory ProjectJobSummaryModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectJobSummaryModelFromJson(json);
}

@freezed
class ProjectSummaryModel with _$ProjectSummaryModel {
  const factory ProjectSummaryModel({
    @JsonKey(name: 'project_id') required String projectId,
    @JsonKey(name: 'display_name') required String displayName,
    @JsonKey(name: 'status') required ProjectStatus status,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
    @JsonKey(name: 'asset_count') required int assetCount,
    @JsonKey(name: 'total_size_bytes') required int totalSizeBytes,
    @JsonKey(name: 'job_progress') double? jobProgress,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    @JsonKey(name: 'latest_asset') ProjectAssetSummaryModel? latestAsset,
    @JsonKey(name: 'latest_job') ProjectJobSummaryModel? latestJob,
  }) = _ProjectSummaryModel;

  factory ProjectSummaryModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectSummaryModelFromJson(json);
}
