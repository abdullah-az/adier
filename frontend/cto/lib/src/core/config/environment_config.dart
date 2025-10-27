enum Environment {
  development,
  staging,
  production,
}

class EnvironmentConfig {
  final Environment environment;
  final String apiBaseUrl;
  final int connectTimeout;
  final int receiveTimeout;
  final bool enableLogging;
  final int maxUploadRetries;

  const EnvironmentConfig({
    required this.environment,
    required this.apiBaseUrl,
    this.connectTimeout = 30000,
    this.receiveTimeout = 30000,
    this.enableLogging = true,
    this.maxUploadRetries = 3,
  });

  static const development = EnvironmentConfig(
    environment: Environment.development,
    apiBaseUrl: 'http://localhost:8000/api',
    enableLogging: true,
  );

  static const staging = EnvironmentConfig(
    environment: Environment.staging,
    apiBaseUrl: 'https://staging-api.example.com/api',
    enableLogging: true,
  );

  static const production = EnvironmentConfig(
    environment: Environment.production,
    apiBaseUrl: 'https://api.example.com/api',
    enableLogging: false,
  );

  bool get isDevelopment => environment == Environment.development;
  bool get isStaging => environment == Environment.staging;
  bool get isProduction => environment == Environment.production;
}
