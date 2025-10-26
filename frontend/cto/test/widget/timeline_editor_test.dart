import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/features/timeline/timeline_controller.dart';
import 'package:cto/src/features/timeline/timeline_editor_page.dart';
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

  testWidgets('Timeline editor supports reordering and export', (tester) async {
    await tester.pumpWidget(_buildApp(const TimelineEditorPage()));
    await tester.pumpAndSettle();

    // Initial order.
    var tiles = tester.widgetList<ListTile>(find.byType(ListTile)).toList();
    expect(tiles.first.title, isA<Text>());
    expect((tiles.first.title! as Text).data, 'Intro');

    final dragTarget = find.text('Main Content');
    final gesture = await tester.startGesture(tester.getCenter(dragTarget));
    await tester.pump(const Duration(milliseconds: 300));
    await gesture.moveBy(const Offset(0, -220));
    await tester.pump(const Duration(milliseconds: 300));
    await gesture.up();
    await tester.pumpAndSettle();

    tiles = tester.widgetList<ListTile>(find.byType(ListTile)).toList();
    expect((tiles.first.title! as Text).data, 'Main Content');

    await tester.tap(find.byKey(const Key('timeline_add_segment')));
    await tester.pumpAndSettle();
    expect(find.byType(ListTile), findsNWidgets(4));

    await tester.tap(find.byKey(const Key('timeline_export_button')));
    await tester.pump();
    expect(find.byKey(const Key('export_dialog')), findsOneWidget);

    await tester.tap(find.byKey(const Key('export_confirm_button')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Export queued successfully'), findsOneWidget);
  });

  testWidgets('Timeline editor golden layout', (tester) async {
    await tester.pumpWidget(_buildApp(const TimelineEditorPage()));
    await tester.pumpAndSettle();

    await expectLater(
      find.byType(TimelineEditorPage),
      matchesGoldenFile('goldens/timeline_editor.png'),
    );
  });
}
