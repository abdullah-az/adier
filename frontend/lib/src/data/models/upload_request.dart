import 'package:flutter/foundation.dart';

@immutable
class UploadRequest {
  const UploadRequest({
    required this.fileName,
    required this.mimeType,
    required this.fileSizeBytes,
  });

  final String fileName;
  final String mimeType;
  final int fileSizeBytes;
}
