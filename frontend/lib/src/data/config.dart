class DataConfig {
  static const String developmentBaseUrl = 'http://localhost:8000/api';
  static const String stagingBaseUrl = 'https://staging-api.example.com/api';
  static const String productionBaseUrl = 'https://api.example.com/api';

  static String getBaseUrlForEnvironment(String environment) {
    switch (environment.toLowerCase()) {
      case 'development':
      case 'dev':
        return developmentBaseUrl;
      case 'staging':
      case 'stage':
        return stagingBaseUrl;
      case 'production':
      case 'prod':
        return productionBaseUrl;
      default:
        return developmentBaseUrl;
    }
  }

  static const Duration defaultTimeout = Duration(seconds: 30);
  static const int defaultRetryCount = 3;
  static const bool defaultEnableLogging = true;

  static const Duration webSocketReconnectDelay = Duration(seconds: 3);
  static const int maxWebSocketReconnectAttempts = 5;
}