import 'dart:convert';
import 'dart:io';

void main(List<String> arguments) {
  final l10nDir = Directory('lib/l10n');
  if (!l10nDir.existsSync()) {
    stderr.writeln('Localization directory lib/l10n not found.');
    exitCode = 1;
    return;
  }

  final arbFiles = l10nDir
      .listSync()
      .whereType<File>()
      .where((file) => file.path.endsWith('.arb'))
      .toList();

  final baseFile = arbFiles.firstWhere(
    (file) => file.path.endsWith('app_en.arb'),
    orElse: () => throw StateError('Base localization file app_en.arb not found.'),
  );

  final baseJson = jsonDecode(baseFile.readAsStringSync()) as Map<String, dynamic>;
  final baseKeys = baseJson.keys.where((key) => !key.startsWith('@')).toSet();

  var hasIssues = false;

  for (final file in arbFiles) {
    if (identical(file, baseFile)) {
      continue;
    }

    final data = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
    final keys = data.keys.where((key) => !key.startsWith('@')).toSet();

    final missing = baseKeys.difference(keys);
    final extras = keys.difference(baseKeys);

    if (missing.isNotEmpty || extras.isNotEmpty) {
      hasIssues = true;
      stderr.writeln('Localization mismatch in ${file.path}:');
      if (missing.isNotEmpty) {
        stderr.writeln('  Missing keys: ${missing.toList()..sort()}');
      }
      if (extras.isNotEmpty) {
        stderr.writeln('  Extra keys: ${extras.toList()..sort()}');
      }
    }
  }

  if (hasIssues) {
    stderr.writeln('Localization check failed. Update ARB files to match app_en.arb.');
    exitCode = 1;
  } else {
    stdout.writeln('All localization files contain matching keys.');
  }
}
