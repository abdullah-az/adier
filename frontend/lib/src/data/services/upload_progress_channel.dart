import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/media_asset.dart';
import '../models/upload_progress_event.dart';

abstract class UploadProgressChannel {
  /// Subscribes to progress events for the given [assetId].
  Stream<UploadProgressEvent> watch(String assetId);

  /// Starts emitting progress events for [asset].
  void trackUpload(MediaAsset asset);

  /// Marks the upload as failed and notifies listeners.
  void markFailed(String assetId, {String? errorMessage});

  /// Stops emitting events for the given [assetId].
  void clear(String assetId);

  /// Disposes the channel and releases resources.
  void dispose();
}

class InMemoryUploadProgressChannel implements UploadProgressChannel {
  InMemoryUploadProgressChannel({this.tick = const Duration(milliseconds: 600)});

  final Duration tick;

  final Map<String, StreamController<UploadProgressEvent>> _controllers =
      <String, StreamController<UploadProgressEvent>>{};
  final Map<String, Timer> _timers = <String, Timer>{};

  @override
  Stream<UploadProgressEvent> watch(String assetId) {
    return _controllerFor(assetId).stream;
  }

  @override
  void trackUpload(MediaAsset asset) {
    final controller = _controllerFor(asset.id);
    _timers[asset.id]?.cancel();
    var progress = 0.02;
    controller.add(
      UploadProgressEvent(
        assetId: asset.id,
        status: MediaAssetStatus.uploading,
        progress: progress,
      ),
    );

    _timers[asset.id] = Timer.periodic(tick, (timer) {
      if (!controller.hasListener) {
        return;
      }

      progress = (progress + 0.14).clamp(0, 1);

      if (progress < 0.72) {
        controller.add(
          UploadProgressEvent(
            assetId: asset.id,
            status: MediaAssetStatus.uploading,
            progress: progress,
          ),
        );
        return;
      }

      if (progress < 0.98) {
        controller.add(
          UploadProgressEvent(
            assetId: asset.id,
            status: MediaAssetStatus.processing,
            progress: progress,
          ),
        );
        return;
      }

      controller.add(
        UploadProgressEvent(
          assetId: asset.id,
          status: MediaAssetStatus.ready,
          progress: 1,
        ),
      );
      timer.cancel();
      _timers.remove(asset.id);
    });
  }

  @override
  void markFailed(String assetId, {String? errorMessage}) {
    if (!_controllers.containsKey(assetId)) {
      return;
    }
    _timers.remove(assetId)?.cancel();
    _controllers[assetId]!.add(
      UploadProgressEvent(
        assetId: assetId,
        status: MediaAssetStatus.failed,
        progress: 0,
        errorMessage: errorMessage,
      ),
    );
  }

  @override
  void clear(String assetId) {
    _timers.remove(assetId)?.cancel();
    _controllers.remove(assetId)?.close();
  }

  @override
  void dispose() {
    for (final timer in _timers.values) {
      timer.cancel();
    }
    _timers.clear();
    for (final controller in _controllers.values) {
      controller.close();
    }
    _controllers.clear();
  }

  StreamController<UploadProgressEvent> _controllerFor(String assetId) {
    return _controllers.putIfAbsent(
      assetId,
      () => StreamController<UploadProgressEvent>.broadcast(
        onCancel: () {
          if (!_controllers.containsKey(assetId)) {
            return;
          }
        },
      ),
    );
  }
}
