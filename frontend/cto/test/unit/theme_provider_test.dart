import 'package:cto/src/core/theme/theme_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ThemeModeNotifier', () {
    test('initial state is light mode', () {
      final notifier = ThemeModeNotifier();
      expect(notifier.state, ThemeMode.light);
    });

    test('toggle switches between light and dark modes', () {
      final notifier = ThemeModeNotifier();

      notifier.toggleThemeMode();
      expect(notifier.state, ThemeMode.dark);

      notifier.toggleThemeMode();
      expect(notifier.state, ThemeMode.light);
    });

    test('setThemeMode updates to provided mode', () {
      final notifier = ThemeModeNotifier();

      notifier.setThemeMode(ThemeMode.dark);
      expect(notifier.state, ThemeMode.dark);

      notifier.setThemeMode(ThemeMode.system);
      expect(notifier.state, ThemeMode.system);
    });
  });
}
