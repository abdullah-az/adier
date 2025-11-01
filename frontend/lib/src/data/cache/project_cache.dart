import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/project.dart';

abstract class ProjectCache {
  Future<List<Project>> loadProjects();

  Future<void> saveProjects(List<Project> projects);

  Future<void> clear();
}

class SharedPreferencesProjectCache implements ProjectCache {
  SharedPreferencesProjectCache({Future<SharedPreferences> Function()? instanceBuilder})
      : _instanceBuilder = instanceBuilder ?? SharedPreferences.getInstance;

  static const String _cacheKey = 'app_cached_projects';
  final Future<SharedPreferences> Function() _instanceBuilder;

  @override
  Future<void> clear() async {
    final prefs = await _instanceBuilder();
    await prefs.remove(_cacheKey);
  }

  @override
  Future<List<Project>> loadProjects() async {
    final prefs = await _instanceBuilder();
    final raw = prefs.getString(_cacheKey);
    if (raw == null || raw.isEmpty) {
      return List<Project>.unmodifiable(const <Project>[]);
    }

    final dynamic decoded = jsonDecode(raw);
    if (decoded is! List<dynamic>) {
      return List<Project>.unmodifiable(const <Project>[]);
    }
    final List<Map<String, dynamic>> entries = decoded.cast<Map<String, dynamic>>();
    final projects = entries.map(Project.fromJson).toList(growable: false);
    return List<Project>.unmodifiable(projects);
  }

  @override
  Future<void> saveProjects(List<Project> projects) async {
    final prefs = await _instanceBuilder();
    final payload = jsonEncode(
      projects.map((project) => project.toJson()).toList(growable: false),
    );
    await prefs.setString(_cacheKey, payload);
  }
}

@visibleForTesting
class InMemoryProjectCache implements ProjectCache {
  InMemoryProjectCache([List<Project>? projects])
      : _projects = List<Project>.from(projects ?? const <Project>[]);

  final List<Project> _projects;

  @override
  Future<void> clear() async {
    _projects.clear();
  }

  @override
  Future<List<Project>> loadProjects() async {
    return List<Project>.unmodifiable(_projects);
  }

  @override
  Future<void> saveProjects(List<Project> projects) async {
    _projects
      ..clear()
      ..addAll(projects);
  }
}
