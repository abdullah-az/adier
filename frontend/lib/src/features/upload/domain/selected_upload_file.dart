import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/foundation.dart';

import '../../../data/models/upload_request.dart';

@immutable
class SelectedUploadFile {
  const SelectedUploadFile({
    required this.name,
    required this.mimeType,
    required this.sizeBytes,
    this.bytes,
  });

  final String name;
  final String mimeType;
  final int sizeBytes;
  final Uint8List? bytes;

  UploadRequest toUploadRequest() {
    return UploadRequest(
      fileName: name,
      mimeType: mimeType,
      fileSizeBytes: sizeBytes,
    );
  }

  String get sizeLabel => formatBytes(sizeBytes);

  static String formatBytes(int bytes, {int decimals = 1}) {
    if (bytes <= 0) {
      return '0 B';
    }
    const suffixes = <String>['B', 'KB', 'MB', 'GB', 'TB'];
    final i = (math.log(bytes) / math.log(1024)).floor();
    final size = bytes / math.pow(1024, i);
    return '${size.toStringAsFixed(i == 0 ? 0 : decimals)} ${suffixes[i]}';
  }
}
