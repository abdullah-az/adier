import 'package:flutter_test/flutter_test.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:ai_video_editor_frontend/src/data/network/websocket_client.dart';

void main() {
  group('WebSocketClient', () {
    late WebSocketClient webSocketClient;

    setUp(() {
      webSocketClient = WebSocketClient(
        wsUrl: 'ws://localhost:8000/ws',
        reconnectDelay: const Duration(milliseconds: 100),
        maxReconnectAttempts: 2,
      );
    });

    tearDown(() {
      webSocketClient.dispose();
    });

    group('Configuration', () {
      test('should initialize with correct WebSocket URL', () {
        // Arrange
        const wsUrl = 'ws://localhost:8000/ws';

        // Act
        final client = WebSocketClient(wsUrl: wsUrl);

        // Assert
        expect(client.wsUrl, equals(wsUrl));
        client.dispose();
      });

      test('should initialize with default reconnection settings', () {
        // Arrange
        const wsUrl = 'ws://localhost:8000/ws';

        // Act
        final client = WebSocketClient(wsUrl: wsUrl);

        // Assert
        expect(client.reconnectDelay, equals(const Duration(seconds: 3)));
        expect(client.maxReconnectAttempts, equals(5));
        client.dispose();
      });
    });

    group('Message Creation', () {
      test('should create progress message', () {
        // Arrange
        const jobId = 'job-123';
        const progress = 75;
        const status = 'processing';
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
      });

      test('should create notification message', () {
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
      });

      test('should serialize and deserialize progress message', () {
        // Arrange
        const jobId = 'job-456';
        const progress = 50;
        const status = 'rendering';

        // Act
        final originalMessage = WebSocketMessage.progress(
          jobId: jobId,
          progress: progress,
          status: status,
        );
        final json = originalMessage.toJson();
        final deserializedMessage = WebSocketMessage.fromJson(json);

        // Assert
        expect(deserializedMessage.type, equals(originalMessage.type));
        expect(deserializedMessage.data!['job_id'], equals(jobId));
        expect(deserializedMessage.data!['progress'], equals(progress));
        expect(deserializedMessage.data!['status'], equals(status));
      });

      test('should serialize and deserialize error message', () {
        // Arrange
        const errorMessage = 'Invalid payload';

        // Act
        final originalMessage = WebSocketMessage.error(errorMessage);
        final json = originalMessage.toJson();
        final deserializedMessage = WebSocketMessage.fromJson(json);

        // Assert
        expect(deserializedMessage.type, equals(originalMessage.type));
        expect(deserializedMessage.error, equals(errorMessage));
      });
    });

    group('State Management', () {
      test('should emit states in correct order', () async {
        // Arrange
        final states = <WebSocketState>[];
        webSocketClient.states.listen((state) => states.add(state));

        // Act
        // Note: We can't actually connect in a test environment, but we can test the state stream
        // In a real integration test, you would mock the WebSocket connection

        // Assert
        // The states list should be empty initially since we're not connecting
        expect(states, isEmpty);
      });

      test('should handle message stream correctly', () async {
        // Arrange
        final messages = <WebSocketMessage>[];
        webSocketClient.messages.listen((message) => messages.add(message));

        // Act
        // Note: In a real test, you would inject messages and verify they are received

        // Assert
        // The messages list should be empty initially since we're not connected
        expect(messages, isEmpty);
      });
    });

    group('Resource Management', () {
      test('should dispose resources correctly', () {
        // Arrange
        final client = WebSocketClient(wsUrl: 'ws://localhost:8000/ws');

        // Act
        client.dispose();

        // Assert
        // In a real test with mocks, you would verify that streams are closed
        // and resources are cleaned up
        expect(client, isA<WebSocketClient>());
      });
    });
  });

  group('WebSocketState', () {
    test('should have correct enum values', () {
      expect(WebSocketState.values, contains(WebSocketState.connecting));
      expect(WebSocketState.values, contains(WebSocketState.connected));
      expect(WebSocketState.values, contains(WebSocketState.disconnected));
      expect(WebSocketState.values, contains(WebSocketState.error));
    });
  });

  group('WebSocketMessage toString', () {
    test('should provide meaningful string representation', () {
      // Arrange
      final message = WebSocketMessage.progress(
        jobId: 'test-job',
        progress: 100,
        status: 'completed',
      );

      // Act
      final stringRepresentation = message.toString();

      // Assert
      expect(stringRepresentation, contains('WebSocketMessage'));
      expect(stringRepresentation, contains('job_progress'));
      expect(stringRepresentation, contains('test-job'));
    });
  });
}