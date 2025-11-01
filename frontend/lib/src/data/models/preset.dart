import 'package:flutter/foundation.dart';

@immutable
class Preset {
  const Preset({
    required this.id,
    required this.name,
    required this.createdAt,
    required this.settings,
    this.description,
  });

  final String id;
  final String name;
  final DateTime createdAt;
  final Map<String, dynamic> settings;
  final String? description;

  Preset copyWith({
    String? name,
    DateTime? createdAt,
    Map<String, dynamic>? settings,
    String? description,
  }) {
    return Preset(
      id: id,
      name: name ?? this.name,
      createdAt: createdAt ?? this.createdAt,
      settings: settings != null ? Map<String, dynamic>.unmodifiable(settings) : this.settings,
      description: description ?? this.description,
    );
  }

  factory Preset.fromJson(Map<String, dynamic> json) {
    return Preset(
      id: json['id'] as String,
      name: json['name'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      settings: Map<String, dynamic>.unmodifiable(
        Map<String, dynamic>.from(json['settings'] as Map<String, dynamic>),
      ),
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'name': name,
      'createdAt': createdAt.toIso8601String(),
      'settings': Map<String, dynamic>.from(settings),
      if (description != null) 'description': description,
    };
  }

  @override
  int get hashCode => Object.hash(id, name, createdAt, settings, description);

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) {
      return true;
    }
    return other is Preset &&
        other.id == id &&
        other.name == name &&
        other.createdAt == createdAt &&
        mapEquals(other.settings, settings) &&
        other.description == description;
  }

  @override
  String toString() => 'Preset(id: $id, name: $name)';
}
