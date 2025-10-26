import 'package:flutter/material.dart';

import '../../../data/models/preview_models.dart';

class SubtitleOverlayWidget extends StatelessWidget {
  const SubtitleOverlayWidget({
    required this.subtitles,
    required this.currentPosition,
    super.key,
  });

  final List<SubtitleCue> subtitles;
  final Duration currentPosition;

  SubtitleCue? _getCurrentSubtitle() {
    final positionSeconds = currentPosition.inMilliseconds / 1000.0;

    for (final cue in subtitles) {
      if (positionSeconds >= cue.startTime && positionSeconds <= cue.endTime) {
        return cue;
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final currentSubtitle = _getCurrentSubtitle();

    if (currentSubtitle == null) {
      return const SizedBox.shrink();
    }

    return Positioned(
      bottom: 80,
      left: 16,
      right: 16,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          currentSubtitle.text,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w500,
            shadows: [
              Shadow(
                offset: Offset(1, 1),
                blurRadius: 2,
                color: Colors.black,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
