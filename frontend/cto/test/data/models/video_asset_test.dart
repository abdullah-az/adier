import 'package:cto/src/data/models/video_asset.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('VideoAsset Model', () {
    test('should deserialize from JSON correctly', () {
      final json = {
        'id': 'asset_123',
        'project_id': 'proj_123',
        'filename': 'video.mp4',
        'original_filename': 'my_video.mp4',
        'relative_path': 'uploads/project_123/video.mp4',
        'checksum': 'abc123',
        'size_bytes': 1048576,
        'mime_type': 'video/mp4',
        'category': 'source',
        'status': 'uploaded',
        'thumbnail_path': 'thumbnails/video.jpg',
        'source_asset_ids': ['asset_100'],
        'metadata': {'duration': 120},
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
      };

      final asset = VideoAsset.fromJson(json);

      expect(asset.id, 'asset_123');
      expect(asset.projectId, 'proj_123');
      expect(asset.filename, 'video.mp4');
      expect(asset.originalFilename, 'my_video.mp4');
      expect(asset.sizeBytes, 1048576);
      expect(asset.category, VideoAssetCategory.source);
    });

    test('should serialize to JSON correctly', () {
      final asset = VideoAsset(
        id: 'asset_123',
        projectId: 'proj_123',
        filename: 'video.mp4',
        originalFilename: 'my_video.mp4',
        relativePath: 'uploads/project_123/video.mp4',
        checksum: 'abc123',
        sizeBytes: 1048576,
        mimeType: 'video/mp4',
        createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
        updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
      );

      final json = asset.toJson();

      expect(json['id'], 'asset_123');
      expect(json['project_id'], 'proj_123');
      expect(json['size_bytes'], 1048576);
    });
  });

  group('VideoUploadResponse Model', () {
    test('should deserialize from JSON correctly', () {
      final json = {
        'asset_id': 'asset_123',
        'filename': 'video.mp4',
        'original_filename': 'my_video.mp4',
        'size_bytes': 1048576,
        'project_id': 'proj_123',
        'status': 'uploaded',
        'message': 'Upload successful',
      };

      final response = VideoUploadResponse.fromJson(json);

      expect(response.assetId, 'asset_123');
      expect(response.filename, 'video.mp4');
      expect(response.message, 'Upload successful');
    });
  });
}
