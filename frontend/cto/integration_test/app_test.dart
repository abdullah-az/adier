import 'package:cto/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('upload to export end-to-end flow', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    await tester.pumpAndSettle();

    expect(find.text('Quick actions'), findsOneWidget);

    await tester.tap(find.text('Upload'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('upload_add_button')));
    await tester.pumpAndSettle();

    expect(find.byType(ListTile), findsWidgets);

    await tester.tap(find.byKey(const Key('upload_go_to_timeline')));
    await tester.pumpAndSettle();

    expect(find.textContaining('Timeline editor'), findsOneWidget);

    await tester.drag(find.text('Main Content'), const Offset(0, -200));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('open_subtitle_editor')));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('subtitle_start_field')), '0.0');
    await tester.enterText(find.byKey(const Key('subtitle_end_field')), '2.0');
    await tester.enterText(find.byKey(const Key('subtitle_text_field')), 'Integration subtitle');

    await tester.tap(find.byKey(const Key('subtitle_add_button')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Integration subtitle'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('timeline_export_button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('export_dialog')), findsOneWidget);

    await tester.tap(find.byKey(const Key('export_confirm_button')));
    await tester.pumpAndSettle();
    expect(find.text('Export queued successfully'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();

    expect(find.text('Quick actions'), findsOneWidget);

    await tester.tap(find.text('Export'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('export_page_open_dialog')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('export_cancel_button')));
    await tester.pumpAndSettle();

    await tester.pageBack();
    await tester.pumpAndSettle();

    expect(find.text('Quick actions'), findsOneWidget);
  });
}
