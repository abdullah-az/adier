import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../localization/locale_controller.dart';
import '../localization/locale_preferences.dart';
import 'service_registry.dart';

final serviceRegistryProvider = Provider<ServiceRegistry>((ref) {
  throw UnimplementedError('The serviceRegistryProvider must be overridden at bootstrap.');
});

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

final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);
