import 'dart:async';

import 'package:dio/dio.dart';

import '../errors/api_failure.dart';

typedef RetryEvaluator = bool Function(DioException error);
typedef ProgressListener = void Function(int sent, int total);

class RetryInterceptor extends Interceptor {
  RetryInterceptor({
    required Dio dio,
    this.retryEvaluator,
    this.maxRetries = 2,
    this.retryDelay = const Duration(milliseconds: 500),
  }) : _dio = dio;

  final Dio _dio;
  final RetryEvaluator? retryEvaluator;
  final int maxRetries;
  final Duration retryDelay;

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final requestOptions = err.requestOptions;
    final extra = requestOptions.extra;
    final currentAttempt = (extra['retry_attempt'] as int?) ?? 0;
    final shouldRetry =
        (retryEvaluator?.call(err) ?? _defaultRetryEvaluator(err)) && currentAttempt < maxRetries;

    if (!shouldRetry) {
      return handler.next(err);
    }

    await Future<void>.delayed(retryDelay * (currentAttempt + 1));

    final newOptions = requestOptions.copyWith(
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
    );

    newOptions.extra = Map<String, dynamic>.of(extra)
      ..update('retry_attempt', (value) => (value as int) + 1, ifAbsent: () => 1);

    try {
      final response = await _dio.fetch<dynamic>(newOptions);
      return handler.resolve(response);
    } on DioException catch (e) {
      return handler.next(e);
    } catch (e, stackTrace) {
      return handler.reject(DioException(
        requestOptions: requestOptions,
        error: e,
        stackTrace: stackTrace,
        type: DioExceptionType.unknown,
      ));
    }
  }

  bool _defaultRetryEvaluator(DioException error) {
    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.unknown ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout;
  }
}

class FailureMappingInterceptor extends Interceptor {
  const FailureMappingInterceptor();

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.error is ApiFailure) {
      return handler.next(err);
    }

    handler.next(err.copyWith(error: _mapFailure(err)));
  }

  ApiFailure _mapFailure(DioException err) {
    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return TimeoutFailure(message: 'Request timed out');
      case DioExceptionType.badResponse:
        final statusCode = err.response?.statusCode ?? 500;
        final data = err.response?.data;
        if (statusCode == 401) {
          return UnauthorizedFailure(message: 'Unauthorized request');
        }
        if (statusCode == 403) {
          return ForbiddenFailure(message: 'Access forbidden');
        }
        if (statusCode == 404) {
          return NotFoundFailure(message: 'Resource not found');
        }
        if (statusCode == 422 && data is Map<String, dynamic>) {
          return ValidationFailure(
            message: data['message'] as String? ?? 'Validation error',
            errors: (data['errors'] as Map<dynamic, dynamic>?)?.map(
              (key, value) => MapEntry(
                key.toString(),
                value is List ? value.map((dynamic e) => e.toString()).toList() : <String>[],
              ),
            ),
          );
        }
        final message = data is Map<String, dynamic>
            ? data['message']?.toString() ?? 'Server error'
            : 'Server error';
        return ServerFailure(
          statusCode: statusCode,
          message: message,
          data: data is Map<String, dynamic> ? data : null,
        );
      case DioExceptionType.badCertificate:
      case DioExceptionType.connectionError:
        return NetworkFailure(
          message: 'Network connection error',
          exception: err.error is Exception ? err.error as Exception : null,
        );
      case DioExceptionType.cancel:
        return NetworkFailure(message: 'Request was cancelled');
      case DioExceptionType.unknown:
      default:
        final error = err.error;
        if (error is ApiFailure) {
          return error;
        }
        return UnknownFailure(message: 'Unexpected error occurred', error: error);
    }
  }
}

class UploadProgressInterceptor extends Interceptor {
  UploadProgressInterceptor({this.progressKey = 'uploadProgressListener'});

  final String progressKey;

  @override
  void onSendProgress(
    int sent,
    int total,
    RequestOptions options,
    ProgressInterceptorHandler handler,
  ) {
    final listener = options.extra[progressKey];
    if (listener is ProgressListener) {
      listener(sent, total);
    }
    handler.next(sent, total, options);
  }
}
