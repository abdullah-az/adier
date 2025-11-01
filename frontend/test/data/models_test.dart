import 'package:flutter_test/flutter_test.dart';

import 'package:ai_video_editor_frontend/src/data/models/index.dart';

void main() {
  group('Project Model', () {
    test('should create Project from JSON', () {
      // Arrange
      final json = {
        'id': 'project-123',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'name': 'Test Project',
        'description': 'A test project',
        'status': 'active',
        'storage_path': '/storage/projects/123',
      };

      // Act
      final project = Project.fromJson(json);

      // Assert
      expect(project.id, equals('project-123'));
      expect(project.name, equals('Test Project'));
      expect(project.description, equals('A test project'));
      expect(project.status, equals(ProjectStatus.active));
      expect(project.storagePath, equals('/storage/projects/123'));
      expect(project.createdAt, isA<DateTime>());
      expect(project.updatedAt, isA<DateTime>());
    });

    test('should serialize Project to JSON', () {
      // Arrange
      final project = Project(
        id: 'project-456',
        createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
        updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        name: 'Another Project',
        status: ProjectStatus.archived,
      );

      // Act
      final json = project.toJson();

      // Assert
      expect(json['id'], equals('project-456'));
      expect(json['name'], equals('Another Project'));
      expect(json['status'], equals('archived'));
      expect(json['description'], isNull);
      expect(json['storage_path'], isNull);
    });

    test('should copy Project with new values', () {
      // Arrange
      final original = Project(
        id: 'project-123',
        createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
        updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        name: 'Original Project',
        status: ProjectStatus.active,
      );

      // Act
      final updated = original.copyWith(
        name: 'Updated Project',
        description: 'Updated description',
        status: ProjectStatus.archived,
      );

      // Assert
      expect(updated.id, equals(original.id));
      expect(updated.name, equals('Updated Project'));
      expect(updated.description, equals('Updated description'));
      expect(updated.status, equals(ProjectStatus.archived));
      expect(updated.createdAt, equals(original.createdAt));
      expect(updated.updatedAt, equals(original.updatedAt));
    });
  });

  group('MediaAsset Model', () {
    test('should create MediaAsset from JSON', () {
      // Arrange
      final json = {
        'id': 'asset-123',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'project_id': 'project-123',
        'type': 'source',
        'filename': 'video.mp4',
        'file_path': '/storage/assets/video.mp4',
        'mime_type': 'video/mp4',
        'size_bytes': 1024000,
        'duration_seconds': 30.5,
        'checksum': 'abc123',
        'analysis_cache': {'resolution': '1920x1080'},
      };

      // Act
      final asset = MediaAsset.fromJson(json);

      // Assert
      expect(asset.id, equals('asset-123'));
      expect(asset.projectId, equals('project-123'));
      expect(asset.type, equals(MediaAssetType.source));
      expect(asset.filename, equals('video.mp4'));
      expect(asset.filePath, equals('/storage/assets/video.mp4'));
      expect(asset.mimeType, equals('video/mp4'));
      expect(asset.sizeBytes, equals(1024000));
      expect(asset.durationSeconds, equals(30.5));
      expect(asset.checksum, equals('abc123'));
      expect(asset.analysisCache, equals({'resolution': '1920x1080'}));
    });
  });

  group('Clip Model', () {
    test('should create Clip from JSON', () {
      // Arrange
      final json = {
        'id': 'clip-123',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'project_id': 'project-123',
        'source_asset_id': 'asset-123',
        'title': 'Test Clip',
        'description': 'A test clip',
        'status': 'draft',
        'start_time': 10.5,
        'end_time': 20.5,
      };

      // Act
      final clip = Clip.fromJson(json);

      // Assert
      expect(clip.id, equals('clip-123'));
      expect(clip.projectId, equals('project-123'));
      expect(clip.sourceAssetId, equals('asset-123'));
      expect(clip.title, equals('Test Clip'));
      expect(clip.description, equals('A test clip'));
      expect(clip.status, equals(ClipStatus.draft));
      expect(clip.startTime, equals(10.5));
      expect(clip.endTime, equals(20.5));
    });
  });

  group('ProcessingJob Model', () {
    test('should create ProcessingJob from JSON', () {
      // Arrange
      final json = {
        'id': 'job-123',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'clip_version_id': 'version-123',
        'job_type': 'render',
        'status': 'in_progress',
        'queue_name': 'high_priority',
        'priority': 5,
        'payload': {'format': 'mp4', 'quality': 'high'},
        'result_payload': {'output_path': '/output/rendered.mp4'},
        'error_message': null,
        'started_at': '2024-01-01T00:05:00Z',
        'completed_at': null,
      };

      // Act
      final job = ProcessingJob.fromJson(json);

      // Assert
      expect(job.id, equals('job-123'));
      expect(job.clipVersionId, equals('version-123'));
      expect(job.jobType, equals(ProcessingJobType.render));
      expect(job.status, equals(ProcessingJobStatus.inProgress));
      expect(job.queueName, equals('high_priority'));
      expect(job.priority, equals(5));
      expect(job.payload, equals({'format': 'mp4', 'quality': 'high'}));
      expect(job.resultPayload, equals({'output_path': '/output/rendered.mp4'}));
      expect(job.errorMessage, isNull);
      expect(job.startedAt, isA<DateTime>());
      expect(job.completedAt, isNull);
    });
  });

  group('PlatformPreset Model', () {
    test('should create PlatformPreset from JSON', () {
      // Arrange
      final json = {
        'id': 'preset-123',
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
        'key': 'youtube_1080p',
        'name': 'YouTube 1080p',
        'category': 'export',
        'description': 'Export preset for YouTube 1080p videos',
        'configuration': {
          'resolution': '1920x1080',
          'fps': 30,
          'bitrate': '8000k',
          'codec': 'h264',
        },
      };

      // Act
      final preset = PlatformPreset.fromJson(json);

      // Assert
      expect(preset.id, equals('preset-123'));
      expect(preset.key, equals('youtube_1080p'));
      expect(preset.name, equals('YouTube 1080p'));
      expect(preset.category, equals(PresetCategory.export));
      expect(preset.description, equals('Export preset for YouTube 1080p videos'));
      expect(preset.configuration, equals({
        'resolution': '1920x1080',
        'fps': 30,
        'bitrate': '8000k',
        'codec': 'h264',
      }));
    });
  });

  group('Enums', () {
    test('should convert ProjectStatus from string', () {
      expect(ProjectStatus.fromString('active'), equals(ProjectStatus.active));
      expect(ProjectStatus.fromString('archived'), equals(ProjectStatus.archived));
      expect(ProjectStatus.fromString('invalid'), equals(ProjectStatus.active)); // default
    });

    test('should convert MediaAssetType from string', () {
      expect(MediaAssetType.fromString('source'), equals(MediaAssetType.source));
      expect(MediaAssetType.fromString('generated'), equals(MediaAssetType.generated));
      expect(MediaAssetType.fromString('thumbnail'), equals(MediaAssetType.thumbnail));
      expect(MediaAssetType.fromString('transcript'), equals(MediaAssetType.transcript));
      expect(MediaAssetType.fromString('invalid'), equals(MediaAssetType.source)); // default
    });

    test('should convert ProcessingJobType from string', () {
      expect(ProcessingJobType.fromString('ingest'), equals(ProcessingJobType.ingest));
      expect(ProcessingJobType.fromString('transcribe'), equals(ProcessingJobType.transcribe));
      expect(ProcessingJobType.fromString('generate_clip'), equals(ProcessingJobType.generateClip));
      expect(ProcessingJobType.fromString('render'), equals(ProcessingJobType.render));
      expect(ProcessingJobType.fromString('export'), equals(ProcessingJobType.export));
      expect(ProcessingJobType.fromString('invalid'), equals(ProcessingJobType.ingest)); // default
    });

    test('should convert ProcessingJobStatus from string', () {
      expect(ProcessingJobStatus.fromString('pending'), equals(ProcessingJobStatus.pending));
      expect(ProcessingJobStatus.fromString('queued'), equals(ProcessingJobStatus.queued));
      expect(ProcessingJobStatus.fromString('in_progress'), equals(ProcessingJobStatus.inProgress));
      expect(ProcessingJobStatus.fromString('completed'), equals(ProcessingJobStatus.completed));
      expect(ProcessingJobStatus.fromString('failed'), equals(ProcessingJobStatus.failed));
      expect(ProcessingJobStatus.fromString('cancelled'), equals(ProcessingJobStatus.cancelled));
      expect(ProcessingJobStatus.fromString('invalid'), equals(ProcessingJobStatus.pending)); // default
    });
  });
}