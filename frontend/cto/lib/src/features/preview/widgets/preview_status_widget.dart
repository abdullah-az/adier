import 'package:flutter/material.dart';

import '../../../data/models/preview_models.dart';

typedef RefreshCallback = Future<void> Function();

class PreviewStatusWidget extends StatelessWidget {
  const PreviewStatusWidget({
    required this.previewJob,
    required this.onRefresh,
    required this.isRefreshing,
    super.key,
  });

  final PreviewJob previewJob;
  final RefreshCallback onRefresh;
  final bool isRefreshing;

  @override
  Widget build(BuildContext context) {
    Widget content;

    if (previewJob.isReady) {
      content = Row(
        children: [
          const Icon(Icons.check_circle, color: Colors.green),
          const SizedBox(width: 12),
          Text(
            'Preview ready',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const Spacer(),
          TextButton.icon(
            onPressed: isRefreshing ? null : onRefresh,
            icon: isRefreshing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            label: const Text('Refresh'),
          ),
        ],
      );
    } else if (previewJob.hasFailed) {
      content = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.error, color: Colors.red),
              const SizedBox(width: 12),
              Text(
                'Preview failed',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: isRefreshing ? null : onRefresh,
                icon: isRefreshing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
          if (previewJob.errorMessage != null) ...[
            const SizedBox(height: 8),
            Text(previewJob.errorMessage!),
          ],
        ],
      );
    } else {
      final progress = previewJob.progress ?? 0;
      final normalizedProgress = progress > 1 ? progress / 100 : progress;
      content = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 3),
              ),
              const SizedBox(width: 12),
              Text(
                'Generating preview... (${(normalizedProgress * 100).clamp(0, 100).toStringAsFixed(0)}%)',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: isRefreshing ? null : onRefresh,
                icon: isRefreshing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.refresh),
                label: const Text('Refresh'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(value: normalizedProgress.clamp(0.0, 1.0)),
          const SizedBox(height: 8),
          Text(
            switch (previewJob.status) {
              JobStatus.queued => 'Queued for processing',
              JobStatus.running => 'Processing...',
              JobStatus.completed => 'Completed',
              JobStatus.failed => 'Failed',
              JobStatus.cancelled => 'Cancelled',
            },
          ),
        ],
      );
    }

    return Material(
      elevation: 2,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: content,
      ),
    );
  }
}
