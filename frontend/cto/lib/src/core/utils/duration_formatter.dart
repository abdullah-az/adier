class DurationFormatter {
  const DurationFormatter._();

  static String format(Duration duration) {
    final isNegative = duration.isNegative;
    final absDuration = duration.abs();
    final hours = absDuration.inHours;
    final minutes = absDuration.inMinutes % 60;
    final seconds = absDuration.inSeconds % 60;
    final buffer = StringBuffer();
    if (isNegative) {
      buffer.write('-');
    }
    if (hours > 0) {
      buffer
        ..write(hours)
        ..write(':')
        ..write(minutes.toString().padLeft(2, '0'))
        ..write(':')
        ..write(seconds.toString().padLeft(2, '0'));
      return buffer.toString();
    }
    buffer
      ..write(minutes.toString().padLeft(2, '0'))
      ..write(':')
      ..write(seconds.toString().padLeft(2, '0'));
    return buffer.toString();
  }

  static String formatRange(Duration start, Duration end) {
    return '${format(start)} - ${format(end)}';
  }

  static String formatCompact(Duration duration) {
    final totalSeconds = duration.inSeconds;
    if (totalSeconds >= 3600) {
      final hours = totalSeconds ~/ 3600;
      final minutes = (totalSeconds % 3600) ~/ 60;
      return '${hours}h ${minutes}m';
    }
    final minutes = totalSeconds ~/ 60;
    final seconds = totalSeconds % 60;
    if (minutes == 0) {
      return '${seconds}s';
    }
    return '${minutes}m ${seconds}s';
  }
}
