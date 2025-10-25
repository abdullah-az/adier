import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_constants.dart';

class LocaleNotifier extends StateNotifier<Locale> {
  LocaleNotifier() : super(const Locale(AppConstants.englishCode));

  void setLocale(Locale locale) {
    state = locale;
  }

  void toggleLocale() {
    if (state.languageCode == AppConstants.englishCode) {
      state = const Locale(AppConstants.arabicCode);
    } else {
      state = const Locale(AppConstants.englishCode);
    }
  }
}

final localeProvider = StateNotifierProvider<LocaleNotifier, Locale>((ref) {
  return LocaleNotifier();
});
