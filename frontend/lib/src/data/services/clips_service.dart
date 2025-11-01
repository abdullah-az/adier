import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';
import '../models/clip.dart';

class ClipsService {
  final ApiClient _apiClient;

  ClipsService(this._apiClient);

  Future<List<Clip>> getClips({
    String? projectId,
    ClipStatus? status,
    int? page,
    int? limit,
  }) async {
    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/clips',
        queryParameters: {
          if (projectId != null) 'project_id': projectId,
          if (status != null) 'status': status.value,
          if (page != null) 'page': page,
          if (limit != null) 'limit': limit,
        },
      );
      
      final clips = <Clip>[];
      for (final item in response.data!) {
        clips.add(Clip.fromJson(item as Map<String, dynamic>));
      }
      
      return clips;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Clip> getClip(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/clips/$id');
      return Clip.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Clip> createClip({
    required String projectId,
    required String title,
    String? description,
    String? sourceAssetId,
    double? startTime,
    double? endTime,
    ClipStatus? status,
  }) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/clips',
        data: {
          'project_id': projectId,
          'title': title,
          if (description != null) 'description': description,
          if (sourceAssetId != null) 'source_asset_id': sourceAssetId,
          if (startTime != null) 'start_time': startTime,
          if (endTime != null) 'end_time': endTime,
          'status': status?.value ?? ClipStatus.draft.value,
        },
      );
      return Clip.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Clip> updateClip(String id, {
    String? title,
    String? description,
    ClipStatus? status,
    double? startTime,
    double? endTime,
  }) async {
    try {
      final response = await _apiClient.patch<Map<String, dynamic>>(
        '/clips/$id',
        data: {
          if (title != null) 'title': title,
          if (description != null) 'description': description,
          if (status != null) 'status': status.value,
          if (startTime != null) 'start_time': startTime,
          if (endTime != null) 'end_time': endTime,
        },
      );
      return Clip.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<void> deleteClip(String id) async {
    try {
      await _apiClient.delete<void>('/clips/$id');
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<List<ClipVersion>> getClipVersions(String clipId) async {
    try {
      final response = await _apiClient.get<List<dynamic>>('/clips/$clipId/versions');
      
      final versions = <ClipVersion>[];
      for (final item in response.data!) {
        versions.add(ClipVersion.fromJson(item as Map<String, dynamic>));
      }
      
      return versions;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ClipVersion> getClipVersion(String clipId, int versionNumber) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/clips/$clipId/versions/$versionNumber');
      return ClipVersion.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<ClipVersion> createClipVersion({
    required String clipId,
    String? presetId,
    String? notes,
  }) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/clips/$clipId/versions',
        data: {
          if (presetId != null) 'preset_id': presetId,
          if (notes != null) 'notes': notes,
        },
      );
      return ClipVersion.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}