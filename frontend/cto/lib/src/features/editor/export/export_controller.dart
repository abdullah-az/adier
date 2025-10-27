import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/utils/timeline_utils.dart';
import '../../../data/providers/editor_providers.dart';
import '../../../data/repositories/editor_repository.dart';

class ExportState {
  const ExportState({
    this.isExporting = false,
    this.format = 'mp4',
    this.exportId,
    this.error,
  });

  final bool isExporting;
  final String format;
  final String? exportId;
  final String? error;

  bool get hasError => error != null;
  bool get isComplete => exportId != null && !isExporting;

  ExportState copyWith({
    bool? isExporting,
    String? format,
    String? exportId,
    String? error,
    bool resetError = false,
  }) {
    return ExportState(
      isExporting: isExporting ?? this.isExporting,
      format: format ?? this.format,
      exportId: exportId ?? this.exportId,
      error: resetError ? null : (error ?? this.error),
    );
  }
}

class ExportController extends StateNotifier<ExportState> {
  ExportController({
    required EditorRepository repository,
    required TimelineProfiler profiler,
  })  : _repository = repository,
        _profiler = profiler,
        super(const ExportState());

  final EditorRepository _repository;
  final TimelineProfiler _profiler;

  Future<void> exportProject(String uploadId, {String? format}) async {
    final stopwatch = Stopwatch()..start();
    final desiredFormat = format ?? state.format;
    state = state.copyWith(
      isExporting: true,
      format: desiredFormat,
      resetError: true,
    );
    try {
      final exportId = await _repository.exportProject(uploadId, format: desiredFormat);
      state = state.copyWith(
        isExporting: false,
        exportId: exportId,
      );
    } catch (error) {
      state = state.copyWith(
        isExporting: false,
        error: error.toString(),
      );
    } finally {
      stopwatch.stop();
      _profiler.record('exportProject', stopwatch.elapsed);
    }
  }

  void updateFormat(String format) {
    state = state.copyWith(format: format);
  }

  void reset() {
    state = const ExportState();
  }
}

final exportControllerProvider = StateNotifierProvider<ExportController, ExportState>((ref) {
  final repository = ref.watch(editorRepositoryProvider);
  final profiler = ref.watch(timelineProfilerProvider);
  return ExportController(repository: repository, profiler: profiler);
});
