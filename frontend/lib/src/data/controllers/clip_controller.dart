import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/clip.dart';
import '../repositories/clip_repository.dart';

class ClipController extends StateNotifier<AsyncValue<List<Clip>>> {
  ClipController(this._repository, {required String projectId})
      : _projectId = projectId,
        super(AsyncValue<List<Clip>>.data(const <Clip>[]));

  final ClipRepository _repository;
  final String _projectId;

  Future<void> loadClips() async {
    state = const AsyncValue<List<Clip>>.loading();
    final value = await AsyncValue.guard(() async {
      final clips = await _repository.fetchClips(_projectId);
      return List<Clip>.unmodifiable(clips);
    });
    state = value;
  }
}
