import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../l10n/app_localizations.dart';
import '../../../core/utils/duration_formatter.dart';
import '../../../data/models/timeline_models.dart';

class TimelineMetadataPanel extends StatelessWidget {
  const TimelineMetadataPanel({
    super.key,
    required this.metadata,
    required this.totalDuration,
    required this.hasUnsavedChanges,
    required this.isSaving,
    required this.onRefresh,
    required this.isOverLimit,
  });

  final ProjectMetadata metadata;
  final Duration totalDuration;
  final bool hasUnsavedChanges;
  final bool isSaving;
  final VoidCallback onRefresh;
  final bool isOverLimit;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final maxDuration = metadata.maxDuration;
    final remaining = metadata.remainingDuration;
    final progress = maxDuration.inMilliseconds > 0
        ? (totalDuration.inMilliseconds / maxDuration.inMilliseconds)
            .clamp(0, 1)
        : null;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    l10n.timelineMetadataTitle,
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  tooltip: l10n.timelineRefresh,
                  onPressed: onRefresh,
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (progress != null)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  LinearProgressIndicator(value: progress),
                  const SizedBox(height: 8),
                  Text(
                    l10n.timelineMetadataProgress(
                      DurationFormatter.format(totalDuration),
                      DurationFormatter.format(maxDuration),
                    ),
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ),
            const SizedBox(height: 16),
            _MetadataRow(
              label: l10n.timelineMetadataProjectId,
              value: metadata.projectId,
            ),
            _MetadataRow(
              label: l10n.timelineMetadataClips,
              value: metadata.clipCount.toString(),
            ),
            _MetadataRow(
              label: l10n.timelineMetadataTotalDuration,
              value: DurationFormatter.format(totalDuration),
            ),
            if (maxDuration > Duration.zero)
              _MetadataRow(
                label: l10n.timelineMetadataMaxDuration,
                value: DurationFormatter.format(maxDuration),
              ),
            if (maxDuration > Duration.zero)
              _MetadataRow(
                label: l10n.timelineMetadataRemaining,
                value: DurationFormatter.format(remaining),
                valueStyle: isOverLimit
                    ? theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.error,
                      )
                    : null,
              ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (isSaving)
                  Chip(
                    avatar: const SizedBox.square(
                      dimension: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    label: Text(l10n.timelineMetadataSaving),
                    backgroundColor:
                        theme.colorScheme.primaryContainer.withOpacity(0.6),
                  )
                else if (hasUnsavedChanges)
                  Chip(
                    avatar: const Icon(Icons.error_outline, size: 16),
                    label: Text(l10n.timelineMetadataUnsavedChanges),
                    backgroundColor: theme.colorScheme.tertiaryContainer,
                  )
                else
                  Chip(
                    avatar: const Icon(Icons.check_circle, size: 16),
                    label: Text(l10n.timelineMetadataSynced),
                    backgroundColor: theme.colorScheme.secondaryContainer,
                  ),
                if (metadata.lastSavedAt != null)
                  Chip(
                    avatar: const Icon(Icons.schedule, size: 16),
                    label: Text(
                      l10n.timelineMetadataLastSaved(
                        DateFormat.yMMMd()
                            .add_jm()
                            .format(metadata.lastSavedAt!),
                      ),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MetadataRow extends StatelessWidget {
  const _MetadataRow({
    required this.label,
    required this.value,
    this.valueStyle,
  });

  final String label;
  final String value;
  final TextStyle? valueStyle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: theme.textTheme.bodySmall,
            ),
          ),
          Text(
            value,
            style: valueStyle ?? theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}
