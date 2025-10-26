import 'package:cto/src/core/localization/locale_provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('LocaleNotifier', () {
    test('defaults to English locale', () {
      final notifier = LocaleNotifier();
      expect(notifier.state, const Locale('en'));
    });

    test('toggle switches between English and Arabic', () {
      final notifier = LocaleNotifier();

      notifier.toggleLocale();
      expect(notifier.state, const Locale('ar'));

      notifier.toggleLocale();
      expect(notifier.state, const Locale('en'));
    });

    test('setLocale assigns provided locale', () {
      final notifier = LocaleNotifier();

      notifier.setLocale(const Locale('ar'));
      expect(notifier.state, const Locale('ar'));
    });
  });
}
