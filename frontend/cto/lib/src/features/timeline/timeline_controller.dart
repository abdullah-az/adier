import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models/timeline_segment.dart';

final timelineControllerProvider =
    StateNotifierProvider<TimelineController, List<TimelineSegment>>(
  (ref) => TimelineController(),
);

class TimelineController extends StateNotifier<List<TimelineSegment>> {
  TimelineController({List<TimelineSegment>? initialSegments})
      : _counter = initialSegments?.length ?? _defaultSegments.length,
        super(initialSegments ?? _defaultSegments);

  static final List<TimelineSegment> _defaultSegments = [
    const TimelineSegment(
      id: 'segment-1',
      label: 'Intro',
      duration: Duration(seconds: 4),
    ),
    const TimelineSegment(
      id: 'segment-2',
      label: 'Main Content',
      duration: Duration(seconds: 7),
    ),
    const TimelineSegment(
      id: 'segment-3',
      label: 'Call To Action',
      duration: Duration(seconds: 5),
    ),
  ];

  int _counter;

  void reorderSegments(int oldIndex, int newIndex) {
    final updated = List<TimelineSegment>.from(state);
    if (newIndex > oldIndex) {
      newIndex -= 1;
    }
    final item = updated.removeAt(oldIndex);
    updated.insert(newIndex, item);
    state = updated;
  }

  void updateSegment(
    String id, {
    String? label,
    Duration? duration,
  }) {
    state = [
      for (final segment in state)
        if (segment.id == id)
          segment.copyWith(
            label: label,
            duration: duration,
          )
        else
          segment,
    ];
  }

  void addSegment(Duration duration) {
    _counter += 1;
    final segment = TimelineSegment(
      id: 'segment-${_counter}',
      label: 'Segment ${_counter}',
      duration: duration,
    );
    state = [
      ...state,
      segment,
    ];
  }
}
