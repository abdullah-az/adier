import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/project_summary_model.dart';
import '../../../data/providers/project_provider.dart';

class ProjectLibraryNotifier
    extends AutoDisposeAsyncNotifier<List<ProjectSummaryModel>> {
  Timer? _pollTimer;

  @override
  Future<List<ProjectSummaryModel>> build() async {
    ref.onDispose(() => _pollTimer?.cancel());

    final projects = await _fetchProjects();
    _startPolling();
    return projects;
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchProjects);
  }

  Future<List<ProjectSummaryModel>> _fetchProjects() async {
    final repository = ref.read(projectRepositoryProvider);
    return repository.fetchProjects();
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (_) async {
      try {
        final projects = await _fetchProjects();
        if (!mounted) return;
        state = AsyncData(projects);
      } catch (error, stackTrace) {
        if (!mounted) return;
        state = AsyncError(error, stackTrace, previous: state);
      }
    });
  }
}

final projectLibraryProvider = AutoDisposeAsyncNotifierProvider<
    ProjectLibraryNotifier, List<ProjectSummaryModel>>(ProjectLibraryNotifier.new);
