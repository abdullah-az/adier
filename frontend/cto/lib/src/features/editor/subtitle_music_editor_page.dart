import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../l10n/app_localizations.dart';
import '../../core/constants/app_constants.dart';
import '../../core/localization/locale_provider.dart';
import '../../data/models/music_track.dart';
import '../../data/models/subtitle_segment.dart';
import 'controllers/music_library_controller.dart';
import 'controllers/subtitle_editor_controller.dart';

class SubtitleMusicEditorPage extends ConsumerStatefulWidget {
  const SubtitleMusicEditorPage({required this.videoId, super.key});

  final String videoId;

  @override
  ConsumerState<SubtitleMusicEditorPage> createState() => _SubtitleMusicEditorPageState();
}

class _SubtitleMusicEditorPageState extends ConsumerState<SubtitleMusicEditorPage> {
  @override
  void initState() {
    super.initState();

    ref.listen<SubtitleEditorState>(
      subtitleEditorProvider(widget.videoId),
      (previous, next) {
        if (previous?.totalDuration != next.totalDuration) {
          ref.read(musicLibraryProvider(widget.videoId).notifier).updateTimelineDuration(next.totalDuration);
        }

        if (next.errorMessage != null && next.errorMessage!.isNotEmpty && next.errorMessage != previous?.errorMessage) {
          final wasSaving = previous?.isSaving == true;
          if (!wasSaving) {
            _showSnackBar(next.errorMessage!, isError: true);
          }
        }
      },
    );

    ref.listen<MusicLibraryState>(
      musicLibraryProvider(widget.videoId),
      (previous, next) {
        if (next.errorMessage != null && next.errorMessage!.isNotEmpty && next.errorMessage != previous?.errorMessage) {
          final wasSaving = previous?.isSaving == true;
          if (!wasSaving) {
            _showSnackBar(next.errorMessage!, isError: true);
          }
        }
      },
    );
  }

