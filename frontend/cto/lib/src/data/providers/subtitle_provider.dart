import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/subtitle_segment.dart';
import '../repositories/subtitle_repository.dart';

final subtitleRepositoryProvider = Provider<SubtitleRepository>((ref) {
  return SubtitleRepository();
});

final subtitleSegmentsProvider = FutureProvider.family<List<SubtitleSegment>, String>((ref, videoId) async {
  final repository = ref.read(subtitleRepositoryProvider);
  return repository.fetchSubtitles(videoId);
});
