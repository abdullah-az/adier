import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:responsive_framework/responsive_framework.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/constants/app_constants.dart';
import '../../data/models/project_model.dart';
import '../../data/providers/project_provider.dart';
import '../projects/utils/project_formatters.dart';
import '../projects/widgets/project_status_chip.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context);
    final uploadState = ref.watch(uploadControllerProvider);
    final libraryState = ref.watch(projectLibraryProvider);
    final breakpoints = ResponsiveBreakpoints.of(context);

    return RefreshIndicator(
      onRefresh: () => ref.read(projectLibraryProvider.notifier).refresh(showLoading: true),
      edgeOffset: 16,
      child: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          _UploadCard(
            uploadState: uploadState,
            onPickFile: () => ref.read(uploadControllerProvider.notifier).pickAndUpload(),
            onCancel: () => ref.read(uploadControllerProvider.notifier).cancelUpload(),
            onReset: () => ref.read(uploadControllerProvider.notifier).reset(),
            l10n: l10n,
          ),
          const SizedBox(height: 32),
          _LibraryHeader(
            l10n: l10n,
            isLoading: libraryState.isLoading,
            onRefresh: () => ref.read(projectLibraryProvider.notifier).refresh(showLoading: true),
          ),
          const SizedBox(height: 16),
          if (libraryState.hasError) ...[
            _LibraryErrorCard(
              l10n: l10n,
              onRetry: () => ref.read(projectLibraryProvider.notifier).refresh(showLoading: true),
            ),
            const SizedBox(height: 16),
          ],
          if (libraryState.isLoading && libraryState.projects.isEmpty)
            const _LibraryLoading()
          else if (libraryState.projects.isEmpty)
            _LibraryEmptyState(l10n: l10n)
          else
            _ProjectGrid(
              projects: libraryState.projects,
              l10n: l10n,
              locale: locale,
              breakpoints: breakpoints,
            ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _UploadCard extends StatelessWidget {
  const _UploadCard({
    required this.uploadState,
    required this.onPickFile,
    required this.onCancel,
    required this.onReset,
    required this.l10n,
  });

  final UploadState uploadState;
  final VoidCallback onPickFile;
  final VoidCallback onCancel;
  final VoidCallback onReset;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUploading = uploadState.isUploading;
    final hasError = uploadState.hasError;
    final isSuccess = uploadState.isSuccess;
    final rawSuccessName = uploadState.project?.name ?? uploadState.fileName ?? '';
    final successName = rawSuccessName.trim().isEmpty
        ? l10n.uploadProgressFallbackName
        : rawSuccessName;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Icon(
                    Icons.cloud_upload_outlined,
                    color: theme.colorScheme.onPrimaryContainer,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l10n.uploadCardTitle,
                        style: theme.textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        l10n.uploadCardSubtitle,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                FilledButton.icon(
                  onPressed: isUploading ? null : onPickFile,
                  icon: const Icon(Icons.video_call_outlined),
                  label: Text(isSuccess ? l10n.uploadAnotherButtonLabel : l10n.uploadButtonLabel),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (isUploading) _UploadProgress(state: uploadState, onCancel: onCancel, l10n: l10n),
            if (hasError)
              _UploadFeedbackBanner(
                icon: Icons.error_outline,
                backgroundColor: theme.colorScheme.errorContainer,
                foregroundColor: theme.colorScheme.onErrorContainer,
                message: _resolveUploadErrorMessage(context),
                action: TextButton(
                  onPressed: onPickFile,
                  child: Text(l10n.uploadRetry),
                ),
              )
            else if (isSuccess)
              _UploadFeedbackBanner(
                icon: Icons.check_circle_outline,
                backgroundColor: theme.colorScheme.primaryContainer,
                foregroundColor: theme.colorScheme.onPrimaryContainer,
                message: l10n.uploadSuccess(successName),
                action: TextButton(
                  onPressed: onReset,
                  child: Text(l10n.uploadDoneDismiss),
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _resolveUploadErrorMessage(BuildContext context) {
    final error = uploadState.error;
    if (error == 'invalid_format') {
      return l10n.uploadInvalidFormat;
    }
    if (error is DioException && error.type == DioExceptionType.connectionTimeout) {
      return l10n.uploadNetworkError;
    }
    if (error is DioException && error.type == DioExceptionType.connectionError) {
      return l10n.uploadNetworkError;
    }
    return l10n.uploadGenericError;
  }
}

class _UploadProgress extends StatelessWidget {
  const _UploadProgress({
    required this.state,
    required this.onCancel,
    required this.l10n,
  });

  final UploadState state;
  final VoidCallback onCancel;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final progressLabel = formatPercentage(state.progress, fractionDigits: 0);
    final speedLabel = formatSpeed(state.speedBytesPerSecond, l10n);
    final sentLabel = formatBytes(state.sentBytes, l10n, precision: 1);
    final totalLabel = formatBytes(state.totalBytes, l10n, precision: 1);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    state.fileName ?? l10n.uploadProgressFallbackName,
                    style: theme.textTheme.titleMedium,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    l10n.uploadProgressLabel(progressLabel),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            TextButton.icon(
              onPressed: onCancel,
              icon: const Icon(Icons.close),
              label: Text(l10n.uploadCancel),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: state.progress.clamp(0, 1).toDouble(),
            minHeight: 10,
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 16,
          runSpacing: 4,
          children: [
            Text(l10n.uploadTransferredLabel(sentLabel, totalLabel)),
            Text(speedLabel),
          ],
        ),
      ],
    );
  }
}

class _UploadFeedbackBanner extends StatelessWidget {
  const _UploadFeedbackBanner({
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
    required this.message,
    required this.action,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
  final String message;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: foregroundColor),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: foregroundColor, fontWeight: FontWeight.w600),
            ),
          ),
          action,
        ],
      ),
    );
  }
}

