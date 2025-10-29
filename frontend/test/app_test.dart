import 'package:ai_video_editor_frontend/src/app.dart';
import 'package:ai_video_editor_frontend/src/core/config/app_config.dart';
import 'package:ai_video_editor_frontend/src/core/di/providers.dart';
import 'package:ai_video_editor_frontend/src/core/di/service_registry.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets('renders navigation shell with initial destination', (tester) async {
    final config = AppConfig.fromFlavor(AppFlavor.development);
    final registry = ServiceRegistry()
      ..registerSingleton<AppConfig>(config, overrideExisting: true);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appConfigProvider.overrideWithValue(config),
          serviceRegistryProvider.overrideWithValue(registry),
        ],
        child: const App(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.textContaining('AI Video Editor'), findsWidgets);
    expect(find.text('Dashboard'), findsWidgets);
  });
}
