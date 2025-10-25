import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

Future<MultipartFile> buildMultipartFileImpl(PlatformFile file) =>
    throw UnsupportedError('Multipart uploads are not supported on this platform.');
