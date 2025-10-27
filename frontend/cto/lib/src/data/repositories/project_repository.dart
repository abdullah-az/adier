import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../errors/api_failure.dart';
import '../models/project.dart';
import '../models/video_asset.dart';

class ProjectRepository {
  ProjectRepository(this._client);

  final ApiClient _client;

  Future<Project> getProject(String projectId) async {
    try {
      final response = await _client.get<Map<String, dynamic>>('/projects/$projectId');
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return Project.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<List<Project>> getProjects() async {
    try {
      final response = await _client.get<List<dynamic>>('/projects');
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return response.data!
          .cast<Map<String, dynamic>>()
          .map((json) => Project.fromJson(json))
          .toList();
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Project> createProject({
    required String name,
    String? description,
    Map<String, dynamic>? metadata,
  }) async {
    try {
      final response = await _client.post<Map<String, dynamic>>(
        '/projects',
        data: {
          'name': name,
          if (description != null) 'description': description,
          if (metadata != null) 'metadata': metadata,
        },
      );
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return Project.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<Project> updateProject(
    String projectId, {
    String? name,
    String? description,
    Map<String, dynamic>? metadata,
  }) async {
    try {
      final response = await _client.put<Map<String, dynamic>>(
        '/projects/$projectId',
        data: {
          if (name != null) 'name': name,
          if (description != null) 'description': description,
          if (metadata != null) 'metadata': metadata,
        },
      );
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return Project.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<void> deleteProject(String projectId) async {
    try {
      await _client.delete('/projects/$projectId');
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<List<VideoAsset>> getProjectVideos(String projectId) async {
    try {
      final response = await _client.get<List<dynamic>>('/projects/$projectId/videos');
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return response.data!
          .cast<Map<String, dynamic>>()
          .map((json) => VideoAsset.fromJson(json))
          .toList();
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<VideoUploadResponse> uploadVideo(
    String projectId, {
    required String filePath,
    required String fileName,
    void Function(double progress)? onProgress,
    CancelToken? cancelToken,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          filePath,
          filename: fileName,
        ),
      });

      final response = await _client.post<Map<String, dynamic>>(
        '/projects/$projectId/videos',
        data: formData,
        cancelToken: cancelToken,
        onSendProgress: onProgress != null
            ? (sent, total) {
                onProgress(sent / total);
              }
            : null,
      );

      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return VideoUploadResponse.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<void> deleteVideo(String projectId, String assetId) async {
    try {
      await _client.delete('/projects/$projectId/videos/$assetId');
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<StorageStats> getProjectStorageStats(String projectId) async {
    try {
      final response =
          await _client.get<Map<String, dynamic>>('/projects/$projectId/storage/stats');
      if (response.data == null) {
        throw ParsingFailure(message: 'Empty response from server');
      }
      return StorageStats.fromJson(response.data!);
    } catch (e) {
      throw mapDioError(e);
    }
  }

  Future<void> clearProjectStorage(String projectId) async {
    try {
      await _client.delete('/projects/$projectId/storage');
    } catch (e) {
      throw mapDioError(e);
    }
  }
}

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return ProjectRepository(client);
});
