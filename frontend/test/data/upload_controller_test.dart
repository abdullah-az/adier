import 'package:ai_video_editor_frontend/src/data/api/video_editor_api_client.dart';
import 'package:ai_video_editor_frontend/src/data/models/clip.dart';
import 'package:ai_video_editor_frontend/src/data/models/media_asset.dart';
import 'package:ai_video_editor_frontend/src/data/models/project.dart';
import 'package:ai_video_editor_frontend/src/data/models/preset.dart';
import 'package:ai_video_editor_frontend/src/data/models/upload_request.dart';
import 'package:ai_video_editor_frontend/src/data/repositories/media_asset_repository.dart';
import 'package:ai_video_editor_frontend/src/data/controllers/upload_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('UploadController', () {
    late _FakeVideoEditorApiClient apiClient;
    late MediaAssetRepository repository;
    late UploadController controller;

    setUp(() {
      apiClient = _FakeVideoEditorApiClient();
      repository = MediaAssetRepository(apiClient: apiClient);
      controller = UploadController(repository);
    });

    test('emits loading then data on successful upload initiation', () async {
      final uploadRequest = UploadRequest(
        fileName: 'clip.mp4',
        mimeType: 'video/mp4',
        fileSizeBytes: 1024,
      );
      final asset = MediaAsset(
        id: 'asset-1',
        projectId: 'project-1',
        fileName: uploadRequest.fileName,
        status: MediaAssetStatus.uploading,
        createdAt: DateTime.utc(2024, 5, 1),
        uploadUrl: Uri.parse('https://upload.local/asset-1'),
        sizeBytes: uploadRequest.fileSizeBytes,
        mimeType: uploadRequest.mimeType,
      );
      apiClient.uploadResponse = asset;

      final future = controller.initiateUpload(
        projectId: 'project-1',
        request: uploadRequest,
      );

      expect(controller.state.isLoading, isTrue);
      await future;

      expect(controller.state.hasValue, isTrue);
      expect(controller.state.value, asset);
    });

    test('emits error state when upload initiation fails', () async {
      final uploadRequest = UploadRequest(
        fileName: 'clip.mp4',
        mimeType: 'video/mp4',
        fileSizeBytes: 1024,
      );
      apiClient.shouldThrow = true;

      await controller.initiateUpload(
        projectId: 'project-1',
        request: uploadRequest,
      );

      expect(controller.state.hasError, isTrue);
      expect(controller.state.error, same(apiClient.exception));
    });

    test('reset clears the state back to null data', () {
      controller.reset();

      expect(controller.state.hasValue, isTrue);
      expect(controller.state.value, isNull);
    });
  });
}

class _FakeVideoEditorApiClient implements VideoEditorApiClient {
  MediaAsset? uploadResponse;
  bool shouldThrow = false;
  final Exception exception = Exception('upload-failed');

  @override
  Future<Project> createProject(String name) {
    throw UnimplementedError();
  }

  @override
  Future<List<Clip>> fetchClips(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<List<MediaAsset>> fetchMediaAssets(String projectId) async {
    return const <MediaAsset>[];
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
  }) async {
    if (shouldThrow || uploadResponse == null) {
      throw exception;
    }
    return uploadResponse!;
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
