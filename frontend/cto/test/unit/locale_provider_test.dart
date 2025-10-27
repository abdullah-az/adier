import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cto/src/core/localization/locale_provider.dart';
import 'package:cto/src/core/constants/app_constants.dart';

void main() {
  group('LocaleNotifier', () {
    test('defaults to English locale', () {
      final notifier = LocaleNotifier();

      expect(notifier.state, const Locale(AppConstants.englishCode));
    });

    test('toggles between English and Arabic', () {
      final notifier = LocaleNotifier();

      notifier.toggleLocale();
      expect(notifier.state, const Locale(AppConstants.arabicCode));

      notifier.toggleLocale();
      expect(notifier.state, const Locale(AppConstants.englishCode));
    });

    test('supports explicit locale updates', () {
      final notifier = LocaleNotifier();

      notifier.setLocale(const Locale(AppConstants.arabicCode));
      expect(notifier.state, const Locale(AppConstants.arabicCode));
    });
  });
}
