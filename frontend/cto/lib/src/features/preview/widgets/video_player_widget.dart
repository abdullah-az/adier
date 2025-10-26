import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

class VideoPlayerWidget extends StatelessWidget {
  const VideoPlayerWidget({
    required this.controller,
    this.overlay,
    super.key,
  });

  final VideoPlayerController controller;
  final Widget? overlay;

  @override
  Widget build(BuildContext context) {
    if (!controller.value.isInitialized) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    return Center(
      child: AspectRatio(
        aspectRatio: controller.value.aspectRatio == 0
            ? 16 / 9
            : controller.value.aspectRatio,
        child: Stack(
          fit: StackFit.expand,
          children: [
            VideoPlayer(controller),
            if (overlay != null) overlay!,
          ],
        ),
      ),
    );
  }
}
