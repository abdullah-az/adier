import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/home/home_page.dart';
import '../../features/auth/auth_page.dart';
import '../../features/profile/profile_page.dart';
import '../../features/upload/upload_page.dart';
import '../../features/timeline/timeline_editor_page.dart';
import '../../features/subtitles/subtitle_editor_page.dart';
import '../../features/export/export_page.dart';
import '../constants/app_constants.dart';

final appRouter = GoRouter(
  initialLocation: AppConstants.homeRoute,
  routes: [
    GoRoute(
      path: AppConstants.homeRoute,
      name: 'home',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: AppConstants.authRoute,
      name: 'auth',
      builder: (context, state) => const AuthPage(),
    ),
    GoRoute(
      path: AppConstants.profileRoute,
      name: 'profile',
      builder: (context, state) => const ProfilePage(),
    ),
    GoRoute(
      path: AppConstants.uploadRoute,
      name: 'upload',
      builder: (context, state) => const UploadPage(),
    ),
    GoRoute(
      path: AppConstants.timelineRoute,
      name: 'timeline',
      builder: (context, state) => const TimelineEditorPage(),
    ),
    GoRoute(
      path: AppConstants.subtitlesRoute,
      name: 'subtitles',
      builder: (context, state) => const SubtitleEditorPage(),
    ),
    GoRoute(
      path: AppConstants.exportRoute,
      name: 'export',
      builder: (context, state) => const ExportPage(),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(
      child: Text('Page not found: ${state.uri}'),
    ),
  ),
);
