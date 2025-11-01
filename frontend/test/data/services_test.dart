import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:ai_video_editor_frontend/src/data/services/health_service.dart';
import 'package:ai_video_editor_frontend/src/data/network/api_client.dart';
import 'package:ai_video_editor_frontend/src/data/network/exceptions.dart';

import 'services_test.mocks.dart';

@GenerateMocks([ApiClient])
void main() {
  group('HealthService', () {
    late HealthService healthService;
    late MockApiClient mockApiClient;

    setUp(() {
      mockApiClient = MockApiClient();
      healthService = HealthService(mockApiClient);
    });

    group('checkHealth', () {
      test('should return health response on success', () async {
        // Arrange
        final responseData = {
          'status': 'ok',
          'app': 'ai-video-editor',
          'environment': 'development',
        };
        
        when(mockApiClient.get<Map<String, dynamic>>('/health'))
            .thenAnswer((_) async => Response<Map<String, dynamic>>(
              data: responseData,
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health'),
            ));

        // Act
        final result = await healthService.checkHealth();

        // Assert
        expect(result.status, equals('ok'));
        expect(result.app, equals('ai-video-editor'));
        expect(result.environment, equals('development'));
        verify(mockApiClient.get<Map<String, dynamic>>('/health')).called(1);
      });

      test('should throw ApiException on failure', () async {
        // Arrange
        final apiException = ApiException.connectionError();
        when(mockApiClient.get<Map<String, dynamic>>('/health'))
            .thenThrow(apiException);

        // Act & Assert
        expect(
          () => healthService.checkHealth(),
          throwsA(isA<ApiException>()),
        );
        verify(mockApiClient.get<Map<String, dynamic>>('/health')).called(1);
      });
    });

    group('checkDiagnostics', () {
      test('should return diagnostics response on success', () async {
        // Arrange
        final responseData = {
          'status': 'ok',
          'app': 'ai-video-editor',
          'environment': 'development',
          'queue': {
            'connected': true,
            'broker_url': 'localhost:6379',
            'redis_version': '7.0.0',
            'connected_clients': 10,
          },
        };
        
        when(mockApiClient.get<Map<String, dynamic>>('/health/diagnostics'))
            .thenAnswer((_) async => Response<Map<String, dynamic>>(
              data: responseData,
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health/diagnostics'),
            ));

        // Act
        final result = await healthService.checkDiagnostics();

        // Assert
        expect(result.status, equals('ok'));
        expect(result.app, equals('ai-video-editor'));
        expect(result.environment, equals('development'));
        expect(result.queue.connected, isTrue);
        expect(result.queue.brokerUrl, equals('localhost:6379'));
        expect(result.queue.redisVersion, equals('7.0.0'));
        expect(result.queue.connectedClients, equals(10));
        verify(mockApiClient.get<Map<String, dynamic>>('/health/diagnostics')).called(1);
      });

      test('should handle queue connection error', () async {
        // Arrange
        final responseData = {
          'status': 'degraded',
          'app': 'ai-video-editor',
          'environment': 'development',
          'queue': {
            'connected': false,
            'broker_url': 'localhost:6379',
            'error': 'Connection refused',
          },
        };
        
        when(mockApiClient.get<Map<String, dynamic>>('/health/diagnostics'))
            .thenAnswer((_) async => Response<Map<String, dynamic>>(
              data: responseData,
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health/diagnostics'),
            ));

        // Act
        final result = await healthService.checkDiagnostics();

        // Assert
        expect(result.status, equals('degraded'));
        expect(result.queue.connected, isFalse);
        expect(result.queue.error, equals('Connection refused'));
        verify(mockApiClient.get<Map<String, dynamic>>('/health/diagnostics')).called(1);
      });
    });
  });

  group('HealthResponse', () {
    test('should create from JSON', () {
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
    });

    test('should serialize to JSON', () {
      // Arrange
      const response = HealthResponse(
        status: 'ok',
        app: 'test-app',
        environment: 'test',
      );

      // Act
      final json = response.toJson();

      // Assert
      expect(json['status'], equals('ok'));
      expect(json['app'], equals('test-app'));
      expect(json['environment'], equals('test'));
    });

    test('should provide meaningful toString', () {
      // Arrange
      const response = HealthResponse(
        status: 'ok',
        app: 'test-app',
        environment: 'test',
      );

      // Act
      final stringRepresentation = response.toString();

      // Assert
      expect(stringRepresentation, contains('HealthResponse'));
      expect(stringRepresentation, contains('ok'));
      expect(stringRepresentation, contains('test-app'));
      expect(stringRepresentation, contains('test'));
    });
  });

  group('DiagnosticsResponse', () {
    test('should create from JSON', () {
      // Arrange
      final json = {
        'status': 'ok',
        'app': 'test-app',
        'environment': 'test',
        'queue': {
          'connected': true,
          'broker_url': 'localhost:6379',
          'redis_version': '7.0.0',
          'connected_clients': 5,
        },
      };

      // Act
      final response = DiagnosticsResponse.fromJson(json);

      // Assert
      expect(response.status, equals('ok'));
      expect(response.app, equals('test-app'));
      expect(response.environment, equals('test'));
      expect(response.queue.connected, isTrue);
      expect(response.queue.brokerUrl, equals('localhost:6379'));
      expect(response.queue.redisVersion, equals('7.0.0'));
      expect(response.queue.connectedClients, equals(5));
    });

    test('should serialize to JSON', () {
      // Arrange
      final queueStatus = QueueStatus(
        connected: true,
        brokerUrl: 'localhost:6379',
        redisVersion: '7.0.0',
        connectedClients: 5,
      );
      final response = DiagnosticsResponse(
        status: 'ok',
        app: 'test-app',
        environment: 'test',
        queue: queueStatus,
      );

      // Act
      final json = response.toJson();

      // Assert
      expect(json['status'], equals('ok'));
      expect(json['app'], equals('test-app'));
      expect(json['environment'], equals('test'));
      expect(json['queue']['connected'], isTrue);
      expect(json['queue']['broker_url'], equals('localhost:6379'));
    });
  });

  group('QueueStatus', () {
    test('should create from JSON with all fields', () {
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

    test('should create from JSON with error', () {
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

    test('should serialize to JSON', () {
      // Arrange
      const queueStatus = QueueStatus(
        connected: true,
        brokerUrl: 'localhost:6379',
        redisVersion: '7.0.0',
        connectedClients: 10,
      );

      // Act
      final json = queueStatus.toJson();

      // Assert
      expect(json['connected'], isTrue);
      expect(json['broker_url'], equals('localhost:6379'));
      expect(json['redis_version'], equals('7.0.0'));
      expect(json['connected_clients'], equals(10));
      expect(json['error'], isNull);
    });
  });
}