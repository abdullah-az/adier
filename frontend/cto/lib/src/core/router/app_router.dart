import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/home/home_page.dart';
import '../../features/auth/auth_page.dart';
import '../../features/profile/profile_page.dart';
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
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(
      child: Text('Page not found: ${state.uri}'),
    ),
  ),
);
