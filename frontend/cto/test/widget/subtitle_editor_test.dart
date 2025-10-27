import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/models/timeline_segment.dart';
import 'package:cto/src/features/editor/subtitle/subtitle_editor.dart';
import 'package:cto/src/features/editor/timeline/timeline_controller.dart';

class _TestTimelineController extends StateNotifier<AsyncValue<TimelineSummary>> {
  _TestTimelineController(TimelineSummary summary)
      : super(AsyncValue.data(summary));
}

void main() {
  final summary = buildTimelineSummary([
    const TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1500),
    const TimelineSegment(id: 'b', label: 'Main', startMs: 1500, endMs: 3500),
  ]);

  Widget _buildWidget() {
    return ProviderScope(
      overrides: [
        timelineControllerProvider.overrideWith((ref) => _TestTimelineController(summary)),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: const Scaffold(
          body: SizedBox(
            height: 300,
            child: SubtitleEditor(),
          ),
        ),
      ),
    );
  }

  testWidgets('SubtitleEditor lists cues', (tester) async {
    await tester.pumpWidget(_buildWidget());
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('subtitle_list')), findsOneWidget);
    expect(find.byType(ListTile), findsNWidgets(summary.cues.length));
  });
}
