import 'package:flutter/foundation.dart';

import '../../../data/models/media_asset.dart';

@immutable
class UploadRecord {
  const UploadRecord({
    required this.assetId,
    required this.projectId,
    required this.fileName,
    required this.status,
    required this.createdAt,
    this.progress = 0,
    this.errorMessage,
  });

  final String assetId;
  final String projectId;
  final String fileName;
  final MediaAssetStatus status;
  final DateTime createdAt;
  final double progress;
  final String? errorMessage;

  bool get isComplete => status == MediaAssetStatus.ready;
  bool get isFailed => status == MediaAssetStatus.failed;
  bool get isProcessing => status == MediaAssetStatus.processing || status == MediaAssetStatus.uploading;

  UploadRecord copyWith({
    String? fileName,
    MediaAssetStatus? status,
    DateTime? createdAt,
    double? progress,
    String? errorMessage,
  }) {
    return UploadRecord(
      assetId: assetId,
      projectId: projectId,
      fileName: fileName ?? this.fileName,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      progress: progress ?? this.progress,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }

  factory UploadRecord.fromAsset(MediaAsset asset, {double progress = 0}) {
    return UploadRecord(
      assetId: asset.id,
      projectId: asset.projectId,
      fileName: asset.fileName,
      status: asset.status,
      createdAt: asset.createdAt,
      progress: progress,
    );
  }
}
