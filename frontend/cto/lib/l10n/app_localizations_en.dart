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
  String get timeline => 'Timeline';

  @override
  String get timelineError => 'Unable to load timeline.';

  @override
  String get timelineEmpty => 'Add clips to build your story.';

  @override
  String timelineTotalDuration(String duration) {
    return 'Total duration: $duration';
  }

  @override
  String get subtitles => 'Subtitles';

  @override
  String get subtitleError => 'Unable to load subtitles.';

  @override
  String get subtitlesEmpty => 'Generate captions from the timeline.';

  @override
  String get upload => 'Upload';

  @override
  String get selectFile => 'Select sample file';

  @override
  String get uploadInProgress => 'Uploading…';

  @override
  String get uploadCompleted => 'Upload complete';

  @override
  String get uploadFailed => 'Upload failed';

  @override
  String get selectedFile => 'Selected file';

  @override
  String get editorTitle => 'Editor';

  @override
  String get export => 'Export';

  @override
  String get exportTitle => 'Export project';

  @override
  String get exportSubtitle =>
      'Generate a downloadable video for your project.';

  @override
  String get exportFormat => 'Format';

  @override
  String get exportInProgress => 'Preparing export…';

  @override
  String exportSuccess(String exportId) {
    return 'Export ready: $exportId';
  }

  @override
  String get exportError => 'Export failed';

  @override
  String get cancel => 'Cancel';
}
