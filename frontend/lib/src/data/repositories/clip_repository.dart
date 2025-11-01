import '../api/video_editor_api_client.dart';
import '../models/clip.dart';

class ClipRepository {
  const ClipRepository({required VideoEditorApiClient apiClient})
      : _apiClient = apiClient;

  final VideoEditorApiClient _apiClient;

  Future<List<Clip>> fetchClips(String projectId) async {
    final clips = await _apiClient.fetchClips(projectId);
    return List<Clip>.unmodifiable(clips);
  }
}
