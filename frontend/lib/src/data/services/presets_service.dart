import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';
import '../models/platform_preset.dart';

class PresetsService {
  final ApiClient _apiClient;

  PresetsService(this._apiClient);

  Future<List<PlatformPreset>> getPresets({
    PresetCategory? category,
    int? page,
    int? limit,
  }) async {
    try {
      final response = await _apiClient.get<List<dynamic>>(
        '/presets',
        queryParameters: {
          if (category != null) 'category': category.value,
          if (page != null) 'page': page,
          if (limit != null) 'limit': limit,
        },
      );
      
      final presets = <PlatformPreset>[];
      for (final item in response.data!) {
        presets.add(PlatformPreset.fromJson(item as Map<String, dynamic>));
      }
      
      return presets;
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<PlatformPreset> getPreset(String id) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/presets/$id');
      return PlatformPreset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<PlatformPreset> getPresetByKey(String key) async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/presets/key/$key');
      return PlatformPreset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<PlatformPreset> createPreset({
    required String key,
    required String name,
    required PresetCategory category,
    String? description,
    required Map<String, dynamic> configuration,
  }) async {
    try {
      final response = await _apiClient.post<Map<String, dynamic>>(
        '/presets',
        data: {
          'key': key,
          'name': name,
          'category': category.value,
          'description': description,
          'configuration': configuration,
        },
      );
      return PlatformPreset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<PlatformPreset> updatePreset(String id, {
    String? name,
    PresetCategory? category,
    String? description,
    Map<String, dynamic>? configuration,
  }) async {
    try {
      final response = await _apiClient.patch<Map<String, dynamic>>(
        '/presets/$id',
        data: {
          if (name != null) 'name': name,
          if (category != null) 'category': category.value,
          if (description != null) 'description': description,
          if (configuration != null) 'configuration': configuration,
        },
      );
      return PlatformPreset.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<void> deletePreset(String id) async {
    try {
      await _apiClient.delete<void>('/presets/$id');
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}