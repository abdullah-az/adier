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
  String get timelineEditorTitle => 'محرر الخط الزمني';

  @override
  String get timelineRefresh => 'تحديث';

  @override
  String get timelineErrorMaxDuration =>
      'إضافة هذا المقطع ستتجاوز المدة المسموح بها للمشروع.';

  @override
  String get timelineErrorOverlap =>
      'هذا المقطع يتداخل مع مقطع آخر من المصدر نفسه.';

  @override
  String get timelineErrorClipTooShort =>
      'مدة المقطع قصيرة جداً. الرجاء زيادة الطول قبل الحفظ.';

  @override
  String get timelineErrorMergeNotAllowed => 'لا يمكن دمج هذين المقطعين.';

  @override
  String get timelineErrorSplitInvalid =>
      'يرجى اختيار نقطة صالحة داخل المقطع للتقسيم.';

  @override
  String get timelineErrorSaveFailed => 'تعذر حفظ الخط الزمني. حاول مجدداً.';

  @override
  String get timelineErrorLoadFailed => 'تعذر تحميل الخط الزمني. يرجى التحديث.';

  @override
  String get timelineErrorTranscriptSearch => 'فشل البحث في النص. حاول مرة أخرى.';

  @override
  String get timelineSuggestionsTitle => 'المشاهد والمقاطع';

  @override
  String get timelineSegmentSourceAi => 'اقتراحات الذكاء الاصطناعي';

  @override
  String get timelineSegmentSourceTranscript => 'بحث النص التفريغي';

  @override
  String get timelineNoSuggestions => 'لا توجد اقتراحات حالياً.';

  @override
  String get timelineAiSuggestionAdd => 'إضافة إلى الخط الزمني';

  @override
  String get timelineAiSuggestionRemove => 'إزالة';

  @override
  String get timelineQualityLabel => 'الجودة';

  @override
  String get timelineConfidenceLabel => 'الثقة';

  @override
  String timelineDurationLabel(String duration) {
    return 'المدة: $duration';
  }

  @override
  String timelineTrimLabel(String start, String end) {
    return 'نطاق القص: $start → $end';
  }

  @override
  String get timelineTrimUnavailable => 'لا يمكن قص هذا المقطع.';

  @override
  String get timelineSplitClip => 'تقسيم المقطع';

  @override
  String timelineSplitInstruction(String start, String end) {
    return 'اختر نقطة تقسيم بين $start و $end.';
  }

  @override
  String timelineSplitSelected(String position) {
    return 'تقسيم عند $position';
  }

  @override
  String get timelineSplitCancel => 'إلغاء';

  @override
  String get timelineSplitConfirm => 'تقسيم';

  @override
  String get timelineMergeClip => 'دمج مع المقطع التالي';

  @override
  String get timelineRemoveClip => 'إزالة المقطع';

  @override
  String get timelineSaving => 'جارٍ الحفظ…';

  @override
  String get timelineSourceAi => 'ذكاء اصطناعي';

  @override
  String get timelineSourceTranscript => 'النص التفريغي';

  @override
  String get timelineSourceManual => 'يدوي';

  @override
  String get timelineBuilderTitle => 'منشئ الخط الزمني';

  @override
  String get timelineDropHere => 'إفلت للإضافة إلى الخط الزمني';

  @override
  String get timelineEmptyState =>
      'اسحب اقتراحات الذكاء الاصطناعي أو نتائج البحث هنا لبدء بناء قصتك.';

  @override
  String get timelineReorderTooltip => 'إعادة ترتيب المقطع';

  @override
  String get timelineMetadataTitle => 'نظرة عامة على المشروع';

  @override
  String timelineMetadataProgress(String current, String max) {
    return 'استخدام $current من $max';
  }

  @override
  String get timelineMetadataProjectId => 'معرّف المشروع';

  @override
  String get timelineMetadataClips => 'عدد المقاطع';

  @override
  String get timelineMetadataTotalDuration => 'المدة الإجمالية';

  @override
  String get timelineMetadataMaxDuration => 'المدة القصوى';

  @override
  String get timelineMetadataRemaining => 'المتبقي';

  @override
  String get timelineMetadataSaving => 'جارٍ حفظ الخط الزمني…';

  @override
  String get timelineMetadataUnsavedChanges => 'تغييرات غير محفوظة';

  @override
  String get timelineMetadataSynced => 'متزامن';

  @override
  String timelineMetadataLastSaved(String time) {
    return 'آخر حفظ $time';
  }

  @override
  String get timelineTranscriptSearchPlaceholder => 'بحث في النص التفريغي';

  @override
  String get timelineTranscriptSearchButton => 'بحث';

  @override
  String get timelineTranscriptSearchEmpty =>
      'استخدم البحث في النص للعثور على مقاطع محددة.';

  @override
  String timelineTranscriptNoResults(String query) {
    return 'لا توجد نتائج للنص "$query".';
  }

  @override
  String get timelineTranscriptAdd => 'إضافة المقطع';
}
