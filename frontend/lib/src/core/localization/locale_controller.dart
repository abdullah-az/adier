import 'dart:ui';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'locale_preferences.dart';

const _supportedLocaleCodes = <String>{'en', 'ar'};

class LocaleController extends StateNotifier<Locale> {
  LocaleController(this._preferences) : super(const Locale('en')) {
    _initialize();
  }

  final LocalePreferences _preferences;

  Future<void> _initialize() async {
    final stored = await _preferences.loadLocale();
    if (stored == null || !_supportedLocaleCodes.contains(stored.languageCode)) {
      return;
    }
    final normalized = Locale(stored.languageCode);
    if (!mounted) {
      return;
    }
    state = normalized;
  }

  Future<void> setLocale(Locale locale) async {
    final code = locale.languageCode;
    if (!_supportedLocaleCodes.contains(code)) {
      throw ArgumentError.value(locale, 'locale', 'Unsupported locale');
    }
    final normalized = Locale(code);
    state = normalized;
    await _preferences.saveLocale(normalized);
  }
}
