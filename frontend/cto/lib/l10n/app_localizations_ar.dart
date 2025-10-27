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
  String get welcome => 'مرحبًا';

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
    return 'مرحبًا، $name!';
  }

  @override
  String get uploadCardTitle => 'تحميل فيديو';

  @override
  String get uploadCardSubtitle => 'اختر ملف فيديو لإنشاء مشروع جديد.';

  @override
  String get uploadButtonLabel => 'تحميل فيديو';

  @override
  String get uploadAnotherButtonLabel => 'تحميل ملف آخر';

  @override
  String get uploadCancel => 'إلغاء التحميل';

  @override
  String get uploadRetry => 'المحاولة مرة أخرى';

  @override
  String get uploadDoneDismiss => 'إغلاق';

  @override
  String uploadProgressLabel(String progress) {
    return 'جارٍ التحميل $progress';
  }

  @override
  String get uploadProgressFallbackName => 'فيديو بدون اسم';

  @override
  String uploadTransferredLabel(String sent, String total) {
    return 'تم نقل $sent من $total';
  }

  @override
  String uploadSpeedLabel(String value, String unit) {
    return 'السرعة: $value $unit/ث';
  }

  @override
  String get uploadSpeedUnknown => 'جاري حساب السرعة…';

  @override
  String get uploadInvalidFormat =>
      'صيغة الملف غير مدعومة. يرجى اختيار ملف فيديو (MP4 أو MOV أو MKV أو AVI أو WEBM).';

  @override
  String get uploadNetworkError =>
      'تعذر الاتصال بالخادم. تحقق من الاتصال وحاول مرة أخرى.';

  @override
  String get uploadGenericError =>
      'حدث خطأ أثناء التحميل. يرجى المحاولة من جديد.';

  @override
  String uploadSuccess(String projectName) {
    return 'تم اكتمال التحميل. بدأنا معالجة "$projectName".';
  }

  @override
  String get projectLibraryTitle => 'مكتبة المشاريع';

  @override
  String get projectLibrarySubtitle =>
      'تابع تقدّم التحميل وراجع مقاطع الفيديو المعالجة.';

  @override
  String get projectLibraryErrorTitle => 'تعذر تحميل المشاريع';

  @override
  String get projectLibraryErrorSubtitle =>
      'لم نتمكن من جلب أحدث المشاريع. اسحب للتحديث أو حاول مجددًا.';

  @override
  String get projectLibraryEmptyTitle => 'لا توجد مشاريع بعد';

  @override
  String get projectLibraryEmptySubtitle => 'حمّل أول فيديو لك لتراه هنا.';

  @override
  String get projectStatusUploading => 'جارٍ التحميل';

  @override
  String get projectStatusQueued => 'قيد الانتظار';

  @override
  String get projectStatusProcessing => 'جارٍ المعالجة';

  @override
  String get projectStatusCompleted => 'مكتمل';

  @override
  String get projectStatusFailed => 'فشل';

  @override
  String get projectStatusCancelled => 'أُلغي';

  @override
  String projectProcessingProgress(String progress) {
    return 'اكتمل $progress من المعالجة';
  }

  @override
  String get projectViewDetails => 'عرض التفاصيل';

  @override
  String projectLastUpdated(String timestamp) {
    return 'آخر تحديث $timestamp';
  }

  @override
  String get fileSizeUnitB => 'بايت';

  @override
  String get fileSizeUnitKb => 'ك.ب';

  @override
  String get fileSizeUnitMb => 'م.ب';

  @override
  String get fileSizeUnitGb => 'ج.ب';

  @override
  String get projectDetailTitle => 'تفاصيل المشروع';

  @override
  String projectDetailTitleWithName(String name) {
    return 'المشروع: $name';
  }

  @override
  String get projectDetailProcessingMessage =>
      'نقوم الآن بمعالجة الفيديو. سيتم تحديث هذه الصفحة تلقائيًا مع تقدم العمل.';

  @override
  String get projectDetailDescriptionPlaceholder =>
      'ستظهر تفاصيل المشروع هنا عند توفرها.';

  @override
  String get projectDetailInformationHeading => 'معلومات المشروع';

  @override
  String get projectDetailStatus => 'الحالة';

  @override
  String get projectDetailUpdated => 'آخر تحديث';

  @override
  String get projectDetailFileSize => 'حجم الملف';

  @override
  String get projectDetailDuration => 'المدة';

  @override
  String get projectDetailErrorTitle => 'تعذر تحميل هذا المشروع';

  @override
  String get projectDetailErrorSubtitle =>
      'تحقق من الاتصال أو حاول مرة أخرى بعد قليل.';

  @override
  String get projectDetailErrorInline =>
      'حدثت مشكلة أثناء تحديث المشروع. اضغط إعادة المحاولة للمحاولة مرة أخرى.';

  @override
  String get refresh => 'تحديث';

  @override
  String get retry => 'إعادة المحاولة';
}
