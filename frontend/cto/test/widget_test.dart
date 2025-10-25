import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:cto/main.dart';

void main() {
  testWidgets('App smoke test - loads home page', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MyApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('CTO App'), findsWidgets);
    expect(find.text('Welcome'), findsOneWidget);
  });

  testWidgets('Theme toggle works', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MyApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.dark_mode), findsOneWidget);

    await tester.tap(find.byIcon(Icons.dark_mode));
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.light_mode), findsOneWidget);
  });

  testWidgets('Language toggle works', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MyApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Welcome'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.language).last);
    await tester.pumpAndSettle();

    expect(find.text('مرحبا'), findsOneWidget);
  });
}
