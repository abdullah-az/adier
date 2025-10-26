class AppConstants {
  static const String appName = 'CTO App';
  
  // API Configuration
  static const String apiBaseUrl = 'http://localhost:8000/api';
  static const int apiTimeout = 30000;
  
  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String languageKey = 'app_language';
  static const String themeKey = 'app_theme';
  
  // Routes
  static const String homeRoute = '/';
  static const String authRoute = '/auth';
  static const String profileRoute = '/profile';
  static const String uploadRoute = '/upload';
  static const String timelineRoute = '/timeline';
  static const String subtitlesRoute = '/subtitles';
  static const String exportRoute = '/export';
  
  // Supported Locales
  static const String englishCode = 'en';
  static const String arabicCode = 'ar';
}
