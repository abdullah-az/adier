import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../l10n/app_localizations.dart';

String formatProjectDateTime(DateTime dateTime, Locale locale) {
  final localizedDate = dateTime.toLocal();
  final localeName = locale.toLanguageTag();
  final dateFormatter = DateFormat.yMMMd(localeName).add_jm();
  return dateFormatter.format(localizedDate);
}

({String value, String unit}) fileSizeParts(
  num bytes,
  AppLocalizations l10n, {
  int precision = 1,
}) {
  final size = bytes.toDouble().abs();
  const base = 1024;
  final localeName = l10n.localeName;

  final units = <({int power, String Function(AppLocalizations) label})>[
    (power: 3, label: (l10n) => l10n.fileSizeUnitGb),
    (power: 2, label: (l10n) => l10n.fileSizeUnitMb),
    (power: 1, label: (l10n) => l10n.fileSizeUnitKb),
    (power: 0, label: (l10n) => l10n.fileSizeUnitB),
  ];

  for (final unit in units) {
    final divisor = math.pow(base, unit.power).toDouble();
    final normalized = size / divisor;
    final isLastUnit = unit.power == 0;
    if (normalized >= 1 || isLastUnit) {
      final decimals = normalized >= 100 || isLastUnit ? 0 : precision;
      final formatter = NumberFormat.decimalPatternDigits(
        locale: localeName,
        decimalDigits: decimals,
      );
      return (value: formatter.format(normalized), unit: unit.label(l10n));
    }
  }

  final formatter = NumberFormat.decimalPatternDigits(
    locale: localeName,
    decimalDigits: precision,
  );
  return (value: formatter.format(size), unit: l10n.fileSizeUnitB);
}

String formatBytes(num? bytes, AppLocalizations l10n, {int precision = 1}) {
  if (bytes == null || bytes <= 0) {
    return '0 ${l10n.fileSizeUnitB}';
  }
  final parts = fileSizeParts(bytes, l10n, precision: precision);
  return '${parts.value} ${parts.unit}';
}

String formatSpeed(double speedBytesPerSecond, AppLocalizations l10n) {
  if (speedBytesPerSecond <= 0) {
    return l10n.uploadSpeedUnknown;
  }
  final parts = fileSizeParts(speedBytesPerSecond, l10n, precision: 1);
  return l10n.uploadSpeedLabel(parts.value, parts.unit);
}

String formatPercentage(double? value, {int fractionDigits = 0}) {
  if (value == null || value.isNaN) {
    return '0%';
  }
  final percent = (value * 100).clamp(0, 100);
  return '${percent.toStringAsFixed(fractionDigits)}%';
}

String formatDurationFromSeconds(int? seconds) {
  if (seconds == null || seconds <= 0) {
    return '--';
  }

  final duration = Duration(seconds: seconds);
  final hours = duration.inHours;
  final minutes = duration.inMinutes.remainder(60);
  final secs = duration.inSeconds.remainder(60);

  final buffer = StringBuffer();
  if (hours > 0) {
    buffer
      ..write(hours.toString().padLeft(2, '0'))
      ..write(':')
      ..write(minutes.toString().padLeft(2, '0'))
      ..write(':')
      ..write(secs.toString().padLeft(2, '0'));
  } else {
    buffer
      ..write(minutes.toString().padLeft(2, '0'))
      ..write(':')
      ..write(secs.toString().padLeft(2, '0'));
  }
  return buffer.toString();
}
