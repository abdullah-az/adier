import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cto/l10n/app_localizations.dart';
import 'package:cto/src/core/utils/timeline_utils.dart';
import 'package:cto/src/data/models/timeline_segment.dart';
import 'package:cto/src/features/editor/timeline/timeline_controller.dart';
import 'package:cto/src/features/editor/timeline/timeline_editor.dart';

class _TestTimelineController extends StateNotifier<AsyncValue<TimelineSummary>> {
  _TestTimelineController(TimelineSummary summary)
      : super(AsyncValue.data(summary));
}

void main() {
  final summary = buildTimelineSummary([
    const TimelineSegment(id: 'a', label: 'Intro', startMs: 0, endMs: 1500, color: Colors.blue),
    const TimelineSegment(id: 'b', label: 'Main', startMs: 1500, endMs: 4000, color: Colors.red),
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
            height: 400,
            child: TimelineEditor(),
          ),
        ),
      ),
    );
  }

  testWidgets('TimelineEditor renders segments', (tester) async {
    await tester.pumpWidget(_buildWidget());
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('timeline_list')), findsOneWidget);
    expect(find.byType(ListTile), findsNWidgets(summary.segments.length));
    expect(find.textContaining('Total duration'), findsOneWidget);
  });
}
