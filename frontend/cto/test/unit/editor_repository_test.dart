import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/src/data/models/subtitle_cue.dart';
import 'package:cto/src/data/models/timeline_segment.dart';
import 'package:cto/src/data/repositories/editor_repository.dart';

class _MockDio extends Mock implements Dio {}

void main() {
  setUpAll(() {
    registerFallbackValue(<String, dynamic>{});
  });

  late Dio dio;
  late EditorRepository repository;

  setUp(() {
    dio = _MockDio();
    repository = EditorRepository(dio: dio);
  });

  test('uploadMedia returns upload id', () async {
    when(
      () => dio.post<Map<String, dynamic>>(
        '/uploads',
        data: any(named: 'data'),
      ),
    ).thenAnswer(
      (_) async => Response<Map<String, dynamic>>(
        data: {'uploadId': 'upload_1'},
        requestOptions: RequestOptions(path: '/uploads'),
      ),
    );

    final uploadId = await repository.uploadMedia('path.mp4');

    expect(uploadId, 'upload_1');
  });

  test('fetchTimeline maps timeline segments', () async {
    when(() => dio.get<List<dynamic>>('/uploads/upload_1/timeline')).thenAnswer(
      (_) async => Response<List<dynamic>>(
        data: [
          {'id': 'seg_1', 'label': 'Intro', 'startMs': 0, 'endMs': 1000},
        ],
        requestOptions: RequestOptions(path: '/uploads/upload_1/timeline'),
      ),
    );

    final segments = await repository.fetchTimeline('upload_1');

    expect(segments, hasLength(1));
    expect(segments.first, isA<TimelineSegment>());
    expect(segments.first.label, 'Intro');
  });

  test('fetchSubtitles maps subtitle cues', () async {
    when(() => dio.get<List<dynamic>>('/uploads/upload_1/subtitles')).thenAnswer(
      (_) async => Response<List<dynamic>>(
        data: [
          {'id': 'cue_1', 'text': 'Hello', 'startMs': 0, 'endMs': 1000},
        ],
        requestOptions: RequestOptions(path: '/uploads/upload_1/subtitles'),
      ),
    );

    final cues = await repository.fetchSubtitles('upload_1');

    expect(cues, hasLength(1));
    expect(cues.first, isA<SubtitleCue>());
    expect(cues.first.text, 'Hello');
  });

  test('exportProject returns export id', () async {
    when(
      () => dio.post<Map<String, dynamic>>(
        '/uploads/upload_1/export',
        data: any(named: 'data'),
      ),
    ).thenAnswer(
      (_) async => Response<Map<String, dynamic>>(
        data: {'exportId': 'export_1'},
        requestOptions: RequestOptions(path: '/uploads/upload_1/export'),
      ),
    );

    final exportId = await repository.exportProject('upload_1');

    expect(exportId, 'export_1');
  });

  test('throws exception when upload response missing uploadId', () async {
    when(
      () => dio.post<Map<String, dynamic>>(
        '/uploads',
        data: any(named: 'data'),
      ),
    ).thenAnswer(
      (_) async => Response<Map<String, dynamic>>(
        data: {},
        requestOptions: RequestOptions(path: '/uploads'),
      ),
    );

    expect(
      () => repository.uploadMedia('path.mp4'),
      throwsA(isA<Exception>()),
    );
  });
}
