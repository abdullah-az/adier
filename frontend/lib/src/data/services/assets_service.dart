import 'dart:io';
import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';
import '../models/media_asset.dart';

class AssetsService {
  final ApiClient _apiClient;

  AssetsService(this._apiClient);

  Future<List<MediaAsset>> getAssets({
    String? projectId,
    MediaAssetType? type,
    int? page,
    int? limit,
  }) async {
    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/assets',
        queryParameters: {
          if (projectId != null) 'project_id': projectId,
          if (type != null) 'type': type.value,
          if (page != null) 'page': page,
          if (limit != null) 'limit': limit,
        },
      );
      
      final assets = <MediaAsset>[];
      for (final item in response.data!) {
        assets.add(MediaAsset.fromJson(item as Map<String, dynamic>));
      }
      
      return assets;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<MediaAsset> getAsset(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/assets/$id');
      return MediaAsset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<MediaAsset> uploadAsset({
    required String projectId,
    required MediaAssetType type,
    required String filename,
    required File file,
    String? mimeType,
  }) async {
    try {
      final formData = FormData.fromMap({
        'project_id': projectId,
        'type': type.value,
        'file': await MultipartFile.fromFile(file.path, filename: filename),
        if (mimeType != null) 'mime_type': mimeType,
      });

      final response = await _apiClient.post<Map<String, dynamic>>(
        '/assets/upload',
        data: formData,
      );
      
      return MediaAsset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<void> deleteAsset(String id) async {
    try {
      await _apiClient.delete<void>('/assets/$id');
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<String> getAssetDownloadUrl(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/assets/$id/download-url');
      return response.data!['url'] as String;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}