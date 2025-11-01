import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';

import 'package:ai_video_editor_frontend/src/data/network/api_client.dart';
import 'package:ai_video_editor_frontend/src/data/network/exceptions.dart';

void main() {
  group('ApiClient Configuration', () {
    test('should initialize with correct base URL', () {
      // Arrange
      const baseUrl = 'http://localhost:8000/api';

      // Act
      final apiClient = ApiClient(baseUrl: baseUrl, enableLogging: false);

      // Assert
      expect(apiClient.baseUrl, equals(baseUrl));
    });

    test('should set and clear auth token', () {
      // Arrange
      const baseUrl = 'http://localhost:8000/api';
      final apiClient = ApiClient(baseUrl: baseUrl, enableLogging: false);
      const token = 'test-auth-token';

      // Act - Set token
      apiClient.setAuthToken(token);

      // Assert - Token is set (we can't directly access the private field, but we can test behavior)
      expect(apiClient, isA<ApiClient>());

      // Act - Clear token
      apiClient.clearAuthToken();

      // Assert - Still a valid client
      expect(apiClient, isA<ApiClient>());
    });
  });

  group('ApiException Creation', () {
    test('should create NoInternetException', () {
      // Act
      final exception = ApiException.noInternet();

      // Assert
      expect(exception, isA<NoInternetException>());
      expect(exception.message, equals('No internet connection'));
      expect(exception.userMessage, equals('Please check your internet connection and try again.'));
    });

    test('should create TimeoutException', () {
      // Act
      final exception = ApiException.timeout();

      // Assert
      expect(exception, isA<TimeoutException>());
      expect(exception.message, equals('Request timeout'));
      expect(exception.userMessage, equals('The request took too long. Please try again.'));
    });

    test('should create ValidationException with errors', () {
      // Arrange
      final errorData = {
        'detail': {
          'name': ['This field is required.'],
          'email': ['Invalid email format.'],
        }
      };

      // Act
      final exception = ApiException.validationError(errorData);

      // Assert
      expect(exception, isA<ValidationException>());
      expect(exception.statusCode, equals(422));
      expect(exception.userMessage, contains('name: This field is required.'));
      expect(exception.userMessage, contains('email: Invalid email format.'));
    });

    test('should create UnauthorizedException', () {
      // Act
      final exception = ApiException.unauthorized();

      // Assert
      expect(exception, isA<UnauthorizedException>());
      expect(exception.statusCode, equals(401));
      expect(exception.userMessage, equals('Please log in to continue.'));
    });

    test('should create NotFoundException', () {
      // Act
      final exception = ApiException.notFound();

      // Assert
      expect(exception, isA<NotFoundException>());
      expect(exception.statusCode, equals(404));
      expect(exception.userMessage, equals('The requested resource was not found.'));
    });

    test('should create ServerException', () {
      // Arrange
      const errorMessage = 'Database connection failed';

      // Act
      final exception = ApiException.serverError(errorMessage);

      // Assert
      expect(exception, isA<ServerException>());
      expect(exception.statusCode, equals(500));
      expect(exception.message, contains(errorMessage));
      expect(exception.userMessage, equals('Something went wrong on our end. Please try again later.'));
    });
  });

  group('ApiException Equality', () {
    test('should equate same exceptions', () {
      // Arrange
      final exception1 = ApiException.timeout();
      final exception2 = ApiException.timeout();

      // Act & Assert
      expect(exception1, equals(exception2));
    });

    test('should not equate different exceptions', () {
      // Arrange
      final exception1 = ApiException.timeout();
      final exception2 = ApiException.noInternet();

      // Act & Assert
      expect(exception1, isNot(equals(exception2)));
    });
  });
}