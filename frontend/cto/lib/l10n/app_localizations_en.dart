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
  String get timelineEditorTitle => 'Timeline Editor';

  @override
  String get timelineRefresh => 'Refresh';

  @override
  String get timelineErrorMaxDuration =>
      'Adding this clip would exceed the allowed project duration.';

  @override
  String get timelineErrorOverlap =>
      'This clip overlaps with another clip from the same source.';

  @override
  String get timelineErrorClipTooShort =>
      'Clip duration is too short. Increase the length before saving.';

  @override
  String get timelineErrorMergeNotAllowed => 'These clips cannot be merged.';

  @override
  String get timelineErrorSplitInvalid =>
      'Select a valid point within the clip to split.';

  @override
  String get timelineErrorSaveFailed =>
      "Couldn't save the timeline. Please retry.";

  @override
  String get timelineErrorLoadFailed =>
      'Unable to load the timeline. Please refresh.';

  @override
  String get timelineErrorTranscriptSearch =>
      'Transcript search failed. Try again.';

  @override
  String get timelineSuggestionsTitle => 'Scenes & Segments';

  @override
  String get timelineSegmentSourceAi => 'AI Suggestions';

  @override
  String get timelineSegmentSourceTranscript => 'Transcript Search';

  @override
  String get timelineNoSuggestions => 'No suggestions available yet.';

  @override
  String get timelineAiSuggestionAdd => 'Add to timeline';

  @override
  String get timelineAiSuggestionRemove => 'Remove';

  @override
  String get timelineQualityLabel => 'Quality';

  @override
  String get timelineConfidenceLabel => 'Confidence';

  @override
  String timelineDurationLabel(String duration) {
    return 'Duration: $duration';
  }

  @override
  String timelineTrimLabel(String start, String end) {
    return 'Trim range: $start → $end';
  }

  @override
  String get timelineTrimUnavailable => 'Trimming unavailable for this clip.';

  @override
  String get timelineSplitClip => 'Split clip';

  @override
  String timelineSplitInstruction(String start, String end) {
    return 'Select a split point between $start and $end.';
  }

  @override
  String timelineSplitSelected(String position) {
    return 'Split at $position';
  }

  @override
  String get timelineSplitCancel => 'Cancel';

  @override
  String get timelineSplitConfirm => 'Split';

  @override
  String get timelineMergeClip => 'Merge with next clip';

  @override
  String get timelineRemoveClip => 'Remove clip';

  @override
  String get timelineSaving => 'Saving…';

  @override
  String get timelineSourceAi => 'AI';

  @override
  String get timelineSourceTranscript => 'Transcript';

  @override
  String get timelineSourceManual => 'Manual';

  @override
  String get timelineBuilderTitle => 'Timeline builder';

  @override
  String get timelineDropHere => 'Drop to add to timeline';

  @override
  String get timelineEmptyState =>
      'Drag AI suggestions or search results here to start building your story.';

  @override
  String get timelineReorderTooltip => 'Reorder clip';

  @override
  String get timelineMetadataTitle => 'Project overview';

  @override
  String timelineMetadataProgress(String current, String max) {
    return 'Using $current of $max';
  }

  @override
  String get timelineMetadataProjectId => 'Project ID';

  @override
  String get timelineMetadataClips => 'Clips';

  @override
  String get timelineMetadataTotalDuration => 'Total duration';

  @override
  String get timelineMetadataMaxDuration => 'Max duration';

  @override
  String get timelineMetadataRemaining => 'Remaining';

  @override
  String get timelineMetadataSaving => 'Saving timeline…';

  @override
  String get timelineMetadataUnsavedChanges => 'Unsaved changes';

  @override
  String get timelineMetadataSynced => 'Synced';

  @override
  String timelineMetadataLastSaved(String time) {
    return 'Last saved $time';
  }

  @override
  String get timelineTranscriptSearchPlaceholder => 'Search transcript';

  @override
  String get timelineTranscriptSearchButton => 'Search';

  @override
  String get timelineTranscriptSearchEmpty =>
      'Use the transcript search to find specific segments.';

  @override
  String timelineTranscriptNoResults(String query) {
    return 'No transcript results for "$query".';
  }

  @override
  String get timelineTranscriptAdd => 'Add segment';
}