  void _showSnackBar(String message, {required bool isError}) {
    if (!mounted) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: isError ? Theme.of(context).colorScheme.error : null,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final subtitleState = ref.watch(subtitleEditorProvider(widget.videoId));
    final musicState = ref.watch(musicLibraryProvider(widget.videoId));
    final subtitleController = ref.read(subtitleEditorProvider(widget.videoId).notifier);
    final musicController = ref.read(musicLibraryProvider(widget.videoId).notifier);

    final l10n = AppLocalizations.of(context)!;
    final locale = ref.watch(localeProvider);
    final isRtl = locale.languageCode == AppConstants.arabicCode;

    final segments = subtitleState.segments;
    final currentOverlay = _overlayTextForPosition(segments, subtitleState.previewPosition);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (subtitleState.isLoading && segments.isEmpty)
            const Center(child: Padding(padding: EdgeInsets.symmetric(vertical: 24), child: CircularProgressIndicator())),
          if (!subtitleState.isLoading && subtitleState.errorMessage != null && segments.isEmpty)
            _ErrorPlaceholder(
              message: subtitleState.errorMessage!,
              onRetry: subtitleController.refresh,
            ),
          if (segments.isNotEmpty || !subtitleState.isLoading)
            LayoutBuilder(
              builder: (context, constraints) {
                final isWide = constraints.maxWidth > 1100;
                if (isWide) {
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Flexible(
                        flex: 2,
                        child: _SubtitlePanel(
                          state: subtitleState,
                          controller: subtitleController,
                          l10n: l10n,
                          isRtl: isRtl,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Flexible(
                        flex: 3,
                        child: Column(
                          children: [
                            _PreviewPanel(
                              state: subtitleState,
                              overlayText: currentOverlay,
                              onPositionChanged: subtitleController.updatePreviewPosition,
                              l10n: l10n,
                            ),
                            const SizedBox(height: 16),
                            _MusicPanel(
                              state: musicState,
                              controller: musicController,
                              l10n: l10n,
                              timelineDuration: subtitleState.totalDuration,
                            ),
                          ],
                        ),
                      ),
                    ],
                  );
                }

                return Column(
                  children: [
                    _SubtitlePanel(
                      state: subtitleState,
                      controller: subtitleController,
                      l10n: l10n,
                      isRtl: isRtl,
                    ),
                    const SizedBox(height: 16),
                    _PreviewPanel(
                      state: subtitleState,
                      overlayText: currentOverlay,
                      onPositionChanged: subtitleController.updatePreviewPosition,
                      l10n: l10n,
                    ),
                    const SizedBox(height: 16),
                    _MusicPanel(
                      state: musicState,
                      controller: musicController,
                      l10n: l10n,
                      timelineDuration: subtitleState.totalDuration,
                    ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }
}

class _SubtitlePanel extends StatelessWidget {
  const _SubtitlePanel({
    required this.state,
    required this.controller,
    required this.l10n,
    required this.isRtl,
  });

  final SubtitleEditorState state;
  final SubtitleEditorController controller;
  final AppLocalizations l10n;
  final bool isRtl;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    l10n.subtitleSegments,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                FilledButton.icon(
                  onPressed: state.isLoading ? null : () => controller.addSegmentAfter(state.selectedSegmentId),
                  icon: const Icon(Icons.add),
                  label: Text(l10n.addSegment),
                ),
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed: (!state.hasChanges || state.isSaving)
                      ? null
                      : () async {
                          final success = await controller.saveChanges();
                          if (!context.mounted) return;
                          final messenger = ScaffoldMessenger.of(context);
                          messenger.hideCurrentSnackBar();
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text(
                                success ? l10n.subtitleUpdateSuccess : l10n.subtitleUpdateFailure,
                              ),
                              backgroundColor:
                                  success ? null : Theme.of(context).colorScheme.error,
                            ),
                          );
                        },
                  icon: state.isSaving
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.save),
                  label: Text(state.isSaving ? l10n.saving : l10n.saveChanges),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (state.segments.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text(
                    l10n.noSegmentsPlaceholder,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
              )
            else
              ListView.separated(
                physics: const NeverScrollableScrollPhysics(),
                shrinkWrap: true,
                itemBuilder: (context, index) {
                  final segment = state.segments[index];
                  final nextSegment = index < state.segments.length - 1 ? state.segments[index + 1] : null;
                  return SubtitleSegmentTile(
                    segment: segment,
                    isSelected: state.selectedSegmentId == segment.id,
                    onSelect: () => controller.selectSegment(segment.id),
                    onTextChanged: (text) => controller.updateSegmentText(segment.id, text),
                    onToggleVisibility: () => controller.toggleVisibility(segment.id),
                    onAdjustStart: (adjustment) => controller.adjustStart(segment.id, adjustment),
                    onAdjustEnd: (adjustment) => controller.adjustEnd(segment.id, adjustment),
                    onSetStart: (duration) => controller.setStart(segment.id, duration),
                    onSetEnd: (duration) => controller.setEnd(segment.id, duration),
                    onSplit: () => controller.splitSegment(segment.id),
                    onMergeWithNext: nextSegment == null ? null : () => controller.mergeWithNext(segment.id),
                    isRtl: isRtl,
                    l10n: l10n,
                  );
                },
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemCount: state.segments.length,
              ),
          ],
        ),
      ),
    );
  }
}

class SubtitleSegmentTile extends HookWidget {
  const SubtitleSegmentTile({
    required this.segment,
    required this.isSelected,
    required this.onSelect,
    required this.onTextChanged,
    required this.onToggleVisibility,
    required this.onAdjustStart,
    required this.onAdjustEnd,
    required this.onSetStart,
    required this.onSetEnd,
    required this.onSplit,
    required this.onMergeWithNext,
    required this.isRtl,
    required this.l10n,
    super.key,
  });

  final SubtitleSegment segment;
  final bool isSelected;
  final VoidCallback onSelect;
  final ValueChanged<String> onTextChanged;
  final VoidCallback onToggleVisibility;
  final ValueChanged<Duration> onAdjustStart;
  final ValueChanged<Duration> onAdjustEnd;
  final ValueChanged<Duration> onSetStart;
  final ValueChanged<Duration> onSetEnd;
  final VoidCallback onSplit;
  final VoidCallback? onMergeWithNext;
  final bool isRtl;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final textController = useTextEditingController(text: segment.text);
    final startController = useTextEditingController(text: _formatDuration(segment.start));
    final endController = useTextEditingController(text: _formatDuration(segment.end));

