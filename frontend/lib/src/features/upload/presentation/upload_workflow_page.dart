import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/responsive/breakpoints.dart';
import '../../application/upload_workflow_controller.dart';
import '../../domain/upload_message.dart';
import 'widgets/offline_status_banner.dart';
import 'widgets/project_creation_card.dart';
import 'widgets/upload_dashboard_card.dart';
import 'widgets/upload_file_selector_card.dart';

class UploadWorkflowPage extends ConsumerWidget {
  const UploadWorkflowPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context)!;

    ref.listen<UploadWorkflowState>(uploadWorkflowControllerProvider, (previous, next) {
      final message = next.message;
      if (message == null || message == previous?.message) {
        return;
      }

      final text = _messageText(l10n, message);
      if (text.isEmpty) {
        ref.read(uploadWorkflowControllerProvider.notifier).clearMessage();
        return;
      }

      final messenger = ScaffoldMessenger.of(context);
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(
          content: Text(text),
          behavior: SnackBarBehavior.floating,
          backgroundColor: message.type == UploadMessageType.error
              ? theme.colorScheme.errorContainer
              : theme.colorScheme.primaryContainer,
        ),
      );
      ref.read(uploadWorkflowControllerProvider.notifier).clearMessage();
    });

    final state = ref.watch(uploadWorkflowControllerProvider);
    final controller = ref.read(uploadWorkflowControllerProvider.notifier);

    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= AppBreakpoints.medium;
        final padding = EdgeInsets.symmetric(
          horizontal: isWide ? 32 : 16,
          vertical: isWide ? 24 : 16,
        );

        final content = isWide
            ? Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(
                    flex: 3,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        OfflineStatusBanner(visible: state.isOffline, l10n: l10n),
                        ProjectCreationCard(
                          state: state,
                          l10n: l10n,
                          onNameChanged: controller.updateProjectName,
                          onSubmit: controller.createProject,
                          onReset: controller.resetProject,
                        ),
                        const SizedBox(height: 24),
                        UploadFileSelectorCard(
                          state: state,
                          l10n: l10n,
                          onFileSelected: controller.selectFile,
                          onClearSelection: controller.clearSelectedFile,
                          onUpload: controller.startUpload,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 24),
                  Expanded(
                    flex: 4,
                    child: UploadDashboardCard(
                      state: state,
                      l10n: l10n,
                      onRetry: controller.retryUpload,
                    ),
                  ),
                ],
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  OfflineStatusBanner(visible: state.isOffline, l10n: l10n),
                  ProjectCreationCard(
                    state: state,
                    l10n: l10n,
                    onNameChanged: controller.updateProjectName,
                    onSubmit: controller.createProject,
                    onReset: controller.resetProject,
                  ),
                  const SizedBox(height: 16),
                  UploadFileSelectorCard(
                    state: state,
                    l10n: l10n,
                    onFileSelected: controller.selectFile,
                    onClearSelection: controller.clearSelectedFile,
                    onUpload: controller.startUpload,
                  ),
                  const SizedBox(height: 16),
                  UploadDashboardCard(
                    state: state,
                    l10n: l10n,
                    onRetry: controller.retryUpload,
                  ),
                ],
              );

        return SingleChildScrollView(
          padding: padding,
          child: Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: isWide ? 1220 : 760),
              child: content,
            ),
          ),
        );
      },
    );
  }
}

String _messageText(AppLocalizations l10n, UploadMessage message) {
  switch (message.code) {
    case UploadMessageCode.projectCreated:
      final projectName = message.details?['projectName'] as String? ?? '';
      return l10n.uploadMessageProjectCreated(projectName);
    case UploadMessageCode.projectCreationFailed:
      final reason = message.details?['reason'] as String? ?? '';
      return l10n.uploadMessageProjectCreationFailed(reason);
    case UploadMessageCode.invalidProjectName:
      return l10n.uploadMessageInvalidProjectName;
    case UploadMessageCode.offline:
      return l10n.uploadMessageOffline;
    case UploadMessageCode.uploadStarted:
      final fileName = message.details?['fileName'] as String? ?? '';
      return l10n.uploadMessageUploadStarted(fileName);
    case UploadMessageCode.uploadCompleted:
      final fileName = message.details?['fileName'] as String? ?? '';
      return l10n.uploadMessageUploadCompleted(fileName);
    case UploadMessageCode.uploadFailed:
      final fileName = message.details?['fileName'] as String? ?? '';
      final reason = (message.details?['reason'] as String? ?? '').trim();
      if (reason.isEmpty) {
        return l10n.uploadMessageUploadFailedNoReason(fileName);
      }
      return l10n.uploadMessageUploadFailed(fileName, reason);
  }
}
