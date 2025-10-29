import 'package:flutter/widgets.dart';

class AppBreakpoints {
  const AppBreakpoints._();

  static const double compact = 600;
  static const double medium = 1024;
  static const double expanded = 1440;

  static bool isCompact(BuildContext context) {
    return MediaQuery.sizeOf(context).width < medium;
  }

  static bool isMedium(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    return width >= medium && width < expanded;
  }

  static bool isExpanded(BuildContext context) {
    return MediaQuery.sizeOf(context).width >= expanded;
  }
}
