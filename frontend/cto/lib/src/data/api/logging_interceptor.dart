import 'dart:convert';

import 'package:dio/dio.dart';

class LoggingInterceptor extends Interceptor {
  LoggingInterceptor({this.enabled = true});

  final bool enabled;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (!enabled) {
      return handler.next(options);
    }

    print('┌──────────────────────────────────────────────────────────────────');
    print('│ ➡️  REQUEST: ${options.method} ${options.uri}');
    print('├──────────────────────────────────────────────────────────────────');
    if (options.headers.isNotEmpty) {
      print('│ Headers:');
      options.headers.forEach((key, value) {
        if (key.toLowerCase() != 'authorization') {
          print('│   $key: $value');
        } else {
          print('│   $key: [REDACTED]');
        }
      });
    }
    if (options.queryParameters.isNotEmpty) {
      print('│ Query Parameters:');
      options.queryParameters.forEach((key, value) {
        print('│   $key: $value');
      });
    }
    if (options.data != null) {
      print('│ Body:');
      _printData(options.data);
    }
    print('└──────────────────────────────────────────────────────────────────');

    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    if (!enabled) {
      return handler.next(response);
    }

    print('┌──────────────────────────────────────────────────────────────────');
    print('│ ⬅️  RESPONSE: ${response.requestOptions.method} ${response.requestOptions.uri}');
    print('├──────────────────────────────────────────────────────────────────');
    print('│ Status Code: ${response.statusCode}');
    if (response.headers.map.isNotEmpty) {
      print('│ Response Headers:');
      response.headers.forEach((key, values) {
        print('│   $key: ${values.join(', ')}');
      });
    }
    if (response.data != null) {
      print('│ Response Data:');
      _printData(response.data);
    }
    print('└──────────────────────────────────────────────────────────────────');

    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (!enabled) {
      return handler.next(err);
    }

    print('┌──────────────────────────────────────────────────────────────────');
    print('│ ❌ ERROR: ${err.requestOptions.method} ${err.requestOptions.uri}');
    print('├──────────────────────────────────────────────────────────────────');
    print('│ Type: ${err.type}');
    print('│ Message: ${err.message}');
    if (err.response?.statusCode != null) {
      print('│ Status Code: ${err.response?.statusCode}');
    }
    if (err.response?.data != null) {
      print('│ Error Data:');
      _printData(err.response?.data);
    }
    print('└──────────────────────────────────────────────────────────────────');

    handler.next(err);
  }

  void _printData(dynamic data) {
    if (data is FormData) {
      print('│   [FormData]');
      return;
    }

    try {
      final prettyJson = const JsonEncoder.withIndent('  ').convert(data);
      prettyJson.split('\n').forEach((line) {
        print('│   $line');
      });
    } catch (_) {
      print('│   ${data.toString()}');
    }
  }
}
