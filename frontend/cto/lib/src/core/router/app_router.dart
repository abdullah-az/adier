import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/project_model.dart';
import '../../features/auth/auth_page.dart';
import '../../features/home/home_page.dart';
import '../../features/profile/profile_page.dart';
import '../../features/projects/project_detail_page.dart';
import '../constants/app_constants.dart';
import 'app_shell.dart';

final appRouter = GoRouter(
  initialLocation: AppConstants.homeRoute,
  routes: [
    ShellRoute(
      builder: (context, state, child) => AppShell(
        state: state,
        child: child,
      ),
      routes: [
        GoRoute(
          path: AppConstants.homeRoute,
          name: AppConstants.homeRouteName,
          builder: (context, state) => const HomePage(),
        ),
        GoRoute(
          path: AppConstants.authRoute,
          name: AppConstants.authRouteName,
          builder: (context, state) => const AuthPage(),
        ),
        GoRoute(
          path: AppConstants.profileRoute,
          name: AppConstants.profileRouteName,
          builder: (context, state) => const ProfilePage(),
        ),
        GoRoute(
          path: AppConstants.projectDetailRoute,
          name: AppConstants.projectDetailRouteName,
          builder: (context, state) {
            final projectId = state.pathParameters['id'] ?? '';
            final project = state.extra is ProjectModel ? state.extra as ProjectModel : null;
            return ProjectDetailPage(
              projectId: projectId,
              initialProject: project,
            );
          },
        ),
      ],
    ),
  ],
  errorBuilder: (context, state) => AppShell(
    state: state,
    child: Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text('Page not found: ${state.uri}'),
      ),
    ),
  ),
);
