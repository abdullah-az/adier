import 'package:flutter/foundation.dart';

enum UploadMessageType { info, error }

@immutable
class UploadMessage {
  const UploadMessage({
    required this.type,
    required this.code,
    this.details,
  });

  const UploadMessage.info(String code, {Map<String, Object?>? details})
      : this(type: UploadMessageType.info, code: code, details: details);

  const UploadMessage.error(String code, {Map<String, Object?>? details})
      : this(type: UploadMessageType.error, code: code, details: details);

  final UploadMessageType type;
  final String code;
  final Map<String, Object?>? details;
}

class UploadMessageCode {
  const UploadMessageCode._();

  static const String projectCreated = 'projectCreated';
  static const String projectCreationFailed = 'projectCreationFailed';
  static const String invalidProjectName = 'invalidProjectName';
  static const String offline = 'offline';
  static const String uploadStarted = 'uploadStarted';
  static const String uploadCompleted = 'uploadCompleted';
  static const String uploadFailed = 'uploadFailed';
}
