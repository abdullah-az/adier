import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/subtitle_segment.dart';

class SubtitleRepository {
  SubtitleRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<List<SubtitleSegment>> fetchSubtitles(String videoId) async {
    try {
      final response = await _dio.get('/videos/$videoId/subtitles');
      final data = response.data;
      final List<dynamic> segmentsJson = data is Map<String, dynamic>
          ? (data['segments'] as List<dynamic>? ?? const <dynamic>[])
          : (data as List<dynamic>);
      return segmentsJson
          .map((segment) => SubtitleSegment.fromJson(segment as Map<String, dynamic>))
          .toList();
    } catch (error) {
      throw Exception('Failed to load subtitles: $error');
    }
  }

  Future<void> updateSubtitles(String videoId, List<SubtitleSegment> segments) async {
    try {
      await _dio.put(
        '/videos/$videoId/subtitles',
        data: <String, dynamic>{
          'segments': segments.map((segment) => segment.toJson()).toList(),
        },
      );
    } catch (error) {
      throw Exception('Failed to update subtitles: $error');
    }
  }
}
