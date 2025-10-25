import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

import '../../core/constants/app_constants.dart';
import '../models/job_model.dart';
import '../models/project_summary_model.dart';
import '../models/video_asset_model.dart';
import '../models/video_upload_result_model.dart';
import 'upload_multipart_helper.dart';

class ProjectRepository {
  ProjectRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<List<ProjectSummaryModel>> fetchProjects() async {
    final response = await _dio.get('/projects');
    final data = response.data as List<dynamic>;
    return data
        .map((item) => ProjectSummaryModel.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<ProjectSummaryModel> fetchProjectSummary(String projectId) async {
    final response = await _dio.get('/projects/${Uri.encodeComponent(projectId)}');
    return ProjectSummaryModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<VideoAssetModel>> fetchProjectAssets(String projectId) async {
    final response = await _dio.get('/projects/${Uri.encodeComponent(projectId)}/videos');
    final data = response.data as List<dynamic>;
    return data
        .map((item) => VideoAssetModel.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<JobModel>> fetchProjectJobs(String projectId) async {
    final response = await _dio.get('/projects/${Uri.encodeComponent(projectId)}/jobs');
    final data = response.data as List<dynamic>;
    return data
        .map((item) => JobModel.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<JobModel> createJob({
    required String projectId,
    required String jobType,
    Map<String, dynamic>? payload,
  }) async {
    final response = await _dio.post(
      '/projects/${Uri.encodeComponent(projectId)}/jobs',
      data: {
        'job_type': jobType,
        'payload': payload ?? <String, dynamic>{},
      },
    );
    return JobModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<VideoUploadResultModel> uploadVideo({
    required String projectId,
    required PlatformFile file,
    required CancelToken cancelToken,
    ProgressCallback? onSendProgress,
  }) async {
    final multipartFile = await buildMultipartFile(file);
    final formData = FormData.fromMap({'file': multipartFile});

    final response = await _dio.post(
      '/projects/${Uri.encodeComponent(projectId)}/videos',
      data: formData,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      options: Options(contentType: 'multipart/form-data'),
    );

    return VideoUploadResultModel.fromJson(response.data as Map<String, dynamic>);
  }
}
