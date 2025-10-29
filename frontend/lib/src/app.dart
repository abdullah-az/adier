import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/config/app_config.dart';
import 'core/di/providers.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

class App extends ConsumerWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final themeMode = ref.watch(themeModeProvider);
    final config = ref.watch(appConfigProvider);
    ref.watch(serviceRegistryProvider);

    final title = config.flavor == AppFlavor.production
        ? 'AI Video Editor'
        : 'AI Video Editor • ${config.flavor.label}';

    return MaterialApp.router(
      title: title,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      routerConfig: router,
      builder: (context, child) {
        final mediaQuery = MediaQuery.of(context);
        return MediaQuery(
          data: mediaQuery.copyWith(textScaler: mediaQuery.textScaler.clamp(minScaleFactor: 0.9, maxScaleFactor: 1.1)),
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
