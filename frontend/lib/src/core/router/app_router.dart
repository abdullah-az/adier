import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/dashboard/presentation/dashboard_page.dart';
import '../../features/settings/presentation/settings_page.dart';
import '../../features/shell/presentation/app_shell.dart';
import '../../features/workspace/presentation/workspace_page.dart';
import '../config/app_config.dart';
import 'routes.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'rootNavigator');
final _shellNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'shellNavigator');

final appRouterProvider = Provider<GoRouter>((ref) {
  final config = ref.watch(appConfigProvider);

  final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: AppRoute.dashboard.path,
    debugLogDiagnostics: config.isDebugging,
    routes: <RouteBase>[
      GoRoute(
        path: '/',
        redirect: (context, state) => AppRoute.dashboard.path,
      ),
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => AppShell(
          state: state,
          child: child,
        ),
        routes: <RouteBase>[
          GoRoute(
            path: AppRoute.dashboard.relativePath,
            name: AppRoute.dashboard.name,
            pageBuilder: (context, state) => const NoTransitionPage<void>(
              child: DashboardPage(),
            ),
          ),
          GoRoute(
            path: AppRoute.workspace.relativePath,
            name: AppRoute.workspace.name,
            pageBuilder: (context, state) => const NoTransitionPage<void>(
              child: WorkspacePage(),
            ),
          ),
          GoRoute(
            path: AppRoute.settings.relativePath,
            name: AppRoute.settings.name,
            pageBuilder: (context, state) => const NoTransitionPage<void>(
              child: SettingsPage(),
            ),
          ),
        ],
      ),
    ],
  );

  ref.onDispose(router.dispose);
  return router;
});