    useEffect(() {
      if (textController.text != segment.text) {
        textController.text = segment.text;
      }
      if (startController.text != _formatDuration(segment.start)) {
        startController.text = _formatDuration(segment.start);
      }
      if (endController.text != _formatDuration(segment.end)) {
        endController.text = _formatDuration(segment.end);
      }
      return null;
    }, [segment.id, segment.start, segment.end, segment.text]);

    return Material(
      borderRadius: BorderRadius.circular(12),
      color: isSelected
          ? Theme.of(context).colorScheme.primaryContainer
          : Theme.of(context).colorScheme.surfaceVariant,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onSelect,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    segment.isVisible ? Icons.subtitles : Icons.subtitles_off,
                    color: segment.isVisible
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _segmentTitle(segment),
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  Switch(
                    value: segment.isVisible,
                    onChanged: (_) => onToggleVisibility(),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: textController,
                maxLines: null,
                textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
                decoration: InputDecoration(
                  labelText: l10n.segmentText,
                  border: const OutlineInputBorder(),
                ),
                onChanged: onTextChanged,
              ),
              const SizedBox(height: 12),
              _DurationField(
                controller: startController,
                label: l10n.startTime,
                onSubmit: (value) {
                  final parsed = _tryParseDuration(value);
                  if (parsed != null) {
                    onSetStart(parsed);
                  } else {
                    startController.text = _formatDuration(segment.start);
                  }
                },
                onAdjust: onAdjustStart,
              ),
              const SizedBox(height: 12),
              _DurationField(
                controller: endController,
                label: l10n.endTime,
                onSubmit: (value) {
                  final parsed = _tryParseDuration(value);
                  if (parsed != null) {
                    onSetEnd(parsed);
                  } else {
                    endController.text = _formatDuration(segment.end);
                  }
                },
                onAdjust: onAdjustEnd,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: onSplit,
                    icon: const Icon(Icons.call_split),
                    label: Text(l10n.splitSegment),
                  ),
                  OutlinedButton.icon(
                    onPressed: onMergeWithNext == null ? null : onMergeWithNext,
                    icon: const Icon(Icons.merge_type),
                    label: Text(l10n.mergeWithNext),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _segmentTitle(SubtitleSegment segment) {
    final start = _formatDuration(segment.start);
    final end = _formatDuration(segment.end);
    return '$start → $end';
  }
}

class _DurationField extends StatelessWidget {
  const _DurationField({
    required this.controller,
    required this.label,
    required this.onSubmit,
    required this.onAdjust,
  });

  final TextEditingController controller;
  final String label;
  final ValueChanged<String> onSubmit;
  final ValueChanged<Duration> onAdjust;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              labelText: label,
              border: const OutlineInputBorder(),
            ),
            onSubmitted: onSubmit,
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          tooltip: '-0.25s',
          onPressed: () => onAdjust(const Duration(milliseconds: -250)),
          icon: const Icon(Icons.remove_circle_outline),
        ),
        IconButton(
          tooltip: '+0.25s',
          onPressed: () => onAdjust(const Duration(milliseconds: 250)),
          icon: const Icon(Icons.add_circle_outline),
        ),
      ],
    );
  }
}

class _PreviewPanel extends StatelessWidget {
  const _PreviewPanel({
    required this.state,
    required this.overlayText,
    required this.onPositionChanged,
    required this.l10n,
  });

  final SubtitleEditorState state;
  final String overlayText;
  final ValueChanged<Duration> onPositionChanged;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final totalMs = max(state.totalDuration.inMilliseconds.toDouble(), 1);
    final currentMs = state.previewPosition.inMilliseconds.clamp(0, totalMs).toDouble();

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.livePreview,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          gradient: const LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              Colors.transparent,
                              Colors.black54,
                            ],
                          ),
                        ),
                      ),
                    ),
                    Align(
                      alignment: Alignment.bottomCenter,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          overlayText.isEmpty ? l10n.previewEmptySubtitle : overlayText,
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                color: Colors.white,
                              ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              '${l10n.timelinePosition}: ${_formatDuration(Duration(milliseconds: currentMs.round()))}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            Slider(
              min: 0,
              max: totalMs,
              value: currentMs,
              onChanged: (value) => onPositionChanged(Duration(milliseconds: value.round())),
            ),
          ],
        ),
      ),
    );
  }
}

class _MusicPanel extends StatelessWidget {
  const _MusicPanel({
    required this.state,
    required this.controller,
    required this.l10n,
    required this.timelineDuration,
  });

