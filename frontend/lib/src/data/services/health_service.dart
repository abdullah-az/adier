import 'package:dio/dio.dart';
import '../network/api_client.dart';
import '../network/exceptions.dart';

class HealthService {
  final ApiClient _apiClient;

  HealthService(this._apiClient);

  Future<HealthResponse> checkHealth() async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/health');
      return HealthResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }

  Future<DiagnosticsResponse> checkDiagnostics() async {
    try {
      final response = await _apiClient.get<Map<String, dynamic>>('/health/diagnostics');
      return DiagnosticsResponse.fromJson(response.data!);
    } on DioException catch (e) {
      throw e.error ?? ApiException.unknown(e.message ?? 'Unknown error');
    }
  }
}

class HealthResponse {
  final String status;
  final String app;
  final String environment;

  const HealthResponse({
    required this.status,
    required this.app,
    required this.environment,
  });

  factory HealthResponse.fromJson(Map<String, dynamic> json) {
    return HealthResponse(
      status: json['status'] as String,
      app: json['app'] as String,
      environment: json['environment'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'app': app,
      'environment': environment,
    };
  }

  @override
  String toString() {
    return 'HealthResponse(status: $status, app: $app, environment: $environment)';
  }
}

class DiagnosticsResponse {
  final String status;
  final String app;
  final String environment;
  final QueueStatus queue;

  const DiagnosticsResponse({
    required this.status,
    required this.app,
    required this.environment,
    required this.queue,
  });

  factory DiagnosticsResponse.fromJson(Map<String, dynamic> json) {
    return DiagnosticsResponse(
      status: json['status'] as String,
      app: json['app'] as String,
      environment: json['environment'] as String,
      queue: QueueStatus.fromJson(json['queue'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'app': app,
      'environment': environment,
      'queue': queue.toJson(),
    };
  }

  @override
  String toString() {
    return 'DiagnosticsResponse(status: $status, app: $app, environment: $environment, queue: $queue)';
  }
}

class QueueStatus {
  final bool connected;
  final String brokerUrl;
  final String? redisVersion;
  final int? connectedClients;
  final String? error;

  const QueueStatus({
    required this.connected,
    required this.brokerUrl,
    this.redisVersion,
    this.connectedClients,
    this.error,
  });

  factory QueueStatus.fromJson(Map<String, dynamic> json) {
    return QueueStatus(
      connected: json['connected'] as bool,
      brokerUrl: json['broker_url'] as String,
      redisVersion: json['redis_version'] as String?,
      connectedClients: json['connected_clients'] as int?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'connected': connected,
      'broker_url': brokerUrl,
      'redis_version': redisVersion,
      'connected_clients': connectedClients,
      'error': error,
    };
  }

  @override
  String toString() {
    return 'QueueStatus(connected: $connected, brokerUrl: $brokerUrl, redisVersion: $redisVersion, connectedClients: $connectedClients, error: $error)';
  }
}