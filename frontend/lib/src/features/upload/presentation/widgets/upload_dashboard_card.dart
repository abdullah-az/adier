import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:intl/intl.dart';

import '../../../data/models/media_asset.dart';
import '../../application/upload_workflow_controller.dart';
import '../../domain/upload_record.dart';
import '../../../core/responsive/breakpoints.dart';

class UploadDashboardCard extends StatelessWidget {
  const UploadDashboardCard({
    super.key,
    required this.state,
    required this.l10n,
    required this.onRetry,
  });

  final UploadWorkflowState state;
  final AppLocalizations l10n;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final uploads = state.uploads;
    final isCompact = MediaQuery.sizeOf(context).width < AppBreakpoints.medium;

    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(l10n.uploadDashboardTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: 12),
            Text(
              l10n.uploadDashboardSubtitle,
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 20),
            if (uploads.isEmpty)
              _EmptyDashboardState(isCompact: isCompact, l10n: l10n)
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemBuilder: (context, index) {
                  final record = uploads[index];
                  final isActive = state.activeUploadId == record.assetId;
                  return _UploadRecordTile(
                    record: record,
                    l10n: l10n,
                    isActive: isActive,
                    showRetry: isActive && record.isFailed,
                    onRetry: onRetry,
                  );
                },
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemCount: uploads.length,
              ),
          ],
        ),
      ),
    );
  }
}

class _EmptyDashboardState extends StatelessWidget {
  const _EmptyDashboardState({required this.isCompact, required this.l10n});

  final bool isCompact;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(
        horizontal: isCompact ? 16 : 24,
        vertical: isCompact ? 18 : 24,
      ),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: theme.colorScheme.surfaceVariant,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: <Widget>[
          Icon(Icons.playlist_play_rounded, size: 48, color: theme.colorScheme.outline),
          const SizedBox(height: 12),
          Text(
            l10n.uploadDashboardEmptyStateTitle,
            style: theme.textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            l10n.uploadDashboardEmptyStateSubtitle,
            style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.outline),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _UploadRecordTile extends StatelessWidget {
  const _UploadRecordTile({
    required this.record,
    required this.l10n,
    required this.isActive,
    required this.showRetry,
    required this.onRetry,
  });

  final UploadRecord record;
  final AppLocalizations l10n;
  final bool isActive;
  final bool showRetry;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final progress = record.progress.clamp(0.0, 1.0);
    final statusLabel = _statusLabel(l10n, record.status);
    final percentLabel = NumberFormat.percentPattern(l10n.localeName).format(progress.clamp(0, 1));
    final statusColor = _statusColor(theme, record.status);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Icon(_statusIcon(record.status), color: statusColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    record.fileName,
                    style: theme.textTheme.bodyLarge,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    statusLabel,
                    style: theme.textTheme.bodyMedium?.copyWith(color: statusColor),
                  ),
                ],
              ),
            ),
            if (showRetry)
              TextButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: Text(l10n.uploadDashboardRetryButton),
              )
            else
              Text(
                percentLabel,
                style: theme.textTheme.labelLarge,
              ),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: record.isFailed ? (progress > 0 ? progress : null) : progress,
            minHeight: 8,
            backgroundColor: theme.colorScheme.surfaceVariant,
            valueColor: AlwaysStoppedAnimation<Color>(statusColor),
          ),
        ),
        if (record.isFailed && record.errorMessage != null && record.errorMessage!.isNotEmpty) ...<Widget>[
          const SizedBox(height: 8),
          Text(
            record.errorMessage!,
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.error),
          ),
        ],
      ],
    );
  }

  String _statusLabel(AppLocalizations l10n, MediaAssetStatus status) {
    return switch (status) {
      MediaAssetStatus.uploading => l10n.uploadDashboardStatusUploading,
      MediaAssetStatus.processing => l10n.uploadDashboardStatusProcessing,
      MediaAssetStatus.ready => l10n.uploadDashboardStatusReady,
      MediaAssetStatus.failed => l10n.uploadDashboardStatusFailed,
      MediaAssetStatus.pending => l10n.uploadDashboardStatusPending,
    };
  }

  IconData _statusIcon(MediaAssetStatus status) {
    return switch (status) {
      MediaAssetStatus.uploading => Icons.file_upload_rounded,
      MediaAssetStatus.processing => Icons.auto_fix_high_rounded,
      MediaAssetStatus.ready => Icons.check_circle_rounded,
      MediaAssetStatus.failed => Icons.error_rounded,
      MediaAssetStatus.pending => Icons.hourglass_bottom,
    };
  }

  Color _statusColor(ThemeData theme, MediaAssetStatus status) {
    return switch (status) {
      MediaAssetStatus.uploading => theme.colorScheme.primary,
      MediaAssetStatus.processing => theme.colorScheme.tertiary,
      MediaAssetStatus.ready => theme.colorScheme.secondary,
      MediaAssetStatus.failed => theme.colorScheme.error,
      MediaAssetStatus.pending => theme.colorScheme.outline,
    };
  }
}
