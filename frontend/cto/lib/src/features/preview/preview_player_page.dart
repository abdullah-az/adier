import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import 'package:video_player/video_player.dart';

import '../../core/constants/app_constants.dart';
import '../../core/services/websocket_service.dart';
import '../../data/models/preview_models.dart';
import '../../data/providers/preview_provider.dart';
import 'widgets/preview_controls_widget.dart';
import 'widgets/preview_status_widget.dart';
import 'widgets/subtitle_overlay_widget.dart';
import 'widgets/timeline_scrubber_widget.dart';
import 'widgets/video_player_widget.dart';

class PreviewPlayerPage extends HookConsumerWidget {
  const PreviewPlayerPage({
    required this.projectId,
    required this.jobId,
    super.key,
  });

  final String projectId;
  final String jobId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (jobId.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.info_outline, size: 64),
              const SizedBox(height: 16),
              Text(
                'No preview job specified',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              const Text(
                'Provide a job ID via the "job" query parameter to load a preview.',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    final previewJobAsync = ref.watch(previewJobProvider((projectId: projectId, jobId: jobId)));
    final isRefreshing = useState(false);
    final websocketService = useMemoized(
      () => WebSocketService(
        endpoint: Uri.parse(
          '${AppConstants.apiBaseUrl.replaceAll('http', 'ws')}/projects/$projectId/jobs/$jobId/events',
        ),
      ),
    );

    useEffect(() {
      final service = websocketService;
      final notifier = ref.read(previewJobProvider((projectId: projectId, jobId: jobId)).notifier);

      service.connect(
        onMessage: (message) {
          if (message['type'] == 'job_update') {
            notifier.updateFromWebSocket(message['data'] as Map<String, dynamic>);
          }
        },
        onError: (error, stackTrace) {
          debugPrint('WebSocket error: $error');
        },
        onDone: () {
          debugPrint('WebSocket connection closed');
        },
      );

      return service.disconnect;
    }, [websocketService]);

    return previewJobAsync.when(
      loading: () => const Center(
        child: CircularProgressIndicator(),
      ),
      error: (error, stack) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                'Failed to load preview',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(error.toString(), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {
                  ref.invalidate(previewJobProvider((projectId: projectId, jobId: jobId)));
                },
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      data: (previewJob) {
        if (!previewJob.isReady) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: PreviewStatusWidget(
                previewJob: previewJob,
                isRefreshing: isRefreshing.value,
                onRefresh: () async {
                  isRefreshing.value = true;
                  try {
                    await ref
                        .read(previewJobProvider((projectId: projectId, jobId: jobId)).notifier)
                        .refresh();
                  } finally {
                    isRefreshing.value = false;
                  }
                },
              ),
            ),
          );
        }

        return _PreviewPlayerContent(
          previewJob: previewJob,
          projectId: projectId,
          jobId: jobId,
          isRefreshing: isRefreshing.value,
          onRefresh: () async {
            isRefreshing.value = true;
            try {
              await ref
                  .read(previewJobProvider((projectId: projectId, jobId: jobId)).notifier)
                  .refresh();
            } finally {
              isRefreshing.value = false;
            }
          },
        );
      },
    );
  }
}

class _PreviewPlayerContent extends HookConsumerWidget {
  const _PreviewPlayerContent({
    required this.previewJob,
    required this.projectId,
    required this.jobId,
    required this.isRefreshing,
    required this.onRefresh,
  });

  final PreviewJob previewJob;
  final String projectId;
  final String jobId;
  final bool isRefreshing;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = useMemoized(
      () => VideoPlayerController.networkUrl(Uri.parse(previewJob.proxyVideoUrl!)),
      [previewJob.proxyVideoUrl],
    );

    final initFuture = useMemoized(() => controller.initialize(), [controller]);
    final snapshot = useFuture(initFuture);

    final isPlaying = useState(false);
    final currentPosition = useState(Duration.zero);
    final volume = useState(1.0);

    useEffect(() {
      void listener() {
        currentPosition.value = controller.value.position;
        isPlaying.value = controller.value.isPlaying;
      }

      controller.addListener(listener);
      return () => controller.removeListener(listener);
    }, [controller]);

    useEffect(() {
      return () => controller.dispose();
    }, [controller]);

    final subtitlesAsync = previewJob.subtitleUrl != null
        ? ref.watch(subtitlesProvider(previewJob.subtitleUrl!))
        : const AsyncValue<List<SubtitleCue>>.data([]);

    Widget? subtitleOverlay;
    subtitlesAsync.when(
      data: (subtitles) {
        if (subtitles.isNotEmpty) {
          subtitleOverlay = SubtitleOverlayWidget(
            subtitles: subtitles,
            currentPosition: currentPosition.value,
          );
        }
      },
      loading: () {
        subtitleOverlay = const Positioned(
          bottom: 24,
          left: 24,
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        );
      },
      error: (error, stackTrace) {
        subtitleOverlay = Positioned(
          bottom: 24,
          left: 24,
          right: 24,
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.6),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              'Failed to load subtitles',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white),
            ),
          ),
        );
      },
    );

    if (snapshot.connectionState != ConnectionState.done) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (snapshot.hasError) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text('Failed to load video', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(snapshot.error.toString(), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: onRefresh,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: PreviewStatusWidget(
            previewJob: previewJob,
            isRefreshing: isRefreshing,
            onRefresh: onRefresh,
          ),
        ),
        Expanded(
          child: Container(
            color: Colors.black,
            child: Stack(
              children: [
                VideoPlayerWidget(
                  controller: controller,
                  overlay: subtitleOverlay,
                ),
              ],
            ),
          ),
        ),
        PreviewControlsWidget(
          isPlaying: isPlaying.value,
          volume: volume.value,
          onPlayPause: () {
            if (isPlaying.value) {
              controller.pause();
            } else {
              controller.play();
            }
          },
          onVolumeChanged: (newVolume) {
            volume.value = newVolume;
            controller.setVolume(newVolume);
          },
        ),
        if (previewJob.timeline != null)
          Padding(
            padding: const EdgeInsets.all(16),
            child: TimelineScrubberWidget(
              timeline: previewJob.timeline!,
              currentPosition: currentPosition.value,
              onSeek: (position) {
                controller.seekTo(position);
              },
              onClipSelected: (clip) {
                final seekPosition = Duration(milliseconds: (clip.startTime * 1000).round());
                controller.seekTo(seekPosition);
              },
            ),
          ),
      ],
    );
  }
}
