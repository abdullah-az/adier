import '../api/video_editor_api_client.dart';
import '../models/preset.dart';

class PresetRepository {
  const PresetRepository({required VideoEditorApiClient apiClient})
      : _apiClient = apiClient;

  final VideoEditorApiClient _apiClient;

  Future<List<Preset>> fetchPresets() async {
    final presets = await _apiClient.fetchPresets();
    return List<Preset>.unmodifiable(presets);
  }
}
