import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app.dart';
import 'config/app_config.dart';
import 'di/providers.dart';
import 'di/service_registry.dart';
import 'localization/locale_preferences.dart';

Future<void> bootstrap({required AppFlavor flavor}) async {
  WidgetsFlutterBinding.ensureInitialized();

  final config = AppConfig.fromFlavor(flavor);
  final localePreferences = createLocalePreferences();
  final registry = ServiceRegistry()
    ..registerSingleton<AppConfig>(config, overrideExisting: true)
    ..registerSingleton<LocalePreferences>(localePreferences, overrideExisting: true);

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
