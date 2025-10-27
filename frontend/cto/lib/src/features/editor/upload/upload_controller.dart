import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/utils/timeline_utils.dart';
import '../../../data/providers/editor_providers.dart';
import '../../../data/repositories/editor_repository.dart';

class UploadState {
  const UploadState({
    this.isUploading = false,
    this.progress = 0,
    this.uploadId,
    this.fileName,
    this.error,
  });

  final bool isUploading;
  final double progress;
  final String? uploadId;
  final String? fileName;
  final String? error;

  bool get hasError => error != null;
  bool get isComplete => uploadId != null && !isUploading && !hasError;

  UploadState copyWith({
    bool? isUploading,
    double? progress,
    String? uploadId,
    String? fileName,
    String? error,
    bool resetError = false,
  }) {
    return UploadState(
      isUploading: isUploading ?? this.isUploading,
      progress: progress ?? this.progress,
      uploadId: uploadId ?? this.uploadId,
      fileName: fileName ?? this.fileName,
      error: resetError ? null : (error ?? this.error),
    );
  }
}

class UploadController extends StateNotifier<UploadState> {
  UploadController({
    required EditorRepository repository,
    required TimelineProfiler profiler,
  })  : _repository = repository,
        _profiler = profiler,
        super(const UploadState());

  final EditorRepository _repository;
  final TimelineProfiler _profiler;

  Future<void> uploadDemoFile() async {
    await uploadMedia('demo_video.mp4');
  }

  Future<void> uploadMedia(String filePath) async {
    final stopwatch = Stopwatch()..start();
    state = state.copyWith(
      isUploading: true,
      progress: 0,
      fileName: filePath,
      resetError: true,
    );
    await Future<void>.delayed(const Duration(milliseconds: 30));
    state = state.copyWith(progress: 0.4);
    try {
      final uploadId = await _repository.uploadMedia(filePath);
      state = state.copyWith(
        isUploading: false,
        progress: 1,
        uploadId: uploadId,
      );
    } catch (error) {
      state = state.copyWith(
        isUploading: false,
        error: error.toString(),
      );
    } finally {
      stopwatch.stop();
      _profiler.record('uploadMedia', stopwatch.elapsed);
    }
  }

  void reset() {
    state = const UploadState();
  }
}

final uploadControllerProvider = StateNotifierProvider<UploadController, UploadState>((ref) {
  final repository = ref.watch(editorRepositoryProvider);
  final profiler = ref.watch(timelineProfilerProvider);
  return UploadController(repository: repository, profiler: profiler);
});
