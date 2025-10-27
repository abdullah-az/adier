import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/project_model.dart';

typedef UploadProgressCallback = void Function(int sentBytes, int totalBytes);

class ProjectRepository {
  ProjectRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<List<ProjectModel>> fetchProjects() async {
    try {
      final response = await _dio.get('/projects');
      final data = response.data;
      if (data is List) {
        return data
            .map((raw) => ProjectModel.fromJson(raw as Map<String, dynamic>))
            .toList();
      }
      throw const FormatException('Invalid response format for projects list');
    } catch (error, stackTrace) {
      Error.throwWithStackTrace(
        Exception('Failed to load projects: $error'),
        stackTrace,
      );
    }
  }

  Future<ProjectModel> fetchProject(String id) async {
    try {
      final response = await _dio.get('/projects/$id');
      final data = response.data;
      if (data is Map<String, dynamic>) {
        return ProjectModel.fromJson(data);
      }
      throw const FormatException('Invalid response format for project');
    } catch (error, stackTrace) {
      Error.throwWithStackTrace(
        Exception('Failed to load project: $error'),
        stackTrace,
      );
    }
  }

  Future<ProjectModel> uploadVideo({
    required String fileName,
    String? filePath,
    List<int>? bytes,
    Map<String, dynamic>? metadata,
    UploadProgressCallback? onProgress,
    CancelToken? cancelToken,
  }) async {
    if (filePath == null && bytes == null) {
      throw ArgumentError('Either filePath or bytes must be provided.');
    }

    final multipartFile = bytes != null
        ? MultipartFile.fromBytes(bytes, filename: fileName)
        : await MultipartFile.fromFile(filePath!, filename: fileName);

    final payload = <String, dynamic>{
      'file': multipartFile,
      if (metadata != null) ...metadata,
    };

    try {
      final response = await _dio.post(
        '/projects/upload',
        data: FormData.fromMap(payload),
        onSendProgress: onProgress,
        cancelToken: cancelToken,
      );
      final data = response.data;
      if (data is Map<String, dynamic>) {
        return ProjectModel.fromJson(data);
      }
      throw const FormatException('Invalid response format for upload');
    } catch (error, stackTrace) {
      Error.throwWithStackTrace(
        Exception('Failed to upload video: $error'),
        stackTrace,
      );
    }
  }

  Future<ProjectModel?> triggerProcessing(String projectId) async {
    try {
      final response = await _dio.post('/projects/$projectId/process');
      final data = response.data;
      if (data is Map<String, dynamic>) {
        return ProjectModel.fromJson(data);
      }
      return null;
    } catch (_) {
      // Processing trigger failures should not block the upload flow.
      return null;
    }
  }
}
