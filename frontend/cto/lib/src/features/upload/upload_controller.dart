import 'package:flutter_riverpod/flutter_riverpod.dart';

class UploadItem {
  const UploadItem({
    required this.id,
    required this.name,
    required this.progress,
    required this.duration,
    this.completed = false,
  });

  final String id;
  final String name;
  final double progress;
  final Duration duration;
  final bool completed;

  UploadItem copyWith({
    String? id,
    String? name,
    double? progress,
    Duration? duration,
    bool? completed,
  }) {
    return UploadItem(
      id: id ?? this.id,
      name: name ?? this.name,
      progress: progress ?? this.progress,
      duration: duration ?? this.duration,
      completed: completed ?? this.completed,
    );
  }
}

final uploadControllerProvider =
    StateNotifierProvider<UploadController, List<UploadItem>>(
  (ref) => UploadController(),
);

class UploadController extends StateNotifier<List<UploadItem>> {
  UploadController({List<UploadItem>? initialUploads})
      : _counter = initialUploads?.length ?? 0,
        super(initialUploads ?? const []);

  int _counter;

  void addMockUpload() {
    _counter += 1;
    final newItem = UploadItem(
      id: 'upload-$_counter',
      name: 'Recording $_counter',
      progress: 0,
      duration: Duration(seconds: 5 + _counter * 2),
    );
    state = [
      ...state,
      newItem,
    ];
  }

  void incrementProgress(String id, [double delta = 0.25]) {
    state = [
      for (final item in state)
        if (item.id == id)
          item.copyWith(
            progress: (item.progress + delta).clamp(0.0, 1.0),
            completed: (item.progress + delta) >= 1.0,
          )
        else
          item,
    ];
  }

  void removeUpload(String id) {
    state = [
      for (final item in state)
        if (item.id != id) item,
    ];
  }

  void clear() {
    state = const [];
  }
}
