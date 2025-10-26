import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:responsive_framework/responsive_framework.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/constants/app_constants.dart';
import '../../core/localization/locale_provider.dart';
import '../../core/theme/theme_provider.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);
    final breakpoints = ResponsiveBreakpoints.of(context);
    final isLargeScreen = breakpoints.largerThan(TABLET);

    final iconSize = isLargeScreen ? 120.0 : 96.0;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Icon(
                Icons.flutter_dash,
                size: iconSize,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                l10n.welcome,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 12),
              Text(
                l10n.hello('User'),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 32),
              Card(
                margin: EdgeInsets.zero,
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        l10n.settings,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.language),
                        title: Text(l10n.language),
                        subtitle: Text(
                          locale.languageCode == AppConstants.englishCode
                              ? l10n.english
                              : l10n.arabic,
                        ),
                      ),
                      const Divider(),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          themeMode == ThemeMode.light
                              ? Icons.light_mode
                              : Icons.dark_mode,
                        ),
                        title: Text(l10n.darkMode),
                        subtitle: Text(
                          themeMode == ThemeMode.light
                              ? l10n.lightMode
                              : l10n.darkMode,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Wrap(
                spacing: 16,
                runSpacing: 16,
                alignment: WrapAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () => context.push(AppConstants.authRoute),
                    icon: const Icon(Icons.login),
                    label: Text(l10n.auth),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => context.push(AppConstants.profileRoute),
                    icon: const Icon(Icons.person),
                    label: Text(l10n.profile),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
