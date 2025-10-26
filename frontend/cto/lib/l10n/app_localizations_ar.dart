// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appTitle => 'تطبيق CTO';

  @override
  String get welcome => 'مرحبا';

  @override
  String get home => 'الرئيسية';

  @override
  String get profile => 'الملف الشخصي';

  @override
  String get settings => 'الإعدادات';

  @override
  String get auth => 'المصادقة';

  @override
  String get language => 'اللغة';

  @override
  String get darkMode => 'الوضع الداكن';

  @override
  String get lightMode => 'الوضع الفاتح';

  @override
  String get english => 'الإنجليزية';

  @override
  String get arabic => 'العربية';

  @override
  String get authPlaceholder => 'سيتم إضافة تسجيل الدخول وإنشاء الحساب هنا.';

  @override
  String get profilePlaceholder => 'سيتم عرض معلومات الملف الشخصي هنا.';

  @override
  String hello(String name) {
    return 'مرحبا، $name!';
  }
}
