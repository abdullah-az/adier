import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/repositories/editor_repository.dart';
import 'package:cto/src/features/editor/export/export_controller.dart';
import 'package:cto/src/features/editor/export/export_dialog.dart';

class _MockEditorRepository extends Mock implements EditorRepository {}

class _FakeProfiler extends TimelineProfiler {
  @override
  void record(String label, Duration duration) {}
}

void main() {
  setUpAll(() {
    registerFallbackValue('mp4');
  });

  late EditorRepository repository;

  setUp(() {
    repository = _MockEditorRepository();
  });

  Widget _buildDialog() {
    return ProviderScope(
      overrides: [
        exportControllerProvider.overrideWith(
          (ref) => ExportController(repository: repository, profiler: _FakeProfiler()),
        ),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) => ExportDialog(uploadId: 'upload_1'),
        ),
      ),
    );
  }

  testWidgets('ExportDialog triggers export', (tester) async {
    when(() => repository.exportProject('upload_1', format: any(named: 'format')))
        .thenAnswer((_) async => 'export_1');

    await tester.pumpWidget(_buildDialog());

    await tester.tap(find.byKey(const Key('confirm_export_button')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.textContaining('export_1'), findsOneWidget);
    verify(() => repository.exportProject('upload_1', format: any(named: 'format'))).called(1);
  });
}
