import 'package:ai_video_editor_frontend/src/features/workspace/presentation/timeline_editor.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_video_editor_frontend/src/data/models/clip.dart' as model;

void main() {
  group('TimelineEditor', () {
    testWidgets('dragging left handle snaps to nearest marker and calls onTrimUpdate', (tester) async {
      final clip = model.Clip(
        id: 'c1',
        projectId: 'p1',
        sequence: 0,
        duration: const Duration(seconds: 10),
        playbackUrl: Uri.parse('https://stream/1'),
        createdAt: DateTime.utc(2024, 1, 1),
        inPointMs: 0,
        outPointMs: 10000,
        markers: const <int>[1000, 2000, 3500, 7000],
        transcriptSnippet: 'Hello world from transcript',
        qualityScore: 0.92,
      );

      String? updatedId;
      int? updatedIn;
      int? updatedOut;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TimelineEditor(
              clips: <model.Clip>[clip],
              secondsPerPixel: 0.05, // 20px per second
              onTrimUpdate: (id, inMs, outMs) async {
                updatedId = id;
                updatedIn = inMs;
                updatedOut = outMs;
              },
              onMerge: (_) async {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Drag the left handle to the right near 2000ms marker
      final leftHandle = find.byKey(const ValueKey<String>('handle-left-c1'));

      // Perform a small drag
      await tester.drag(leftHandle, const Offset(40, 0));
      await tester.pumpAndSettle();

      // End the drag to trigger commit by lifting finger (handled automatically after drag)

      expect(updatedId, 'c1');
      // Should snap to 2000 (within tolerance)
      expect(updatedIn, 2000);
      expect(updatedOut, 10000);
    });

    testWidgets('pressing M merges selected clip with next and calls onMerge', (tester) async {
      final c1 = model.Clip(
        id: 'c1',
        projectId: 'p1',
        sequence: 0,
        duration: const Duration(seconds: 4),
        playbackUrl: Uri.parse('https://stream/1'),
        createdAt: DateTime.utc(2024, 1, 1),
      );
      final c2 = model.Clip(
        id: 'c2',
        projectId: 'p1',
        sequence: 1,
        duration: const Duration(seconds: 6),
        playbackUrl: Uri.parse('https://stream/2'),
        createdAt: DateTime.utc(2024, 1, 1),
      );

      List<String>? merged;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TimelineEditor(
              clips: <model.Clip>[c1, c2],
              onTrimUpdate: (_, __, ___) async {},
              onMerge: (ids) async {
                merged = ids;
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Select first clip
      await tester.tap(find.byKey(const ValueKey<String>('clip-c1')));
      await tester.pump();

      // Send M key to trigger merge
      await tester.sendKeyDownEvent(LogicalKeyboardKey.keyM);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.keyM);
      await tester.pumpAndSettle();

      expect(merged, isNotNull);
      expect(merged, equals(<String>['c1', 'c2']));
    });
  });
}
