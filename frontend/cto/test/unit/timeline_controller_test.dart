import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/models/timeline_segment.dart';
import 'package:cto/src/data/repositories/editor_repository.dart';
import 'package:cto/src/features/editor/timeline/timeline_controller.dart';

class _MockEditorRepository extends Mock implements EditorRepository {}

class _MockTimelineProfiler extends Mock implements TimelineProfiler {}

void main() {
  late EditorRepository repository;
  late TimelineCache cache;
  late TimelineProfiler profiler;
  late TimelineController controller;

  setUp(() {
    repository = _MockEditorRepository();
    cache = TimelineCache();
    profiler = _MockTimelineProfiler();
    controller = TimelineController(
      repository: repository,
      cache: cache,
      profiler: profiler,
    );
  });

  test('loadTimeline fetches segments and caches summary', () async {
    when(() => repository.fetchTimeline('upload_1')).thenAnswer(
      (_) async => const [
        TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1000),
      ],
    );

    await controller.loadTimeline('upload_1');

    expect(controller.state.hasValue, isTrue);
    expect(controller.state.value?.segments, isNotEmpty);
    expect(cache.read('upload_1'), isNotNull);
    verify(() => profiler.record(any(), any())).called(1);
  });

  test('loadTimeline uses cache when available', () async {
    when(() => repository.fetchTimeline('upload_1')).thenAnswer(
      (_) async => const [
        TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1000),
      ],
    );

    await controller.loadTimeline('upload_1');
    clearInteractions(repository);

    await controller.loadTimeline('upload_1');

    verifyNever(() => repository.fetchTimeline(any()));
  });
}
