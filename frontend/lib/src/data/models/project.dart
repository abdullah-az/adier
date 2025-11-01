import 'package:json_annotation/json_annotation.dart';
import 'base_model.dart';
import 'enums.dart';

part 'project.g.dart';

@JsonSerializable()
class Project extends BaseModel {
  @JsonKey(name: 'name')
  final String name;
  
  @JsonKey(name: 'description')
  final String? description;
  
  @JsonKey(name: 'status')
  final ProjectStatus status;
  
  @JsonKey(name: 'storage_path')
  final String? storagePath;

  const Project({
    required super.id,
    required super.createdAt,
    required super.updatedAt,
    required this.name,
    this.description,
    required this.status,
    this.storagePath,
  });

  factory Project.fromJson(Map<String, dynamic> json) =>
      _$ProjectFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectToJson(this);

  Project copyWith({
    String? id,
    DateTime? createdAt,
    DateTime? updatedAt,
    String? name,
    String? description,
    ProjectStatus? status,
    String? storagePath,
  }) {
    return Project(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      name: name ?? this.name,
      description: description ?? this.description,
      status: status ?? this.status,
      storagePath: storagePath ?? this.storagePath,
    );
  }
}

@JsonSerializable()
class ProjectCreateRequest {
  @JsonKey(name: 'name')
  final String name;
  
  @JsonKey(name: 'description')
  final String? description;
  
  @JsonKey(name: 'status')
  final ProjectStatus? status;
  
  @JsonKey(name: 'storage_path')
  final String? storagePath;

  const ProjectCreateRequest({
    required this.name,
    this.description,
    this.status,
    this.storagePath,
  });

  factory ProjectCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$ProjectCreateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectCreateRequestToJson(this);
}

@JsonSerializable()
class ProjectUpdateRequest {
  @JsonKey(name: 'name')
  final String? name;
  
  @JsonKey(name: 'description')
  final String? description;
  
  @JsonKey(name: 'status')
  final ProjectStatus? status;
  
  @JsonKey(name: 'storage_path')
  final String? storagePath;

  const ProjectUpdateRequest({
    this.name,
    this.description,
    this.status,
    this.storagePath,
  });

  factory ProjectUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$ProjectUpdateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectUpdateRequestToJson(this);
}