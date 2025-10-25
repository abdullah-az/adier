import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../repositories/timeline_repository.dart';

final timelineRepositoryProvider = Provider<TimelineRepository>((ref) {
  return TimelineRepository();
});
