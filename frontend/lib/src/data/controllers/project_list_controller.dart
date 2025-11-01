import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/project.dart';
import '../repositories/project_repository.dart';

class ProjectListController extends StateNotifier<AsyncValue<List<Project>>> {
  ProjectListController(this._repository)
      : super(const AsyncValue<List<Project>>.loading());

  final ProjectRepository _repository;

  Future<void> loadProjects({bool forceRefresh = false}) async {
    state = const AsyncValue<List<Project>>.loading();
    final value = await AsyncValue.guard(() async {
      final projects = await _repository.fetchProjects(forceRefresh: forceRefresh);
      return List<Project>.unmodifiable(projects);
    });
    state = value;
  }

  Future<void> refresh() => loadProjects(forceRefresh: true);
}
