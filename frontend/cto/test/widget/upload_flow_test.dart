import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/repositories/editor_repository.dart';
import 'package:cto/src/features/editor/upload/upload_controller.dart';
import 'package:cto/src/features/editor/upload/upload_flow.dart';

class _MockEditorRepository extends Mock implements EditorRepository {}

class _FakeProfiler extends TimelineProfiler {
  @override
  void record(String label, Duration duration) {}
}

void main() {
  late EditorRepository repository;

  setUp(() {
    repository = _MockEditorRepository();
  });

  Widget _buildWidget(Widget child, {UploadController? controller}) {
    return ProviderScope(
      overrides: [
        uploadControllerProvider.overrideWith((ref) {
          return controller ?? UploadController(repository: repository, profiler: _FakeProfiler());
        }),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: Center(child: child)),
      ),
    );
  }

  testWidgets('UploadFlow progresses from upload to completion', (tester) async {
    when(() => repository.uploadMedia(any())).thenAnswer((_) async {
      await Future<void>.delayed(const Duration(milliseconds: 10));
      return 'upload_1';
    });

    await tester.pumpWidget(_buildWidget(const UploadFlow()));

    expect(find.text('Upload'), findsOneWidget);

    await tester.tap(find.byKey(const Key('upload_button')));
    await tester.pump();

    expect(find.byKey(const Key('upload_progress')), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 50));
    await tester.pump();

    expect(find.byKey(const Key('upload_complete')), findsOneWidget);
  });
}
