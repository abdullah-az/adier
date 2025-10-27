import 'dart:async';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/project_model.dart';
import '../repositories/project_repository.dart';

const _uploadExtensions = <String>{'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'};
const _pollingInterval = Duration(seconds: 6);

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  return ProjectRepository();
});

final projectLibraryProvider = StateNotifierProvider<ProjectLibraryNotifier, ProjectLibraryState>((ref) {
  final repository = ref.watch(projectRepositoryProvider);
  return ProjectLibraryNotifier(ref: ref, repository: repository);
});

final projectDetailProvider = FutureProvider.autoDispose.family<ProjectModel, String>((ref, id) async {
  final repository = ref.watch(projectRepositoryProvider);
  return repository.fetchProject(id);
});

enum UploadStatus {
  idle,
  validating,
  uploading,
  cancelling,
  success,
  failure,
}

class UploadState {
  const UploadState({
    required this.status,
    required this.progress,
    required this.sentBytes,
    required this.totalBytes,
    required this.speedBytesPerSecond,
    this.fileName,
    this.error,
    this.project,
  });

  const UploadState.initial()
      : status = UploadStatus.idle,
        progress = 0,
        sentBytes = 0,
        totalBytes = 0,
        speedBytesPerSecond = 0,
        fileName = null,
        error = null,
        project = null;

  final UploadStatus status;
  final double progress;
  final int sentBytes;
  final int totalBytes;
  final double speedBytesPerSecond;
  final String? fileName;
  final Object? error;
  final ProjectModel? project;

  bool get isUploading => status == UploadStatus.uploading;
  bool get hasError => status == UploadStatus.failure;
  bool get isSuccess => status == UploadStatus.success;

  UploadState copyWith({
    UploadStatus? status,
    double? progress,
    int? sentBytes,
    int? totalBytes,
    double? speedBytesPerSecond,
    String? fileName = _noFileName,
    Object? error = _noError,
    ProjectModel? project = _noProject,
  }) {
    return UploadState(
      status: status ?? this.status,
      progress: progress ?? this.progress,
      sentBytes: sentBytes ?? this.sentBytes,
      totalBytes: totalBytes ?? this.totalBytes,
      speedBytesPerSecond: speedBytesPerSecond ?? this.speedBytesPerSecond,
      fileName: fileName == _noFileName ? this.fileName : fileName,
      error: error == _noError ? this.error : error,
      project: project == _noProject ? this.project : project,
    );
  }

  static const _noError = Object();
  static const _noProject = Object();
  static const _noFileName = Object();
}

class ProjectLibraryState {
  const ProjectLibraryState({
    required this.isLoading,
    required this.projects,
    this.error,
  });

  const ProjectLibraryState.initial()
      : isLoading = true,
        projects = const <ProjectModel>[],
        error = null;

  final bool isLoading;
  final List<ProjectModel> projects;
  final Object? error;

  bool get hasError => error != null;

  ProjectLibraryState copyWith({
    bool? isLoading,
    List<ProjectModel>? projects,
    Object? error = _noError,
  }) {
    return ProjectLibraryState(
      isLoading: isLoading ?? this.isLoading,
      projects: projects ?? this.projects,
      error: error == _noError ? this.error : error,
    );
  }

  static const _noError = Object();
}

class ProjectLibraryNotifier extends StateNotifier<ProjectLibraryState> {
  ProjectLibraryNotifier({required this.ref, required this.repository})
      : super(const ProjectLibraryState.initial()) {
    _initialize();
  }

  final Ref ref;
  final ProjectRepository repository;

  Timer? _pollingTimer;

  Future<void> _initialize() async {
    await refresh(showLoading: true);
    _startPolling();
    ref.onDispose(_cancelPolling);
  }

  Future<void> refresh({bool showLoading = false}) async {
    if (showLoading) {
      state = state.copyWith(isLoading: true, error: null);
    }

    try {
      final projects = await repository.fetchProjects();
      state = state.copyWith(
        isLoading: false,
        projects: _sortProjects(projects),
        error: null,
      );
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        error: error,
      );
    }
  }

  void upsertProject(ProjectModel project) {
    final projects = [...state.projects];
    final index = projects.indexWhere((element) => element.id == project.id);
    if (index == -1) {
      projects.add(project);
    } else {
      projects[index] = project;
    }
    state = state.copyWith(projects: _sortProjects(projects), error: null);
  }

  void _startPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = Timer.periodic(_pollingInterval, (_) async {
      try {
        final projects = await repository.fetchProjects();
        state = state.copyWith(
          projects: _sortProjects(projects),
          error: null,
        );
      } catch (error) {
        state = state.copyWith(error: error);
      }
    });
  }

  void _cancelPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }

  @override
  void dispose() {
    _cancelPolling();
    super.dispose();
  }

  List<ProjectModel> _sortProjects(List<ProjectModel> items) {
    final sorted = [...items];
    sorted.sort(
      (a, b) => b.updatedAt.compareTo(a.updatedAt),
    );
    return sorted;
  }
}

