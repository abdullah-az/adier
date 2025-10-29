import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

import '../../../core/config/app_config.dart';
import '../../../core/di/providers.dart';
import '../../../core/localization/localization_extensions.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);
    final config = ref.watch(appConfigProvider);
    final l10n = AppLocalizations.of(context)!;
    final flavorLabel = config.flavor.localizedLabel(l10n);

    String themeModeLabelFor(ThemeMode mode) {
      return switch (mode) {
        ThemeMode.system => l10n.themeModeSystem,
        ThemeMode.light => l10n.themeModeLight,
        ThemeMode.dark => l10n.themeModeDark,
      };
    }

    return ListView(
      padding: const EdgeInsets.all(24),
      children: <Widget>[
        Text(l10n.settingsHeading, style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 24),
        ListTile(
          leading: const Icon(Icons.palette_outlined),
          title: Text(l10n.themeModeLabel),
          subtitle: Text(themeModeLabelFor(themeMode)),
          trailing: SegmentedButton<ThemeMode>(
            segments: <ButtonSegment<ThemeMode>>[
              ButtonSegment(value: ThemeMode.system, label: Text(l10n.themeModeSystem)),
              ButtonSegment(value: ThemeMode.light, label: Text(l10n.themeModeLight)),
              ButtonSegment(value: ThemeMode.dark, label: Text(l10n.themeModeDark)),
            ],
            selected: <ThemeMode>{themeMode},
            onSelectionChanged: (selection) {
              final mode = selection.isNotEmpty ? selection.first : null;
              if (mode != null) {
                ref.read(themeModeProvider.notifier).state = mode;
              }
            },
          ),
        ),
        const Divider(),
        ListTile(
          leading: const Icon(Icons.language_outlined),
          title: Text(l10n.languageLabel),
          subtitle: Text(locale.languageCode == 'ar' ? l10n.languageArabic : l10n.languageEnglish),
          trailing: SegmentedButton<Locale>(
            segments: <ButtonSegment<Locale>>[
              ButtonSegment(value: const Locale('en'), label: Text(l10n.languageEnglish)),
              ButtonSegment(value: const Locale('ar'), label: Text(l10n.languageArabic)),
            ],
            selected: <Locale>{locale},
            onSelectionChanged: (selection) {
              if (selection.isEmpty) {
                return;
              }
              final selectedLocale = selection.first;
              if (selectedLocale.languageCode != locale.languageCode) {
                ref.read(localeProvider.notifier).setLocale(selectedLocale);
              }
            },
          ),
        ),
        const Divider(),
        ListTile(
          leading: const Icon(Icons.bug_report_outlined),
          title: Text(l10n.diagnosticsTitle),
          subtitle: Text(l10n.diagnosticsSubtitle(flavorLabel, config.apiBaseUrl)),
        ),
      ],
    );
  }
}
