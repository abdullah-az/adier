import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import 'controller/project_timeline_controller.dart';
import 'state/project_timeline_state.dart';
import 'widgets/project_timeline_workspace.dart';

class ProjectDetailPage extends HookConsumerWidget {
  const ProjectDetailPage({super.key, required this.projectId});

  final String projectId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final timelineAsync =
        ref.watch(projectTimelineControllerProvider(projectId));

    final searchController = useTextEditingController(
      text: timelineAsync.valueOrNull?.searchQuery ?? '',
    );

    useEffect(() {
      final query = timelineAsync.valueOrNull?.searchQuery ?? '';
      if (searchController.text != query) {
        searchController.value = TextEditingValue(
          text: query,
          selection: TextSelection.collapsed(offset: query.length),
        );
      }
      return null;
    }, [timelineAsync.valueOrNull?.searchQuery]);

    ref.listen(
      projectTimelineControllerProvider(projectId),
      (previous, next) {
        final prevError = previous?.valueOrNull?.errorMessage;
        final nextError = next.valueOrNull?.errorMessage;
        if (nextError != null && nextError != prevError) {
          if (nextError == TimelineErrorCodes.saveFailed ||
              nextError == TimelineErrorCodes.loadFailed) {
            final message = _mapErrorToMessage(l10n, nextError);
            if (message != null && context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(message)),
              );
            }
          }
        }
      },
    );

    final controller =
        ref.read(projectTimelineControllerProvider(projectId).notifier);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.timelineEditorTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: timelineAsync.isLoading
                ? null
                : () => controller.refresh(),
            tooltip: l10n.timelineRefresh,
          ),
        ],
      ),
      body: timelineAsync.when(
        data: (timelineState) {
          final errorMessage = timelineState.errorMessage == null
              ? null
              : _mapErrorToMessage(l10n, timelineState.errorMessage!);
          return ProjectTimelineWorkspace(
            state: timelineState,
            projectId: projectId,
            errorMessage: errorMessage,
            searchController: searchController,
            onSelectSource: controller.setActiveSource,
            onToggleSuggestion: controller.toggleSuggestionSelection,
            onDropSuggestion: controller.addSuggestionToTimeline,
            onReorderClip: controller.reorderClip,
            onTrimClip: controller.trimClip,
            onRemoveClip: controller.removeClip,
            onMergeClip: controller.mergeClipWithNext,
            onSplitClip: controller.splitClip,
            onAddTranscriptSegment: controller.addTranscriptSegment,
            onSearchTranscript: controller.searchTranscript,
            onRefreshRequested: controller.refresh,
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _TimelineErrorView(
          message: _mapErrorToMessage(l10n, TimelineErrorCodes.loadFailed) ??
              l10n.timelineErrorLoadFailed,
          onRetry: controller.refresh,
        ),
      ),
    );
  }
}

String? _mapErrorToMessage(AppLocalizations l10n, String code) {
  switch (code) {
    case TimelineErrorCodes.maxDurationExceeded:
      return l10n.timelineErrorMaxDuration;
    case TimelineErrorCodes.clipOverlap:
      return l10n.timelineErrorOverlap;
    case TimelineErrorCodes.clipTooShort:
      return l10n.timelineErrorClipTooShort;
    case TimelineErrorCodes.mergeIncompatible:
      return l10n.timelineErrorMergeNotAllowed;
    case TimelineErrorCodes.invalidSplitPoint:
      return l10n.timelineErrorSplitInvalid;
    case TimelineErrorCodes.saveFailed:
      return l10n.timelineErrorSaveFailed;
    case TimelineErrorCodes.loadFailed:
      return l10n.timelineErrorLoadFailed;
    case TimelineErrorCodes.transcriptSearchFailed:
      return l10n.timelineErrorTranscriptSearch;
    default:
      return null;
  }
}

class _TimelineErrorView extends StatelessWidget {
  const _TimelineErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.timeline_outlined,
              size: 48,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              icon: const Icon(Icons.refresh),
              label: Text(AppLocalizations.of(context)!.timelineRefresh),
              onPressed: onRetry,
            ),
          ],
        ),
      ),
    );
  }
}
