import 'package:flutter/foundation.dart';

import 'media_asset.dart';

@immutable
class UploadProgressEvent {
  const UploadProgressEvent({
    required this.assetId,
    required this.status,
    required this.progress,
    this.errorMessage,
  })  : assert(progress >= 0 && progress <= 1, 'Progress must be between 0 and 1.');

  final String assetId;
  final MediaAssetStatus status;
  final double progress;
  final String? errorMessage;

  UploadProgressEvent copyWith({
    MediaAssetStatus? status,
    double? progress,
    String? errorMessage,
  }) {
    return UploadProgressEvent(
      assetId: assetId,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}
