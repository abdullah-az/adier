import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/app_config.dart';
import '../../../core/di/providers.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final config = ref.watch(appConfigProvider);

    return ListView(
      padding: const EdgeInsets.all(24),
      children: <Widget>[
        Text('Settings', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 24),
        ListTile(
          leading: const Icon(Icons.palette_outlined),
          title: const Text('Theme mode'),
          subtitle: Text(themeMode.name.toUpperCase()),
          trailing: SegmentedButton<ThemeMode>(
            segments: const <ButtonSegment<ThemeMode>>[
              ButtonSegment(value: ThemeMode.system, label: Text('System')),
              ButtonSegment(value: ThemeMode.light, label: Text('Light')),
              ButtonSegment(value: ThemeMode.dark, label: Text('Dark')),
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
          leading: const Icon(Icons.bug_report_outlined),
          title: const Text('Diagnostics'),
          subtitle: Text('Flavor: ${config.flavor.label}\nAPI base URL: ${config.apiBaseUrl}'),
        ),
      ],
    );
  }
}
