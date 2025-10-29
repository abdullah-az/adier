import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTypography {
  const AppTypography._();

  static TextTheme textTheme(Brightness brightness) {
    final base = brightness == Brightness.dark
        ? ThemeData.dark().textTheme
        : ThemeData.light().textTheme;

    final themed = GoogleFonts.interTextTheme(base);

    return themed.copyWith(
      displayLarge: themed.displayLarge?.copyWith(fontWeight: FontWeight.w600),
      displayMedium: themed.displayMedium?.copyWith(fontWeight: FontWeight.w600),
      displaySmall: themed.displaySmall?.copyWith(fontWeight: FontWeight.w600),
      headlineMedium: themed.headlineMedium?.copyWith(fontWeight: FontWeight.w600),
      headlineSmall: themed.headlineSmall?.copyWith(fontWeight: FontWeight.w600),
      titleLarge: themed.titleLarge?.copyWith(fontWeight: FontWeight.w600),
      bodyLarge: themed.bodyLarge?.copyWith(height: 1.4),
      bodyMedium: themed.bodyMedium?.copyWith(height: 1.4),
      bodySmall: themed.bodySmall?.copyWith(height: 1.4),
      labelLarge: themed.labelLarge?.copyWith(fontWeight: FontWeight.w600),
    );
  }
}
