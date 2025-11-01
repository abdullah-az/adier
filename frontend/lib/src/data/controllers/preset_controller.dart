import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/preset.dart';
import '../repositories/preset_repository.dart';

class PresetController extends StateNotifier<AsyncValue<List<Preset>>> {
  PresetController(this._repository)
      : super(AsyncValue<List<Preset>>.data(const <Preset>[]));

  final PresetRepository _repository;

  Future<void> loadPresets() async {
    state = const AsyncValue<List<Preset>>.loading();
    final value = await AsyncValue.guard(() async {
      final presets = await _repository.fetchPresets();
      return List<Preset>.unmodifiable(presets);
    });
    state = value;
  }
}
