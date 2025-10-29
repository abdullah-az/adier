import 'dart:ui';

import 'package:shared_preferences/shared_preferences.dart';

import 'locale_preferences_stub.dart';

class SharedPreferencesLocalePreferences implements LocalePreferences {
  static const _localeKey = 'selected_locale_code';

  @override
  Future<Locale?> loadLocale() async {
    final prefs = await SharedPreferences.getInstance();
    final code = prefs.getString(_localeKey);
    if (code == null || code.isEmpty) {
      return null;
    }
    return Locale(code);
  }

  @override
  Future<void> saveLocale(Locale locale) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_localeKey, locale.languageCode);
  }

  @override
  Future<void> clearLocale() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_localeKey);
  }
}

LocalePreferences getLocalePreferences() => SharedPreferencesLocalePreferences();
