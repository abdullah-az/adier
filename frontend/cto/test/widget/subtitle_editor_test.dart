import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/features/subtitles/subtitle_controller.dart';
import 'package:cto/src/features/subtitles/subtitle_editor_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _buildApp(Widget child, {List<Override> overrides = const []}) {
  return ProviderScope(
    overrides: overrides,
    child: MaterialApp(
      locale: const Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: child,
    ),
  );
}

void main() {
  setUp(() {
    final binding = TestWidgetsFlutterBinding.ensureInitialized()
        as TestWidgetsFlutterBinding;
    binding.window.devicePixelRatioTestValue = 1.0;
    binding.window.physicalSizeTestValue = const Size(1080, 1920);
  });

  tearDown(() {
    final binding = TestWidgetsFlutterBinding.ensureInitialized()
        as TestWidgetsFlutterBinding;
    binding.window.clearPhysicalSizeTestValue();
    binding.window.clearDevicePixelRatioTestValue();
  });

  testWidgets('Subtitle editor adds entries and validates input', (tester) async {
    await tester.pumpWidget(_buildApp(const SubtitleEditorPage()));
    await tester.pumpAndSettle();

    final initialCount = tester.widgetList<ListTile>(find.byType(ListTile)).length;

    await tester.enterText(find.byKey(const Key('subtitle_start_field')), '0.5');
    await tester.enterText(find.byKey(const Key('subtitle_end_field')), '2.5');
    await tester.enterText(find.byKey(const Key('subtitle_text_field')), 'New subtitle');

    await tester.tap(find.byKey(const Key('subtitle_add_button')));
    await tester.pumpAndSettle();

    final updatedCount = tester.widgetList<ListTile>(find.byType(ListTile)).length;
    expect(updatedCount, initialCount + 1);

    await tester.tap(find.byKey(const Key('subtitle_add_button')));
    await tester.pump();
    expect(find.text('Enter valid start/end times and text.'), findsOneWidget);
  });

  testWidgets('Subtitle editor matches golden', (tester) async {
    await tester.pumpWidget(_buildApp(const SubtitleEditorPage()));
    await tester.pumpAndSettle();

    await expectLater(
      find.byType(SubtitleEditorPage),
      matchesGoldenFile('goldens/subtitle_editor.png'),
    );
  });
}
