import '../api/video_editor_api_client.dart';
import '../models/media_asset.dart';
import '../models/upload_request.dart';

class MediaAssetRepository {
  const MediaAssetRepository({required VideoEditorApiClient apiClient})
      : _apiClient = apiClient;

  final VideoEditorApiClient _apiClient;

  Future<List<MediaAsset>> fetchMediaAssets(String projectId) async {
    final assets = await _apiClient.fetchMediaAssets(projectId);
    return List<MediaAsset>.unmodifiable(assets);
  }

  Future<MediaAsset> initiateUpload({
    required String projectId,
    required UploadRequest request,
  }) {
    return _apiClient.initiateUpload(projectId: projectId, request: request);
  }
}
