import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/subtitle_cue.dart';
import '../models/timeline_segment.dart';

class EditorRepository {
  EditorRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<String> uploadMedia(String filePath) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/uploads',
        data: <String, dynamic>{'path': filePath},
      );
      final data = response.data;
      if (data == null || data['uploadId'] == null) {
        throw const FormatException('Missing uploadId in response');
      }
      return data['uploadId'] as String;
    } catch (error) {
      throw Exception('Failed to upload media: $error');
    }
  }

  Future<List<TimelineSegment>> fetchTimeline(String uploadId) async {
    try {
      final response = await _dio.get<List<dynamic>>('/uploads/$uploadId/timeline');
      final rawData = response.data ?? <dynamic>[];
      return rawData.map((dynamic json) {
        final map = json as Map<String, dynamic>;
        return TimelineSegment(
          id: map['id'] as String,
          label: map['label'] as String,
          startMs: map['startMs'] as int,
          endMs: map['endMs'] as int,
        );
      }).toList();
    } catch (error) {
      throw Exception('Failed to fetch timeline: $error');
    }
  }

  Future<List<SubtitleCue>> fetchSubtitles(String uploadId) async {
    try {
      final response = await _dio.get<List<dynamic>>('/uploads/$uploadId/subtitles');
      final rawData = response.data ?? <dynamic>[];
      return rawData.map((dynamic json) {
        final map = json as Map<String, dynamic>;
        return SubtitleCue(
          id: map['id'] as String,
          text: map['text'] as String,
          startMs: map['startMs'] as int,
          endMs: map['endMs'] as int,
        );
      }).toList();
    } catch (error) {
      throw Exception('Failed to fetch subtitles: $error');
    }
  }

  Future<String> exportProject(String uploadId, {String format = 'mp4'}) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/uploads/$uploadId/export',
        data: <String, dynamic>{'format': format},
      );
      final data = response.data;
      if (data == null || data['exportId'] == null) {
        throw const FormatException('Missing exportId in response');
      }
      return data['exportId'] as String;
    } catch (error) {
      throw Exception('Failed to export project: $error');
    }
  }
}
