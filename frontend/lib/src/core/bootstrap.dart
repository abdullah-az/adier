import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app.dart';
import '../data/api/video_editor_api_client.dart';
import '../data/cache/project_cache.dart';
import '../data/repositories/clip_repository.dart';
import '../data/repositories/media_asset_repository.dart';
import '../data/repositories/preset_repository.dart';
import '../data/repositories/project_repository.dart';
import '../data/services/upload_progress_channel.dart';
import 'config/app_config.dart';
import 'di/providers.dart';
import 'di/service_registry.dart';
import 'localization/locale_preferences.dart';

Future<void> bootstrap({required AppFlavor flavor}) async {
  WidgetsFlutterBinding.ensureInitialized();

  final config = AppConfig.fromFlavor(flavor);
  final localePreferences = createLocalePreferences();
  final apiClient = InMemoryVideoEditorApiClient();
  final projectCache = SharedPreferencesProjectCache();
  final projectRepository = ProjectRepository(
    apiClient: apiClient,
    cache: projectCache,
  );
  final mediaAssetRepository = MediaAssetRepository(apiClient: apiClient);
  final clipRepository = ClipRepository(apiClient: apiClient);
  final presetRepository = PresetRepository(apiClient: apiClient);
  final progressChannel = InMemoryUploadProgressChannel();

  final registry = ServiceRegistry()
    ..registerSingleton<AppConfig>(config, overrideExisting: true)
    ..registerSingleton<LocalePreferences>(localePreferences, overrideExisting: true)
    ..registerSingleton<VideoEditorApiClient>(apiClient, overrideExisting: true)
    ..registerSingleton<ProjectCache>(projectCache, overrideExisting: true)
    ..registerSingleton<ProjectRepository>(projectRepository, overrideExisting: true)
    ..registerSingleton<MediaAssetRepository>(mediaAssetRepository, overrideExisting: true)
    ..registerSingleton<UploadProgressChannel>(progressChannel, overrideExisting: true)
    ..registerSingleton<ClipRepository>(clipRepository, overrideExisting: true)
    ..registerSingleton<PresetRepository>(presetRepository, overrideExisting: true);

  runApp(
    ProviderScope(
      overrides: [
        appConfigProvider.overrideWithValue(config),
        serviceRegistryProvider.overrideWithValue(registry),
      ],
      child: const App(),
    ),
  );
}
