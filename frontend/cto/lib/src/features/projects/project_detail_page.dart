import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import '../../data/models/project_model.dart';
import '../../data/providers/project_provider.dart';
import 'utils/project_formatters.dart';
import 'widgets/project_status_chip.dart';

class ProjectDetailPage extends ConsumerWidget {
  const ProjectDetailPage({
    required this.projectId,
    this.initialProject,
    super.key,
  });

  final String projectId;
  final ProjectModel? initialProject;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context);
    final asyncProject = ref.watch(projectDetailProvider(projectId));

    final project = asyncProject.value ?? initialProject;
    final isLoading = asyncProject.isLoading && project == null;
    final hasError = asyncProject.hasError && project == null;

    return RefreshIndicator(
      onRefresh: () async {
        await ref.refresh(projectDetailProvider(projectId).future);
      },
      edgeOffset: 16,
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 960),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (project != null)
                    _HeaderSection(project: project, l10n: l10n, locale: locale),
                  if (project == null && isLoading)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 40),
                      child: Center(child: CircularProgressIndicator()),
                    )
                  else if (hasError)
                    _ErrorState(
                      l10n: l10n,
                      onRetry: () => ref.refresh(projectDetailProvider(projectId)),
                    )
                  else if (project != null) ...[
                    const SizedBox(height: 24),
                    _OverviewCard(project: project, l10n: l10n, locale: locale),
                    const SizedBox(height: 24),
                    _MetadataCard(project: project, l10n: l10n, locale: locale),
                  ],
                  if (asyncProject.hasError && project != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: _InlineErrorMessage(
                        l10n: l10n,
                        onRetry: () => ref.refresh(projectDetailProvider(projectId)),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeaderSection extends StatelessWidget {
  const _HeaderSection({
    required this.project,
    required this.l10n,
    required this.locale,
  });

  final ProjectModel project;
  final AppLocalizations l10n;
  final Locale locale;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          project.name,
          style: theme.textTheme.headlineMedium,
        ),
        const SizedBox(height: 12),
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ProjectStatusChip(status: project.status, l10n: l10n),
            const SizedBox(width: 16),
            Text(
              l10n.projectLastUpdated(formatProjectDateTime(project.updatedAt, locale)),
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _OverviewCard extends StatelessWidget {
  const _OverviewCard({
    required this.project,
    required this.l10n,
    required this.locale,
  });

  final ProjectModel project;
  final AppLocalizations l10n;
  final Locale locale;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isProcessing = project.status == ProjectStatus.processing || project.status == ProjectStatus.uploading;
    final progress = (project.progress ?? 0).clamp(0.0, 1.0);
    final progressLabel = formatPercentage(progress, fractionDigits: 0);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _DetailThumbnail(thumbnailUrl: project.thumbnailUrl),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (isProcessing) ...[
                  LinearProgressIndicator(value: progress > 0 ? progress : null),
                  const SizedBox(height: 8),
                  Text(
                    l10n.projectProcessingProgress(progressLabel),
                    style: theme.textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    l10n.projectDetailProcessingMessage,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ] else ...[
                  Text(
                    project.description?.isNotEmpty == true
                        ? project.description!
                        : l10n.projectDetailDescriptionPlaceholder,
                    style: theme.textTheme.bodyLarge,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetadataCard extends StatelessWidget {
  const _MetadataCard({
    required this.project,
    required this.l10n,
    required this.locale,
  });

  final ProjectModel project;
  final AppLocalizations l10n;
  final Locale locale;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.projectDetailInformationHeading,
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            _MetadataRow(
              label: l10n.projectDetailStatus,
              value: projectStatusLabel(project.status, l10n),
              icon: Icons.info_outline,
            ),
            const SizedBox(height: 12),
            _MetadataRow(
              label: l10n.projectDetailUpdated,
              value: formatProjectDateTime(project.updatedAt, locale),
              icon: Icons.access_time,
            ),
            if (project.fileSizeBytes != null) ...[
              const SizedBox(height: 12),
              _MetadataRow(
                label: l10n.projectDetailFileSize,
                value: formatBytes(project.fileSizeBytes, l10n, precision: 1),
                icon: Icons.sd_storage,
              ),
            ],
            if (project.durationSeconds != null) ...[
              const SizedBox(height: 12),
              _MetadataRow(
                label: l10n.projectDetailDuration,
                value: formatDurationFromSeconds(project.durationSeconds),
                icon: Icons.timelapse,
              ),
            ],
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
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: theme.colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: theme.textTheme.bodyLarge,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DetailThumbnail extends StatelessWidget {
  const _DetailThumbnail({this.thumbnailUrl});

  final String? thumbnailUrl;

  @override
  Widget build(BuildContext context) {
    if (thumbnailUrl == null || thumbnailUrl!.isEmpty) {
      return AspectRatio(
        aspectRatio: 16 / 9,
        child: Container(
          color: Theme.of(context).colorScheme.surfaceVariant,
          child: const Center(
            child: Icon(Icons.movie_creation_outlined, size: 56),
          ),
        ),
      );
    }

    return AspectRatio(
      aspectRatio: 16 / 9,
      child: Image.network(
        thumbnailUrl!,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) {
          return Container(
            color: Theme.of(context).colorScheme.surfaceVariant,
            child: const Center(
              child: Icon(Icons.movie_creation_outlined, size: 56),
            ),
          );
        },
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.l10n,
    required this.onRetry,
  });

  final AppLocalizations l10n;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: theme.colorScheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline, size: 32, color: theme.colorScheme.onErrorContainer),
            const SizedBox(height: 12),
            Text(
              l10n.projectDetailErrorTitle,
              style: theme.textTheme.titleMedium?.copyWith(
                color: theme.colorScheme.onErrorContainer,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.projectDetailErrorSubtitle,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onErrorContainer,
              ),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: onRetry,
              style: FilledButton.styleFrom(
                backgroundColor: theme.colorScheme.onErrorContainer,
                foregroundColor: theme.colorScheme.error,
              ),
              child: Text(l10n.retry),
            ),
          ],
        ),
      ),
    );
  }
}

class _InlineErrorMessage extends StatelessWidget {
  const _InlineErrorMessage({
    required this.l10n,
    required this.onRetry,
  });

  final AppLocalizations l10n;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer.withOpacity(0.4),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: theme.colorScheme.error),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              l10n.projectDetailErrorInline,
              style: theme.textTheme.bodyMedium,
            ),
          ),
          TextButton(
            onPressed: onRetry,
            child: Text(l10n.retry),
          ),
        ],
      ),
    );
  }
}
