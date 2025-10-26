import 'package:flutter/material.dart';

class PreviewControlsWidget extends StatelessWidget {
  const PreviewControlsWidget({
    required this.isPlaying,
    required this.volume,
    required this.onPlayPause,
    required this.onVolumeChanged,
    super.key,
  });

  final bool isPlaying;
  final double volume;
  final VoidCallback onPlayPause;
  final ValueChanged<double> onVolumeChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            iconSize: 32,
            tooltip: isPlaying ? 'Pause' : 'Play',
            onPressed: onPlayPause,
          ),
          const SizedBox(width: 16),
          IconButton(
            icon: Icon(volume > 0 ? Icons.volume_up : Icons.volume_off),
            tooltip: volume > 0 ? 'Mute' : 'Unmute',
            onPressed: () {
              onVolumeChanged(volume > 0 ? 0 : 1.0);
            },
          ),
          Expanded(
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 2,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
              ),
              child: Slider(
                min: 0,
                max: 1,
                value: volume,
                onChanged: onVolumeChanged,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
