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
    Locale('ar'),
    Locale('en'),
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

  /// A greeting message
  ///
  /// In en, this message translates to:
  /// **'Hello, {name}!'**
  String hello(String name);

  /// Label for light theme
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get lightTheme;

  /// Label for dark theme
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get darkTheme;

  /// Section title for quick actions
  ///
  /// In en, this message translates to:
  /// **'Quick actions'**
  String get quickActions;

  /// Navigation label for authentication
  ///
  /// In en, this message translates to:
  /// **'Auth'**
  String get auth;

  /// Navigation label for upload page
  ///
  /// In en, this message translates to:
  /// **'Upload'**
  String get upload;

  /// Navigation label for timeline editor
  ///
  /// In en, this message translates to:
  /// **'Timeline'**
  String get timeline;

  /// Navigation label for subtitle editor
  ///
  /// In en, this message translates to:
  /// **'Subtitles'**
  String get subtitles;

  /// Navigation label for export page
  ///
  /// In en, this message translates to:
  /// **'Export'**
  String get export;

  /// Tooltip for adding media uploads
  ///
  /// In en, this message translates to:
  /// **'Add media'**
  String get addMedia;

  /// Description text for upload page
  ///
  /// In en, this message translates to:
  /// **'Select or record media files to begin processing.'**
  String get uploadDescription;

  /// Empty state message for uploads
  ///
  /// In en, this message translates to:
  /// **'No uploads yet. Add media to begin.'**
  String get uploadEmpty;

  /// Label showing upload duration
  ///
  /// In en, this message translates to:
  /// **'Duration: {seconds} s'**
  String uploadDuration(int seconds);

  /// Tooltip for advancing upload progress
  ///
  /// In en, this message translates to:
  /// **'Advance upload'**
  String get advanceUpload;

  /// Button label to navigate to timeline
  ///
  /// In en, this message translates to:
  /// **'Continue to timeline'**
  String get goToTimeline;

  /// Title for timeline editor page
  ///
  /// In en, this message translates to:
  /// **'Timeline editor'**
  String get timelineEditor;

  /// Tooltip to add a timeline segment
  ///
  /// In en, this message translates to:
  /// **'Add segment'**
  String get addSegment;

  /// Summary of timeline content
  ///
  /// In en, this message translates to:
  /// **'{count} segments · Total {duration}'**
  String timelineSummary(int count, String duration);

  /// Helper text for timeline interactions
  ///
  /// In en, this message translates to:
  /// **'Drag and drop segments to adjust the story.'**
  String get timelineHint;

  /// Displays segment duration percentage
  ///
  /// In en, this message translates to:
  /// **'Duration {duration} ({percent}% of total)'**
  String segmentDuration(String duration, String percent);

  /// Displays segment start position
  ///
  /// In en, this message translates to:
  /// **'Starts at {start} ({percent}% position)'**
  String segmentStart(String start, String percent);

  /// Button label to open subtitle editor
  ///
  /// In en, this message translates to:
  /// **'Open subtitle editor'**
  String get openSubtitles;

  /// Message shown when export starts
  ///
  /// In en, this message translates to:
  /// **'Export queued successfully'**
  String get exportSuccess;

  /// Dialog title for export
  ///
  /// In en, this message translates to:
  /// **'Export project'**
  String get exportProjectTitle;

  /// Label for export format selection
  ///
  /// In en, this message translates to:
  /// **'Format'**
  String get exportFormat;

  /// Label for export resolution selection
  ///
  /// In en, this message translates to:
  /// **'Resolution'**
  String get exportResolution;

  /// Label for including subtitles
  ///
  /// In en, this message translates to:
  /// **'Include subtitles'**
  String get exportIncludeSubtitles;

  /// Cancel button label
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// Button label to start export
  ///
  /// In en, this message translates to:
  /// **'Start export'**
  String get exportProjectAction;

  /// Export preparation step
  ///
  /// In en, this message translates to:
  /// **'Review timeline order'**
  String get exportStepReview;

  /// Export preparation step
  ///
  /// In en, this message translates to:
  /// **'Choose export quality'**
  String get exportStepQuality;

  /// Export preparation step
  ///
  /// In en, this message translates to:
  /// **'Confirm subtitle track'**
  String get exportStepSubtitles;

  /// Summary before export
  ///
  /// In en, this message translates to:
  /// **'Ready to export {segmentCount} segments · {duration}'**
  String exportSummary(int segmentCount, String duration);

  /// Title for subtitle editor
  ///
  /// In en, this message translates to:
  /// **'Subtitle editor'**
  String get subtitleEditor;

  /// Description for subtitle editor
  ///
  /// In en, this message translates to:
  /// **'Manage caption timings and text.'**
  String get subtitleEditorDescription;

  /// Label for subtitle start field
  ///
  /// In en, this message translates to:
  /// **'Start (s)'**
  String get subtitleStartLabel;

  /// Label for subtitle end field
  ///
  /// In en, this message translates to:
  /// **'End (s)'**
  String get subtitleEndLabel;

  /// Helper text for subtitle time fields
  ///
  /// In en, this message translates to:
  /// **'Seconds with decimals allowed'**
  String get subtitleTimeHelper;

  /// Label for subtitle text field
  ///
  /// In en, this message translates to:
  /// **'Subtitle text'**
  String get subtitleTextLabel;

  /// Button label to add subtitle
  ///
  /// In en, this message translates to:
  /// **'Add subtitle'**
  String get addSubtitle;

  /// Validation error for subtitle form
  ///
  /// In en, this message translates to:
  /// **'Enter valid start/end times and text.'**
  String get subtitleValidationError;

  /// Displays subtitle time range
  ///
  /// In en, this message translates to:
  /// **'From {start} to {end}'**
  String subtitleTimeRange(String start, String end);
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
