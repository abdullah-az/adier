import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../errors/api_failure.dart';
import '../providers/environment_provider.dart';
import 'dio_interceptors.dart';
import 'logging_interceptor.dart';

final dioProvider = Provider<Dio>((ref) {
  final config = ref.watch(environmentConfigProvider);

  final options = BaseOptions(
    baseUrl: config.apiBaseUrl,
    connectTimeout: Duration(milliseconds: config.connectTimeout),
    receiveTimeout: Duration(milliseconds: config.receiveTimeout),
    sendTimeout: Duration(milliseconds: config.receiveTimeout),
    responseType: ResponseType.json,
    contentType: Headers.jsonContentType,
  );

  final dio = Dio(options);

  dio.interceptors.addAll([
    LoggingInterceptor(enabled: config.enableLogging),
    UploadProgressInterceptor(),
    FailureMappingInterceptor(),
    RetryInterceptor(
      dio: dio,
      maxRetries: config.maxUploadRetries,
      retryDelay: const Duration(milliseconds: 800),
    ),
  ]);

  return dio;
});

class ApiClient {
  ApiClient(this._dio);

  final Dio _dio;

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
  }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
      onReceiveProgress: onReceiveProgress,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
    ProgressCallback? onSendProgress,
  }) {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
      onReceiveProgress: onReceiveProgress,
      onSendProgress: onSendProgress,
    );
  }

  Future<Response<T>> put<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
    ProgressCallback? onSendProgress,
  }) {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
      onReceiveProgress: onReceiveProgress,
      onSendProgress: onSendProgress,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
  }) {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
      cancelToken: cancelToken,
      onReceiveProgress: onReceiveProgress,
    );
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiClient(dio);
});

ApiFailure mapDioError(Object error) {
  if (error is ApiFailure) {
    return error;
  }
  if (error is DioException) {
    final failure = error.error;
    if (failure is ApiFailure) {
      return failure;
    }
    return UnknownFailure(
      message: error.message ?? 'Unknown error',
      error: error,
    );
  }
  return UnknownFailure(message: error.toString(), error: error);
}
