import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cto/src/core/theme/theme_provider.dart';

void main() {
  group('ThemeModeNotifier', () {
    test('defaults to light mode', () {
      final notifier = ThemeModeNotifier();

      expect(notifier.state, ThemeMode.light);
    });

    test('toggles between light and dark', () {
      final notifier = ThemeModeNotifier();

      notifier.toggleThemeMode();
      expect(notifier.state, ThemeMode.dark);

      notifier.toggleThemeMode();
      expect(notifier.state, ThemeMode.light);
    });

    test('supports explicit mode updates', () {
      final notifier = ThemeModeNotifier();

      notifier.setThemeMode(ThemeMode.dark);
      expect(notifier.state, ThemeMode.dark);
    });
  });
}
