import 'package:freezed_annotation/freezed_annotation.dart';

part 'export_job.freezed.dart';
part 'export_job.g.dart';

enum ExportJobStatus {
  @JsonValue('queued') queued('queued'),
  @JsonValue('running') running('running'),
  @JsonValue('completed') completed('completed'),
  @JsonValue('failed') failed('failed');

  const ExportJobStatus(this.value);
  final String value;
}

@freezed
class JobLogEntry with _$JobLogEntry {
  const factory JobLogEntry({
    required DateTime timestamp,
    required String level,
    required String message,
    @Default({}) Map<String, dynamic> details,
  }) = _JobLogEntry;

  factory JobLogEntry.fromJson(Map<String, dynamic> json) => _$JobLogEntryFromJson(json);
}

@freezed
class ExportJob with _$ExportJob {
  const factory ExportJob({
    required String id,
    @JsonKey(name: 'project_id') required String projectId,
    @JsonKey(name: 'job_type') required String jobType,
    required ExportJobStatus status,
    required double progress,
    required int attempts,
    @JsonKey(name: 'max_attempts') required int maxAttempts,
    @JsonKey(name: 'retry_delay_seconds') required double retryDelaySeconds,
    @Default({}) Map<String, dynamic> payload,
    @Default({}) Map<String, dynamic> result,
    @JsonKey(name: 'error_message') String? errorMessage,
    @Default(<JobLogEntry>[]) List<JobLogEntry> logs,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'updated_at') required DateTime updatedAt,
  }) = _ExportJob;

  factory ExportJob.fromJson(Map<String, dynamic> json) => _$ExportJobFromJson(json);
}
