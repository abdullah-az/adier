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
      body: ListView(
        padding: const EdgeInsets.all(24.0),
        children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
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
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Text(
                l10n.hello('User'),
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
            ],
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
                      themeMode == ThemeMode.light ? l10n.lightTheme : l10n.darkTheme,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            l10n.quickActions,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          _ActionList(
            actions: [
              _ActionItem(
                title: l10n.auth,
                icon: Icons.login,
                route: AppConstants.authRoute,
              ),
              _ActionItem(
                title: l10n.profile,
                icon: Icons.person,
                route: AppConstants.profileRoute,
              ),
              _ActionItem(
                title: l10n.upload,
                icon: Icons.cloud_upload_outlined,
                route: AppConstants.uploadRoute,
              ),
              _ActionItem(
                title: l10n.timeline,
                icon: Icons.timeline,
                route: AppConstants.timelineRoute,
              ),
              _ActionItem(
                title: l10n.subtitles,
                icon: Icons.subtitles_outlined,
                route: AppConstants.subtitlesRoute,
              ),
              _ActionItem(
                title: l10n.export,
                icon: Icons.ios_share,
                route: AppConstants.exportRoute,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ActionItem {
  const _ActionItem({
    required this.title,
    required this.icon,
    required this.route,
  });

  final String title;
  final IconData icon;
  final String route;
}

class _ActionList extends StatelessWidget {
  const _ActionList({
    required this.actions,
  });

  final List<_ActionItem> actions;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      key: const Key('home_actions_list'),
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemBuilder: (context, index) {
        final action = actions[index];
        return Card(
          child: ListTile(
            leading: Icon(action.icon),
            title: Text(action.title),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(action.route),
          ),
        );
      },
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemCount: actions.length,
    );
  }
}
