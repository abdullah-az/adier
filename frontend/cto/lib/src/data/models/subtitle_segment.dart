import 'package:freezed_annotation/freezed_annotation.dart';

part 'subtitle_segment.freezed.dart';
part 'subtitle_segment.g.dart';

@freezed
class SubtitleSegment with _$SubtitleSegment {
  const factory SubtitleSegment({
    required int index,
    @JsonKey(name: 'start_time') required double startTime,
    @JsonKey(name: 'end_time') required double endTime,
    required String text,
    String? speaker,
    @Default({}) Map<String, dynamic> metadata,
  }) = _SubtitleSegment;

  factory SubtitleSegment.fromJson(Map<String, dynamic> json) =>
      _$SubtitleSegmentFromJson(json);
}

@freezed
class SubtitleSpec with _$SubtitleSpec {
  const factory SubtitleSpec({
    required String path,
    String? encoding,
    @JsonKey(name: 'force_style') String? forceStyle,
  }) = _SubtitleSpec;

  factory SubtitleSpec.fromJson(Map<String, dynamic> json) => _$SubtitleSpecFromJson(json);
}

@freezed
class TranscriptionResult with _$TranscriptionResult {
  const factory TranscriptionResult({
    @JsonKey(name: 'asset_id') required String assetId,
    required List<SubtitleSegment> segments,
    String? language,
    required double confidence,
    @JsonKey(name: 'full_text') String? fullText,
    @Default({}) Map<String, dynamic> metadata,
  }) = _TranscriptionResult;

  factory TranscriptionResult.fromJson(Map<String, dynamic> json) =>
      _$TranscriptionResultFromJson(json);
}
