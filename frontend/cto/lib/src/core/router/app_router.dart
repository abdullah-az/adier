import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/auth_page.dart';
import '../../features/editor/subtitle_music_editor_page.dart';
import '../../features/home/home_page.dart';
import '../../features/profile/profile_page.dart';
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
          path: AppConstants.editorRoute,
          name: AppConstants.editorRouteName,
          builder: (context, state) {
            final videoId = state.pathParameters['videoId'] ?? AppConstants.defaultVideoId;
            return SubtitleMusicEditorPage(videoId: videoId);
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
