// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'processing_job.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProcessingJob _$ProcessingJobFromJson(Map<String, dynamic> json) =>
    ProcessingJob(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      clipVersionId: json['clip_version_id'] as String?,
      jobType: ProcessingJobType.fromString(json['job_type'] as String),
      status: ProcessingJobStatus.fromString(json['status'] as String),
      queueName: json['queue_name'] as String?,
      priority: json['priority'] as int,
      payload: json['payload'] as Map<String, dynamic>,
      resultPayload: json['result_payload'] as Map<String, dynamic>?,
      errorMessage: json['error_message'] as String?,
      startedAt: json['started_at'] == null
          ? null
          : DateTime.parse(json['started_at'] as String),
      completedAt: json['completed_at'] == null
          ? null
          : DateTime.parse(json['completed_at'] as String),
    );

Map<String, dynamic> _$ProcessingJobToJson(ProcessingJob instance) =>
    <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'clip_version_id': instance.clipVersionId,
      'job_type': instance.jobType.value,
      'status': instance.status.value,
      'queue_name': instance.queueName,
      'priority': instance.priority,
      'payload': instance.payload,
      'result_payload': instance.resultPayload,
      'error_message': instance.errorMessage,
      'started_at': instance.startedAt?.toIso8601String(),
      'completed_at': instance.completedAt?.toIso8601String(),
    };