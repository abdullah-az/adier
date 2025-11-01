import 'package:flutter/foundation.dart';

enum MediaAssetStatus {
  pending,
  uploading,
  processing,
  ready,
  failed,
}

@immutable
class MediaAsset {
  const MediaAsset({
    required this.id,
    required this.projectId,
    required this.fileName,
    required this.status,
    required this.createdAt,
    this.uploadUrl,
    this.sizeBytes,
    this.mimeType,
  });

  final String id;
  final String projectId;
  final String fileName;
  final MediaAssetStatus status;
  final DateTime createdAt;
  final Uri? uploadUrl;
  final int? sizeBytes;
  final String? mimeType;

  MediaAsset copyWith({
    String? fileName,
    MediaAssetStatus? status,
    DateTime? createdAt,
    Uri? uploadUrl,
    int? sizeBytes,
    String? mimeType,
  }) {
    return MediaAsset(
      id: id,
      projectId: projectId,
      fileName: fileName ?? this.fileName,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      uploadUrl: uploadUrl ?? this.uploadUrl,
      sizeBytes: sizeBytes ?? this.sizeBytes,
      mimeType: mimeType ?? this.mimeType,
    );
  }

  factory MediaAsset.fromJson(Map<String, dynamic> json) {
    final statusValue = json['status'] as String;
    return MediaAsset(
      id: json['id'] as String,
      projectId: json['projectId'] as String,
      fileName: json['fileName'] as String,
      status: _statusFromString(statusValue),
      createdAt: DateTime.parse(json['createdAt'] as String),
      uploadUrl: json['uploadUrl'] != null ? Uri.parse(json['uploadUrl'] as String) : null,
      sizeBytes: json['sizeBytes'] as int?,
      mimeType: json['mimeType'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'projectId': projectId,
      'fileName': fileName,
      'status': status.name,
      'createdAt': createdAt.toIso8601String(),
      if (uploadUrl != null) 'uploadUrl': uploadUrl.toString(),
      if (sizeBytes != null) 'sizeBytes': sizeBytes,
      if (mimeType != null) 'mimeType': mimeType,
    };
  }

  static MediaAssetStatus _statusFromString(String value) {
    return MediaAssetStatus.values.firstWhere(
      (status) => status.name == value,
      orElse: () => MediaAssetStatus.pending,
    );
  }

  @override
  int get hashCode => Object.hash(
        id,
        projectId,
        fileName,
        status,
        createdAt,
        uploadUrl,
        sizeBytes,
        mimeType,
      );

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) {
      return true;
    }
    return other is MediaAsset &&
        other.id == id &&
        other.projectId == projectId &&
        other.fileName == fileName &&
        other.status == status &&
        other.createdAt == createdAt &&
        other.uploadUrl == uploadUrl &&
        other.sizeBytes == sizeBytes &&
        other.mimeType == mimeType;
  }

  @override
  String toString() => 'MediaAsset(id: $id, fileName: $fileName, status: ${status.name})';
}
