import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// The different build flavors supported by the application.
enum AppFlavor {
  development,
  staging,
  production,
}

extension AppFlavorX on AppFlavor {
  /// Parses [value] into a known [AppFlavor]. Defaults to
  /// [AppFlavor.development] when the input is unknown.
  static AppFlavor fromName(String value) {
    return AppFlavor.values.firstWhere(
      (flavor) => flavor.name.toLowerCase() == value.toLowerCase(),
      orElse: () => AppFlavor.development,
    );
  }

  String get label => switch (this) {
        AppFlavor.development => 'Development',
        AppFlavor.staging => 'Staging',
        AppFlavor.production => 'Production',
      };

  String get assetConfigPath => 'assets/config/${name.toLowerCase()}.json';
}

class AppConfig {
  const AppConfig({
    required this.flavor,
    required this.apiBaseUrl,
    required this.analyticsEnabled,
  });

  factory AppConfig.fromFlavor(AppFlavor flavor) {
    return switch (flavor) {
      AppFlavor.development => const AppConfig(
          flavor: AppFlavor.development,
          apiBaseUrl: 'http://localhost:8000',
          analyticsEnabled: false,
        ),
      AppFlavor.staging => const AppConfig(
          flavor: AppFlavor.staging,
          apiBaseUrl: 'https://staging.api.aivideoeditor.com',
          analyticsEnabled: true,
        ),
      AppFlavor.production => const AppConfig(
          flavor: AppFlavor.production,
          apiBaseUrl: 'https://api.aivideoeditor.com',
          analyticsEnabled: true,
        ),
    };
  }

  final AppFlavor flavor;
  final String apiBaseUrl;
  final bool analyticsEnabled;

  bool get isDebugging => kDebugMode && flavor == AppFlavor.development;
}

final appConfigProvider = Provider<AppConfig>((ref) {
  throw UnimplementedError('The appConfigProvider must be overridden at bootstrap.');
});
