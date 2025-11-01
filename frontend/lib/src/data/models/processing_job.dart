import 'package:json_annotation/json_annotation.dart';
import 'base_model.dart';
import 'enums.dart';

part 'processing_job.g.dart';

@JsonSerializable()
class ProcessingJob extends BaseModel {
  @JsonKey(name: 'clip_version_id')
  final String? clipVersionId;
  
  @JsonKey(name: 'job_type')
  final ProcessingJobType jobType;
  
  @JsonKey(name: 'status')
  final ProcessingJobStatus status;
  
  @JsonKey(name: 'queue_name')
  final String? queueName;
  
  @JsonKey(name: 'priority')
  final int priority;
  
  @JsonKey(name: 'payload')
  final Map<String, dynamic> payload;
  
  @JsonKey(name: 'result_payload')
  final Map<String, dynamic>? resultPayload;
  
  @JsonKey(name: 'error_message')
  final String? errorMessage;
  
  @JsonKey(name: 'started_at')
  final DateTime? startedAt;
  
  @JsonKey(name: 'completed_at')
  final DateTime? completedAt;

  const ProcessingJob({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    this.clipVersionId,
    required this.jobType,
    required this.status,
    this.queueName,
    required this.priority,
    required this.payload,
    this.resultPayload,
    this.errorMessage,
    this.startedAt,
    this.completedAt,
  });

  factory ProcessingJob.fromJson(Map<String, dynamic> json) =>
      _$ProcessingJobFromJson(json);

  Map<String, dynamic> toJson() => _$ProcessingJobToJson(this);

  ProcessingJob copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? clipVersionId,
    ProcessingJobType? jobType,
    ProcessingJobStatus? status,
    String? queueName,
    int? priority,
    Map<String, dynamic>? payload,
    Map<String, dynamic>? resultPayload,
    String? errorMessage,
    DateTime? startedAt,
    DateTime? completedAt,
  }) {
    return ProcessingJob(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      clipVersionId: clipVersionId ?? this.clipVersionId,
      jobType: jobType ?? this.jobType,
      status: status ?? this.status,
      queueName: queueName ?? this.queueName,
      priority: priority ?? this.priority,
      payload: payload ?? this.payload,
      resultPayload: resultPayload ?? this.resultPayload,
      errorMessage: errorMessage ?? this.errorMessage,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }
}