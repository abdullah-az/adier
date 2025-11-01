import 'package:flutter/foundation.dart';

@immutable
class Project {
  const Project({
    required this.id,
    required this.name,
    required this.updatedAt,
    this.thumbnailUrl,
    this.description,
  });

  final String id;
  final String name;
  final DateTime updatedAt;
  final String? thumbnailUrl;
  final String? description;

  Project copyWith({
    String? name,
    DateTime? updatedAt,
    String? thumbnailUrl,
    String? description,
  }) {
    return Project(
      id: id,
      name: name ?? this.name,
      updatedAt: updatedAt ?? this.updatedAt,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      description: description ?? this.description,
    );
  }

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'] as String,
      name: json['name'] as String,
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      thumbnailUrl: json['thumbnailUrl'] as String?,
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'name': name,
      'updatedAt': updatedAt.toIso8601String(),
      if (thumbnailUrl != null) 'thumbnailUrl': thumbnailUrl,
      if (description != null) 'description': description,
    };
  }

  @override
  int get hashCode => Object.hash(id, name, updatedAt, thumbnailUrl, description);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) {
      return true;
    }
    return other is Project &&
        other.id == id &&
        other.name == name &&
        other.updatedAt == updatedAt &&
        other.thumbnailUrl == thumbnailUrl &&
        other.description == description;
  }

  @override
  String toString() => 'Project(id: $id, name: $name)';
}
