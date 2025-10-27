import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/music_assignment.dart';
import '../models/music_track.dart';

class MusicRepository {
  MusicRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<List<MusicTrack>> fetchTracks() async {
    try {
      final response = await _dio.get('/audio/tracks');
      final data = response.data;
      final List<dynamic> tracksJson = data is Map<String, dynamic>
          ? (data['tracks'] as List<dynamic>? ?? const <dynamic>[])
          : (data as List<dynamic>);
      return tracksJson
          .map((track) => MusicTrack.fromJson(track as Map<String, dynamic>))
          .toList();
    } catch (error) {
      throw Exception('Failed to load music tracks: $error');
    }
  }

  Future<MusicAssignment?> fetchAssignment(String videoId) async {
    try {
      final response = await _dio.get('/videos/$videoId/music-assignment');
      if (response.data == null || response.data is! Map<String, dynamic>) {
        return null;
      }
      return MusicAssignment.fromJson(response.data as Map<String, dynamic>);
    } catch (error) {
      // Treat 404 as "no assignment" rather than an error state
      if (error is DioException && error.response?.statusCode == 404) {
        return null;
      }
      throw Exception('Failed to load music assignment: $error');
    }
  }

  Future<void> updateAssignment(String videoId, MusicAssignment assignment) async {
    try {
      await _dio.put(
        '/videos/$videoId/music-assignment',
        data: assignment.toJson(),
      );
    } catch (error) {
      throw Exception('Failed to update music assignment: $error');
    }
  }
}
