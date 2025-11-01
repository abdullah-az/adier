import 'package:equatable/equatable.dart';

abstract class ApiException extends Equatable implements Exception {
  final String message;
  final String? userMessage;
  final int? statusCode;

  const ApiException({
    required this.message,
    this.userMessage,
    this.statusCode,
  });

  @override
  List<Object?> get props => [message, userMessage, statusCode];

  @override
  String toString() => 'ApiException: $message';

  factory ApiException.noInternet() => const NoInternetException();

  factory ApiException.timeout() => const TimeoutException();

  factory ApiException.connectionError() => const ConnectionException();

  factory ApiException.unauthorized() => const UnauthorizedException();

  factory ApiException.forbidden() => const ForbiddenException();

  factory ApiException.notFound() => const NotFoundException();

  factory ApiException.serverError(String message) => ServerException(message);

  factory ApiException.validationError(Map<String, dynamic> data) {
    return ValidationException(data);
  }

  factory ApiException.httpError(int statusCode, String message) {
    return HttpException(statusCode, message);
  }

  factory ApiException.canceled() => const CanceledException();

  factory ApiException.unknown(String message) => UnknownException(message);
}

class NoInternetException extends ApiException {
  const NoInternetException()
      : super(
          message: 'No internet connection',
          userMessage: 'Please check your internet connection and try again.',
        );
}

class TimeoutException extends ApiException {
  const TimeoutException()
      : super(
          message: 'Request timeout',
          userMessage: 'The request took too long. Please try again.',
        );
}

class ConnectionException extends ApiException {
  const ConnectionException()
      : super(
          message: 'Connection error',
          userMessage: 'Unable to connect to the server. Please try again.',
        );
}

class UnauthorizedException extends ApiException {
  const UnauthorizedException()
      : super(
          message: 'Unauthorized',
          statusCode: 401,
          userMessage: 'Please log in to continue.',
        );
}

class ForbiddenException extends ApiException {
  const ForbiddenException()
      : super(
          message: 'Forbidden',
          statusCode: 403,
          userMessage: 'You don\'t have permission to perform this action.',
        );
}

class NotFoundException extends ApiException {
  const NotFoundException()
      : super(
          message: 'Not found',
          statusCode: 404,
          userMessage: 'The requested resource was not found.',
        );
}

class ServerException extends ApiException {
  const ServerException(String message)
      : super(
          message: 'Server error: $message',
          statusCode: 500,
          userMessage: 'Something went wrong on our end. Please try again later.',
        );
}

class ValidationException extends ApiException {
  final Map<String, dynamic> errors;

  ValidationException(Map<String, dynamic> data)
      : errors = _extractErrors(data),
        super(
          message: 'Validation error',
          statusCode: 422,
          userMessage: _extractUserMessage(data),
        );

  static Map<String, dynamic> _extractErrors(Map<String, dynamic> data) {
    if (data.containsKey('detail') && data['detail'] is Map) {
      return Map<String, dynamic>.from(data['detail']);
    }
    return {};
  }

  static String _extractUserMessage(Map<String, dynamic> data) {
    if (data.containsKey('detail')) {
      final detail = data['detail'];
      if (detail is String) {
        return detail;
      } else if (detail is Map) {
        final errors = <String>[];
        detail.forEach((key, value) {
          if (value is List) {
            errors.addAll(value.map((e) => '$key: $e'));
          } else {
            errors.add('$key: $value');
          }
        });
        return errors.join('; ');
      }
    }
    return 'Invalid data provided';
  }
}

class HttpException extends ApiException {
  const HttpException(int statusCode, String message)
      : super(
          message: 'HTTP $statusCode: $message',
          statusCode: statusCode,
          userMessage: 'An error occurred. Please try again.',
        );
}

class CanceledException extends ApiException {
  const CanceledException()
      : super(
          message: 'Request canceled',
          userMessage: 'The request was canceled.',
        );
}

class UnknownException extends ApiException {
  const UnknownException(String message)
      : super(
          message: 'Unknown error: $message',
          userMessage: 'An unexpected error occurred. Please try again.',
        );
}