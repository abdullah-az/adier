# Flutter Data Client Layer

This directory contains the complete Flutter networking stack for communicating with the FastAPI backend.

## Overview

The data client layer provides:

- **HTTP Client**: Dio-based API client with retry logic, error handling, and connectivity checks
- **WebSocket Client**: Real-time communication for progress updates and notifications
- **Data Models**: Typed models mirroring backend schemas with JSON serialization
- **API Services**: High-level service classes for each backend endpoint
- **Error Handling**: Comprehensive error mapping with user-friendly messages
- **Configuration**: Environment-aware configuration management

## Architecture

```
lib/src/data/
├── models/           # Data models and enums
├── network/          # HTTP client, WebSocket client, exceptions
├── services/         # API service classes
├── config.dart       # Configuration constants
├── index.dart        # Main data layer class
└── example.dart      # Usage examples
```

## Quick Start

### 1. Initialize the Data Layer

```dart
import 'package:ai_video_editor_frontend/src/data/index.dart';
import 'package:ai_video_editor_frontend/src/data/config.dart';

final dataLayer = DataLayer(
  baseUrl: DataConfig.getBaseUrlForEnvironment('development'),
  enableLogging: true,
);
```

### 2. Check Backend Health

```dart
try {
  final health = await dataLayer.healthService.checkHealth();
  print('Backend is healthy: ${health.status}');
} catch (e) {
  print('Health check failed: $e');
}
```

### 3. Work with Projects

```dart
// Create a project
final project = await dataLayer.projectsService.createProject(
  ProjectCreateRequest(
    name: 'My Video Project',
    description: 'A test project',
  ),
);

// List projects
final projects = await dataLayer.projectsService.getProjects();
for (final project in projects) {
  print('- ${project.name}');
}
```

### 4. Real-time Updates

```dart
// Connect to WebSocket
await dataLayer.webSocketClient.connect();

// Listen for progress updates
dataLayer.webSocketClient.messages.listen((message) {
  if (message.type == 'job_progress') {
    final progress = message.data!['progress'] as int;
    print('Job progress: $progress%');
  }
});
```

## API Services

### HealthService
- `checkHealth()` - Basic health check
- `checkDiagnostics()` - Extended diagnostics with queue status

### ProjectsService
- `getProjects()` - List all projects
- `getProject(id)` - Get specific project
- `createProject(request)` - Create new project
- `updateProject(id, request)` - Update existing project
- `deleteProject(id)` - Delete project

### AssetsService
- `getAssets()` - List media assets
- `getAsset(id)` - Get specific asset
- `uploadAsset()` - Upload new media file
- `deleteAsset(id)` - Delete asset
- `getAssetDownloadUrl(id)` - Get download URL

### ClipsService
- `getClips()` - List video clips
- `getClip(id)` - Get specific clip
- `createClip()` - Create new clip
- `updateClip(id, request)` - Update existing clip
- `deleteClip(id)` - Delete clip
- `getClipVersions(clipId)` - List clip versions
- `createClipVersion(clipId)` - Create new version

### JobsService
- `getJobs()` - List processing jobs
- `getJob(id)` - Get specific job
- `createJob()` - Create new processing job
- `cancelJob(id)` - Cancel running job
- `retryJob(id)` - Retry failed job

### PresetsService
- `getPresets()` - List platform presets
- `getPreset(id)` - Get specific preset
- `getPresetByKey(key)` - Get preset by key
- `createPreset()` - Create new preset
- `updatePreset(id, request)` - Update existing preset
- `deletePreset(id)` - Delete preset

## Data Models

### Core Models
- `Project` - Video editing projects
- `MediaAsset` - Uploaded media files
- `Clip` - Video clips with time ranges
- `ClipVersion` - Different versions of clips
- `ProcessingJob` - Background processing tasks
- `PlatformPreset` - Export/processing presets

### Enums
- `ProjectStatus` - Project states (active, archived)
- `MediaAssetType` - Asset types (source, generated, thumbnail, transcript)
- `ClipStatus` - Clip states (draft, in_review, approved, archived)
- `ClipVersionStatus` - Version states (draft, rendering, ready, failed)
- `ProcessingJobStatus` - Job states (pending, queued, in_progress, completed, failed, cancelled)
- `ProcessingJobType` - Job types (ingest, transcribe, generate_clip, render, export)
- `PresetCategory` - Preset categories (export, style, audio)

## Error Handling

The data layer provides comprehensive error handling with user-friendly messages:

