import 'package:flutter/material.dart';

import '../../../core/utils/timeline_utils.dart';
import '../../../data/models/timeline_segment.dart';

class TimelineThumbnail extends StatelessWidget {
  const TimelineThumbnail({
    required this.segments,
    this.height = 48,
    super.key,
  });

  final List<TimelineSegment> segments;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (segments.isEmpty) {
      return SizedBox(height: height);
    }

    return SizedBox(
      height: height,
      child: CustomPaint(
        painter: _TimelineThumbnailPainter(
          segments: segments,
          total: calculateTimelineDuration(segments),
        ),
      ),
    );
  }
}

class _TimelineThumbnailPainter extends CustomPainter {
  _TimelineThumbnailPainter({
    required this.segments,
    required this.total,
  });

  final List<TimelineSegment> segments;
  final Duration total;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    var cursor = 0.0;

    for (final segment in segments) {
      final segmentDuration = segment.duration.inMilliseconds.toDouble();
      final width = total.inMilliseconds == 0
          ? size.width / segments.length
          : (segmentDuration / total.inMilliseconds) * size.width;
      paint.color = segment.color ?? Colors.blueGrey;
      final rect = Rect.fromLTWH(cursor, 0, width, size.height);
      canvas.drawRRect(
        RRect.fromRectAndRadius(rect, const Radius.circular(4)),
        paint,
      );
      cursor += width;
    }
  }

  @override
  bool shouldRepaint(covariant _TimelineThumbnailPainter oldDelegate) {
    return oldDelegate.segments != segments || oldDelegate.total != total;
  }
}
