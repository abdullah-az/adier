import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/features/upload/upload_controller.dart';
import 'package:cto/src/features/upload/upload_page.dart';
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

  testWidgets('Upload flow adds and advances uploads', (tester) async {
    await tester.pumpWidget(_buildApp(const UploadPage()));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('upload_empty_state')), findsOneWidget);

    await tester.tap(find.byKey(const Key('upload_add_button')));
    await tester.pumpAndSettle();

    expect(find.byType(ListTile), findsOneWidget);

    await tester.tap(find.byKey(const Key('upload_progress_upload-1')));
    await tester.pump();

    final progressIndicator = tester.widget<LinearProgressIndicator>(
      find.byType(LinearProgressIndicator),
    );
    expect(progressIndicator.value, 0.25);
  });

  testWidgets('Upload page layout matches golden', (tester) async {
    final overrides = [
      uploadControllerProvider.overrideWith((ref) {
        return UploadController(initialUploads: const [
          UploadItem(
            id: 'upload-1',
            name: 'Camera Clip',
            progress: 0.6,
            duration: Duration(seconds: 12),
            completed: false,
          ),
          UploadItem(
            id: 'upload-2',
            name: 'Screen Recording',
            progress: 1.0,
            duration: Duration(seconds: 20),
            completed: true,
          ),
        ]);
      }),
    ];

    await tester.pumpWidget(_buildApp(const UploadPage(), overrides: overrides));
    await tester.pumpAndSettle();

    await expectLater(
      find.byType(UploadPage),
      matchesGoldenFile('goldens/upload_page.png'),
    );
  });
}
