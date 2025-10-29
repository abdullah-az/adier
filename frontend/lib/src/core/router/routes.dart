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

  String get title => switch (this) {
        AppRoute.dashboard => 'Dashboard',
        AppRoute.workspace => 'Workspace',
        AppRoute.settings => 'Settings',
      };
}