  final MusicLibraryState state;
  final MusicLibraryController controller;
  final AppLocalizations l10n;
  final Duration timelineDuration;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    l10n.musicLibrary,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                FilledButton.icon(
                  onPressed: (!state.hasChanges || state.isSaving)
                      ? null
                      : () async {
                          final success = await controller.saveSelection();
                          if (!context.mounted) return;
                          final messenger = ScaffoldMessenger.of(context);
                          messenger.hideCurrentSnackBar();
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text(
                                success ? l10n.musicUpdateSuccess : l10n.musicUpdateFailure,
                              ),
                              backgroundColor:
                                  success ? null : Theme.of(context).colorScheme.error,
                            ),
                          );
                        },
                  icon: state.isSaving
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.library_music),
                  label: Text(state.isSaving ? l10n.saving : l10n.musicAssign),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (state.isLoading && state.tracks.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (!state.isLoading && state.tracks.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Text(l10n.noMusicTracksPlaceholder),
              )
            else
              Column(
                children: [
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemBuilder: (context, index) {
                      final track = state.tracks[index];
                      return _TrackTile(
                        track: track,
                        state: state,
                        controller: controller,
                        l10n: l10n,
                      );
                    },
                    separatorBuilder: (context, index) => const Divider(),
                    itemCount: state.tracks.length,
                  ),
                  const SizedBox(height: 16),
                  _MusicControls(
                    state: state,
                    controller: controller,
                    l10n: l10n,
                    timelineDuration: timelineDuration,
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _TrackTile extends StatelessWidget {
  const _TrackTile({
    required this.track,
    required this.state,
    required this.controller,
    required this.l10n,
  });

  final MusicTrack track;
  final MusicLibraryState state;
  final MusicLibraryController controller;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final isSelected = state.selectedTrackId == track.id;
    final isPreviewing = state.previewingTrackId == track.id;

    return ListTile(
      selected: isSelected,
      title: Text(track.title),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (track.artist.isNotEmpty || track.mood.isNotEmpty)
            Text(
              [track.artist, track.mood].where((value) => value.isNotEmpty).join(' • '),
            ),
          Text('${l10n.durationLabel}: ${_formatDuration(track.duration)}'),
          if (track.tags.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Wrap(
                spacing: 4,
                children: track.tags.map((tag) => Chip(label: Text(tag))).toList(),
              ),
            ),
        ],
      ),
      onTap: () => controller.selectTrack(track.id),
      trailing: Wrap(
        spacing: 8,
        children: [
          IconButton(
            tooltip: l10n.musicPreview,
            icon: Icon(isPreviewing ? Icons.stop_circle : Icons.play_circle),
            onPressed: () => controller.togglePreview(track.id),
          ),
          Radio<String>(
            value: track.id,
            groupValue: state.selectedTrackId,
            onChanged: (value) {
              if (value != null) controller.selectTrack(value);
            },
          ),
        ],
      ),
    );
  }
}

class _MusicControls extends StatelessWidget {
  const _MusicControls({
    required this.state,
    required this.controller,
    required this.l10n,
    required this.timelineDuration,
  });

  final MusicLibraryState state;
  final MusicLibraryController controller;
  final AppLocalizations l10n;
  final Duration timelineDuration;

