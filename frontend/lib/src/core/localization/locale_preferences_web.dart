// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:ui';

import 'locale_preferences_stub.dart';

class WebLocalePreferences implements LocalePreferences {
  static const _localeKey = 'selected_locale_code';

  @override
  Future<Locale?> loadLocale() async {
    final code = html.window.localStorage[_localeKey];
    if (code == null || code.isEmpty) {
      return null;
    }
    return Locale(code);
  }

  @override
  Future<void> saveLocale(Locale locale) async {
    html.window.localStorage[_localeKey] = locale.languageCode;
  }

  @override
  Future<void> clearLocale() async {
    html.window.localStorage.remove(_localeKey);
  }
}

LocalePreferences getLocalePreferences() => WebLocalePreferences();
