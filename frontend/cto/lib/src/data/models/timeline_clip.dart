import 'package:freezed_annotation/freezed_annotation.dart';

import 'subtitle_segment.dart';

part 'timeline_clip.freezed.dart';
part 'timeline_clip.g.dart';

enum AspectRatio {
  @JsonValue('16:9') sixteenNine('16:9'),
  @JsonValue('9:16') nineSixteen('9:16'),
  @JsonValue('1:1') oneOne('1:1');

  const AspectRatio(this.value);
  final String value;
}

enum ResolutionPreset {
  @JsonValue('540p') p540('540p'),
  @JsonValue('720p') p720('720p'),
  @JsonValue('1080p') p1080('1080p');

  const ResolutionPreset(this.value);
  final String value;
}

enum TransitionType {
  @JsonValue('cut') cut('cut'),
  @JsonValue('crossfade') crossfade('crossfade'),
  @JsonValue('fade_to_black') fadeToBlack('fade_to_black'),
  @JsonValue('fade_to_white') fadeToWhite('fade_to_white');

  const TransitionType(this.value);
  final String value;
}

@freezed
class TransitionSpec with _$TransitionSpec {
  const factory TransitionSpec({
    @JsonKey(defaultValue: TransitionType.cut) TransitionType type,
    @JsonKey(defaultValue: 0.5) double duration,
    @JsonKey(defaultValue: 'fade') String style,
  }) = _TransitionSpec;

  factory TransitionSpec.fromJson(Map<String, dynamic> json) => _$TransitionSpecFromJson(json);
}

@freezed
class WatermarkSpec with _$WatermarkSpec {
  const factory WatermarkSpec({
    required String path,
    @JsonKey(defaultValue: 'top-right') String position,
    @JsonKey(defaultValue: 0.12) double scale,
    @JsonKey(defaultValue: 1.0) double opacity,
  }) = _WatermarkSpec;

  factory WatermarkSpec.fromJson(Map<String, dynamic> json) => _$WatermarkSpecFromJson(json);
}

@freezed
class MusicDuckingSpec with _$MusicDuckingSpec {
  const factory MusicDuckingSpec({
    @JsonKey(defaultValue: true) bool enabled,
    @JsonKey(defaultValue: 0.05) double threshold,
    @JsonKey(defaultValue: 6.0) double ratio,
    @JsonKey(defaultValue: 50.0) double attack,
    @JsonKey(defaultValue: 300.0) double release,
  }) = _MusicDuckingSpec;

  factory MusicDuckingSpec.fromJson(Map<String, dynamic> json) =>
      _$MusicDuckingSpecFromJson(json);
}

@freezed
class BackgroundMusicSpec with _$BackgroundMusicSpec {
  const factory BackgroundMusicSpec({
    String? track,
    @JsonKey(defaultValue: 0.25) double volume,
    @JsonKey(defaultValue: 0.0) double offset,
    @JsonKey(defaultValue: 1.5) double fadeIn,
    @JsonKey(defaultValue: 1.5) double fadeOut,
    @JsonKey(defaultValue: true) bool loop,
    MusicDuckingSpec? ducking,
  }) = _BackgroundMusicSpec;

  factory BackgroundMusicSpec.fromJson(Map<String, dynamic> json) =>
      _$BackgroundMusicSpecFromJson(json);
}

@freezed
class TimelineClip with _$TimelineClip {
  const factory TimelineClip({
    @JsonKey(name: 'asset_id') required String assetId,
    @JsonKey(name: 'in_point') @Default(0.0) double inPoint,
    @JsonKey(name: 'out_point') double? outPoint,
    @JsonKey(defaultValue: true) bool includeAudio,
    TransitionSpec? transition,
    SubtitleSpec? subtitles,
    WatermarkSpec? watermark,
  }) = _TimelineClip;

  factory TimelineClip.fromJson(Map<String, dynamic> json) => _$TimelineClipFromJson(json);
}

@freezed
class ExportTemplate with _$ExportTemplate {
  const factory ExportTemplate({
    required String name,
    @JsonKey(defaultValue: 'mp4') String format,
    required int width,
    required int height,
    AspectRatio? aspectRatio,
    @JsonKey(name: 'video_bitrate') String? videoBitrate,
    @JsonKey(name: 'audio_bitrate') String? audioBitrate,
    @JsonKey(defaultValue: false) bool proxy,
    @JsonKey(name: 'generate_thumbnails', defaultValue: true) bool generateThumbnails,
    WatermarkSpec? watermark,
  }) = _ExportTemplate;

  factory ExportTemplate.fromJson(Map<String, dynamic> json) =>
      _$ExportTemplateFromJson(json);
}

@freezed
class TimelineCompositionRequest with _$TimelineCompositionRequest {
  const factory TimelineCompositionRequest({
    required List<TimelineClip> clips,
    @JsonKey(name: 'aspect_ratio') AspectRatio? aspectRatio,
    @JsonKey(name: 'resolution') ResolutionPreset? resolution,
    @JsonKey(name: 'proxy_resolution') ResolutionPreset? proxyResolution,
    @JsonKey(name: 'background_music') BackgroundMusicSpec? backgroundMusic,
    @JsonKey(name: 'export_templates') List<ExportTemplate>? exportTemplates,
    @JsonKey(name: 'default_watermark') WatermarkSpec? defaultWatermark,
    @JsonKey(name: 'global_subtitles') SubtitleSpec? globalSubtitles,
    @JsonKey(name: 'generate_thumbnails', defaultValue: true) bool generateThumbnails,
  }) = _TimelineCompositionRequest;

  factory TimelineCompositionRequest.fromJson(Map<String, dynamic> json) =>
      _$TimelineCompositionRequestFromJson(json);
}

@freezed
class GeneratedMedia with _$GeneratedMedia {
  const factory GeneratedMedia({
    @JsonKey(name: 'asset_id') required String assetId,
    required String name,
    required String category,
    @JsonKey(name: 'relative_path') required String relativePath,
    @Default({}) Map<String, dynamic> metadata,
  }) = _GeneratedMedia;

  factory GeneratedMedia.fromJson(Map<String, dynamic> json) =>
      _$GeneratedMediaFromJson(json);
}

@freezed
class ThumbnailInfo with _$ThumbnailInfo {
  const factory ThumbnailInfo({
    required String path,
    @JsonKey(name: 'clip_index') int? clipIndex,
    @JsonKey(defaultValue: 0.0) double timestamp,
    @JsonKey(defaultValue: 'clip') String context,
  }) = _ThumbnailInfo;

  factory ThumbnailInfo.fromJson(Map<String, dynamic> json) =>
      _$ThumbnailInfoFromJson(json);
}

@freezed
class TimelineCompositionResult with _$TimelineCompositionResult {
  const factory TimelineCompositionResult({
    required GeneratedMedia timeline,
    GeneratedMedia? proxy,
    @Default(<GeneratedMedia>[]) List<GeneratedMedia> exports,
    @Default(<ThumbnailInfo>[]) List<ThumbnailInfo> thumbnails,
  }) = _TimelineCompositionResult;

  factory TimelineCompositionResult.fromJson(Map<String, dynamic> json) =>
      _$TimelineCompositionResultFromJson(json);
}
