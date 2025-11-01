import 'package:flutter_test/flutter_test.dart';

import 'package:ai_video_editor_frontend/src/data/index.dart';
import 'package:ai_video_editor_frontend/src/data/config.dart';

void main() {
  group('DataLayer Configuration', () {
    test('should initialize with custom configuration', () {
      // Arrange
      const baseUrl = 'http://custom-api.example.com/api';
      const wsUrl = 'ws://custom-api.example.com/ws';

      // Act
      final dataLayer = DataLayer(
        baseUrl: baseUrl,
        webSocketUrl: wsUrl,
        timeout: const Duration(seconds: 45),
        retryCount: 5,
        enableLogging: false,
      );

      // Assert
      expect(dataLayer.apiClient.baseUrl, equals(baseUrl));
      expect(dataLayer.webSocketClient.wsUrl, equals(wsUrl));
      dataLayer.dispose();
    });

    test('should initialize with default configuration', () {
      // Arrange
      const baseUrl = 'http://localhost:8000/api';

      // Act
      final dataLayer = DataLayer(baseUrl: baseUrl);

      // Assert
      expect(dataLayer.apiClient.baseUrl, equals(baseUrl));
      expect(dataLayer.webSocketClient.wsUrl, equals('ws://localhost:8000/api'));
      dataLayer.dispose();
    });

    test('should convert HTTPS to WSS URL', () {
      // Arrange
      const httpsUrl = 'https://api.example.com/api';

      // Act
      final dataLayer = DataLayer(baseUrl: httpsUrl);

      // Assert
      expect(dataLayer.webSocketClient.wsUrl, equals('wss://api.example.com/api'));
      dataLayer.dispose();
    });

    test('should convert HTTP to WS URL', () {
      // Arrange
      const httpUrl = 'http://api.example.com/api';

      // Act
      final dataLayer = DataLayer(baseUrl: httpUrl);

      // Assert
      expect(dataLayer.webSocketClient.wsUrl, equals('ws://api.example.com/api'));
      dataLayer.dispose();
    });
  });

  group('DataLayer Services', () {
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

    test('should initialize all services', () {
      // Assert
      expect(dataLayer.healthService, isNotNull);
      expect(dataLayer.projectsService, isNotNull);
      expect(dataLayer.assetsService, isNotNull);
      expect(dataLayer.clipsService, isNotNull);
      expect(dataLayer.jobsService, isNotNull);
      expect(dataLayer.presetsService, isNotNull);
    });
  });

  group('DataConfig', () {
    test('should return correct base URLs for environments', () {
      expect(DataConfig.getBaseUrlForEnvironment('development'), equals(DataConfig.developmentBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('dev'), equals(DataConfig.developmentBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('staging'), equals(DataConfig.stagingBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('stage'), equals(DataConfig.stagingBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('production'), equals(DataConfig.productionBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('prod'), equals(DataConfig.productionBaseUrl));
      expect(DataConfig.getBaseUrlForEnvironment('unknown'), equals(DataConfig.developmentBaseUrl));
    });

    test('should have correct default configuration values', () {
      expect(DataConfig.defaultTimeout, equals(const Duration(seconds: 30)));
      expect(DataConfig.defaultRetryCount, equals(3));
      expect(DataConfig.defaultEnableLogging, isTrue);
      expect(DataConfig.webSocketReconnectDelay, equals(const Duration(seconds: 3)));
      expect(DataConfig.maxWebSocketReconnectAttempts, equals(5));
    });
  });

  group('DataLayer Authentication', () {
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

    test('should set and clear auth token', () {
      // Arrange
      const token = 'test-auth-token';

      // Act - Set token
      dataLayer.setAuthToken(token);

      // Assert - No exceptions thrown
      expect(dataLayer, isA<DataLayer>());

      // Act - Clear token
      dataLayer.clearAuthToken();

      // Assert - Still valid
      expect(dataLayer, isA<DataLayer>());
    });
  });

  group('DataLayer WebSocket Management', () {
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

    test('should handle WebSocket connection methods', () async {
      // Act & Assert - These should not throw exceptions
      // Note: In a test environment without a real WebSocket server,
      // these methods will fail to connect but should not crash
      try {
        await dataLayer.connectWebSocket();
      } catch (e) {
        // Expected in test environment
      }

      dataLayer.disconnectWebSocket();
      expect(dataLayer, isA<DataLayer>());
    });

    test('should dispose resources correctly', () {
      // Act
      dataLayer.dispose();

      // Assert - Should complete without exceptions
      expect(dataLayer, isA<DataLayer>());
    });
  });

  group('DataLayer Error Handling', () {
    test('should handle invalid WebSocket URL conversion', () {
      // Arrange
      const invalidUrl = 'ftp://api.example.com/api';

      // Act
      final dataLayer = DataLayer(baseUrl: invalidUrl);

      // Assert - Should not crash and use the URL as-is
      expect(dataLayer.webSocketClient.wsUrl, equals(invalidUrl));
      dataLayer.dispose();
    });
  });
}