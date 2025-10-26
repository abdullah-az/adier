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
  String get language => 'اللغة';

  @override
  String get darkMode => 'الوضع الداكن';

  @override
  String get english => 'الإنجليزية';

  @override
  String get arabic => 'العربية';

  @override
  String hello(String name) {
    return 'مرحبا، $name!';
  }

  @override
  String get lightTheme => 'فاتح';

  @override
  String get darkTheme => 'داكن';

  @override
  String get quickActions => 'إجراءات سريعة';

  @override
  String get auth => 'تسجيل الدخول';

  @override
  String get upload => 'رفع';

  @override
  String get timeline => 'الخط الزمني';

  @override
  String get subtitles => 'الترجمة';

  @override
  String get export => 'تصدير';

  @override
  String get addMedia => 'إضافة وسائط';

  @override
  String get uploadDescription => 'اختر أو سجل ملفات الوسائط لبدء المعالجة.';

  @override
  String get uploadEmpty => 'لا توجد عمليات رفع بعد. أضف وسائط للبدء.';

  @override
  String uploadDuration(int seconds) {
    return 'المدة: $seconds ث';
  }

  @override
  String get advanceUpload => 'تقدم الرفع';

  @override
  String get goToTimeline => 'الانتقال إلى الخط الزمني';

  @override
  String get timelineEditor => 'محرر الخط الزمني';

  @override
  String get addSegment => 'إضافة مقطع';

  @override
  String timelineSummary(int count, String duration) {
    return '$count مقاطع · المدة الإجمالية $duration';
  }

  @override
  String get timelineHint => 'قم بالسحب والإفلات لإعادة ترتيب القصة.';

  @override
  String segmentDuration(String duration, String percent) {
    return 'المدة $duration (${percent}% من الإجمالي)';
  }

  @override
  String segmentStart(String start, String percent) {
    return 'يبدأ عند $start (${percent}% من الخط)';
  }

  @override
  String get openSubtitles => 'فتح محرر الترجمة';

  @override
  String get exportSuccess => 'تمت إضافة التصدير بنجاح';

  @override
  String get exportProjectTitle => 'تصدير المشروع';

  @override
  String get exportFormat => 'الصيغة';

  @override
  String get exportResolution => 'الدقة';

  @override
  String get exportIncludeSubtitles => 'تضمين الترجمة';

  @override
  String get cancel => 'إلغاء';

  @override
  String get exportProjectAction => 'بدء التصدير';

  @override
  String get exportStepReview => 'مراجعة ترتيب الخط الزمني';

  @override
  String get exportStepQuality => 'اختيار جودة التصدير';

  @override
  String get exportStepSubtitles => 'تأكيد مسار الترجمة';

  @override
  String exportSummary(int segmentCount, String duration) {
    return 'جاهز لتصدير $segmentCount مقاطع · $duration';
  }

  @override
  String get subtitleEditor => 'محرر الترجمة';

  @override
  String get subtitleEditorDescription => 'أدر توقيت النصوص ومحتواها.';

  @override
  String get subtitleStartLabel => 'البداية (ث)';

  @override
  String get subtitleEndLabel => 'النهاية (ث)';

  @override
  String get subtitleTimeHelper => 'الثواني مع الكسور مسموح بها';

  @override
  String get subtitleTextLabel => 'نص الترجمة';

  @override
  String get addSubtitle => 'إضافة ترجمة';

  @override
  String get subtitleValidationError => 'أدخل وقت بداية/نهاية صالحاً ونصاً.';

  @override
  String subtitleTimeRange(String start, String end) {
    return 'من $start إلى $end';
  }
}
