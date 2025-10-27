import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/utils/timeline_utils.dart';
import '../repositories/editor_repository.dart';

final editorRepositoryProvider = Provider<EditorRepository>((ref) {
  return EditorRepository();
});

final timelineCacheProvider = Provider<TimelineCache>((ref) {
  final cache = TimelineCache();
  ref.onDispose(cache.clear);
  return cache;
});

final timelineProfilerProvider = Provider<TimelineProfiler>((ref) {
  return TimelineProfiler();
});
