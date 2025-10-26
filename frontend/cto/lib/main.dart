import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:responsive_framework/responsive_framework.dart';

import 'l10n/app_localizations.dart';
import 'src/core/constants/app_constants.dart';
import 'src/core/localization/locale_provider.dart';
import 'src/core/router/app_router.dart';
import 'src/core/theme/app_theme.dart';
import 'src/core/theme/theme_provider.dart';

void main() {
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      routerConfig: appRouter,
      title: AppConstants.appName,
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
      themeMode: themeMode,
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      builder: (context, child) {
        final appChild = child ?? const SizedBox.shrink();
        return ResponsiveBreakpoints.builder(
          child: appChild,
          breakpoints: const [
            Breakpoint(start: 0, end: 450, name: MOBILE),
            Breakpoint(start: 451, end: 800, name: TABLET),
            Breakpoint(start: 801, end: 1920, name: DESKTOP),
            Breakpoint(start: 1921, end: double.infinity, name: '4K'),
          ],
        );
      },
    );
  }
}
