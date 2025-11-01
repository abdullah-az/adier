import 'dart:io';
import 'dart:developer' as developer;
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class ApiClient {
  late final Dio _dio;
  final String _baseUrl;
  final Duration timeout;
  final int retryCount;
  final bool enableLogging;

  String get baseUrl => _baseUrl;

  ApiClient({
    required String baseUrl,
    this.timeout = const Duration(seconds: 30),
    this.retryCount = 3,
    this.enableLogging = true,
  }) : _baseUrl = baseUrl {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: timeout,
      receiveTimeout: timeout,
      sendTimeout: timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    _setupInterceptors();
  }

  void _setupInterceptors() {
    // Retry interceptor
    _dio.interceptors.add(
      RetryInterceptor(
        dio: _dio,
        options: RetryOptions(
          retries: retryCount,
          retryInterval: const Duration(seconds: 1),
        ),
      ),
    );

    // Logging interceptor
    if (enableLogging) {
      _dio.interceptors.add(
        LogInterceptor(
          requestBody: true,
          responseBody: true,
          logPrint: (obj) {
            developer.log(obj.toString(), name: 'ApiClient');
          },
        ),
      );
    }

    // Error interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onError: (error, handler) {
          final apiError = _handleError(error);
          handler.reject(DioException(
            requestOptions: error.requestOptions,
            error: apiError,
            type: error.type,
            response: error.response,
          ));
        },
      ),
    );

    // Connectivity interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final connectivity = await Connectivity().checkConnectivity();
          if (connectivity == ConnectivityResult.none) {
            handler.reject(DioException(
              requestOptions: options,
              error: ApiException.noInternet(),
              type: DioExceptionType.unknown,
            ));
            return;
          }
          handler.next(options);
        },
      ),
    );
  }

  ApiException _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException.timeout();
      
      case DioExceptionType.connectionError:
        return ApiException.connectionError();
      
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final data = error.response?.data;
        
        if (data != null && data is Map<String, dynamic>) {
          if (statusCode == 400) {
            return ApiException.validationError(data);
          } else if (statusCode == 401) {
            return ApiException.unauthorized();
          } else if (statusCode == 403) {
            return ApiException.forbidden();
          } else if (statusCode == 404) {
            return ApiException.notFound();
          } else if (statusCode == 422) {
            return ApiException.validationError(data);
          } else if (statusCode! >= 500) {
            return ApiException.serverError(data['detail']?.toString() ?? 'Server error');
          }
        }
        
        return ApiException.httpError(statusCode ?? 0, error.message ?? 'Unknown error');
      
      case DioExceptionType.cancel:
        return ApiException.canceled();
      
      case DioExceptionType.unknown:
      default:
        if (error.error is SocketException) {
          return ApiException.connectionError();
        }
        return ApiException.unknown(error.error?.toString() ?? 'Unknown error');
    }
  }

  // HTTP Methods
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    return _dio.delete<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  void setAuthToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  void clearAuthToken() {
    _dio.options.headers.remove('Authorization');
  }
}

class RetryOptions {
  final int retries;
  final Duration retryInterval;

  const RetryOptions({
    required this.retries,
    required this.retryInterval,
  });
}

class RetryInterceptor extends Interceptor {
  final Dio dio;
  final RetryOptions options;

  RetryInterceptor({
    required this.dio,
    required this.options,
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final extra = err.requestOptions.extra;
    final retryCount = extra['retryCount'] ?? 0;

    if (retryCount < options.retries && _shouldRetry(err)) {
      extra['retryCount'] = retryCount + 1;
      
      await Future.delayed(options.retryInterval);
      
      try {
        final response = await dio.fetch(err.requestOptions);
        handler.resolve(response);
        return;
      } catch (e) {
        handler.next(err);
        return;
      }
    }

    handler.next(err);
  }

  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
           err.type == DioExceptionType.sendTimeout ||
           err.type == DioExceptionType.receiveTimeout ||
           err.type == DioExceptionType.connectionError ||
           (err.type == DioExceptionType.badResponse && 
            err.response?.statusCode != null && 
            err.response!.statusCode! >= 500);
  }
}