part of 'upload_workflow_controller.dart';

enum UploadWorkflowStatus {
  idle,
  creatingProject,
  ready,
  uploading,
  processing,
  success,
  failure,
}

class UploadWorkflowState {
  const UploadWorkflowState({
    this.projectName = '',
    this.project,
    this.selectedFile,
    this.uploads = const <UploadRecord>[],
    this.activeUploadId,
    this.status = UploadWorkflowStatus.idle,
    this.isBusy = false,
    this.message,
    this.isOffline = false,
  });

  final String projectName;
  final Project? project;
  final SelectedUploadFile? selectedFile;
  final List<UploadRecord> uploads;
  final String? activeUploadId;
  final UploadWorkflowStatus status;
  final bool isBusy;
  final UploadMessage? message;
  final bool isOffline;

  bool get hasProject => project != null;
  bool get hasSelectedFile => selectedFile != null;
  bool get isUploading => status == UploadWorkflowStatus.uploading || status == UploadWorkflowStatus.processing;
  bool get isComplete => status == UploadWorkflowStatus.success;
  bool get hasError => status == UploadWorkflowStatus.failure;
  bool get canCreateProject => projectName.trim().isNotEmpty && !isBusy;
  bool get canStartUpload => hasProject && hasSelectedFile && !isBusy && !isOffline;

  UploadRecord? get activeUpload {
    if (activeUploadId == null) {
      return null;
    }
    for (final record in uploads) {
      if (record.assetId == activeUploadId) {
        return record;
      }
    }
    return null;
  }

  UploadWorkflowState copyWith({
    String? projectName,
    Project? project,
    SelectedUploadFile? selectedFile,
    List<UploadRecord>? uploads,
    String? activeUploadId,
    UploadWorkflowStatus? status,
    bool? isBusy,
    UploadMessage? message,
    bool? isOffline,
    bool clearProject = false,
    bool clearSelectedFile = false,
    bool clearActiveUpload = false,
    bool clearMessage = false,
  }) {
    return UploadWorkflowState(
      projectName: projectName ?? this.projectName,
      project: clearProject ? null : (project ?? this.project),
      selectedFile: clearSelectedFile ? null : (selectedFile ?? this.selectedFile),
      uploads: uploads ?? this.uploads,
      activeUploadId: clearActiveUpload ? null : (activeUploadId ?? this.activeUploadId),
      status: status ?? this.status,
      isBusy: isBusy ?? this.isBusy,
      message: clearMessage ? null : (message ?? this.message),
      isOffline: isOffline ?? this.isOffline,
    );
  }
}
