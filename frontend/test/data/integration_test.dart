import 'package:flutter_test/flutter_test.dart';

import 'package:ai_video_editor_frontend/src/data/index.dart';
import 'package:ai_video_editor_frontend/src/data/config.dart';
import 'package:ai_video_editor_frontend/src/data/models/index.dart';

void main() {
  group('Data Layer Integration Tests', () {
    late DataLayer dataLayer;

    setUp(() {
      dataLayer = DataLayer(
        baseUrl: DataConfig.developmentBaseUrl,
        enableLogging: false,
      );
    });

    tearDown(() {
      dataLayer.dispose();
    });

    group('Model Serialization', () {
      test('should serialize and deserialize Project correctly', () {
        // Arrange
        final now = DateTime.now();
        final project = Project(
          id: 'test-project-123',
          createdAt: now,
          updatedAt: now,
          name: 'Test Project',
          description: 'A test project',
          status: ProjectStatus.active,
          storagePath: '/storage/test',
        );

        // Act
        final json = project.toJson();
        final deserialized = Project.fromJson(json);

        // Assert
        expect(deserialized.id, equals(project.id));
        expect(deserialized.name, equals(project.name));
        expect(deserialized.description, equals(project.description));
        expect(deserialized.status, equals(project.status));
        expect(deserialized.storagePath, equals(project.storagePath));
      });

      test('should serialize and deserialize MediaAsset correctly', () {
        // Arrange
        final asset = MediaAsset(
          id: 'test-asset-456',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          projectId: 'test-project-123',
          type: MediaAssetType.source,
          filename: 'test.mp4',
          filePath: '/storage/test.mp4',
          mimeType: 'video/mp4',
          sizeBytes: 1024000,
          durationSeconds: 30.5,
          checksum: 'abc123',
          analysisCache: {'resolution': '1920x1080'},
        );

        // Act
        final json = asset.toJson();
        final deserialized = MediaAsset.fromJson(json);

        // Assert
        expect(deserialized.id, equals(asset.id));
        expect(deserialized.projectId, equals(asset.projectId));
        expect(deserialized.type, equals(asset.type));
        expect(deserialized.filename, equals(asset.filename));
        expect(deserialized.filePath, equals(asset.filePath));
        expect(deserialized.mimeType, equals(asset.mimeType));
        expect(deserialized.sizeBytes, equals(asset.sizeBytes));
        expect(deserialized.durationSeconds, equals(asset.durationSeconds));
        expect(deserialized.checksum, equals(asset.checksum));
        expect(deserialized.analysisCache, equals(asset.analysisCache));
      });

      test('should serialize and deserialize ProcessingJob correctly', () {
        // Arrange
        final job = ProcessingJob(
          id: 'test-job-789',
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
          clipVersionId: 'test-version-123',
          jobType: ProcessingJobType.render,
          status: ProcessingJobStatus.inProgress,
          queueName: 'high_priority',
          priority: 5,
          payload: {'format': 'mp4', 'quality': 'high'},
          resultPayload: null,
          errorMessage: null,
          startedAt: DateTime.now(),
          completedAt: null,
        );

        // Act
        final json = job.toJson();
        final deserialized = ProcessingJob.fromJson(json);

        // Assert
        expect(deserialized.id, equals(job.id));
        expect(deserialized.clipVersionId, equals(job.clipVersionId));
        expect(deserialized.jobType, equals(job.jobType));
        expect(deserialized.status, equals(job.status));
        expect(deserialized.queueName, equals(job.queueName));
        expect(deserialized.priority, equals(job.priority));
        expect(deserialized.payload, equals(job.payload));
        expect(deserialized.resultPayload, equals(job.resultPayload));
        expect(deserialized.errorMessage, equals(job.errorMessage));
        expect(deserialized.startedAt, isNotNull);
        expect(deserialized.completedAt, equals(job.completedAt));
      });
    });

    group('Enum Conversion', () {
      test('should convert all enums correctly', () {
        // Test ProjectStatus
        expect(ProjectStatus.fromString('active'), equals(ProjectStatus.active));
        expect(ProjectStatus.active.value, equals('active'));

        // Test MediaAssetType
        expect(MediaAssetType.fromString('generated'), equals(MediaAssetType.generated));
        expect(MediaAssetType.generated.value, equals('generated'));

        // Test ClipStatus
        expect(ClipStatus.fromString('approved'), equals(ClipStatus.approved));
        expect(ClipStatus.approved.value, equals('approved'));

        // Test ClipVersionStatus
        expect(ClipVersionStatus.fromString('ready'), equals(ClipVersionStatus.ready));
        expect(ClipVersionStatus.ready.value, equals('ready'));

        // Test ProcessingJobStatus
        expect(ProcessingJobStatus.fromString('completed'), equals(ProcessingJobStatus.completed));
        expect(ProcessingJobStatus.completed.value, equals('completed'));

        // Test ProcessingJobType
        expect(ProcessingJobType.fromString('transcribe'), equals(ProcessingJobType.transcribe));
        expect(ProcessingJobType.transcribe.value, equals('transcribe'));

        // Test PresetCategory
        expect(PresetCategory.fromString('audio'), equals(PresetCategory.audio));
        expect(PresetCategory.audio.value, equals('audio'));
      });
    });

    group('WebSocket Messages', () {
      test('should create and serialize progress message', () {
        // Arrange
        const jobId = 'test-job-123';
        const progress = 75;
        const status = 'rendering';
        final metadata = {'frame': 1000, 'total_frames': 1333};

        // Act
        final message = WebSocketMessage.progress(
          jobId: jobId,
          progress: progress,
          status: status,
          metadata: metadata,
        );

        // Assert
        expect(message.type, equals('job_progress'));
        expect(message.data!['job_id'], equals(jobId));
        expect(message.data!['progress'], equals(progress));
        expect(message.data!['status'], equals(status));
        expect(message.data!['metadata'], equals(metadata));

        // Test serialization
        final json = message.toJson();
        expect(json['type'], equals('job_progress'));
        expect(json['data']['job_id'], equals(jobId));

        // Test deserialization
        final deserialized = WebSocketMessage.fromJson(json);
        expect(deserialized.type, equals(message.type));
        expect(deserialized.data!['job_id'], equals(jobId));
      });

      test('should create and serialize notification message', () {
        // Arrange
        const title = 'Job Completed';
        const message = 'Your video has been processed successfully';
        const level = 'success';

        // Act
        final notification = WebSocketMessage.notification(
          title: title,
          message: message,
          level: level,
        );

        // Assert
        expect(notification.type, equals('notification'));
        expect(notification.data!['title'], equals(title));
        expect(notification.data!['message'], equals(message));
        expect(notification.data!['level'], equals(level));
      });

      test('should create error message', () {
        // Arrange
        const errorMessage = 'Connection failed';

        // Act
        final message = WebSocketMessage.error(errorMessage);

        // Assert
        expect(message.type, equals('error'));
        expect(message.error, equals(errorMessage));
        expect(message.data, isNull);
      });
    });

    group('Data Layer Configuration', () {
      test('should initialize with correct configuration', () {
        // Assert
        expect(dataLayer.apiClient.baseUrl, equals(DataConfig.developmentBaseUrl));
        expect(dataLayer.webSocketClient.wsUrl, equals('ws://localhost:8000/api'));
        expect(dataLayer.healthService, isNotNull);
        expect(dataLayer.projectsService, isNotNull);
        expect(dataLayer.assetsService, isNotNull);
        expect(dataLayer.clipsService, isNotNull);
        expect(dataLayer.jobsService, isNotNull);
        expect(dataLayer.presetsService, isNotNull);
      });

      test('should handle authentication methods', () {
        // Act & Assert - Should not throw
        dataLayer.setAuthToken('test-token');
        dataLayer.clearAuthToken();
      });

      test('should handle WebSocket methods', () async {
        // Act & Assert - Should not throw (may fail to connect in test env)
        try {
          await dataLayer.connectWebSocket();
        } catch (e) {
          // Expected in test environment
        }
        dataLayer.disconnectWebSocket();
      });
    });

    group('Request/Response Models', () {
      test('should handle ProjectCreateRequest', () {
        // Arrange
        const request = ProjectCreateRequest(
          name: 'New Project',
          description: 'A new test project',
          status: ProjectStatus.active,
          storagePath: '/storage/new',
        );

        // Act
        final json = request.toJson();
        final deserialized = ProjectCreateRequest.fromJson(json);

        // Assert
        expect(deserialized.name, equals(request.name));
        expect(deserialized.description, equals(request.description));
        expect(deserialized.status, equals(request.status));
        expect(deserialized.storagePath, equals(request.storagePath));
      });

      test('should handle ProjectUpdateRequest', () {
        // Arrange
        final request = ProjectUpdateRequest(
          name: 'Updated Project',
          description: 'Updated description',
          status: ProjectStatus.archived,
        );

        // Act
        final json = request.toJson();
        final deserialized = ProjectUpdateRequest.fromJson(json);

        // Assert
        expect(deserialized.name, equals(request.name));
        expect(deserialized.description, equals(request.description));
        expect(deserialized.status, equals(request.status));
        expect(deserialized.storagePath, isNull);
      });
    });

    group('Health Service Models', () {
      test('should handle HealthResponse', () {
        // Arrange
        final json = {
          'status': 'ok',
          'app': 'test-app',
          'environment': 'test',
        };

        // Act
        final response = HealthResponse.fromJson(json);

        // Assert
        expect(response.status, equals('ok'));
        expect(response.app, equals('test-app'));
        expect(response.environment, equals('test'));

        // Test serialization
        final serialized = response.toJson();
        expect(serialized['status'], equals('ok'));
        expect(serialized['app'], equals('test-app'));
        expect(serialized['environment'], equals('test'));
      });

      test('should handle QueueStatus', () {
        // Arrange
        final json = {
          'connected': true,
          'broker_url': 'localhost:6379',
          'redis_version': '7.0.0',
          'connected_clients': 10,
        };

        // Act
        final queueStatus = QueueStatus.fromJson(json);

        // Assert
        expect(queueStatus.connected, isTrue);
        expect(queueStatus.brokerUrl, equals('localhost:6379'));
        expect(queueStatus.redisVersion, equals('7.0.0'));
        expect(queueStatus.connectedClients, equals(10));
        expect(queueStatus.error, isNull);
      });

      test('should handle QueueStatus with error', () {
        // Arrange
        final json = {
          'connected': false,
          'broker_url': 'localhost:6379',
          'error': 'Connection refused',
        };

        // Act
        final queueStatus = QueueStatus.fromJson(json);

        // Assert
        expect(queueStatus.connected, isFalse);
        expect(queueStatus.brokerUrl, equals('localhost:6379'));
        expect(queueStatus.error, equals('Connection refused'));
        expect(queueStatus.redisVersion, isNull);
        expect(queueStatus.connectedClients, isNull);
      });
    });
  });
}