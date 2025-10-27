import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ar'),
  ];

  /// The title of the application
  ///
  /// In en, this message translates to:
  /// **'CTO App'**
  String get appTitle;

  /// Welcome message
  ///
  /// In en, this message translates to:
  /// **'Welcome'**
  String get welcome;

  /// Home page title
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get home;

  /// Profile page title
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// Settings page title
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// Authentication page title
  ///
  /// In en, this message translates to:
  /// **'Authentication'**
  String get auth;

  /// Language setting label
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// Dark mode toggle label
  ///
  /// In en, this message translates to:
  /// **'Dark Mode'**
  String get darkMode;

  /// Light mode label
  ///
  /// In en, this message translates to:
  /// **'Light Mode'**
  String get lightMode;

  /// English language option
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get english;

  /// Arabic language option
  ///
  /// In en, this message translates to:
  /// **'Arabic'**
  String get arabic;

  /// Placeholder description for authentication feature
  ///
  /// In en, this message translates to:
  /// **'Sign-in and registration flows will live here.'**
  String get authPlaceholder;

  /// Placeholder description for profile feature
  ///
  /// In en, this message translates to:
  /// **'User profile information will be displayed here.'**
  String get profilePlaceholder;

  /// A greeting message
  ///
  /// In en, this message translates to:
  /// **'Hello, {name}!'**
  String hello(String name);

  /// Timeline section title
  ///
  /// In en, this message translates to:
  /// **'Timeline'**
  String get timeline;

  /// Timeline error message
  ///
  /// In en, this message translates to:
  /// **'Unable to load timeline.'**
  String get timelineError;

  /// Timeline empty state
  ///
  /// In en, this message translates to:
  /// **'Add clips to build your story.'**
  String get timelineEmpty;

  /// Timeline total duration label
  ///
  /// In en, this message translates to:
  /// **'Total duration: {duration}'**
  String timelineTotalDuration(String duration);

  /// Subtitle section title
  ///
  /// In en, this message translates to:
  /// **'Subtitles'**
  String get subtitles;

  /// Subtitle error message
  ///
  /// In en, this message translates to:
  /// **'Unable to load subtitles.'**
  String get subtitleError;

  /// Subtitle empty state
  ///
  /// In en, this message translates to:
  /// **'Generate captions from the timeline.'**
  String get subtitlesEmpty;

  /// Upload section title
  ///
  /// In en, this message translates to:
  /// **'Upload'**
  String get upload;

  /// Upload button label
  ///
  /// In en, this message translates to:
  /// **'Select sample file'**
  String get selectFile;

  /// Upload progress label
  ///
  /// In en, this message translates to:
  /// **'Uploading…'**
  String get uploadInProgress;

  /// Upload success label
  ///
  /// In en, this message translates to:
  /// **'Upload complete'**
  String get uploadCompleted;

  /// Upload failure label
  ///
  /// In en, this message translates to:
  /// **'Upload failed'**
  String get uploadFailed;

  /// Label for selected file
  ///
  /// In en, this message translates to:
  /// **'Selected file'**
  String get selectedFile;

  /// Editor page title
  ///
  /// In en, this message translates to:
  /// **'Editor'**
  String get editorTitle;

  /// Export button label
  ///
  /// In en, this message translates to:
  /// **'Export'**
  String get export;

  /// Export dialog title
  ///
  /// In en, this message translates to:
  /// **'Export project'**
  String get exportTitle;

  /// Export dialog subtitle
  ///
  /// In en, this message translates to:
  /// **'Generate a downloadable video for your project.'**
  String get exportSubtitle;

  /// Export format label
  ///
  /// In en, this message translates to:
  /// **'Format'**
  String get exportFormat;

  /// Export in progress label
  ///
  /// In en, this message translates to:
  /// **'Preparing export…'**
  String get exportInProgress;

  /// Export success message
  ///
  /// In en, this message translates to:
  /// **'Export ready: {exportId}'**
  String exportSuccess(String exportId);

  /// Export error message
  ///
  /// In en, this message translates to:
  /// **'Export failed'**
  String get exportError;

  /// Cancel button label
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
