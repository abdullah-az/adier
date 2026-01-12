import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/models/media_asset.dart';
import '../../../data/models/project.dart';
import '../../../data/models/upload_progress_event.dart';
import '../../../data/repositories/media_asset_repository.dart';
import '../../../data/repositories/project_repository.dart';
import '../../../data/services/upload_progress_channel.dart';
import '../../upload/domain/selected_upload_file.dart';
import '../../upload/domain/upload_message.dart';
import '../../upload/domain/upload_record.dart';
import '../../../core/di/providers.dart';

part 'upload_workflow_state.dart';

class UploadWorkflowController extends StateNotifier<UploadWorkflowState> {
  UploadWorkflowController({
    required ProjectRepository projectRepository,
    required MediaAssetRepository mediaAssetRepository,
    required UploadProgressChannel progressChannel,
    bool isOnline = true,
  })  : _projectRepository = projectRepository,
        _mediaAssetRepository = mediaAssetRepository,
        _progressChannel = progressChannel,
        super(UploadWorkflowState(isOffline: !isOnline));

  final ProjectRepository _projectRepository;
  final MediaAssetRepository _mediaAssetRepository;
  final UploadProgressChannel _progressChannel;

  StreamSubscription<UploadProgressEvent>? _progressSubscription;

  void updateProjectName(String value) {
    state = state.copyWith(
      projectName: value,
      clearMessage: true,
    );
  }

  Future<void> createProject() async {
    final name = state.projectName.trim();
    if (name.isEmpty) {
      state = state.copyWith(
        message: const UploadMessage.error(UploadMessageCode.invalidProjectName),
      );
      return;
    }

    state = state.copyWith(
      status: UploadWorkflowStatus.creatingProject,
      isBusy: true,
      clearMessage: true,
    );

    try {
      final project = await _projectRepository.createProject(name);
      state = state.copyWith(
        project: project,
        status: UploadWorkflowStatus.ready,
        isBusy: false,
        message: UploadMessage.info(
          UploadMessageCode.projectCreated,
          details: <String, Object?>{'projectName': project.name},
        ),
      );

      await _loadExistingUploads(project.id);
    } catch (error) {
      state = state.copyWith(
        status: UploadWorkflowStatus.idle,
        isBusy: false,
        message: UploadMessage.error(
          UploadMessageCode.projectCreationFailed,
          details: <String, Object?>{'reason': error.toString()},
        ),
      );
    }
  }

  Future<void> _loadExistingUploads(String projectId) async {
    try {
      final assets = await _mediaAssetRepository.fetchMediaAssets(projectId);
      final uploads = assets
          .map((asset) => UploadRecord.fromAsset(
                asset,
                progress: _progressForStatus(asset.status),
              ))
          .toList()
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
      state = state.copyWith(uploads: uploads);
    } catch (_) {
      // Ignore; dashboard will show empty state and retry on demand.
    }
  }

  void resetProject() {
    if (state.isBusy) {
      return;
    }
    if (state.activeUploadId != null) {
      _progressChannel.clear(state.activeUploadId!);
    }
    _progressSubscription?.cancel();
    state = state.copyWith(
      projectName: '',
      clearProject: true,
      clearSelectedFile: true,
      clearActiveUpload: true,
      uploads: const <UploadRecord>[],
      status: UploadWorkflowStatus.idle,
      isBusy: false,
      clearMessage: true,
    );
  }

  void selectFile(SelectedUploadFile file) {
    state = state.copyWith(
      selectedFile: file,
      clearMessage: true,
      status: state.project == null ? UploadWorkflowStatus.idle : UploadWorkflowStatus.ready,
    );
  }

  void clearSelectedFile() {
    if (state.isUploading) {
      return;
    }
    state = state.copyWith(
      clearSelectedFile: true,
      clearMessage: true,
    );
  }

  Future<void> startUpload() async {
    final project = state.project;
    final file = state.selectedFile;
    if (project == null || file == null) {
      return;
    }

    state = state.copyWith(
      status: UploadWorkflowStatus.uploading,
      isBusy: true,
      message: UploadMessage.info(
        UploadMessageCode.uploadStarted,
        details: <String, Object?>{'fileName': file.name},
      ),
    );

    try {
      final asset = await _mediaAssetRepository.initiateUpload(
        projectId: project.id,
        request: file.toUploadRequest(),
      );

      final record = UploadRecord.fromAsset(asset, progress: 0);
      final uploads = _upsertRecord(record);
      state = state.copyWith(
        uploads: uploads,
        activeUploadId: asset.id,
        isBusy: false,
        status: UploadWorkflowStatus.uploading,
      );

      _subscribeToProgress(asset.id);
      _progressChannel.trackUpload(asset);
    } catch (error) {
      state = state.copyWith(
        status: UploadWorkflowStatus.failure,
        isBusy: false,
        message: UploadMessage.error(
          UploadMessageCode.uploadFailed,
          details: <String, Object?>{'reason': error.toString()},
        ),
      );
    }
  }

