import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

Future<MultipartFile> buildMultipartFileImpl(PlatformFile file) async {
  if (file.path != null) {
    return MultipartFile.fromFile(
      file.path!,
      filename: file.name,
    );
  }

  if (file.readStream != null) {
    return MultipartFile(
      file.readStream!,
      file.size,
      filename: file.name,
    );
  }

  if (file.bytes != null) {
    return MultipartFile.fromBytes(
      file.bytes!,
      filename: file.name,
    );
  }

  throw const FormatException('File data is not accessible for upload.');
}
