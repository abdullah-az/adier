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
  String get uploadCardTitle => 'Upload a video';

  @override
  String get uploadCardSubtitle =>
      'Select a video file to create a new project.';

  @override
  String get uploadButtonLabel => 'Upload video';

  @override
  String get uploadAnotherButtonLabel => 'Upload another';

  @override
  String get uploadCancel => 'Cancel upload';

  @override
  String get uploadRetry => 'Try again';

  @override
  String get uploadDoneDismiss => 'Dismiss';

  @override
  String uploadProgressLabel(String progress) {
    return 'Uploading $progress';
  }

  @override
  String get uploadProgressFallbackName => 'Unnamed video';

  @override
  String uploadTransferredLabel(String sent, String total) {
    return 'Transferred $sent of $total';
  }

  @override
  String uploadSpeedLabel(String value, String unit) {
    return 'Speed: $value $unit/s';
  }

  @override
  String get uploadSpeedUnknown => 'Calculating speed…';

  @override
  String get uploadInvalidFormat =>
      'Unsupported file format. Please choose a video file (MP4, MOV, MKV, AVI, or WEBM).';

  @override
  String get uploadNetworkError =>
      'We couldn’t reach the server. Check your connection and try again.';

  @override
  String get uploadGenericError =>
      'Something went wrong during the upload. Please try again.';

  @override
  String uploadSuccess(String projectName) {
    return 'Upload complete. We started processing "$projectName".';
  }

  @override
  String get projectLibraryTitle => 'Project library';

  @override
  String get projectLibrarySubtitle =>
      'Monitor upload progress and review your processed videos.';

  @override
  String get projectLibraryErrorTitle => 'Unable to load projects';

  @override
  String get projectLibraryErrorSubtitle =>
      'We couldn’t fetch the latest projects. Pull to refresh or try again.';

  @override
  String get projectLibraryEmptyTitle => 'No projects yet';

  @override
  String get projectLibraryEmptySubtitle =>
      'Upload your first video to see it appear here.';

  @override
  String get projectStatusUploading => 'Uploading';

  @override
  String get projectStatusQueued => 'Queued';

  @override
  String get projectStatusProcessing => 'Processing';

  @override
  String get projectStatusCompleted => 'Completed';

  @override
  String get projectStatusFailed => 'Failed';

  @override
  String get projectStatusCancelled => 'Cancelled';

  @override
  String projectProcessingProgress(String progress) {
    return 'Processing $progress complete';
  }

  @override
  String get projectViewDetails => 'View details';

  @override
  String projectLastUpdated(String timestamp) {
    return 'Last updated $timestamp';
  }

  @override
  String get fileSizeUnitB => 'B';

  @override
  String get fileSizeUnitKb => 'KB';

  @override
  String get fileSizeUnitMb => 'MB';

  @override
  String get fileSizeUnitGb => 'GB';

  @override
  String get projectDetailTitle => 'Project details';

  @override
  String projectDetailTitleWithName(String name) {
    return 'Project: $name';
  }

  @override
  String get projectDetailProcessingMessage =>
      'We’re processing your video. This page will update automatically as we make progress.';

  @override
  String get projectDetailDescriptionPlaceholder =>
      'Project description will appear here once it’s available.';

  @override
  String get projectDetailInformationHeading => 'Project information';

  @override
  String get projectDetailStatus => 'Status';

  @override
  String get projectDetailUpdated => 'Last updated';

  @override
  String get projectDetailFileSize => 'File size';

  @override
  String get projectDetailDuration => 'Duration';

  @override
  String get projectDetailErrorTitle =>
      'We couldn’t load this project';

  @override
  String get projectDetailErrorSubtitle =>
      'Check your connection or try again in a moment.';

  @override
  String get projectDetailErrorInline =>
      'We hit a snag updating the project. Tap retry to try again.';

  @override
  String get refresh => 'Refresh';

  @override
  String get retry => 'Retry';
}
