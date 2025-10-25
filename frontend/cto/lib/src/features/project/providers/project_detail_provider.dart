import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/job_model.dart';
import '../../../data/models/project_summary_model.dart';
import '../../../data/models/video_asset_model.dart';
import '../../../data/providers/project_provider.dart';

class ProjectSummaryNotifier
    extends AutoDisposeAsyncNotifier<ProjectSummaryModel> {
  Timer? _pollTimer;
  late String _projectId;

  @override
  Future<ProjectSummaryModel> build(String projectId) async {
    _projectId = projectId;
    ref.onDispose(() => _pollTimer?.cancel());

    final summary = await _fetch();
    _startPolling();
    return summary;
  }

  Future<ProjectSummaryModel> _fetch() async {
    final repository = ref.read(projectRepositoryProvider);
    return repository.fetchProjectSummary(_projectId);
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 5), (_) async {
      try {
        final summary = await _fetch();
        if (!mounted) return;
        state = AsyncData(summary);
      } catch (error, stackTrace) {
        if (!mounted) return;
        state = AsyncError(error, stackTrace, previous: state);
      }
    });
  }
}

final projectSummaryProvider = AutoDisposeAsyncNotifierProviderFamily<
    ProjectSummaryNotifier, ProjectSummaryModel, String>(ProjectSummaryNotifier.new);

class ProjectJobsNotifier extends AutoDisposeAsyncNotifier<List<JobModel>> {
  Timer? _pollTimer;
  late String _projectId;

  @override
  Future<List<JobModel>> build(String projectId) async {
    _projectId = projectId;
    ref.onDispose(() => _pollTimer?.cancel());

    final jobs = await _fetch();
    _startPolling();
    return jobs;
  }

  Future<List<JobModel>> _fetch() async {
    final repository = ref.read(projectRepositoryProvider);
    return repository.fetchProjectJobs(_projectId);
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) async {
      try {
        final jobs = await _fetch();
        if (!mounted) return;
        state = AsyncData(jobs);
      } catch (error, stackTrace) {
        if (!mounted) return;
        state = AsyncError(error, stackTrace, previous: state);
      }
    });
  }
}

final projectJobsProvider = AutoDisposeAsyncNotifierProviderFamily<
    ProjectJobsNotifier, List<JobModel>, String>(ProjectJobsNotifier.new);

final projectAssetsProvider =
    FutureProvider.autoDispose.family<List<VideoAssetModel>, String>((ref, projectId) async {
  final repository = ref.read(projectRepositoryProvider);
  return repository.fetchProjectAssets(projectId);
});
