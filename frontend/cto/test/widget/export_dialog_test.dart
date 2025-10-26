import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/features/export/export_dialog.dart';
import 'package:cto/src/features/export/export_page.dart';
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

  testWidgets('Export page opens dialog and confirms export', (tester) async {
    await tester.pumpWidget(_buildApp(const ExportPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('export_page_open_dialog')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('export_dialog')), findsOneWidget);

    await tester.tap(find.byKey(const Key('export_resolution_dropdown')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('4K').last);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('export_subtitles_switch')));
    await tester.pump();

    await tester.tap(find.byKey(const Key('export_confirm_button')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Export queued successfully'), findsOneWidget);
  });

  testWidgets('Export dialog golden', (tester) async {
    await tester.pumpWidget(_buildApp(
      Scaffold(
        body: Center(
          child: Builder(
            builder: (context) {
              return FilledButton(
                onPressed: () => showDialog<void>(
                  context: context,
                  builder: (_) => const ExportDialog(),
                ),
                child: const Text('Open'),
              );
            },
          ),
        ),
      ),
    ));

    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();

    await expectLater(
      find.byKey(const Key('export_dialog')),
      matchesGoldenFile('goldens/export_dialog.png'),
    );
  });
}
