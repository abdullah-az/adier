import 'package:flutter/material.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../data/models/project_model.dart';

String projectStatusLabel(ProjectStatus status, AppLocalizations l10n) {
  switch (status) {
    case ProjectStatus.uploading:
      return l10n.projectStatusUploading;
    case ProjectStatus.queued:
      return l10n.projectStatusQueued;
    case ProjectStatus.processing:
      return l10n.projectStatusProcessing;
    case ProjectStatus.completed:
      return l10n.projectStatusCompleted;
    case ProjectStatus.failed:
      return l10n.projectStatusFailed;
    case ProjectStatus.cancelled:
      return l10n.projectStatusCancelled;
  }
}

class ProjectStatusChip extends StatelessWidget {
  const ProjectStatusChip({
    required this.status,
    required this.l10n,
    super.key,
  });

  final ProjectStatus status;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final (Color background, Color foreground, IconData icon) = _stylesFor(status, colorScheme);

    return Chip(
      avatar: Icon(icon, size: 16, color: foreground),
      label: Text(
        projectStatusLabel(status, l10n),
        style: TextStyle(color: foreground, fontWeight: FontWeight.w600),
      ),
      backgroundColor: background,
      shape: const StadiumBorder(),
      side: BorderSide.none,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    );
  }

  (Color, Color, IconData) _stylesFor(ProjectStatus status, ColorScheme colors) {
    switch (status) {
      case ProjectStatus.completed:
        return (colors.primaryContainer, colors.onPrimaryContainer, Icons.check_circle);
      case ProjectStatus.failed:
        return (colors.errorContainer, colors.onErrorContainer, Icons.error_outline);
      case ProjectStatus.cancelled:
        return (colors.errorContainer, colors.onErrorContainer, Icons.cancel_outlined);
      case ProjectStatus.processing:
        return (colors.tertiaryContainer, colors.onTertiaryContainer, Icons.schedule);
      case ProjectStatus.uploading:
        return (colors.secondaryContainer, colors.onSecondaryContainer, Icons.cloud_upload_outlined);
      case ProjectStatus.queued:
        return (colors.surfaceVariant, colors.onSurfaceVariant, Icons.pause_circle_outline);
    }
  }
}
