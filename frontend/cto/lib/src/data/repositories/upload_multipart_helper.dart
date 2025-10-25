import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

import 'upload_multipart_helper_stub.dart'
    if (dart.library.io) 'upload_multipart_helper_io.dart'
    if (dart.library.html) 'upload_multipart_helper_web.dart';

Future<MultipartFile> buildMultipartFile(PlatformFile file) =>
    buildMultipartFileImpl(file);
