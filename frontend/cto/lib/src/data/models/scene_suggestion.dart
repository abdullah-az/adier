import 'package:freezed_annotation/freezed_annotation.dart';

part 'scene_suggestion.freezed.dart';
part 'scene_suggestion.g.dart';

@freezed
class SceneSuggestion with _$SceneSuggestion {
  const factory SceneSuggestion({
    required String id,
    @JsonKey(name: 'asset_id') required String assetId,
    @JsonKey(name: 'start_time') required double startTime,
    @JsonKey(name: 'end_time') required double endTime,
    required double confidence,
    @JsonKey(name: 'scene_type') String? sceneType,
    String? description,
    @Default({}) Map<String, dynamic> metadata,
  }) = _SceneSuggestion;

  factory SceneSuggestion.fromJson(Map<String, dynamic> json) =>
      _$SceneSuggestionFromJson(json);
}

@freezed
class SceneDetectionResult with _$SceneDetectionResult {
  const factory SceneDetectionResult({
    @JsonKey(name: 'asset_id') required String assetId,
    required List<SceneSuggestion> scenes,
    @JsonKey(name: 'total_duration') required double totalDuration,
    @Default({}) Map<String, dynamic> metadata,
  }) = _SceneDetectionResult;

  factory SceneDetectionResult.fromJson(Map<String, dynamic> json) =>
      _$SceneDetectionResultFromJson(json);
}
