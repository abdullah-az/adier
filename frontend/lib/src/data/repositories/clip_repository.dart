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

  Future<Clip> updateClipTrim({
    required String clipId,
    required int inPointMs,
    required int outPointMs,
  }) async {
    final updated = await _apiClient.updateClipTrim(
      clipId: clipId,
      inPointMs: inPointMs,
      outPointMs: outPointMs,
    );
    return updated;
  }

  Future<Clip> mergeClips({
    required String projectId,
    required List<String> clipIds,
    String? description,
  }) async {
    final merged = await _apiClient.mergeClips(
      projectId: projectId,
      clipIds: clipIds,
      description: description,
    );
    return merged;
  }
}