class UploadController extends StateNotifier<UploadState> {
  UploadController({required this.ref, required this.repository})
      : super(const UploadState.initial());

  final Ref ref;
  final ProjectRepository repository;

  CancelToken? _cancelToken;
  DateTime? _lastProgressTimestamp;
  int _lastSentBytes = 0;

  Future<void> pickAndUpload() async {
    try {
      state = state.copyWith(
        status: UploadStatus.validating,
        error: null,
        fileName: null,
        project: null,
      );

      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowMultiple: false,
        withData: kIsWeb,
        allowedExtensions: _uploadExtensions.toList(),
      );

      if (result == null || result.files.isEmpty) {
        state = const UploadState.initial();
        return;
      }

      final file = result.files.single;
      final extension = file.extension?.toLowerCase();
      if (extension == null || !_uploadExtensions.contains(extension)) {
        state = state.copyWith(
          status: UploadStatus.failure,
          error: 'invalid_format',
          fileName: file.name,
        );
        return;
      }

      await _uploadFile(file);
    } on Exception catch (error) {
      state = state.copyWith(status: UploadStatus.failure, error: error);
    }
  }

  Future<void> _uploadFile(PlatformFile file) async {
    if (state.isUploading) {
      return;
    }

    _cancelToken?.cancel();
    _cancelToken = CancelToken();
    _lastProgressTimestamp = null;
    _lastSentBytes = 0;

    state = state.copyWith(
      status: UploadStatus.uploading,
      progress: 0,
      sentBytes: 0,
      totalBytes: file.size,
      speedBytesPerSecond: 0,
      fileName: file.name,
      error: null,
      project: null,
    );

    try {
      final project = await repository.uploadVideo(
        fileName: file.name,
        filePath: file.path,
        bytes: file.bytes,
        metadata: {
          'size': file.size,
        },
        onProgress: _handleProgress,
        cancelToken: _cancelToken,
      );

      final processedProject = await repository.triggerProcessing(project.id) ??
          project.copyWith(status: ProjectStatus.processing, progress: 0);

      ref.read(projectLibraryProvider.notifier).upsertProject(processedProject);
      state = state.copyWith(
        status: UploadStatus.success,
        progress: 1,
        sentBytes: state.totalBytes,
        speedBytesPerSecond: 0,
        error: null,
        project: processedProject,
      );

      unawaited(
        ref.read(projectLibraryProvider.notifier).refresh(),
      );
    } on DioException catch (error) {
      if (error.type == DioExceptionType.cancel) {
        state = const UploadState.initial();
        return;
      }
      state = state.copyWith(status: UploadStatus.failure, error: error);
    } catch (error) {
      state = state.copyWith(status: UploadStatus.failure, error: error);
    }
  }

  void _handleProgress(int sent, int total) {
    final now = DateTime.now();
    double speed = state.speedBytesPerSecond;

    if (_lastProgressTimestamp != null) {
      final elapsed = now.difference(_lastProgressTimestamp!).inMilliseconds;
      if (elapsed > 0) {
        final bytesDelta = max(0, sent - _lastSentBytes);
        speed = bytesDelta / (elapsed / 1000);
      }
    }

    _lastProgressTimestamp = now;
    _lastSentBytes = sent;

    state = state.copyWith(
      progress: total == 0 ? 0 : sent / total,
      sentBytes: sent,
      totalBytes: total,
      speedBytesPerSecond: speed,
    );
  }

  void cancelUpload() {
    if (!state.isUploading) {
      return;
    }

    state = state.copyWith(status: UploadStatus.cancelling);
    _cancelToken?.cancel('cancelled');
    state = const UploadState.initial();
  }

  void reset() {
    state = const UploadState.initial();
  }
}

final uploadControllerProvider = StateNotifierProvider<UploadController, UploadState>((ref) {
  final repository = ref.watch(projectRepositoryProvider);
  return UploadController(ref: ref, repository: repository);
});
