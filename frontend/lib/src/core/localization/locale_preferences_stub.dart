import 'dart:ui';

abstract class LocalePreferences {
  Future<Locale?> loadLocale();
  Future<void> saveLocale(Locale locale);
  Future<void> clearLocale();
}

LocalePreferences getLocalePreferences() {
  throw UnsupportedError('Locale preferences are not supported on this platform.');
}
