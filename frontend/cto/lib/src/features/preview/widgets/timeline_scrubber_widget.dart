import 'package:flutter/material.dart';

import '../../../data/models/preview_models.dart';

typedef TimelineSeekCallback = void Function(Duration position);

typedef ClipSelectCallback = void Function(TimelineClip clip);

class TimelineScrubberWidget extends StatelessWidget {
  const TimelineScrubberWidget({
    required this.timeline,
    required this.currentPosition,
    required this.onSeek,
    required this.onClipSelected,
    super.key,
  });

  final TimelineComposition timeline;
  final Duration currentPosition;
  final TimelineSeekCallback onSeek;
  final ClipSelectCallback onClipSelected;

  double _calculatePlayheadPosition(BoxConstraints constraints) {
    if (timeline.duration == 0) return 0;
    final currentSeconds = currentPosition.inMilliseconds / 1000.0;
    final progress = (currentSeconds / timeline.duration).clamp(0.0, 1.0);
    return constraints.maxWidth * progress;
  }

  TimelineClip? _activeClip() {
    final currentSeconds = currentPosition.inMilliseconds / 1000.0;
    for (final clip in timeline.clips) {
      if (currentSeconds >= clip.startTime && currentSeconds <= clip.endTime) {
        return clip;
      }
    }
    return null;
  }

  Color _parseColor(String? colorString, BuildContext context) {
    if (colorString == null) {
      return Theme.of(context).colorScheme.primary.withOpacity(0.3);
    }
    
    try {
      if (colorString.startsWith('#')) {
        return Color(int.parse(colorString.replaceAll('#', '0xff')));
      }
      return Color(int.parse(colorString));
    } catch (_) {
      return Theme.of(context).colorScheme.primary.withOpacity(0.3);
    }
  }

  @override
  Widget build(BuildContext context) {
    final activeClip = _activeClip();

    return LayoutBuilder(
      builder: (context, constraints) {
        final playheadPosition = _calculatePlayheadPosition(constraints);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(
              height: 60,
              child: Stack(
                children: [
                  Row(
                    children: timeline.clips.map((clip) {
                      final widthFraction = clip.duration / timeline.duration;
                      final color = _parseColor(clip.color, context);
                      final isActive = activeClip?.id == clip.id;

                      return Expanded(
                        flex: (widthFraction * 1000).round().clamp(1, 1000),
                        child: InkWell(
                          onTap: () => onClipSelected(clip),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 250),
                            margin: const EdgeInsets.symmetric(horizontal: 2),
                            decoration: BoxDecoration(
                              color: isActive
                                  ? Theme.of(context).colorScheme.primary.withOpacity(0.6)
                                  : color,
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                color: isActive
                                    ? Theme.of(context).colorScheme.primary
                                    : Colors.transparent,
                                width: 2,
                              ),
                            ),
                            child: Center(
                              child: Text(
                                clip.label ?? 'Clip',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: isActive ? Colors.white : Colors.black,
                                    ),
                                overflow: TextOverflow.ellipsis,
                                maxLines: 2,
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  Positioned(
                    left: playheadPosition - 1,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      width: 2,
                      color: Colors.redAccent,
                    ),
                  ),
                ],
              ),
            ),
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 4,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
              ),
              child: Slider(
                min: 0,
                max: timeline.duration,
                value: (currentPosition.inMilliseconds / 1000.0)
                    .clamp(0, timeline.duration)
                    .toDouble(),
                onChanged: (value) {
                  onSeek(Duration(milliseconds: (value * 1000).round()));
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(_formatDuration(currentPosition)),
                  Text(_formatDuration(Duration(milliseconds: (timeline.duration * 1000).round()))),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final twoDigitMinutes = twoDigits(duration.inMinutes.remainder(60));
    final twoDigitSeconds = twoDigits(duration.inSeconds.remainder(60));
    final milliseconds = (duration.inMilliseconds.remainder(1000) / 10).round();
    return '${twoDigits(duration.inHours)}:$twoDigitMinutes:$twoDigitSeconds.${milliseconds.toString().padLeft(2, '0')}';
  }
}