class _LibraryHeader extends StatelessWidget {
  const _LibraryHeader({
    required this.l10n,
    required this.isLoading,
    required this.onRefresh,
  });

  final AppLocalizations l10n;
  final bool isLoading;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                l10n.projectLibraryTitle,
                style: theme.textTheme.headlineSmall,
              ),
              const SizedBox(height: 4),
              Text(
                l10n.projectLibrarySubtitle,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
        if (isLoading)
          Padding(
            padding: const EdgeInsets.only(left: 16),
            child: SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(
                  theme.colorScheme.primary,
                ),
              ),
            ),
          )
        else
          IconButton(
            tooltip: l10n.refresh,
            onPressed: onRefresh,
            icon: const Icon(Icons.refresh),
          ),
      ],
    );
  }
}

class _LibraryErrorCard extends StatelessWidget {
  const _LibraryErrorCard({
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
        padding: const EdgeInsets.all(20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.warning_amber_rounded, color: theme.colorScheme.onErrorContainer),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.projectLibraryErrorTitle,
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: theme.colorScheme.onErrorContainer,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    l10n.projectLibraryErrorSubtitle,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onErrorContainer,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: onRetry,
                    style: TextButton.styleFrom(foregroundColor: theme.colorScheme.onErrorContainer),
                    child: Text(l10n.retry),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LibraryLoading extends StatelessWidget {
  const _LibraryLoading();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 40),
      child: Center(
        child: CircularProgressIndicator(),
      ),
    );
  }
}

class _LibraryEmptyState extends StatelessWidget {
  const _LibraryEmptyState({required this.l10n});

  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Icon(
              Icons.video_library_outlined,
              size: 48,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              l10n.projectLibraryEmptyTitle,
              style: theme.textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              l10n.projectLibraryEmptySubtitle,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProjectGrid extends StatelessWidget {
  const _ProjectGrid({
    required this.projects,
    required this.l10n,
    required this.locale,
    required this.breakpoints,
  });

  final List<ProjectModel> projects;
  final AppLocalizations l10n;
  final Locale locale;
  final ResponsiveBreakpointsData breakpoints;

  int _resolveCrossAxisCount(double width) {
    if (width >= 1400) {
      return 4;
    }
    if (width >= 1100) {
      return 3;
    }
    if (breakpoints.largerThan(TABLET)) {
      return 2;
    }
    if (breakpoints.largerThan(MOBILE)) {
      return 2;
    }
    return 1;
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width - 48; // account for horizontal padding
    final crossAxisCount = _resolveCrossAxisCount(width);

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: projects.length,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        mainAxisSpacing: 16,
        crossAxisSpacing: 16,
        childAspectRatio: crossAxisCount == 1 ? 16 / 10 : 16 / 11,
      ),
      itemBuilder: (context, index) {
        final project = projects[index];
        return _ProjectCard(
          project: project,
          l10n: l10n,
          locale: locale,
        );
      },
    );
  }
}

class _ProjectCard extends StatelessWidget {
  const _ProjectCard({
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
    final hasProgress = project.status == ProjectStatus.processing || project.status == ProjectStatus.uploading;
    final progress = (project.progress ?? (project.status == ProjectStatus.completed ? 1.0 : 0.0)).clamp(0.0, 1.0);
    final progressLabel = formatPercentage(progress, fractionDigits: 0);

    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: () {
        context.push('${AppConstants.projectsRoute}/${project.id}', extra: project);
      },
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _ProjectThumbnail(thumbnailUrl: project.thumbnailUrl),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Text(
                            project.name,
                            style: theme.textTheme.titleMedium,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 12),
                        ProjectStatusChip(status: project.status, l10n: l10n),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      l10n.projectLastUpdated(formatProjectDateTime(project.updatedAt, locale)),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const Spacer(),
                    if (hasProgress) ...[
                      LinearProgressIndicator(value: progress == 0 ? null : progress),
                      const SizedBox(height: 6),
                      Text(
                        l10n.projectProcessingProgress(progressLabel),
                        style: theme.textTheme.bodySmall,
                      ),
                    ] else ...[
                      TextButton(
                        onPressed: () {
                          context.push('${AppConstants.projectsRoute}/${project.id}', extra: project);
                        },
                        child: Text(l10n.projectViewDetails),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProjectThumbnail extends StatelessWidget {
  const _ProjectThumbnail({this.thumbnailUrl});

  final String? thumbnailUrl;

  @override
  Widget build(BuildContext context) {
    if (thumbnailUrl == null || thumbnailUrl!.isEmpty) {
      return AspectRatio(
        aspectRatio: 16 / 9,
        child: Container(
          color: Theme.of(context).colorScheme.surfaceVariant,
          child: const Center(
            child: Icon(Icons.movie_outlined, size: 42),
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
              child: Icon(Icons.movie_outlined, size: 42),
            ),
          );
        },
      ),
    );
  }
}
