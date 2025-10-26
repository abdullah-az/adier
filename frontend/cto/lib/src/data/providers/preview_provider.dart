import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/preview_models.dart';
import '../repositories/preview_repository.dart';

final previewRepositoryProvider = Provider<PreviewRepository>((ref) {
  return PreviewRepository();
});

class PreviewJobNotifier extends StateNotifier<AsyncValue<PreviewJob>> {
  PreviewJobNotifier(this._repository, {required this.projectId, required this.jobId})
      : super(const AsyncValue.loading()) {
    _fetch();
  }

  final PreviewRepository _repository;
  final String projectId;
  final String jobId;

  Future<void> _fetch() async {
    state = const AsyncValue.loading();
    try {
      final job = await _repository.getPreviewJob(projectId: projectId, jobId: jobId);
      state = AsyncValue.data(job);
    } catch (e, stackTrace) {
      state = AsyncValue.error(e, stackTrace);
    }
  }

  Future<void> refresh() async {
    await _fetch();
  }

  void updateFromWebSocket(Map<String, dynamic> data) {
    final currentJob = state.value;
    if (currentJob == null) return;

    try {
      final updatedJob = PreviewJob(
        id: currentJob.id,
        projectId: currentJob.projectId,
        status: data['status'] != null
            ? JobStatus.fromString(data['status'] as String)
            : currentJob.status,
        proxyVideoUrl: data['proxy_video_url'] as String? ?? currentJob.proxyVideoUrl,
        subtitleUrl: data['subtitle_url'] as String? ?? currentJob.subtitleUrl,
        timeline: data['timeline'] != null
            ? TimelineComposition.fromJson(data['timeline'] as Map<String, dynamic>)
            : currentJob.timeline,
        progress: data['progress'] != null
            ? (data['progress'] as num).toDouble()
            : currentJob.progress,
        errorMessage: data['error_message'] as String? ?? currentJob.errorMessage,
      );
      state = AsyncValue.data(updatedJob);
    } catch (e, stackTrace) {
      state = AsyncValue.error(e, stackTrace);
    }
  }
}

final previewJobProvider = StateNotifierProvider.family<PreviewJobNotifier, AsyncValue<PreviewJob>,
    ({String projectId, String jobId})>((ref, params) {
  final repository = ref.watch(previewRepositoryProvider);
  return PreviewJobNotifier(
    repository,
    projectId: params.projectId,
    jobId: params.jobId,
  );
});

final subtitlesProvider = FutureProvider.family<List<SubtitleCue>, String>((ref, subtitleUrl) async {
  final repository = ref.read(previewRepositoryProvider);
  return repository.getSubtitles(subtitleUrl);
});
