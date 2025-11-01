import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/media_asset.dart';
import '../models/upload_request.dart';
import '../repositories/media_asset_repository.dart';

class UploadController extends StateNotifier<AsyncValue<MediaAsset?>> {
  UploadController(this._repository)
      : super(const AsyncValue<MediaAsset?>.data(null));

  final MediaAssetRepository _repository;

  Future<void> initiateUpload({
    required String projectId,
    required UploadRequest request,
  }) async {
    state = const AsyncValue<MediaAsset?>.loading();
    try {
      final asset = await _repository.initiateUpload(
        projectId: projectId,
        request: request,
      );
      state = AsyncValue<MediaAsset?>.data(asset);
    } catch (error, stackTrace) {
      state = AsyncValue<MediaAsset?>.error(error, stackTrace);
    }
  }

  void reset() {
    state = const AsyncValue<MediaAsset?>.data(null);
  }
}
