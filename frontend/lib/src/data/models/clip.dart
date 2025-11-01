import 'package:json_annotation/json_annotation.dart';
import 'base_model.dart';
import 'enums.dart';

part 'clip.g.dart';

@JsonSerializable()
class Clip extends BaseModel {
  @JsonKey(name: 'project_id')
  final String projectId;
  
  @JsonKey(name: 'source_asset_id')
  final String? sourceAssetId;
  
  @JsonKey(name: 'title')
  final String title;
  
  @JsonKey(name: 'description')
  final String? description;
  
  @JsonKey(name: 'status')
  final ClipStatus status;
  
  @JsonKey(name: 'start_time')
  final double? startTime;
  
  @JsonKey(name: 'end_time')
  final double? endTime;

  const Clip({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    required this.projectId,
    this.sourceAssetId,
    required this.title,
    this.description,
    required this.status,
    this.startTime,
    this.endTime,
  });

  factory Clip.fromJson(Map<String, dynamic> json) =>
      _$ClipFromJson(json);

  Map<String, dynamic> toJson() => _$ClipToJson(this);

  Clip copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? projectId,
    String? sourceAssetId,
    String? title,
    String? description,
    ClipStatus? status,
    double? startTime,
    double? endTime,
  }) {
    return Clip(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      projectId: projectId ?? this.projectId,
      sourceAssetId: sourceAssetId ?? this.sourceAssetId,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
    );
  }
}

@JsonSerializable()
class ClipVersion extends BaseModel {
  @JsonKey(name: 'clip_id')
  final String clipId;
  
  @JsonKey(name: 'output_asset_id')
  final String? outputAssetId;
  
  @JsonKey(name: 'preset_id')
  final String? presetId;
  
  @JsonKey(name: 'version_number')
  final int versionNumber;
  
  @JsonKey(name: 'status')
  final ClipVersionStatus status;
  
  @JsonKey(name: 'notes')
  final String? notes;
  
  @JsonKey(name: 'quality_metrics')
  final Map<String, dynamic>? qualityMetrics;

  const ClipVersion({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    required this.clipId,
    this.outputAssetId,
    this.presetId,
    required this.versionNumber,
    required this.status,
    this.notes,
    this.qualityMetrics,
  });

  factory ClipVersion.fromJson(Map<String, dynamic> json) =>
      _$ClipVersionFromJson(json);

  Map<String, dynamic> toJson() => _$ClipVersionToJson(this);

  ClipVersion copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? clipId,
    String? outputAssetId,
    String? presetId,
    int? versionNumber,
    ClipVersionStatus? status,
    String? notes,
    Map<String, dynamic>? qualityMetrics,
  }) {
    return ClipVersion(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      clipId: clipId ?? this.clipId,
      outputAssetId: outputAssetId ?? this.outputAssetId,
      presetId: presetId ?? this.presetId,
      versionNumber: versionNumber ?? this.versionNumber,
      status: status ?? this.status,
      notes: notes ?? this.notes,
      qualityMetrics: qualityMetrics ?? this.qualityMetrics,
    );
  }
}