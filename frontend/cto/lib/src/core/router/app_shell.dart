import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../l10n/app_localizations.dart';
import '../constants/app_constants.dart';
import '../localization/locale_provider.dart';
import '../theme/theme_provider.dart';

class AppShell extends ConsumerWidget {
  const AppShell({
    required this.state,
    required this.child,
    super.key,
  });

  final GoRouterState state;
  final Widget child;

  String _titleForRoute(AppLocalizations l10n) {
    switch (state.name) {
      case AppConstants.homeRouteName:
        return l10n.appTitle;
      case AppConstants.authRouteName:
        return l10n.auth;
      case AppConstants.profileRouteName:
        return l10n.profile;
      case AppConstants.editorRouteName:
        return l10n.subtitleEditorTitle;
      default:
        return l10n.appTitle;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);
    final isEnglish = locale.languageCode == AppConstants.englishCode;

    final router = GoRouter.of(context);
    final canPop = router.canPop();

    return Scaffold(
      appBar: AppBar(
        leading: canPop
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => context.pop(),
                tooltip: MaterialLocalizations.of(context).backButtonTooltip,
              )
            : null,
        title: Text(_titleForRoute(l10n)),
        actions: [
          IconButton(
            icon: Icon(
              themeMode == ThemeMode.light ? Icons.dark_mode : Icons.light_mode,
            ),
            tooltip: themeMode == ThemeMode.light ? l10n.darkMode : l10n.lightMode,
            onPressed: () {
              ref.read(themeModeProvider.notifier).toggleThemeMode();
            },
          ),
          IconButton(
            icon: Icon(isEnglish ? Icons.language : Icons.translate),
            tooltip: isEnglish ? l10n.arabic : l10n.english,
            onPressed: () {
              ref.read(localeProvider.notifier).toggleLocale();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: KeyedSubtree(
            key: state.pageKey,
            child: child,
          ),
        ),
      ),
    );
  }
}
