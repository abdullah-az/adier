import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';
import '../models/project.dart';

class ProjectsService {
  final ApiClient _apiClient;

  ProjectsService(this._apiClient);

  Future<List<Project>> getProjects({int? page, int? limit}) async {
    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/projects',
        queryParameters: {
          if (page != null) 'page': page,
          if (limit != null) 'limit': limit,
        },
      );
      
      final projects = <Project>[];
      for (final item in response.data!) {
        projects.add(Project.fromJson(item as Map<String, dynamic>));
      }
      
      return projects;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Project> getProject(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/projects/$id');
      return Project.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Project> createProject(ProjectCreateRequest request) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/projects',
        data: request.toJson(),
      );
      return Project.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<Project> updateProject(String id, ProjectUpdateRequest request) async {
    try {
      final response = await _apiClient.patch<Map<String, dynamic>>(
        '/projects/$id',
        data: request.toJson(),
      );
      return Project.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<void> deleteProject(String id) async {
    try {
      await _apiClient.delete<void>('/projects/$id');
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}