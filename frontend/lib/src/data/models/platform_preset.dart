import 'package:json_annotation/json_annotation.dart';
import 'base_model.dart';
import 'enums.dart';

part 'platform_preset.g.dart';

@JsonSerializable()
class PlatformPreset extends BaseModel {
  @JsonKey(name: 'key')
  final String key;
  
  @JsonKey(name: 'name')
  final String name;
  
  @JsonKey(name: 'category')
  final PresetCategory category;
  
  @JsonKey(name: 'description')
  final String? description;
  
  @JsonKey(name: 'configuration')
  final Map<String, dynamic> configuration;

  const PlatformPreset({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    required this.key,
    required this.name,
    required this.category,
    this.description,
    required this.configuration,
  });

  factory PlatformPreset.fromJson(Map<String, dynamic> json) =>
      _$PlatformPresetFromJson(json);

  Map<String, dynamic> toJson() => _$PlatformPresetToJson(this);

  PlatformPreset copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? key,
    String? name,
    PresetCategory? category,
    String? description,
    Map<String, dynamic>? configuration,
  }) {
    return PlatformPreset(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      key: key ?? this.key,
      name: name ?? this.name,
      category: category ?? this.category,
      description: description ?? this.description,
      configuration: configuration ?? this.configuration,
    );
  }
}