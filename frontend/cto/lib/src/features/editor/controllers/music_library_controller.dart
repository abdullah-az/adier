import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';

import '../../../data/models/music_assignment.dart';
import '../../../data/models/music_track.dart';
import '../../../data/providers/music_provider.dart';
import '../../../data/repositories/music_repository.dart';

const Object _musicNoChange = Object();

class MusicLibraryState {
  const MusicLibraryState({
    required this.isLoading,
    required this.isSaving,
    required this.tracks,
    required this.selectedTrackId,
    required this.previewingTrackId,
    required this.volume,
    required this.fadeIn,
    required this.fadeOut,
    required this.applyToFullTimeline,
    required this.clipStart,
    required this.clipEnd,
    required this.timelineDuration,
    required this.initialAssignment,
    this.errorMessage,
  });

  factory MusicLibraryState.initial() {
    return const MusicLibraryState(
      isLoading: true,
      isSaving: false,
      tracks: <MusicTrack>[],
      selectedTrackId: null,
      previewingTrackId: null,
      volume: 0.7,
      fadeIn: Duration.zero,
      fadeOut: Duration.zero,
      applyToFullTimeline: true,
      clipStart: Duration.zero,
      clipEnd: Duration.zero,
      timelineDuration: Duration.zero,
      initialAssignment: null,
      errorMessage: null,
    );
  }

  final bool isLoading;
  final bool isSaving;
  final List<MusicTrack> tracks;
  final String? selectedTrackId;
  final String? previewingTrackId;
  final double volume;
  final Duration fadeIn;
  final Duration fadeOut;
  final bool applyToFullTimeline;
  final Duration clipStart;
  final Duration clipEnd;
  final Duration timelineDuration;
  final MusicAssignment? initialAssignment;
  final String? errorMessage;

  bool get hasChanges {
    final current = currentAssignment;
    if (initialAssignment == null && current == null) {
      return false;
    }
    return current != initialAssignment;
  }

  MusicAssignment? get currentAssignment {
    if (selectedTrackId == null) {
      return null;
    }
    final start = applyToFullTimeline ? Duration.zero : clipStart;
    final end = applyToFullTimeline
        ? (timelineDuration > Duration.zero ? timelineDuration : clipEnd)
        : clipEnd;
    return MusicAssignment(
      trackId: selectedTrackId!,
      volume: volume,
      fadeIn: fadeIn,
      fadeOut: fadeOut,
      applyToFullTimeline: applyToFullTimeline,
      start: start,
      end: end,
    );
  }

  MusicLibraryState copyWith({
    bool? isLoading,
    bool? isSaving,
    List<MusicTrack>? tracks,
    Object? selectedTrackId = _musicNoChange,
    Object? previewingTrackId = _musicNoChange,
    double? volume,
    Duration? fadeIn,
    Duration? fadeOut,
    bool? applyToFullTimeline,
    Duration? clipStart,
    Duration? clipEnd,
    Duration? timelineDuration,
    Object? initialAssignment = _musicNoChange,
    Object? errorMessage = _musicNoChange,
  }) {
    return MusicLibraryState(
      isLoading: isLoading ?? this.isLoading,
      isSaving: isSaving ?? this.isSaving,
      tracks: tracks ?? this.tracks,
      selectedTrackId: identical(selectedTrackId, _musicNoChange)
          ? this.selectedTrackId
          : selectedTrackId as String?,
      previewingTrackId: identical(previewingTrackId, _musicNoChange)
          ? this.previewingTrackId
          : previewingTrackId as String?,
      volume: volume ?? this.volume,
      fadeIn: fadeIn ?? this.fadeIn,
      fadeOut: fadeOut ?? this.fadeOut,
      applyToFullTimeline: applyToFullTimeline ?? this.applyToFullTimeline,
      clipStart: clipStart ?? this.clipStart,
      clipEnd: clipEnd ?? this.clipEnd,
      timelineDuration: timelineDuration ?? this.timelineDuration,
      initialAssignment: identical(initialAssignment, _musicNoChange)
          ? this.initialAssignment
          : initialAssignment as MusicAssignment?,
      errorMessage: identical(errorMessage, _musicNoChange)
          ? this.errorMessage
          : errorMessage as String?,
    );
  }
}

class MusicLibraryController extends StateNotifier<MusicLibraryState> {
  MusicLibraryController({
    required MusicRepository repository,
    required this.videoId,
  })  : _repository = repository,
        super(MusicLibraryState.initial()) {
    _player = AudioPlayer();
    _playerSubscription = _player.playerStateStream.listen((playerState) {
      final isFinished = playerState.processingState == ProcessingState.completed;
      final isIdle = playerState.processingState == ProcessingState.idle;
      if (isFinished || (isIdle && !playerState.playing)) {
        state = state.copyWith(previewingTrackId: null);
      }
    });
  }

