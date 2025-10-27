import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/repositories/editor_repository.dart';
import 'package:cto/src/features/editor/upload/upload_controller.dart';

class _MockEditorRepository extends Mock implements EditorRepository {}

class _MockTimelineProfiler extends Mock implements TimelineProfiler {}

void main() {
  late EditorRepository repository;
  late TimelineProfiler profiler;
  late UploadController controller;

  setUp(() {
    repository = _MockEditorRepository();
    profiler = _MockTimelineProfiler();
    controller = UploadController(repository: repository, profiler: profiler);
  });

  test('uploadMedia success updates state', () async {
    when(() => repository.uploadMedia(any())).thenAnswer((_) async => 'upload_1');

    await controller.uploadMedia('demo.mp4');

    expect(controller.state.isComplete, isTrue);
    expect(controller.state.uploadId, 'upload_1');
    verify(() => profiler.record(any(), any())).called(1);
  });

  test('uploadMedia failure sets error state', () async {
    when(() => repository.uploadMedia(any())).thenThrow(Exception('error'));

    await controller.uploadMedia('demo.mp4');

    expect(controller.state.hasError, isTrue);
    expect(controller.state.isUploading, isFalse);
  });
}
