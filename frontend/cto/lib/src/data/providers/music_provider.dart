import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/music_assignment.dart';
import '../models/music_track.dart';
import '../repositories/music_repository.dart';

final musicRepositoryProvider = Provider<MusicRepository>((ref) {
  return MusicRepository();
});

final musicTracksProvider = FutureProvider<List<MusicTrack>>((ref) async {
  final repository = ref.read(musicRepositoryProvider);
  return repository.fetchTracks();
});

final musicAssignmentProvider = FutureProvider.family<MusicAssignment?, String>((ref, videoId) async {
  final repository = ref.read(musicRepositoryProvider);
  return repository.fetchAssignment(videoId);
});
