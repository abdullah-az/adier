import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../errors/api_failure.dart';
import '../models/export_job.dart';
import '../models/scene_suggestion.dart';
import '../models/subtitle_segment.dart';
import '../models/timeline_clip.dart';

class ProcessingRepository {
  ProcessingRepository(this._client);

  final ApiClient _client;

  Future<ExportJob> createJob({
    required String projectId,
    required String jobType,
    Map<String, dynamic>? payload,
    int? maxAttempts,
    double? retryDelaySeconds,
  }) async {
    try {
      final response = await _client.post<Map<String, dynamic>>(
        '/projects/$projectId/jobs',
        data: {
          'job_type': jobType,
          if (payload != null) 'payload': payload,
          if (maxAttempts != null) 'max_attempts': maxAttempts,
          if (retryDelaySeconds != null) 'retry_delay_seconds': retryDelaySeconds,
        },
      );
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return ExportJob.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<List<ExportJob>> listJobs(
    String projectId, {
    List<ExportJobStatus>? statuses,
  }) async {
    try {
      final response = await _client.get<List<dynamic>>(
        '/projects/$projectId/jobs',
        queryParameters: statuses != null && statuses.isNotEmpty
            ? {'status': statuses.map((s) => s.value).toList()}
            : null,
      );
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return response.data!
          .cast<Map<String, dynamic>>()
          .map((json) => ExportJob.fromJson(json))
          .toList();
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<ExportJob> getJob(String projectId, String jobId) async {
    try {
      final response = await _client.get<Map<String, dynamic>>('/projects/$projectId/jobs/$jobId');
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return ExportJob.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<ExportJob> submitIngestJob({
    required String projectId,
    required String assetId,
  }) async {
    return createJob(
      projectId: projectId,
      jobType: 'ingest',
      payload: {'asset_id': assetId},
    );
  }

  Future<ExportJob> submitSceneDetectionJob({
    required String projectId,
    required String assetId,
  }) async {
    return createJob(
      projectId: projectId,
      jobType: 'scene_detection',
      payload: {'asset_id': assetId},
    );
  }

  Future<ExportJob> submitTranscriptionJob({
    required String projectId,
    required String assetId,
    String? language,
  }) async {
    return createJob(
      projectId: projectId,
      jobType: 'transcription',
      payload: {
        'asset_id': assetId,
        if (language != null) 'language': language,
      },
    );
  }

  Future<ExportJob> submitExportJob({
    required String projectId,
    required TimelineCompositionRequest request,
  }) async {
    return createJob(
      projectId: projectId,
      jobType: 'export',
      payload: request.toJson(),
    );
  }

  Future<SceneDetectionResult?> getSceneDetectionResult(ExportJob job) async {
    try {
      if (job.status != ExportJobStatus.completed) {
        return null;
      }
      final result = job.result;
      if (result.isEmpty) {
        return null;
      }
      return SceneDetectionResult.fromJson(result);
    } catch (e) {
      throw ParsingFailure(
        message: 'Failed to parse scene detection result',
        exception: e is Exception ? e : null,
      );
    }
  }

  Future<TranscriptionResult?> getTranscriptionResult(ExportJob job) async {
    try {
      if (job.status != ExportJobStatus.completed) {
        return null;
      }
      final result = job.result;
      if (result.isEmpty) {
        return null;
      }
      return TranscriptionResult.fromJson(result);
    } catch (e) {
      throw ParsingFailure(
        message: 'Failed to parse transcription result',
        exception: e is Exception ? e : null,
      );
    }
  }

  Future<TimelineCompositionResult?> getExportResult(ExportJob job) async {
    try {
      if (job.status != ExportJobStatus.completed) {
        return null;
      }
      final result = job.result;
      if (result.isEmpty) {
        return null;
      }
      return TimelineCompositionResult.fromJson(result);
    } catch (e) {
      throw ParsingFailure(
        message: 'Failed to parse export result',
        exception: e is Exception ? e : null,
      );
    }
  }

  Stream<ExportJob> watchJob(String projectId, String jobId) async* {
    try {
      var currentJob = await getJob(projectId, jobId);
      yield currentJob;

      while (currentJob.status == ExportJobStatus.queued ||
          currentJob.status == ExportJobStatus.running) {
        await Future.delayed(const Duration(seconds: 2));
        currentJob = await getJob(projectId, jobId);
        yield currentJob;
      }
    } catch (e) {
      throw mapDioError(e);
    }
  }
}

final processingRepositoryProvider = Provider<ProcessingRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return ProcessingRepository(client);
});
