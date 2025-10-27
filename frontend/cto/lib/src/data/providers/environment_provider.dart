import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/config/environment_config.dart';

const _environmentKey = 'API_ENV';
const _apiBaseUrlKey = 'API_BASE_URL';
const _connectTimeoutKey = 'API_CONNECT_TIMEOUT';
const _receiveTimeoutKey = 'API_RECEIVE_TIMEOUT';
const _loggingKey = 'API_ENABLE_LOGGING';
const _uploadRetriesKey = 'API_UPLOAD_RETRIES';

Environment _parseEnvironment(String value) {
  switch (value.toLowerCase()) {
    case 'staging':
      return Environment.staging;
    case 'production':
      return Environment.production;
    default:
      return Environment.development;
  }
}

EnvironmentConfig _resolveEnvironmentConfig() {
  const envValue = String.fromEnvironment(_environmentKey, defaultValue: 'development');
  const baseUrlOverride = String.fromEnvironment(_apiBaseUrlKey);
  const connectTimeoutValue = int.fromEnvironment(_connectTimeoutKey, defaultValue: EnvironmentConfig.development.connectTimeout);
  const receiveTimeoutValue = int.fromEnvironment(_receiveTimeoutKey, defaultValue: EnvironmentConfig.development.receiveTimeout);
  const loggingValue = bool.hasEnvironment(_loggingKey)
      ? bool.fromEnvironment(_loggingKey, defaultValue: EnvironmentConfig.development.enableLogging)
      : EnvironmentConfig.development.enableLogging;
  const uploadRetriesValue = int.fromEnvironment(_uploadRetriesKey, defaultValue: EnvironmentConfig.development.maxUploadRetries);

  final environment = _parseEnvironment(envValue);

  final defaultConfig = switch (environment) {
    Environment.development => EnvironmentConfig.development,
    Environment.staging => EnvironmentConfig.staging,
    Environment.production => EnvironmentConfig.production,
  };

  return EnvironmentConfig(
    environment: environment,
    apiBaseUrl: baseUrlOverride.isEmpty ? defaultConfig.apiBaseUrl : baseUrlOverride,
    connectTimeout: connectTimeoutValue,
    receiveTimeout: receiveTimeoutValue,
    enableLogging: loggingValue,
    maxUploadRetries: uploadRetriesValue,
  );
}

final environmentConfigProvider = Provider<EnvironmentConfig>((ref) {
  return _resolveEnvironmentConfig();
}, name: 'environmentConfigProvider');
