import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

Future<MultipartFile> buildMultipartFileImpl(PlatformFile file) async {
  if (file.bytes != null) {
    return MultipartFile.fromBytes(
      file.bytes!,
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

  throw const FormatException('File bytes are required for uploads on the web.');
}
