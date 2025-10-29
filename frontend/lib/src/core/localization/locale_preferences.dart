import 'locale_preferences_stub.dart'
    if (dart.library.html) 'locale_preferences_web.dart'
    if (dart.library.io) 'locale_preferences_io.dart';

export 'locale_preferences_stub.dart';

LocalePreferences createLocalePreferences() => getLocalePreferences();
