import 'package:flutter_gen/gen_l10n/app_localizations.dart';

enum AppRoute {
  dashboard('/dashboard'),
  workspace('/workspace'),
  settings('/settings');

  const AppRoute(this.path);

  final String path;

  String get name => switch (this) {
        AppRoute.dashboard => 'dashboard',
        AppRoute.workspace => 'workspace',
        AppRoute.settings => 'settings',
      };

  String get relativePath => path.substring(1);

  String label(AppLocalizations l10n) => switch (this) {
        AppRoute.dashboard => l10n.navDashboard,
        AppRoute.workspace => l10n.navWorkspace,
        AppRoute.settings => l10n.navSettings,
      };
}