  @override
  Widget build(BuildContext context) {
    final timeline = timelineDuration > Duration.zero ? timelineDuration : const Duration(seconds: 30);
    final timelineMs = max(1.0, timeline.inMilliseconds.toDouble());
    final rawStartMs = state.clipStart.inMilliseconds.toDouble();
    final rawEndMs = state.clipEnd.inMilliseconds.toDouble();
    final startMs = rawStartMs.clamp(0, timelineMs).toDouble();
    final endMs = rawEndMs.clamp(startMs + 1, timelineMs).toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.volume),
        Slider(
          value: state.volume,
          min: 0,
          max: 1,
          divisions: 20,
          label: state.volume.toStringAsFixed(2),
          onChanged: controller.setVolume,
        ),
        Row(
          children: [
            Expanded(child: Text('${l10n.fadeIn}: ${_formatDuration(state.fadeIn)}')),
            Expanded(
              child: Slider(
                value: state.fadeIn.inMilliseconds.clamp(0, 10000).toDouble(),
                min: 0,
                max: 10000,
                divisions: 20,
                onChanged: (value) => controller.setFadeIn(Duration(milliseconds: value.round())),
              ),
            ),
          ],
        ),
        Row(
          children: [
            Expanded(child: Text('${l10n.fadeOut}: ${_formatDuration(state.fadeOut)}')),
            Expanded(
              child: Slider(
                value: state.fadeOut.inMilliseconds.clamp(0, 10000).toDouble(),
                min: 0,
                max: 10000,
                divisions: 20,
                onChanged: (value) => controller.setFadeOut(Duration(milliseconds: value.round())),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Text(l10n.placement),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            ChoiceChip(
              label: Text(l10n.placementFullTimeline),
              selected: state.applyToFullTimeline,
              onSelected: (value) {
                if (value) controller.setPlacement(true);
              },
            ),
            ChoiceChip(
              label: Text(l10n.placementClip),
              selected: !state.applyToFullTimeline,
              onSelected: (value) {
                if (value) controller.setPlacement(false);
              },
            ),
          ],
        ),
        if (!state.applyToFullTimeline) ...[
          const SizedBox(height: 16),
          Text('${l10n.clipRange}: ${_formatDuration(Duration(milliseconds: startMs.round()))} → ${_formatDuration(Duration(milliseconds: endMs.round()))}'),
          RangeSlider(
            min: 0,
            max: timelineMs,
            divisions: max(1, timeline.inSeconds),
            values: RangeValues(startMs, endMs),
            onChanged: (values) {
              controller.setClipRange(
                Duration(milliseconds: values.start.round()),
                Duration(milliseconds: values.end.round()),
              );
            },
          ),
        ],
      ],
    );
  }
}

class _ErrorPlaceholder extends StatelessWidget {
  const _ErrorPlaceholder({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message,
              style: Theme.of(context).textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: Text(AppLocalizations.of(context)!.retry),
            ),
          ],
        ),
      ),
    );
  }
}

String _formatDuration(Duration duration) {
  final isNegative = duration.isNegative;
  final positive = isNegative ? duration.abs() : duration;
  final hours = positive.inHours;
  final minutes = positive.inMinutes.remainder(60).toString().padLeft(2, '0');
  final seconds = positive.inSeconds.remainder(60).toString().padLeft(2, '0');
  final milliseconds = positive.inMilliseconds.remainder(1000).toString().padLeft(3, '0');
  final buffer = StringBuffer();
  if (isNegative) buffer.write('-');
  if (hours > 0) {
    buffer
      ..write(hours.toString().padLeft(2, '0'))
      ..write(':');
  }
  buffer
    ..write(minutes)
    ..write(':')
    ..write(seconds)
    ..write('.')
    ..write(milliseconds);
  return buffer.toString();
}

Duration? _tryParseDuration(String input) {
  final trimmed = input.trim();
  if (trimmed.isEmpty) {
    return null;
  }

  final parts = trimmed.split('.');
  final timePart = parts[0];
  final millisPart = parts.length > 1 ? parts[1] : '0';

  final timeSegments = timePart.split(':').map((segment) => segment.trim()).where((segment) => segment.isNotEmpty).toList();
  if (timeSegments.isEmpty || timeSegments.length > 3) {
    return null;
  }

  int hours = 0;
  int minutes = 0;
  int seconds = 0;

  if (timeSegments.length == 3) {
    hours = int.tryParse(timeSegments[0]) ?? 0;
    minutes = int.tryParse(timeSegments[1]) ?? 0;
    seconds = int.tryParse(timeSegments[2]) ?? 0;
  } else if (timeSegments.length == 2) {
    minutes = int.tryParse(timeSegments[0]) ?? 0;
    seconds = int.tryParse(timeSegments[1]) ?? 0;
  } else {
    seconds = int.tryParse(timeSegments[0]) ?? 0;
  }

  final milliseconds = int.tryParse(millisPart.padRight(3, '0').substring(0, 3)) ?? 0;

  final total = Duration(hours: hours, minutes: minutes, seconds: seconds, milliseconds: milliseconds);
  return total;
}

String _overlayTextForPosition(List<SubtitleSegment> segments, Duration position) {
  final visible = segments
      .where((segment) => segment.isVisible && position >= segment.start && position <= segment.end)
      .map((segment) => segment.text.trim())
      .where((text) => text.isNotEmpty)
      .toList();
  return visible.join('\n');
}
