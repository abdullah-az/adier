import 'package:file_picker/file_picker.dart';

enum UploadStatus {
  pending,
  uploading,
  completed,
  failed,
  canceled,
}

class UploadTask {
  const UploadTask({
    required this.projectId,
    required this.fileName,
    required this.totalBytes,
    this.file,
    this.sentBytes = 0,
    this.progress = 0,
    this.status = UploadStatus.pending,
    this.speedBytesPerSecond,
    this.errorMessage,
    this.assetId,
  });

  final String projectId;
  final String fileName;
  final int totalBytes;
  final PlatformFile? file;
  final int sentBytes;
  final double progress;
  final UploadStatus status;
  final double? speedBytesPerSecond;
  final String? errorMessage;
  final String? assetId;

  UploadTask copyWith({
    String? projectId,
    String? fileName,
    int? totalBytes,
    PlatformFile? file,
    int? sentBytes,
    double? progress,
    UploadStatus? status,
    double? speedBytesPerSecond,
    String? errorMessage,
    String? assetId,
    bool clearFile = false,
    bool resetError = false,
    bool clearAsset = false,
  }) {
    return UploadTask(
      projectId: projectId ?? this.projectId,
      fileName: fileName ?? this.fileName,
      totalBytes: totalBytes ?? this.totalBytes,
      file: clearFile ? null : file ?? this.file,
      sentBytes: sentBytes ?? this.sentBytes,
      progress: progress ?? this.progress,
      status: status ?? this.status,
      speedBytesPerSecond: speedBytesPerSecond ?? this.speedBytesPerSecond,
      errorMessage: resetError ? null : (errorMessage ?? this.errorMessage),
      assetId: clearAsset ? null : assetId ?? this.assetId,
    );
  }

  bool get isActive =>
      status == UploadStatus.pending || status == UploadStatus.uploading;

  bool get canResume => status == UploadStatus.failed || status == UploadStatus.canceled;
}
