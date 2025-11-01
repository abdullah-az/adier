export 'models/index.dart';
export 'network/index.dart';
import 'network/index.dart';
import 'services/index.dart';

class DataLayer {
  late final ApiClient apiClient;
  late final WebSocketClient webSocketClient;
  late final HealthService healthService;
  late final ProjectsService projectsService;
  late final AssetsService assetsService;
  late final ClipsService clipsService;
  late final JobsService jobsService;
  late final PresetsService presetsService;

  DataLayer({
    required String baseUrl,
    String? webSocketUrl,
    Duration timeout = const Duration(seconds: 30),
    int retryCount = 3,
    bool enableLogging = true,
  }) {
    // Initialize API client
    apiClient = ApiClient(
      baseUrl: baseUrl,
      timeout: timeout,
      retryCount: retryCount,
      enableLogging: enableLogging,
    );

    // Initialize WebSocket client
    final wsUrl = webSocketUrl ?? _convertToWebSocketUrl(baseUrl);
    webSocketClient = WebSocketClient(wsUrl: wsUrl);

    // Initialize services
    healthService = HealthService(apiClient);
    projectsService = ProjectsService(apiClient);
    assetsService = AssetsService(apiClient);
    clipsService = ClipsService(apiClient);
    jobsService = JobsService(apiClient);
    presetsService = PresetsService(apiClient);
  }

  String _convertToWebSocketUrl(String httpUrl) {
    if (httpUrl.startsWith('https://')) {
      return httpUrl.replaceFirst('https://', 'wss://');
    } else if (httpUrl.startsWith('http://')) {
      return httpUrl.replaceFirst('http://', 'ws://');
    }
    return httpUrl;
  }

  void setAuthToken(String token) {
    apiClient.setAuthToken(token);
  }

  void clearAuthToken() {
    apiClient.clearAuthToken();
  }

  Future<void> connectWebSocket() async {
    await webSocketClient.connect();
  }

  void disconnectWebSocket() {
    webSocketClient.disconnect();
  }

  void dispose() {
    webSocketClient.dispose();
  }
}