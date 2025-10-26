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
  String get language => 'Language';

  @override
  String get darkMode => 'Dark Mode';

  @override
  String get english => 'English';

  @override
  String get arabic => 'Arabic';

  @override
  String hello(String name) {
    return 'Hello, $name!';
  }

  @override
  String get lightTheme => 'Light';

  @override
  String get darkTheme => 'Dark';

  @override
  String get quickActions => 'Quick actions';

  @override
  String get auth => 'Auth';

  @override
  String get upload => 'Upload';

  @override
  String get timeline => 'Timeline';

  @override
  String get subtitles => 'Subtitles';

  @override
  String get export => 'Export';

  @override
  String get addMedia => 'Add media';

  @override
  String get uploadDescription => 'Select or record media files to begin processing.';

  @override
  String get uploadEmpty => 'No uploads yet. Add media to begin.';

  @override
  String uploadDuration(int seconds) {
    return 'Duration: $seconds s';
  }

  @override
  String get advanceUpload => 'Advance upload';

  @override
  String get goToTimeline => 'Continue to timeline';

  @override
  String get timelineEditor => 'Timeline editor';

  @override
  String get addSegment => 'Add segment';

  @override
  String timelineSummary(int count, String duration) {
    return '$count segments · Total $duration';
  }

  @override
  String get timelineHint => 'Drag and drop segments to adjust the story.';

  @override
  String segmentDuration(String duration, String percent) {
    return 'Duration $duration ($percent% of total)';
  }

  @override
  String segmentStart(String start, String percent) {
    return 'Starts at $start ($percent% position)';
  }

  @override
  String get openSubtitles => 'Open subtitle editor';

  @override
  String get exportSuccess => 'Export queued successfully';

  @override
  String get exportProjectTitle => 'Export project';

  @override
  String get exportFormat => 'Format';

  @override
  String get exportResolution => 'Resolution';

  @override
  String get exportIncludeSubtitles => 'Include subtitles';

  @override
  String get cancel => 'Cancel';

  @override
  String get exportProjectAction => 'Start export';

  @override
  String get exportStepReview => 'Review timeline order';

  @override
  String get exportStepQuality => 'Choose export quality';

  @override
  String get exportStepSubtitles => 'Confirm subtitle track';

  @override
  String exportSummary(int segmentCount, String duration) {
    return 'Ready to export $segmentCount segments · $duration';
  }

  @override
  String get subtitleEditor => 'Subtitle editor';

  @override
  String get subtitleEditorDescription => 'Manage caption timings and text.';

  @override
  String get subtitleStartLabel => 'Start (s)';

  @override
  String get subtitleEndLabel => 'End (s)';

  @override
  String get subtitleTimeHelper => 'Seconds with decimals allowed';

  @override
  String get subtitleTextLabel => 'Subtitle text';

  @override
  String get addSubtitle => 'Add subtitle';

  @override
  String get subtitleValidationError => 'Enter valid start/end times and text.';

  @override
  String subtitleTimeRange(String start, String end) {
    return 'From $start to $end';
  }
}
