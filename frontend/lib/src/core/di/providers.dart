import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api/video_editor_api_client.dart';
import '../../data/cache/project_cache.dart';
import '../../data/controllers/clip_controller.dart';
import '../../data/controllers/preset_controller.dart';
import '../../data/controllers/project_list_controller.dart';
import '../../data/controllers/upload_controller.dart';
import '../../data/models/clip.dart';
import '../../data/models/media_asset.dart';
import '../../data/models/project.dart';
import '../../data/models/preset.dart';
import '../../data/repositories/clip_repository.dart';
import '../../data/repositories/media_asset_repository.dart';
import '../../data/repositories/preset_repository.dart';
import '../../data/repositories/project_repository.dart';
import '../localization/locale_controller.dart';
import '../localization/locale_preferences.dart';
import 'service_registry.dart';

final serviceRegistryProvider = Provider<ServiceRegistry>((ref) {
  throw UnimplementedError('The serviceRegistryProvider must be overridden at bootstrap.');
});

final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);

final localePreferencesProvider = Provider<LocalePreferences>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<LocalePreferences>();
});

final localeProvider = StateNotifierProvider<LocaleController, Locale>((ref) {
  final preferences = ref.watch(localePreferencesProvider);
  final controller = LocaleController(preferences);
  ref.onDispose(controller.dispose);
  return controller;
});

final videoEditorApiClientProvider = Provider<VideoEditorApiClient>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<VideoEditorApiClient>();
});

final projectCacheProvider = Provider<ProjectCache>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<ProjectCache>();
});

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<ProjectRepository>();
});

final mediaAssetRepositoryProvider = Provider<MediaAssetRepository>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<MediaAssetRepository>();
});

final clipRepositoryProvider = Provider<ClipRepository>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<ClipRepository>();
});

final presetRepositoryProvider = Provider<PresetRepository>((ref) {
  final registry = ref.watch(serviceRegistryProvider);
  return registry.get<PresetRepository>();
});

final projectListControllerProvider = StateNotifierProvider<ProjectListController, AsyncValue<List<Project>>>((ref) {
  final repository = ref.watch(projectRepositoryProvider);
  return ProjectListController(repository);
});

final uploadControllerProvider = StateNotifierProvider<UploadController, AsyncValue<MediaAsset?>>((ref) {
  final repository = ref.watch(mediaAssetRepositoryProvider);
  return UploadController(repository);
});

final clipControllerProvider = StateNotifierProvider.family<ClipController, AsyncValue<List<Clip>>, String>((ref, projectId) {
  final repository = ref.watch(clipRepositoryProvider);
  return ClipController(repository, projectId: projectId);
});

final presetControllerProvider = StateNotifierProvider<PresetController, AsyncValue<List<Preset>>>((ref) {
  final repository = ref.watch(presetRepositoryProvider);
  return PresetController(repository);
});
