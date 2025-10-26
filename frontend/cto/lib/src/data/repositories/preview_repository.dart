import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/preview_models.dart';

class PreviewRepository {
  PreviewRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<PreviewJob> getPreviewJob({required String projectId, required String jobId}) async {
    try {
      final response = await _dio.get('/projects/$projectId/jobs/$jobId');
      return PreviewJob.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      final message = e.response?.data is Map<String, dynamic>
          ? (e.response!.data['message'] as String?) ?? 'Failed to load preview job'
          : 'Failed to load preview job';
      throw Exception(message);
    } catch (e) {
      throw Exception('Failed to load preview job: $e');
    }
  }

  Future<List<SubtitleCue>> getSubtitles(String subtitleUrl) async {
    try {
      final response = await _dio.get(subtitleUrl);
      final data = response.data;
      if (data is List) {
        return data
            .map((item) => SubtitleCue.fromJson(item as Map<String, dynamic>))
            .toList();
      }
      throw Exception('Invalid subtitle data');
    } catch (e) {
      throw Exception('Failed to load subtitles: $e');
    }
  }
}
