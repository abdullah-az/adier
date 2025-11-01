// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'platform_preset.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PlatformPreset _$PlatformPresetFromJson(Map<String, dynamic> json) =>
    PlatformPreset(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      key: json['key'] as String,
      name: json['name'] as String,
      category: PresetCategory.fromString(json['category'] as String),
      description: json['description'] as String?,
      configuration: json['configuration'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$PlatformPresetToJson(PlatformPreset instance) =>
    <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'key': instance.key,
      'name': instance.name,
      'category': instance.category.value,
      'description': instance.description,
      'configuration': instance.configuration,
    };