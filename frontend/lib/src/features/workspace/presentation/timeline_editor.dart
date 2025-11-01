import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../data/models/clip.dart';

class TimelineEditor extends StatefulWidget {
  const TimelineEditor({
    super.key,
    required this.clips,
    required this.onTrimUpdate,
    required this.onMerge,
    this.secondsPerPixel = 0.02, // 50px per second by default
  });

  final List<Clip> clips;
  final Future<void> Function(String clipId, int inPointMs, int outPointMs) onTrimUpdate;
  final Future<void> Function(List<String> clipIds) onMerge;

  /// Timeline scale - how many seconds are represented by a single pixel.
  final double secondsPerPixel;

  @override
  State<TimelineEditor> createState() => _TimelineEditorState();
}

class _TimelineEditorState extends State<TimelineEditor> {
  static const _trackHeight = 80.0;
  static const _handleWidth = 10.0;
  static const _snapTolerancePx = 6.0;

  String? _selectedClipId;
  bool _draggingLeft = false;
  bool _draggingRight = false;
  final Map<String, _WorkingTrim> _working = <String, _WorkingTrim>{};

  @override
  Widget build(BuildContext context) {
    final totalMs = widget.clips.fold<int>(0, (sum, c) => sum + c.duration.inMilliseconds);
    final timelineWidth = _msToPx(totalMs).clamp(320.0, double.infinity);

    return FocusScope(
      autofocus: true,
      child: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.keyM): const _MergeIntent(),
          LogicalKeySet(LogicalKeyboardKey.arrowLeft): const _NudgeIntent(-100),
          LogicalKeySet(LogicalKeyboardKey.arrowRight): const _NudgeIntent(100),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            _MergeIntent: CallbackAction<_MergeIntent>(
              onInvoke: (intent) => _onMergeSelection(),
            ),
            _NudgeIntent: CallbackAction<_NudgeIntent>(
              onInvoke: (intent) => _onNudge(intent.offsetMs),
            ),
          },
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              _buildTrackLabel(context, 'Primary'),
              SizedBox(
                height: _trackHeight,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: SizedBox(
                    width: timelineWidth,
                    child: Row(
                      children: _buildClipBars(context),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              _buildTrackLabel(context, 'Overlays'),
              Container(
                height: _trackHeight,
                alignment: Alignment.center,
                child: const Text('No overlays'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTrackLabel(BuildContext context, String label) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Text(label, style: theme.textTheme.labelLarge),
    );
  }

  List<Widget> _buildClipBars(BuildContext context) {
    final bars = <Widget>[];
    for (final clip in widget.clips) {
      final working = _working[clip.id] ?? _WorkingTrim.fromClip(clip);
      final effStart = working.inMs;
      final effEnd = working.outMs;
      final effDuration = effEnd - effStart;
      final width = math.max(_msToPx(effDuration), 16.0);

      bars.add(
        GestureDetector(
          onTap: () => setState(() => _selectedClipId = clip.id),
          child: Container(
            key: ValueKey<String>('clip-${clip.id}'),
            width: width,
            height: _trackHeight,
            margin: const EdgeInsets.symmetric(horizontal: 4),
            decoration: BoxDecoration(
              color: _selectedClipId == clip.id ? Colors.blue.shade300 : Colors.blue.shade200,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: _selectedClipId == clip.id ? Colors.blue.shade800 : Colors.blue.shade600,
                width: 1.5,
              ),
            ),
            child: Stack(
              children: <Widget>[
                // Transcript and quality label
                Positioned.fill(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        if (clip.transcriptSnippet != null)
                          Text(
                            clip.transcriptSnippet!,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white),
                          ),
                        const Spacer(),
                        if (clip.qualityScore != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.black26,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'Q: ${clip.qualityScore!.toStringAsFixed(2)}',
                              style: Theme.of(context)
                                  .textTheme
                                  .labelSmall
                                  ?.copyWith(color: Colors.white),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                // Markers
                ..._buildMarkers(clip, working, width),
                // Left handle
                _buildHandle(
                  alignment: Alignment.centerLeft,
                  onDragStart: () {
                    setState(() {
                      _selectedClipId = clip.id;
                      _draggingLeft = true;
                      _working[clip.id] = working;
                    });
                  },
                  onDragUpdate: (dx) {
                    final deltaMs = _pxToMs(dx);
                    final nextIn = (working.inMs + deltaMs).clamp(0, working.outMs - 1);
                    final snapped = _snapToMarkers(clip, nextIn);
                    setState(() => _working[clip.id] = working.copyWith(inMs: snapped));
                  },
                  onDragEnd: () => _commitTrim(clip.id),
                  key: ValueKey<String>('handle-left-${clip.id}'),
                ),
                // Right handle
                _buildHandle(
                  alignment: Alignment.centerRight,
                  onDragStart: () {
                    setState(() {
                      _selectedClipId = clip.id;
                      _draggingRight = true;
                      _working[clip.id] = working;
                    });
                  },
                  onDragUpdate: (dx) {
                    final deltaMs = _pxToMs(dx);
                    final nextOut = (working.outMs + deltaMs).clamp(working.inMs + 1, clip.duration.inMilliseconds);
                    final snapped = _snapToMarkers(clip, nextOut);
                    setState(() => _working[clip.id] = working.copyWith(outMs: snapped));
                  },
                  onDragEnd: () => _commitTrim(clip.id),
                  key: ValueKey<String>('handle-right-${clip.id}'),
                ),
              ],
            ),
          ),
        ),
      );
    }
    return bars;
  }

  Iterable<Widget> _buildMarkers(Clip clip, _WorkingTrim working, double width) sync* {
    if (clip.markers.isEmpty) return;
    final clipDurationMs = clip.duration.inMilliseconds;
    for (final m in clip.markers) {
      if (m < working.inMs || m > working.outMs) continue;
      final relative = (m - working.inMs) / (working.outMs - working.inMs);
      final dx = relative * width;
      yield Positioned(
        left: dx - 0.5,
        top: 0,
        bottom: 0,
        child: Container(width: 1, color: Colors.white70),
      );
    }
  }

  Widget _buildHandle({
    required Alignment alignment,
    required VoidCallback onDragStart,
    required void Function(double dx) onDragUpdate,
    required VoidCallback onDragEnd,
    Key? key,
  }) {
    return Align(
      alignment: alignment,
      child: GestureDetector(
        key: key,
        behavior: HitTestBehavior.translucent,
        onPanStart: (_) => onDragStart(),
        onPanUpdate: (details) => onDragUpdate(details.delta.dx),
        onPanEnd: (_) {
          _draggingLeft = false;
          _draggingRight = false;
          onDragEnd();
        },
        child: Container(
          width: _handleWidth,
          margin: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
      ),
    );
  }

  double _msToPx(int ms) => (ms / 1000.0) / widget.secondsPerPixel;
  int _pxToMs(double px) => (px * widget.secondsPerPixel * 1000.0).round();

  int _snapToMarkers(Clip clip, int ms) {
    if (clip.markers.isEmpty) return ms;
    final px = _msToPx(ms);
    double closestDelta = _snapTolerancePx + 1;
    int? snappedMs;
    for (final m in clip.markers) {
      final mPx = _msToPx(m);
      final delta = (mPx - px).abs();
      if (delta < closestDelta) {
        closestDelta = delta;
        snappedMs = m;
      }
    }
    return (snappedMs != null && closestDelta <= _snapTolerancePx) ? snappedMs : ms;
  }

  Future<void> _commitTrim(String clipId) async {
    final working = _working[clipId];
    if (working == null) return;
    await widget.onTrimUpdate(clipId, working.inMs, working.outMs);
  }

  Future<void> _onMergeSelection() async {
    final id = _selectedClipId;
    if (id == null) return;
    final index = widget.clips.indexWhere((c) => c.id == id);
    if (index == -1 || index >= widget.clips.length - 1) return;
    final nextId = widget.clips[index + 1].id;
    await widget.onMerge(<String>[id, nextId]);
  }

  Future<void> _onNudge(int offsetMs) async {
    final id = _selectedClipId;
    if (id == null) return;
    final working = _working[id] ?? _WorkingTrim.fromClip(
      widget.clips.firstWhere((c) => c.id == id),
    );
    if (_draggingLeft) {
      final next = (working.inMs + offsetMs).clamp(0, working.outMs - 1);
      setState(() => _working[id] = working.copyWith(inMs: next));
    } else if (_draggingRight) {
      final clip = widget.clips.firstWhere((c) => c.id == id);
      final next = (working.outMs + offsetMs).clamp(working.inMs + 1, clip.duration.inMilliseconds);
      setState(() => _working[id] = working.copyWith(outMs: next));
    }
  }
}

class _WorkingTrim {
  const _WorkingTrim({required this.inMs, required this.outMs});

  final int inMs;
  final int outMs;

  _WorkingTrim copyWith({int? inMs, int? outMs}) => _WorkingTrim(inMs: inMs ?? this.inMs, outMs: outMs ?? this.outMs);

  factory _WorkingTrim.fromClip(Clip c) {
    final inMs = c.inPointMs ?? 0;
    final outMs = c.outPointMs ?? c.duration.inMilliseconds;
    return _WorkingTrim(inMs: inMs, outMs: outMs);
  }
}

class _MergeIntent extends Intent {
  const _MergeIntent();
}

class _NudgeIntent extends Intent {
  const _NudgeIntent(this.offsetMs);
  final int offsetMs;
}
