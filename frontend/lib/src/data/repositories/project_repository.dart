import '../api/video_editor_api_client.dart';
import '../cache/project_cache.dart';
import '../models/project.dart';

class ProjectRepository {
  ProjectRepository({
    required VideoEditorApiClient apiClient,
    required ProjectCache cache,
  })  : _apiClient = apiClient,
        _cache = cache;

  final VideoEditorApiClient _apiClient;
  final ProjectCache _cache;

  Future<List<Project>> fetchProjects({bool forceRefresh = false}) async {
    if (!forceRefresh) {
      final cachedProjects = await _cache.loadProjects();
      if (cachedProjects.isNotEmpty) {
        return List<Project>.unmodifiable(cachedProjects);
      }
    }

    try {
      final projects = await _apiClient.fetchProjects();
      await _cache.saveProjects(projects);
      return List<Project>.unmodifiable(projects);
    } catch (error, stackTrace) {
      final cachedProjects = await _cache.loadProjects();
      if (cachedProjects.isNotEmpty) {
        return List<Project>.unmodifiable(cachedProjects);
      }
      Error.throwWithStackTrace(error, stackTrace);
    }
  }

  Future<Project> getProjectById(String id) async {
    try {
      final project = await _apiClient.getProjectById(id);
      await _upsertProject(project);
      return project;
    } catch (error, stackTrace) {
      final cachedProjects = await _cache.loadProjects();
      for (final project in cachedProjects) {
        if (project.id == id) {
          return project;
        }
      }
      Error.throwWithStackTrace(error, stackTrace);
    }
  }

  Future<Project> createProject(String name) async {
    final project = await _apiClient.createProject(name);
    await _upsertProject(project);
    return project;
  }

  Future<void> clearCache() => _cache.clear();

  Future<void> _upsertProject(Project project) async {
    final cachedProjects = await _cache.loadProjects();
    final List<Project> updated = <Project>[];
    var replaced = false;
    for (final item in cachedProjects) {
      if (item.id == project.id) {
        updated.add(project);
        replaced = true;
      } else {
        updated.add(item);
      }
    }
    if (!replaced) {
      updated.add(project);
    }
    await _cache.saveProjects(updated);
  }
}
