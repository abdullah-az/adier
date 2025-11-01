// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'project.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Project _$ProjectFromJson(Map<String, dynamic> json) => Project(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      name: json['name'] as String,
      description: json['description'] as String?,
      status: ProjectStatus.fromString(json['status'] as String),
      storagePath: json['storage_path'] as String?,
    );

Map<String, dynamic> _$ProjectToJson(Project instance) => <String, dynamic>{
      'id': instance.id,
      'created_at': instance.createdAt.toIso8601String(),
      'updated_at': instance.updatedAt.toIso8601String(),
      'name': instance.name,
      'description': instance.description,
      'status': instance.status.value,
      'storage_path': instance.storagePath,
    };

ProjectCreateRequest _$ProjectCreateRequestFromJson(Map<String, dynamic> json) =>
    ProjectCreateRequest(
      name: json['name'] as String,
      description: json['description'] as String?,
      status: json['status'] == null
          ? null
          : ProjectStatus.fromString(json['status'] as String),
      storagePath: json['storage_path'] as String?,
    );

Map<String, dynamic> _$ProjectCreateRequestToJson(
        ProjectCreateRequest instance) =>
    <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'status': instance.status?.value,
      'storage_path': instance.storagePath,
    };

ProjectUpdateRequest _$ProjectUpdateRequestFromJson(Map<String, dynamic> json) =>
    ProjectUpdateRequest(
      name: json['name'] as String?,
      description: json['description'] as String?,
      status: json['status'] == null
          ? null
          : ProjectStatus.fromString(json['status'] as String),
      storagePath: json['storage_path'] as String?,
    );

Map<String, dynamic> _$ProjectUpdateRequestToJson(
        ProjectUpdateRequest instance) =>
    <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'status': instance.status?.value,
      'storage_path': instance.storagePath,
    };