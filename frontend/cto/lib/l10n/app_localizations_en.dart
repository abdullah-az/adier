// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'CTO App';

  @override
  String get welcome => 'Welcome';

  @override
  String get home => 'Home';

  @override
  String get profile => 'Profile';

  @override
  String get settings => 'Settings';

  @override
  String get auth => 'Authentication';

  @override
  String get language => 'Language';

  @override
  String get darkMode => 'Dark Mode';

  @override
  String get lightMode => 'Light Mode';

  @override
  String get english => 'English';

  @override
  String get arabic => 'Arabic';

  @override
  String get authPlaceholder =>
      'Sign-in and registration flows will live here.';

  @override
  String get profilePlaceholder =>
      'User profile information will be displayed here.';

  @override
  String hello(String name) {
    return 'Hello, $name!';
  }

  @override
  String get subtitleEditorTitle => 'Subtitle & Music Editor';

  @override
  String get subtitleSegments => 'Subtitle Segments';

  @override
  String get addSegment => 'Add Segment';

  @override
  String get saveChanges => 'Save Changes';

  @override
  String get saving => 'Saving...';

  @override
  String get noSegmentsPlaceholder =>
      'No subtitle segments yet. Add one to get started.';

  @override
  String get segmentText => 'Segment Text';

  @override
  String get startTime => 'Start Time';

  @override
  String get endTime => 'End Time';

  @override
  String get splitSegment => 'Split Segment';

  @override
  String get mergeWithNext => 'Merge with Next';

  @override
  String get subtitleUpdateSuccess => 'Subtitles updated successfully.';

  @override
  String get subtitleUpdateFailure =>
      'Failed to update subtitles. Please try again.';

  @override
  String get livePreview => 'Live Preview';

  @override
  String get previewEmptySubtitle => 'No subtitle at this position.';

  @override
  String get timelinePosition => 'Timeline Position';

  @override
  String get musicLibrary => 'Background Music';

  @override
  String get musicAssign => 'Assign Track';

  @override
  String get noMusicTracksPlaceholder =>
      'No tracks available at the moment.';

  @override
  String get musicPreview => 'Preview';

  @override
  String get durationLabel => 'Duration';

  @override
  String get volume => 'Volume';

  @override
  String get fadeIn => 'Fade In';

  @override
  String get fadeOut => 'Fade Out';

  @override
  String get placement => 'Placement';

  @override
  String get placementFullTimeline => 'Full Timeline';

  @override
  String get placementClip => 'Clip Specific';

  @override
  String get clipRange => 'Clip Range';

  @override
  String get musicUpdateSuccess => 'Music selection saved.';

  @override
  String get musicUpdateFailure =>
      'Failed to save music selection. Please try again.';

  @override
  String get retry => 'Retry';
}
