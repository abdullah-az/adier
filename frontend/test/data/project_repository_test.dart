import 'package:ai_video_editor_frontend/src/data/api/video_editor_api_client.dart';
import 'package:ai_video_editor_frontend/src/data/cache/project_cache.dart';
import 'package:ai_video_editor_frontend/src/data/models/clip.dart';
import 'package:ai_video_editor_frontend/src/data/models/media_asset.dart';
import 'package:ai_video_editor_frontend/src/data/models/project.dart';
import 'package:ai_video_editor_frontend/src/data/models/preset.dart';
import 'package:ai_video_editor_frontend/src/data/models/upload_request.dart';
import 'package:ai_video_editor_frontend/src/data/repositories/project_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ProjectRepository', () {
    late _MockVideoEditorApiClient apiClient;
    late InMemoryProjectCache cache;
    late ProjectRepository repository;

    setUp(() {
      apiClient = _MockVideoEditorApiClient();
      cache = InMemoryProjectCache();
      repository = ProjectRepository(apiClient: apiClient, cache: cache);
    });

    test('fetchProjects caches remote results', () async {
      final project = Project(
        id: 'remote-1',
        name: 'Remote Project',
        updatedAt: DateTime.utc(2024, 1, 1),
      );
      apiClient.projects = <Project>[project];

      final result = await repository.fetchProjects(forceRefresh: true);

      expect(result, equals(<Project>[project]));
      final cached = await cache.loadProjects();
      expect(cached, equals(<Project>[project]));
    });

    test('fetchProjects falls back to cache when api fails', () async {
      final cachedProject = Project(
        id: 'cached-1',
        name: 'Cached Project',
        updatedAt: DateTime.utc(2024, 2, 1),
      );
      await cache.saveProjects(<Project>[cachedProject]);
      apiClient.throwOnFetchProjects = true;

      final result = await repository.fetchProjects(forceRefresh: true);

      expect(result, equals(<Project>[cachedProject]));
    });

    test('fetchProjects rethrows when api fails and cache empty', () async {
      apiClient.throwOnFetchProjects = true;

      await expectLater(
        repository.fetchProjects(forceRefresh: true),
        throwsA(same(apiClient.exception)),
      );
    });

    test('getProjectById returns cached project when network fails', () async {
      final cachedProject = Project(
        id: 'cached-2',
        name: 'Cached Detail',
        updatedAt: DateTime.utc(2024, 3, 1),
      );
      await cache.saveProjects(<Project>[cachedProject]);
      apiClient.throwOnGetProject = true;

      final result = await repository.getProjectById('cached-2');

      expect(result, cachedProject);
    });

    test('createProject persists created project to cache', () async {
      final created = await repository.createProject('new-project');

      final cached = await cache.loadProjects();
      expect(cached, contains(created));
    });
  });
}

class _MockVideoEditorApiClient implements VideoEditorApiClient {
  List<Project> projects = <Project>[];
  bool throwOnFetchProjects = false;
  bool throwOnGetProject = false;
  final Exception exception = Exception('network-error');

  @override
  Future<Project> createProject(String name) async {
    final project = Project(
      id: 'generated-${projects.length + 1}',
      name: name,
      updatedAt: DateTime.utc(2024, 4, 1),
    );
    projects = <Project>[
      ...projects.where((existing) => existing.id != project.id),
      project,
    ];
    return project;
  }

  @override
  Future<List<Clip>> fetchClips(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<List<MediaAsset>> fetchMediaAssets(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<List<Project>> fetchProjects() async {
    if (throwOnFetchProjects) {
      throw exception;
    }
    return List<Project>.unmodifiable(projects);
  }

  @override
  Future<Project> getProjectById(String id) async {
    if (throwOnGetProject) {
      throw exception;
    }
    return projects.firstWhere(
      (project) => project.id == id,
      orElse: () => throw StateError('Project $id not found'),
    );
  }

  @override
  Future<MediaAsset> initiateUpload({
    required String projectId,
    required UploadRequest request,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<List<Preset>> fetchPresets() {
    throw UnimplementedError();
  }

  @override
  Future<Clip> updateClipTrim({
    required String clipId,
    required int inPointMs,
    required int outPointMs,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<Clip> mergeClips({
    required String projectId,
    required List<String> clipIds,
    String? description,
  }) {
    throw UnimplementedError();
  }
}
