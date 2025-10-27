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
  String get subtitleEditorTitle => 'محرر الترجمة والموسيقى';

  @override
  String get subtitleSegments => 'مقاطع الترجمة';

  @override
  String get addSegment => 'إضافة مقطع';

  @override
  String get saveChanges => 'حفظ التغييرات';

  @override
  String get saving => 'جار الحفظ...';

  @override
  String get noSegmentsPlaceholder =>
      'لا توجد مقاطع ترجمة بعد. أضف واحداً للبدء.';

  @override
  String get segmentText => 'نص المقطع';

  @override
  String get startTime => 'وقت البداية';

  @override
  String get endTime => 'وقت النهاية';

  @override
  String get splitSegment => 'تقسيم المقطع';

  @override
  String get mergeWithNext => 'دمج مع التالي';

  @override
  String get subtitleUpdateSuccess => 'تم تحديث الترجمة بنجاح.';

  @override
  String get subtitleUpdateFailure =>
      'فشل تحديث الترجمة. يرجى المحاولة مرة أخرى.';

  @override
  String get livePreview => 'معاينة مباشرة';

  @override
  String get previewEmptySubtitle => 'لا توجد ترجمة في هذا الموضع.';

  @override
  String get timelinePosition => 'موضع المخطط الزمني';

  @override
  String get musicLibrary => 'الموسيقى الخلفية';

  @override
  String get musicAssign => 'تعيين المقطع';

  @override
  String get noMusicTracksPlaceholder => 'لا توجد مقاطع متاحة حالياً.';

  @override
  String get musicPreview => 'معاينة';

  @override
  String get durationLabel => 'المدة';

  @override
  String get volume => 'مستوى الصوت';

  @override
  String get fadeIn => 'تلاشي الدخول';

  @override
  String get fadeOut => 'تلاشي الخروج';

  @override
  String get placement => 'نطاق التطبيق';

  @override
  String get placementFullTimeline => 'كامل المخطط الزمني';

  @override
  String get placementClip => 'مقطع محدد';

  @override
  String get clipRange => 'نطاق المقطع';

  @override
  String get musicUpdateSuccess => 'تم حفظ اختيار الموسيقى.';

  @override
  String get musicUpdateFailure =>
      'فشل حفظ اختيار الموسيقى. يرجى المحاولة مرة أخرى.';

  @override
  String get retry => 'إعادة المحاولة';
}
