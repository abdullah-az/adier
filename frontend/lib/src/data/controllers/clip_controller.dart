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

  Future<void> updateClipTrim({
    required String clipId,
    required int inPointMs,
    required int outPointMs,
  }) async {
    final previous = state;
    try {
      final updated = await _repository.updateClipTrim(
        clipId: clipId,
        inPointMs: inPointMs,
        outPointMs: outPointMs,
      );
      final current = state.value ?? const <Clip>[];
      final next = current.map((c) => c.id == clipId ? updated : c).toList(growable: false);
      state = AsyncValue<List<Clip>>.data(next);
    } catch (e, st) {
      state = AsyncValue<List<Clip>>.error(e, st);
      state = previous; // revert to previous on error
      rethrow;
    }
  }

  Future<Clip> mergeClips({
    required List<String> clipIds,
    String? description,
  }) async {
    final merged = await _repository.mergeClips(
      projectId: _projectId,
      clipIds: clipIds,
      description: description,
    );
    final current = state.value ?? const <Clip>[];
    final next = <Clip>[...current, merged];
    state = AsyncValue<List<Clip>>.data(List<Clip>.unmodifiable(next));
    return merged;
  }
}
