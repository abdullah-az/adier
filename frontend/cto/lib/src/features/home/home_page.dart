import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        actions: [
          IconButton(
            icon: Icon(
              themeMode == ThemeMode.light ? Icons.dark_mode : Icons.light_mode,
            ),
            onPressed: () {
              ref.read(themeModeProvider.notifier).toggleThemeMode();
            },
            tooltip: l10n.darkMode,
          ),
          IconButton(
            icon: const Icon(Icons.language),
            onPressed: () {
              ref.read(localeProvider.notifier).toggleLocale();
            },
            tooltip: l10n.language,
          ),
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.flutter_dash,
                size: 100,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                l10n.welcome,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 16),
              Text(
                l10n.hello('User'),
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 32),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.language),
                        title: Text(l10n.language),
                        subtitle: Text(
                          locale.languageCode == AppConstants.englishCode
                              ? l10n.english
                              : l10n.arabic,
                        ),
                      ),
                      ListTile(
                        leading: Icon(
                          themeMode == ThemeMode.light
                              ? Icons.light_mode
                              : Icons.dark_mode,
                        ),
                        title: Text(l10n.darkMode),
                        subtitle: Text(
                          themeMode == ThemeMode.light ? 'Light' : 'Dark',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () {
                      context.push(AppConstants.authRoute);
                    },
                    icon: const Icon(Icons.login),
                    label: const Text('Auth'),
                  ),
                  const SizedBox(width: 16),
                  ElevatedButton.icon(
                    onPressed: () {
                      context.push(AppConstants.profileRoute);
                    },
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
