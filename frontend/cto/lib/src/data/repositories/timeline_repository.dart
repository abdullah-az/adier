import 'dart:math';

import 'package:dio/dio.dart';

import '../../core/constants/app_constants.dart';
import '../models/timeline_models.dart';

class TimelineRepositoryException implements Exception {
  TimelineRepositoryException(this.message, [this.error]);

  final String message;
  final Object? error;

  @override
  String toString() => 'TimelineRepositoryException: $message';
}

class TimelineRepository {
  TimelineRepository({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConstants.apiBaseUrl,
                connectTimeout:
                    const Duration(milliseconds: AppConstants.apiTimeout),
                receiveTimeout:
                    const Duration(milliseconds: AppConstants.apiTimeout),
              ),
            );

  final Dio _dio;

  Future<ProjectTimelinePayload> fetchProjectTimeline(String projectId) async {
    try {
      final response = await _dio.get('/projects/$projectId/timeline');
      if (response.data is Map<String, dynamic>) {
        return ProjectTimelinePayload.fromJson(
          response.data as Map<String, dynamic>,
        );
      }
      return _fallbackPayload(projectId);
    } on DioException catch (error) {
      // Provide a rich offline fallback for local development or when the
      // backend timeline service is unavailable.
      if (_isNotFound(error) || _isConnectionIssue(error)) {
        return _fallbackPayload(projectId);
      }
      throw TimelineRepositoryException('Failed to load timeline', error);
    } catch (error) {
      return _fallbackPayload(projectId);
    }
  }

  Future<ProjectTimelinePayload> saveTimeline(
    String projectId,
    List<TimelineClip> timeline, {
    List<SceneSuggestion>? suggestions,
  }) async {
    try {
      final response = await _dio.put(
        '/projects/$projectId/timeline',
        data: {
          'timeline': timeline.map((clip) => clip.toJson()).toList(),
        },
      );

      if (response.data is Map<String, dynamic>) {
        return ProjectTimelinePayload.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      return ProjectTimelinePayload(
        timeline: timeline,
        suggestions: suggestions ?? const <SceneSuggestion>[],
        metadata: _metadataFromTimeline(projectId, timeline),
      );
    } on DioException catch (error) {
      throw TimelineRepositoryException('Failed to save timeline', error);
    } catch (error) {
      throw TimelineRepositoryException('Failed to save timeline', error);
    }
  }

  Future<List<TranscriptSegment>> searchTranscript(
    String projectId,
    String query,
  ) async {
    if (query.trim().isEmpty) {
      return const <TranscriptSegment>[];
    }

    try {
      final response = await _dio.get(
        '/projects/$projectId/transcript/search',
        queryParameters: {'q': query},
      );

      if (response.data is Map<String, dynamic>) {
        final data = response.data as Map<String, dynamic>;
        final results = data['results'] as List<dynamic>? ?? <dynamic>[];
        return results
            .map(
              (item) => TranscriptSegment.fromJson(
                item as Map<String, dynamic>,
              ),
            )
            .toList();
      }

      if (response.data is List<dynamic>) {
        return (response.data as List<dynamic>)
            .map((item) => TranscriptSegment.fromJson(
                  item as Map<String, dynamic>,
                ))
            .toList();
      }

      return _fallbackTranscriptSegments(projectId, query);
    } on DioException catch (error) {
      if (_isNotFound(error) || _isConnectionIssue(error)) {
        return _fallbackTranscriptSegments(projectId, query);
      }
      throw TimelineRepositoryException('Transcript search failed', error);
    } catch (error) {
      return _fallbackTranscriptSegments(projectId, query);
    }
  }

  bool _isNotFound(DioException error) {
    return error.response?.statusCode == 404;
  }

  bool _isConnectionIssue(DioException error) {
    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError;
  }

  ProjectTimelinePayload _fallbackPayload(String projectId) {
    final suggestions = <SceneSuggestion>[
      SceneSuggestion(
        id: 'ai-hook',
        title: 'Hook & Problem Statement',
        description:
            'High-energy opening that highlights the main problem and teases the solution.',
        sourceId: 'primary-video',
        start: const Duration(seconds: 0),
        end: const Duration(seconds: 12),
        qualityScore: 0.92,
        confidence: 0.88,
      ),
      SceneSuggestion(
        id: 'ai-demo',
        title: 'Product Demo Highlight',
        description: 'Showcases the core feature solving the identified problem.',
        sourceId: 'primary-video',
        start: const Duration(seconds: 40),
        end: const Duration(minutes: 1, seconds: 5),
        qualityScore: 0.86,
        confidence: 0.82,
      ),
      SceneSuggestion(
        id: 'ai-testimonial',
        title: 'Customer Testimonial',
        description: 'Authentic quote that reinforces the product impact.',
        sourceId: 'secondary-video',
        start: const Duration(minutes: 2),
        end: const Duration(minutes: 2, seconds: 24),
        qualityScore: 0.79,
        confidence: 0.75,
      ),
    ];

    final firstClipId = 'clip-$projectId-1';
    final firstClip = suggestions.first
        .toTimelineClip(projectId: projectId, clipId: firstClipId);

    final timeline = <TimelineClip>[firstClip];
    final suggestionList = <SceneSuggestion>[
      suggestions.first.copyWith(attachedClipId: firstClipId),
      ...suggestions.skip(1),
    ];

    final metadata = ProjectMetadata(
      projectId: projectId,
      title: 'Demo Project',
      description:
          'Interactive timeline workspace with AI suggestions and manual edits.',
      maxDuration: const Duration(minutes: 5),
      currentDuration: timeline.fold<Duration>(
        Duration.zero,
        (sum, clip) => sum + clip.duration,
      ),
      clipCount: timeline.length,
      lastSavedAt: DateTime.now(),
      owner: 'You',
      status: 'draft',
    );

    return ProjectTimelinePayload(
      timeline: timeline,
      suggestions: suggestionList,
      metadata: metadata,
    );
  }

  ProjectMetadata _metadataFromTimeline(
    String projectId,
    List<TimelineClip> timeline,
  ) {
    final totalDuration = timeline.fold<Duration>(
      Duration.zero,
      (sum, clip) => sum + clip.duration,
    );

    return ProjectMetadata(
      projectId: projectId,
      title: 'Project $projectId',
      description: 'Automatically generated metadata snapshot.',
      maxDuration: const Duration(minutes: 5),
      currentDuration: totalDuration,
      clipCount: timeline.length,
      lastSavedAt: DateTime.now(),
      owner: 'You',
      status: 'draft',
    );
  }

  List<TranscriptSegment> _fallbackTranscriptSegments(
    String projectId,
    String query,
  ) {
    final normalizedQuery = query.trim();
    final baseStart = Duration(seconds: 90 + normalizedQuery.length * 2);
    return List<TranscriptSegment>.generate(3, (index) {
      final offset = Duration(seconds: index * 18);
      final start = baseStart + offset;
      final end = start + Duration(seconds: 12 + index * 2);
      return TranscriptSegment(
        id: 'transcript-$projectId-$index',
        sourceId: 'primary-video',
        text:
            '...${normalizedQuery.toUpperCase()} highlighted context snippet ${index + 1}... ',
        start: start,
        end: end,
        confidence: max(0.5, 0.85 - index * 0.1),
      );
    });
  }
}
