import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';
import '../models/processing_job.dart';

class JobsService {
  final ApiClient _apiClient;

  JobsService(this._apiClient);

  Future<List<ProcessingJob>> getJobs({
    String? clipVersionId,
    ProcessingJobType? jobType,
    ProcessingJobStatus? status,
    int? page,
    int? limit,
  }) async {
    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/jobs',
        queryParameters: {
          if (clipVersionId != null) 'clip_version_id': clipVersionId,
          if (jobType != null) 'job_type': jobType.value,
          if (status != null) 'status': status.value,
          if (page != null) 'page': page,
          if (limit != null) 'limit': limit,
        },
      );
      
      final jobs = <ProcessingJob>[];
      for (final item in response.data!) {
        jobs.add(ProcessingJob.fromJson(item as Map<String, dynamic>));
      }
      
      return jobs;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ProcessingJob> getJob(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/jobs/$id');
      return ProcessingJob.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ProcessingJob> createJob({
    required ProcessingJobType jobType,
    required Map<String, dynamic> payload,
    String? clipVersionId,
    String? queueName,
    int priority = 0,
  }) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/jobs',
        data: {
          'job_type': jobType.value,
          'clip_version_id': clipVersionId,
          'queue_name': queueName,
          'priority': priority,
          'payload': payload,
        },
      );
      return ProcessingJob.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ProcessingJob> cancelJob(String id) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>('/jobs/$id/cancel');
      return ProcessingJob.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ProcessingJob> retryJob(String id) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>('/jobs/$id/retry');
      return ProcessingJob.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}