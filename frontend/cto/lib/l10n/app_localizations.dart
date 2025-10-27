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

  /// Title for the subtitle and music editor page
  ///
  /// In en, this message translates to:
  /// **'Subtitle & Music Editor'**
  String get subtitleEditorTitle;

  /// Label for the subtitle segments section
  ///
  /// In en, this message translates to:
  /// **'Subtitle Segments'**
  String get subtitleSegments;

  /// Button label to add a new subtitle segment
  ///
  /// In en, this message translates to:
  /// **'Add Segment'**
  String get addSegment;

  /// Label for a save changes action
  ///
  /// In en, this message translates to:
  /// **'Save Changes'**
  String get saveChanges;

  /// Indicates that the app is saving data
  ///
  /// In en, this message translates to:
  /// **'Saving...'**
  String get saving;

  /// Placeholder shown when there are no subtitle segments
  ///
  /// In en, this message translates to:
  /// **'No subtitle segments yet. Add one to get started.'**
  String get noSegmentsPlaceholder;

  /// Label for the subtitle text input
  ///
  /// In en, this message translates to:
  /// **'Segment Text'**
  String get segmentText;

  /// Label for the segment start time
  ///
  /// In en, this message translates to:
  /// **'Start Time'**
  String get startTime;

  /// Label for the segment end time
  ///
  /// In en, this message translates to:
  /// **'End Time'**
  String get endTime;

  /// Action to split a subtitle segment
  ///
  /// In en, this message translates to:
  /// **'Split Segment'**
  String get splitSegment;

  /// Action to merge the current segment with the next one
  ///
  /// In en, this message translates to:
  /// **'Merge with Next'**
  String get mergeWithNext;

  /// Toast message displayed when subtitles are saved
  ///
  /// In en, this message translates to:
  /// **'Subtitles updated successfully.'**
  String get subtitleUpdateSuccess;

  /// Error message when subtitle saving fails
  ///
  /// In en, this message translates to:
  /// **'Failed to update subtitles. Please try again.'**
  String get subtitleUpdateFailure;

  /// Label for the live preview section
  ///
  /// In en, this message translates to:
  /// **'Live Preview'**
  String get livePreview;

  /// Placeholder when no subtitle is active at current time
  ///
  /// In en, this message translates to:
  /// **'No subtitle at this position.'**
  String get previewEmptySubtitle;

  /// Label for the preview timeline slider
  ///
  /// In en, this message translates to:
  /// **'Timeline Position'**
  String get timelinePosition;

  /// Label for the music selection section
  ///
  /// In en, this message translates to:
  /// **'Background Music'**
  String get musicLibrary;

  /// Action to assign the selected track
  ///
  /// In en, this message translates to:
  /// **'Assign Track'**
  String get musicAssign;

  /// Placeholder when no music tracks are available
  ///
  /// In en, this message translates to:
  /// **'No tracks available at the moment.'**
  String get noMusicTracksPlaceholder;

  /// Action to preview a music track
  ///
  /// In en, this message translates to:
  /// **'Preview'**
  String get musicPreview;

  /// Label for duration information
  ///
  /// In en, this message translates to:
  /// **'Duration'**
  String get durationLabel;

  /// Label for the volume control
  ///
  /// In en, this message translates to:
  /// **'Volume'**
  String get volume;

  /// Label for fade-in control
  ///
  /// In en, this message translates to:
  /// **'Fade In'**
  String get fadeIn;

  /// Label for fade-out control
  ///
  /// In en, this message translates to:
  /// **'Fade Out'**
  String get fadeOut;

  /// Label for music placement options
  ///
  /// In en, this message translates to:
  /// **'Placement'**
  String get placement;

  /// Placement option applying to the full timeline
  ///
  /// In en, this message translates to:
  /// **'Full Timeline'**
  String get placementFullTimeline;

  /// Placement option applying to a clip range
  ///
  /// In en, this message translates to:
  /// **'Clip Specific'**
  String get placementClip;

  /// Label for the clip range controls
  ///
  /// In en, this message translates to:
  /// **'Clip Range'**
  String get clipRange;

  /// Success message when music settings are saved
  ///
  /// In en, this message translates to:
  /// **'Music selection saved.'**
  String get musicUpdateSuccess;

  /// Error message when music save fails
  ///
  /// In en, this message translates to:
  /// **'Failed to save music selection. Please try again.'**
  String get musicUpdateFailure;

  /// Label for retry actions
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;
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