  void retryUpload() {
    if (state.selectedFile == null || state.project == null) {
      return;
    }
    if (state.activeUploadId != null) {
      _progressChannel.clear(state.activeUploadId!);
    }
    _progressSubscription?.cancel();
    state = state.copyWith(
      status: UploadWorkflowStatus.ready,
      clearMessage: true,
      clearActiveUpload: true,
    );
    startUpload();
  }

  void clearMessage() {
    state = state.copyWith(clearMessage: true);
  }

  void updateConnectivity(bool isOnline) {
    if (state.isOffline == !isOnline) {
      return;
    }
    state = state.copyWith(
      isOffline: !isOnline,
      clearMessage: isOnline,
      message: isOnline
          ? null
          : const UploadMessage.error(UploadMessageCode.offline),
    );
  }

  @override
  void dispose() {
    _progressSubscription?.cancel();
    if (state.activeUploadId != null) {
      _progressChannel.clear(state.activeUploadId!);
    }
    super.dispose();
  }

  void _subscribeToProgress(String assetId) {
    _progressSubscription?.cancel();
    _progressSubscription = _progressChannel.watch(assetId).listen(
      (event) {
        final updatedRecord = _recordForEvent(event);
        final uploads = _upsertRecord(updatedRecord);
        final nextStatus = _statusForEvent(event.status);
        UploadMessage? message = state.message;
        if (event.status == MediaAssetStatus.ready) {
          message = UploadMessage.info(
            UploadMessageCode.uploadCompleted,
            details: <String, Object?>{
              'assetId': event.assetId,
              'fileName': updatedRecord.fileName,
            },
          );
          _progressChannel.clear(assetId);
        } else if (event.status == MediaAssetStatus.failed) {
          message = UploadMessage.error(
            UploadMessageCode.uploadFailed,
            details: <String, Object?>{
              'assetId': event.assetId,
              'fileName': updatedRecord.fileName,
              'reason': event.errorMessage ?? '',
            },
          );
          _progressChannel.clear(assetId);
        }

        state = state.copyWith(
          uploads: uploads,
          status: nextStatus,
          message: message,
        );
      },
    );
  }

  UploadRecord _recordForEvent(UploadProgressEvent event) {
    final existing = state.uploads.firstWhere(
      (record) => record.assetId == event.assetId,
      orElse: () => UploadRecord(
        assetId: event.assetId,
        projectId: state.project?.id ?? '',
        fileName: state.selectedFile?.name ?? 'Unnamed',
        status: event.status,
        createdAt: DateTime.now().toUtc(),
        progress: 0,
      ),
    );

    return existing.copyWith(
      status: event.status,
      progress: event.progress,
      errorMessage: event.errorMessage,
    );
  }

  List<UploadRecord> _upsertRecord(UploadRecord record) {
    final uploads = List<UploadRecord>.from(state.uploads);
    final index = uploads.indexWhere((item) => item.assetId == record.assetId);
    if (index >= 0) {
      uploads[index] = record;
    } else {
      uploads.insert(0, record);
    }
    uploads.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return uploads;
  }

  UploadWorkflowStatus _statusForEvent(MediaAssetStatus status) {
    return switch (status) {
      MediaAssetStatus.uploading => UploadWorkflowStatus.uploading,
      MediaAssetStatus.processing => UploadWorkflowStatus.processing,
      MediaAssetStatus.ready => UploadWorkflowStatus.success,
      MediaAssetStatus.failed => UploadWorkflowStatus.failure,
      MediaAssetStatus.pending => UploadWorkflowStatus.ready,
    };
  }

  double _progressForStatus(MediaAssetStatus status) {
    return switch (status) {
      MediaAssetStatus.pending => 0,
      MediaAssetStatus.uploading => 0.3,
      MediaAssetStatus.processing => 0.7,
      MediaAssetStatus.ready => 1,
      MediaAssetStatus.failed => 0,
    };
  }
}

final uploadWorkflowControllerProvider =
    StateNotifierProvider<UploadWorkflowController, UploadWorkflowState>((ref) {
  final projectRepository = ref.watch(projectRepositoryProvider);
  final mediaAssetRepository = ref.watch(mediaAssetRepositoryProvider);
  final progressChannel = ref.watch(uploadProgressChannelProvider);
  final isOnline = ref.watch(connectivityStatusProvider);
  final controller = UploadWorkflowController(
    projectRepository: projectRepository,
    mediaAssetRepository: mediaAssetRepository,
    progressChannel: progressChannel,
    isOnline: isOnline,
  );

  ref.listen<bool>(connectivityStatusProvider, (previous, next) {
    controller.updateConnectivity(next);
  });

  ref.onDispose(controller.dispose);
  return controller;
});
