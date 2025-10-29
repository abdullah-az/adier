import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'service_registry.dart';

final serviceRegistryProvider = Provider<ServiceRegistry>((ref) {
  throw UnimplementedError('The serviceRegistryProvider must be overridden at bootstrap.');
});

final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.system);