  final MusicRepository _repository;
  final String videoId;
  late final AudioPlayer _player;
  StreamSubscription<PlayerState>? _playerSubscription;
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    await _loadLibrary();
  }

  Future<void> _loadLibrary() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final results = await Future.wait([
        _repository.fetchTracks(),
        _repository.fetchAssignment(videoId),
      ]);
      final tracks = results[0] as List<MusicTrack>;
      final assignment = results[1] as MusicAssignment?;

      String? selectedId = assignment?.trackId;
      double volume = assignment?.volume ?? state.volume;
      Duration fadeIn = assignment?.fadeIn ?? state.fadeIn;
      Duration fadeOut = assignment?.fadeOut ?? state.fadeOut;
      bool applyFull = assignment?.applyToFullTimeline ?? true;
      Duration clipStart = assignment?.start ?? Duration.zero;
      Duration clipEnd = assignment?.end ?? state.timelineDuration;

      if (selectedId == null && tracks.isNotEmpty) {
        selectedId = tracks.first.id;
      }

      state = state.copyWith(
        isLoading: false,
        tracks: List<MusicTrack>.unmodifiable(tracks),
        selectedTrackId: selectedId,
        volume: volume,
        fadeIn: fadeIn,
        fadeOut: fadeOut,
        applyToFullTimeline: applyFull,
        clipStart: clipStart,
        clipEnd: clipEnd,
        initialAssignment: assignment,
        errorMessage: null,
      );
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: error.toString(),
      );
    }
  }

  void updateTimelineDuration(Duration duration) {
    if (duration == state.timelineDuration) {
      return;
    }
    final clampedStart = state.applyToFullTimeline
        ? Duration.zero
        : _clampDurationDuration(state.clipStart, Duration.zero, duration);
    final newClipEnd = duration == Duration.zero
        ? Duration.zero
        : (state.applyToFullTimeline
            ? duration
            : _clampDurationDuration(state.clipEnd, clampedStart + const Duration(milliseconds: 200), duration));
    state = state.copyWith(
      timelineDuration: duration,
      clipStart: clampedStart,
      clipEnd: newClipEnd,
    );
  }

  void selectTrack(String trackId) {
    if (state.selectedTrackId == trackId) {
      return;
    }
    if (state.tracks.any((track) => track.id == trackId)) {
      state = state.copyWith(selectedTrackId: trackId);
    }
  }

  void setVolume(double volume) {
    state = state.copyWith(volume: volume.clamp(0.0, 1.0));
  }

  void setFadeIn(Duration duration) {
    if (duration.isNegative) return;
    state = state.copyWith(fadeIn: duration);
  }

  void setFadeOut(Duration duration) {
    if (duration.isNegative) return;
    state = state.copyWith(fadeOut: duration);
  }

  void setPlacement(bool applyToFullTimeline) {
    if (applyToFullTimeline == state.applyToFullTimeline) {
      return;
    }
    if (applyToFullTimeline) {
      state = state.copyWith(
        applyToFullTimeline: true,
        clipStart: Duration.zero,
        clipEnd: state.timelineDuration,
      );
    } else {
      final fallbackEnd = state.timelineDuration == Duration.zero
          ? const Duration(seconds: 5)
          : state.timelineDuration;
      final start = _clampDurationDuration(state.clipStart, Duration.zero, fallbackEnd);
      final end = _clampDurationDuration(
        state.clipEnd,
        start + const Duration(milliseconds: 200),
        fallbackEnd,
      );
      state = state.copyWith(
        applyToFullTimeline: false,
        clipStart: start,
        clipEnd: end,
      );
    }
  }

  void setClipRange(Duration start, Duration end) {
    if (end < start) {
      return;
    }
    final timelineEnd = state.timelineDuration == Duration.zero ? end : state.timelineDuration;
    final clampedStart = _clampDurationDuration(start, Duration.zero, timelineEnd);
    final clampedEnd = _clampDurationDuration(end, clampedStart + const Duration(milliseconds: 200), timelineEnd);
    state = state.copyWith(
      clipStart: clampedStart,
      clipEnd: clampedEnd,
    );
  }

  Future<void> togglePreview(String trackId) async {
    if (state.previewingTrackId == trackId) {
      await _player.stop();
      state = state.copyWith(previewingTrackId: null);
      return;
    }

    MusicTrack? track;
    for (final candidate in state.tracks) {
      if (candidate.id == trackId) {
        track = candidate;
        break;
      }
    }

    if (track == null) {
      state = state.copyWith(errorMessage: 'Track not found');
      return;
    }

    try {
      state = state.copyWith(previewingTrackId: trackId, errorMessage: null);
      await _player.stop();
      await _player.setUrl(track.previewUrl);
      await _player.setVolume(state.volume);
      await _player.play();
    } catch (error) {
      state = state.copyWith(
        previewingTrackId: null,
        errorMessage: error.toString(),
      );
    }
  }

  Future<bool> saveSelection() async {
    final assignment = state.currentAssignment;
    if (assignment == null) {
      return false;
    }
    state = state.copyWith(isSaving: true, errorMessage: null);
    try {
      await _repository.updateAssignment(videoId, assignment);
      state = state.copyWith(
        isSaving: false,
        initialAssignment: assignment,
        errorMessage: null,
      );
      return true;
    } catch (error) {
      state = state.copyWith(
        isSaving: false,
        errorMessage: error.toString(),
      );
      return false;
    }
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = state.copyWith(errorMessage: null);
    }
  }

  @override
  void dispose() {
    _playerSubscription?.cancel();
    _player.dispose();
    super.dispose();
  }
}

final musicLibraryProvider = StateNotifierProvider.autoDispose
    .family<MusicLibraryController, MusicLibraryState, String>((ref, videoId) {
  final repository = ref.read(musicRepositoryProvider);
  final controller = MusicLibraryController(
    repository: repository,
    videoId: videoId,
  );
  scheduleMicrotask(controller.init);
  return controller;
});

Duration _clampDurationDuration(Duration value, Duration min, Duration max) {
  if (max < min) {
    return min;
  }
  if (value < min) {
    return min;
  }
  if (value > max) {
    return max;
  }
  return value;
}
