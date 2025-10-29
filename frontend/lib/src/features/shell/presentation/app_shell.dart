import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/routes.dart';
import '../../../widgets/responsive_scaffold.dart';

class AppShell extends ConsumerWidget {
  const AppShell({
    required this.state,
    required this.child,
    super.key,
  });

  final GoRouterState state;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = GoRouter.of(context);
    final destinations = AppRoute.values
        .map(
          (route) => AdaptiveDestination(
            location: route.path,
            label: route.title,
            icon: _iconForRoute(route, selected: false),
            selectedIcon: _iconForRoute(route, selected: true),
          ),
        )
        .toList();

    final currentLocation = state.matchedLocation;
    final activeDestination = destinations.firstWhere(
      (destination) => currentLocation.startsWith(destination.location),
      orElse: () => destinations.first,
    );

    return ResponsiveScaffold(
      appBar: AppBar(title: Text(activeDestination.label)),
      body: child,
      destinations: destinations,
      currentLocation: currentLocation,
      onDestinationSelected: (destination) => router.go(destination.location),
    );
  }

  IconData _iconForRoute(AppRoute route, {required bool selected}) {
    return switch (route) {
      AppRoute.dashboard =>
        selected ? Icons.space_dashboard_rounded : Icons.space_dashboard_outlined,
      AppRoute.workspace => selected ? Icons.play_circle_filled_rounded : Icons.play_circle_outline,
      AppRoute.settings => selected ? Icons.settings_rounded : Icons.settings_outlined,
    };
  }
}
