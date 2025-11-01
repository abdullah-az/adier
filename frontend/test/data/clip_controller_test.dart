import 'package:ai_video_editor_frontend/src/data/api/video_editor_api_client.dart';
import 'package:ai_video_editor_frontend/src/data/controllers/clip_controller.dart';
import 'package:ai_video_editor_frontend/src/data/models/clip.dart';
import 'package:ai_video_editor_frontend/src/data/models/media_asset.dart';
import 'package:ai_video_editor_frontend/src/data/models/project.dart';
import 'package:ai_video_editor_frontend/src/data/models/preset.dart';
import 'package:ai_video_editor_frontend/src/data/models/upload_request.dart';
import 'package:ai_video_editor_frontend/src/data/repositories/clip_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ClipController', () {
    late _FakeVideoEditorApiClient apiClient;
    late ClipRepository repository;
    late ClipController controller;

    setUp(() {
      apiClient = _FakeVideoEditorApiClient();
      repository = ClipRepository(apiClient: apiClient);
      controller = ClipController(repository, projectId: 'project-1');
    });

    test('loadClips emits data when request succeeds', () async {
      final clip = Clip(
        id: 'clip-1',
        projectId: 'project-1',
        sequence: 0,
        duration: const Duration(seconds: 5),
        playbackUrl: Uri.parse('https://stream.local/1'),
        createdAt: DateTime.utc(2024, 6, 1),
      );
      apiClient.clips = <Clip>[clip];

      final future = controller.loadClips();

      expect(controller.state.isLoading, isTrue);
      await future;

      expect(controller.state.hasValue, isTrue);
      expect(controller.state.value, equals(<Clip>[clip]));
    });

    test('loadClips emits error when request fails', () async {
      apiClient.shouldThrow = true;

      await controller.loadClips();

      expect(controller.state.hasError, isTrue);
      expect(controller.state.error, same(apiClient.exception));
    });
  });
}

class _FakeVideoEditorApiClient implements VideoEditorApiClient {
  List<Clip> clips = const <Clip>[];
  bool shouldThrow = false;
  final Exception exception = Exception('clips-error');

  @override
  Future<Project> createProject(String name) {
    throw UnimplementedError();
  }

  @override
  Future<List<Clip>> fetchClips(String projectId) async {
    if (shouldThrow) {
      throw exception;
    }
    return clips.where((clip) => clip.projectId == projectId).toList(growable: false);
  }

  @override
  Future<List<MediaAsset>> fetchMediaAssets(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<List<Project>> fetchProjects() {
    throw UnimplementedError();
  }

  @override
  Future<Project> getProjectById(String id) {
    throw UnimplementedError();
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
}
