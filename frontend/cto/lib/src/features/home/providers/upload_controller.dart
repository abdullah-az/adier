import 'dart:math';

import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../data/providers/project_provider.dart';
import '../../../data/repositories/project_repository.dart';
import '../models/upload_task.dart';
import 'project_library_provider.dart';

class UploadOutcome {
  const UploadOutcome._({
    required this.projectId,
    this.assetId,
    this.errorMessage,
    required this.status,
  });

  const UploadOutcome.success({required String projectId, required String assetId})
      : this._(projectId: projectId, assetId: assetId, status: UploadResultStatus.success);

  const UploadOutcome.failure({required String projectId, String? errorMessage})
      : this._(projectId: projectId, errorMessage: errorMessage, status: UploadResultStatus.failure);

  const UploadOutcome.canceled({required String projectId})
      : this._(projectId: projectId, status: UploadResultStatus.canceled);

  final String projectId;
  final String? assetId;
  final String? errorMessage;
  final UploadResultStatus status;

  bool get isSuccess => status == UploadResultStatus.success;
  bool get isCanceled => status == UploadResultStatus.canceled;
}

enum UploadResultStatus { success, failure, canceled }

class UploadController extends StateNotifier<List<UploadTask>> {
  UploadController(this._ref) : super(const []);

  final Ref _ref;
  final Uuid _uuid = const Uuid();
  final Map<String, CancelToken> _cancelTokens = {};
  final Map<String, _ProgressSample> _progressSamples = {};

  Future<UploadOutcome> uploadFile(PlatformFile file, {String? projectId}) async {
    final repository = _ref.read(projectRepositoryProvider);
    final targetProjectId = projectId ?? _uuid.v4();

    var task = _initialiseTask(targetProjectId, file);
    _setTask(task);

    final cancelToken = CancelToken();
    _cancelTokens[targetProjectId] = cancelToken;
    _progressSamples[targetProjectId] = _ProgressSample(bytes: 0, timestamp: DateTime.now());

    try {
      task = _updateTask(targetProjectId, (current) =>
          current.copyWith(status: UploadStatus.uploading, progress: 0, sentBytes: 0, resetError: true));

      final result = await repository.uploadVideo(
        projectId: targetProjectId,
        file: file,
        cancelToken: cancelToken,
        onSendProgress: (sent, total) => _handleProgress(targetProjectId, sent, total),
      );

      task = _updateTask(
        targetProjectId,
        (current) => current.copyWith(
          status: UploadStatus.completed,
          progress: 1,
          sentBytes: result.sizeBytes,
          speedBytesPerSecond: null,
          assetId: result.assetId,
          clearFile: !kIsWeb,
        ),
      );

      // Create ingestion job so processing begins immediately.
      await repository.createJob(
        projectId: targetProjectId,
        jobType: 'ingest',
        payload: {'asset_id': result.assetId},
      );

      _ref.invalidate(projectLibraryProvider);
      return UploadOutcome.success(projectId: targetProjectId, assetId: result.assetId);
    } on DioException catch (error) {
      if (CancelToken.isCancel(error)) {
        _updateTask(
          targetProjectId,
          (current) => current.copyWith(status: UploadStatus.canceled, speedBytesPerSecond: null),
        );
        return UploadOutcome.canceled(projectId: targetProjectId);
      }

      final message = error.message ?? 'network_error';
      _updateTask(
        targetProjectId,
        (current) => current.copyWith(
          status: UploadStatus.failed,
          errorMessage: message,
          speedBytesPerSecond: null,
        ),
      );
      return UploadOutcome.failure(projectId: targetProjectId, errorMessage: message);
    } catch (error) {
      final message = error.toString();
      _updateTask(
        targetProjectId,
        (current) => current.copyWith(
          status: UploadStatus.failed,
          errorMessage: message,
          speedBytesPerSecond: null,
        ),
      );
      return UploadOutcome.failure(projectId: targetProjectId, errorMessage: message);
    } finally {
      _progressSamples.remove(targetProjectId);
      _cancelTokens.remove(targetProjectId);
    }
  }

  void cancelUpload(String projectId) {
    final token = _cancelTokens[projectId];
    if (token != null && !token.isCancelled) {
      token.cancel('Cancelled by user');
    }
  }

  Future<UploadOutcome> resumeUpload(String projectId) async {
    final task = state.firstWhere(
      (element) => element.projectId == projectId,
      orElse: () => throw StateError('Upload task not found for project $projectId'),
    );

    if (!task.canResume || task.file == null) {
      return UploadOutcome.failure(projectId: projectId, errorMessage: 'resume_not_possible');
    }

    final refreshed = task.copyWith(
      status: UploadStatus.pending,
      sentBytes: 0,
      progress: 0,
      speedBytesPerSecond: null,
      resetError: true,
    );
    _setTask(refreshed);
    return uploadFile(task.file!, projectId: projectId);
  }

  void removeCompleted(String projectId) {
    final tasks = state.where((task) => task.projectId != projectId).toList(growable: false);
    state = tasks;
  }

  UploadTask _initialiseTask(String projectId, PlatformFile file) {
    final existingIndex = state.indexWhere((task) => task.projectId == projectId);
    if (existingIndex == -1) {
      return UploadTask(
        projectId: projectId,
        fileName: file.name,
        totalBytes: file.size,
        file: file,
      );
    }

    final existing = state[existingIndex];
    return existing.copyWith(
      fileName: file.name,
      totalBytes: file.size,
      file: file,
      sentBytes: 0,
      progress: 0,
      status: UploadStatus.pending,
      speedBytesPerSecond: null,
      resetError: true,
    );
  }

  void _handleProgress(String projectId, int sent, int total) {
    final now = DateTime.now();
    final lastSample = _progressSamples[projectId];
    double? speed;
    if (lastSample != null) {
      final elapsedMs = max(now.difference(lastSample.timestamp).inMilliseconds, 1);
      final deltaBytes = sent - lastSample.bytes;
      if (deltaBytes >= 0) {
        speed = deltaBytes / (elapsedMs / 1000);
      }
    }

    _progressSamples[projectId] = _ProgressSample(bytes: sent, timestamp: now);

    _updateTask(
      projectId,
      (current) => current.copyWith(
        sentBytes: sent,
        progress: total > 0 ? sent / total : 0,
        speedBytesPerSecond: speed,
        status: UploadStatus.uploading,
      ),
    );
  }

  UploadTask _updateTask(String projectId, UploadTask Function(UploadTask current) transform) {
    final tasks = [...state];
    final index = tasks.indexWhere((task) => task.projectId == projectId);
    if (index == -1) {
      throw StateError('Upload task not found for project $projectId');
    }
    final updated = transform(tasks[index]);
    tasks[index] = updated;
    state = tasks;
    return updated;
  }

  void _setTask(UploadTask task) {
    final tasks = [...state];
    final index = tasks.indexWhere((element) => element.projectId == task.projectId);
    if (index == -1) {
      tasks.add(task);
    } else {
      tasks[index] = task;
    }
    state = tasks;
  }
}

class _ProgressSample {
  const _ProgressSample({required this.bytes, required this.timestamp});

  final int bytes;
  final DateTime timestamp;
}

final uploadControllerProvider =
    StateNotifierProvider<UploadController, List<UploadTask>>((ref) {
  return UploadController(ref);
});