```dart
try {
  final project = await dataLayer.projectsService.getProject('invalid-id');
} on ApiException catch (e) {
  // Handle specific error types
  switch (e.runtimeType) {
    case NotFoundException:
      print('Project not found');
      break;
    case ValidationException:
      print('Invalid data: ${e.userMessage}');
      break;
    case ConnectionException:
      print('Network connection failed');
      break;
    default:
      print('Error: ${e.userMessage}');
  }
}
```

### Error Types

- `NoInternetException` - No internet connection
- `TimeoutException` - Request timeout
- `ConnectionException` - Connection failed
- `UnauthorizedException` - Authentication required
- `ForbiddenException` - Insufficient permissions
- `NotFoundException` - Resource not found
- `ServerException` - Server error (5xx)
- `ValidationException` - Data validation failed
- `HttpException` - Generic HTTP error
- `CanceledException` - Request canceled
- `UnknownException` - Unexpected error

## WebSocket Communication

### Connection Management

```dart
// Connect to WebSocket
await dataLayer.webSocketClient.connect();

// Monitor connection state
dataLayer.webSocketClient.states.listen((state) {
  switch (state) {
    case WebSocketState.connecting:
      print('Connecting to WebSocket...');
      break;
    case WebSocketState.connected:
      print('WebSocket connected');
      break;
    case WebSocketState.disconnected:
      print('WebSocket disconnected');
      break;
    case WebSocketState.error:
      print('WebSocket error');
      break;
  }
});

// Disconnect when done
dataLayer.disconnectWebSocket();
```

### Message Types

#### Progress Updates
```dart
// Server sends: {"type": "job_progress", "data": {"job_id": "123", "progress": 75, "status": "rendering"}}
dataLayer.webSocketClient.messages.listen((message) {
  if (message.type == 'job_progress') {
    final jobId = message.data!['job_id'] as String;
    final progress = message.data!['progress'] as int;
    final status = message.data!['status'] as String;
    print('Job $jobId: $progress% ($status)');
  }
});
```

#### Notifications
```dart
// Server sends: {"type": "notification", "data": {"title": "Job Complete", "message": "Your video is ready", "level": "success"}}
dataLayer.webSocketClient.messages.listen((message) {
  if (message.type == 'notification') {
    final title = message.data!['title'] as String;
    final message = message.data!['message'] as String;
    final level = message.data!['level'] as String;
    print('Notification: $title - $message ($level)');
  }
});
```

## Configuration

### Environment Configuration

```dart
// Development
final devDataLayer = DataLayer(
  baseUrl: DataConfig.developmentBaseUrl, // http://localhost:8000/api
);

// Staging
final stagingDataLayer = DataLayer(
  baseUrl: DataConfig.stagingBaseUrl, // https://staging-api.example.com/api
);

// Production
final prodDataLayer = DataLayer(
  baseUrl: DataConfig.productionBaseUrl, // https://api.example.com/api
);
```

### Custom Configuration

```dart
final customDataLayer = DataLayer(
  baseUrl: 'https://your-api.example.com/api',
  timeout: Duration(seconds: 60),
  retryCount: 5,
  enableLogging: false,
);
```

## Authentication

```dart
// Set authentication token
dataLayer.setAuthToken('your-jwt-token');

// Clear authentication
dataLayer.clearAuthToken();
```

## Testing

The data layer includes comprehensive test coverage:

- Unit tests for models and enums
- Integration tests for API services
- Mock-based tests for HTTP clients
- WebSocket client tests
- Error handling tests

Run tests:
```bash
flutter test test/data/
```

## Dependencies

The data layer uses the following key packages:

- `dio` - HTTP client with interceptors and retry logic
- `web_socket_channel` - WebSocket client
- `connectivity_plus` - Network connectivity monitoring
- `json_annotation` - JSON serialization annotations
- `equatable` - Value equality for models
- `mockito` - Mock objects for testing

## Best Practices

1. **Always handle exceptions** - Use try-catch blocks around API calls
2. **Dispose resources** - Call `dataLayer.dispose()` when done
3. **Monitor connectivity** - Handle network state changes gracefully
4. **Use typed models** - Avoid raw JSON, use the provided model classes
5. **Implement retry logic** - The client includes automatic retries, but handle failures
6. **Stream WebSocket messages** - Use streams for real-time updates
7. **Validate inputs** - Use validation exceptions to provide user feedback

## Migration Guide

When updating from a previous version:

1. Check for breaking changes in model fields
2. Update enum usage if new values were added
3. Review API service method signatures
4. Update error handling for new exception types
5. Test WebSocket message formats

## Support

For issues or questions about the data layer:

1. Check the test files for usage examples
2. Review the API service implementations
3. Examine the model definitions
4. Look at the WebSocket client documentation
5. Check the configuration options