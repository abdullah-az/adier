import 'dart:math';

import 'package:intl/intl.dart';

import '../../../l10n/app_localizations.dart';

String formatBytes(int bytes, {int decimals = 1}) {
  if (bytes <= 0) {
    return '0 B';
  }
  const suffixes = ['B', 'KB', 'MB', 'GB', 'TB'];
  final i = (log(bytes) / log(1024)).floor().clamp(0, suffixes.length - 1);
  final size = bytes / pow(1024, i);
  final value = size.toStringAsFixed(i == 0 ? 0 : decimals);
  return '$value ${suffixes[i]}';
}

String formatSpeed(double? bytesPerSecond, AppLocalizations l10n) {
  if (bytesPerSecond == null || bytesPerSecond.isNaN || !bytesPerSecond.isFinite) {
    return l10n.uploadSpeed('--');
  }
  final humanReadable = formatBytes(bytesPerSecond.round());
  return l10n.uploadSpeed(humanReadable);
}

String formatDateTime(DateTime dateTime, AppLocalizations l10n) {
  final formatter = DateFormat.yMMMd(l10n.localeName).add_jm();
  return formatter.format(dateTime.toLocal());
}
