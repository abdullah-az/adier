import 'package:flutter_riverpod/flutter_riverpod.dart';

class SubtitleEntry {
  const SubtitleEntry({
    required this.id,
    required this.start,
    required this.end,
    required this.text,
  });

  final String id;
  final Duration start;
  final Duration end;
  final String text;

  SubtitleEntry copyWith({
    String? id,
    Duration? start,
    Duration? end,
    String? text,
  }) {
    return SubtitleEntry(
      id: id ?? this.id,
      start: start ?? this.start,
      end: end ?? this.end,
      text: text ?? this.text,
    );
  }
}

final subtitleControllerProvider =
    StateNotifierProvider<SubtitleController, List<SubtitleEntry>>(
  (ref) => SubtitleController(),
);

class SubtitleController extends StateNotifier<List<SubtitleEntry>> {
  SubtitleController({List<SubtitleEntry>? initialEntries})
      : _counter = initialEntries?.length ?? _defaultEntries.length,
        super(initialEntries ?? _defaultEntries);

  static final List<SubtitleEntry> _defaultEntries = [
    const SubtitleEntry(
      id: 'subtitle-1',
      start: Duration(seconds: 0),
      end: Duration(seconds: 2),
      text: 'Welcome!',
    ),
    const SubtitleEntry(
      id: 'subtitle-2',
      start: Duration(seconds: 2),
      end: Duration(seconds: 5),
      text: 'Let\'s get started.',
    ),
  ];

  int _counter;

  void addEntry({
    required Duration start,
    required Duration end,
    required String text,
  }) {
    _counter += 1;
    final entry = SubtitleEntry(
      id: 'subtitle-$_counter',
      start: start,
      end: end,
      text: text,
    );
    state = [
      ...state,
      entry,
    ];
  }

  void updateEntry(
    String id, {
    Duration? start,
    Duration? end,
    String? text,
  }) {
    state = [
      for (final entry in state)
        if (entry.id == id)
          entry.copyWith(
            start: start,
            end: end,
            text: text,
          )
        else
          entry,
    ];
  }
}
