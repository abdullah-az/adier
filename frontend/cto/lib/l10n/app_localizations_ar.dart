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

  @override
  String get timeline => 'الخط الزمني';

  @override
  String get timelineError => 'تعذر تحميل الخط الزمني.';

  @override
  String get timelineEmpty => 'أضف المقاطع لبناء قصتك.';

  @override
  String timelineTotalDuration(String duration) {
    return 'المدة الإجمالية: $duration';
  }

  @override
  String get subtitles => 'الترجمة';

  @override
  String get subtitleError => 'تعذر تحميل الترجمات.';

  @override
  String get subtitlesEmpty => 'أنشئ تسميات توضيحية من الخط الزمني.';

  @override
  String get upload => 'رفع';

  @override
  String get selectFile => 'اختر ملفاً تجريبياً';

  @override
  String get uploadInProgress => 'جاري الرفع…';

  @override
  String get uploadCompleted => 'اكتمل الرفع';

  @override
  String get uploadFailed => 'فشل الرفع';

  @override
  String get selectedFile => 'الملف المحدد';

  @override
  String get editorTitle => 'المحرر';

  @override
  String get export => 'تصدير';

  @override
  String get exportTitle => 'تصدير المشروع';

  @override
  String get exportSubtitle => 'أنشئ فيديو قابلاً للتنزيل لمشروعك.';

  @override
  String get exportFormat => 'الصيغة';

  @override
  String get exportInProgress => 'جاري التحضير للتصدير…';

  @override
  String exportSuccess(String exportId) {
    return 'التصدير جاهز: $exportId';
  }

  @override
  String get exportError => 'فشل التصدير';

  @override
  String get cancel => 'إلغاء';
}
