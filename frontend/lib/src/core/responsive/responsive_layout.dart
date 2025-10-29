import 'package:flutter/widgets.dart';

import 'breakpoints.dart';

typedef ResponsiveWidgetBuilder = Widget Function(BuildContext context);

class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.mobile,
    ResponsiveWidgetBuilder? tablet,
    ResponsiveWidgetBuilder? desktop,
  })  : tablet = tablet ?? mobile,
        desktop = desktop ?? tablet ?? mobile;

  final ResponsiveWidgetBuilder mobile;
  final ResponsiveWidgetBuilder tablet;
  final ResponsiveWidgetBuilder desktop;

  @override
  Widget build(BuildContext context) {
    if (AppBreakpoints.isExpanded(context)) {
      return desktop(context);
    }
    if (AppBreakpoints.isMedium(context)) {
      return tablet(context);
    }
    return mobile(context);
  }
}
