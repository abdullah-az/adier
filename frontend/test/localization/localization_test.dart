import 'package:ai_video_editor_frontend/src/app.dart';
import 'package:ai_video_editor_frontend/src/core/config/app_config.dart';
import 'package:ai_video_editor_frontend/src/core/di/providers.dart';
import 'package:ai_video_editor_frontend/src/core/di/service_registry.dart';
import 'package:ai_video_editor_frontend/src/core/localization/locale_preferences_stub.dart';
import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('AppLocalizations', () {
    test('provides English translations', () async {
      final localizations = await AppLocalizations.delegate.load(const Locale('en'));

      expect(localizations.appTitle, 'AI Video Editor');
      expect(localizations.navDashboard, 'Dashboard');
      expect(localizations.languageArabic, 'Arabic');
    });

    test('provides Arabic translations', () async {
      final localizations = await AppLocalizations.delegate.load(const Locale('ar'));

      expect(localizations.appTitle, 'محرر الفيديو بالذكاء الاصطناعي');
      expect(localizations.navDashboard, 'لوحة التحكم');
      expect(localizations.languageArabic, 'العربية');
    });
  });

  testWidgets('switching locale updates strings and directionality', (tester) async {
    final config = AppConfig.fromFlavor(AppFlavor.development);
    final localePreferences = _TestLocalePreferences();
    final registry = ServiceRegistry()
      ..registerSingleton<AppConfig>(config, overrideExisting: true)
      ..registerSingleton<LocalePreferences>(localePreferences, overrideExisting: true);

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

    final materialAppFinder = find.byType(MaterialApp);
    expect(materialAppFinder, findsOneWidget);
    expect(Directionality.of(tester.element(materialAppFinder)), TextDirection.ltr);

    await tester.tap(find.byIcon(Icons.settings_outlined));
    await tester.pumpAndSettle();

    expect(find.text('Settings'), findsWidgets);

    await tester.tap(find.text('Arabic'));
    await tester.pumpAndSettle();

    expect(find.text('الإعدادات'), findsWidgets);
    expect(Directionality.of(tester.element(materialAppFinder)), TextDirection.rtl);
    expect(localePreferences.stored?.languageCode, 'ar');
  });
}

class _TestLocalePreferences implements LocalePreferences {
  Locale? stored;

  @override
  Future<void> clearLocale() async {
    stored = null;
  }

  @override
  Future<Locale?> loadLocale() async => stored;

  @override
  Future<void> saveLocale(Locale locale) async {
    stored = locale;
  }
}
