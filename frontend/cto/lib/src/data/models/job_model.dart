import 'package:freezed_annotation/freezed_annotation.dart';

part 'job_model.freezed.dart';
part 'job_model.g.dart';

@JsonEnum(fieldRename: FieldRename.snake)
enum JobStatusModel {
  queued,
  running,
  completed,
  failed,
}

@freezed
class JobLogEntryModel with _$JobLogEntryModel {
  const factory JobLogEntryModel({
    required DateTime timestamp,
    required String level,
    required String message,
    @Default({}) Map<String, dynamic> details,
  }) = _JobLogEntryModel;

  factory JobLogEntryModel.fromJson(Map<String, dynamic> json) =>
      _$JobLogEntryModelFromJson(json);
}

@freezed
class JobModel with _$JobModel {
  const factory JobModel({
    required String id,
    @JsonKey(name: 'project_id') required String projectId,
    @JsonKey(name: 'job_type') required String jobType,
    @JsonKey(name: 'status') required JobStatusModel status,
    required double progress,
    @Default({}) Map<String, dynamic> payload,
    @Default({}) Map<String, dynamic> result,
    @JsonKey(name: 'error_message') String? errorMessage,
    @Default(<JobLogEntryModel>[]) List<JobLogEntryModel> logs,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
  }) = _JobModel;

  factory JobModel.fromJson(Map<String, dynamic> json) => _$JobModelFromJson(json);
}
