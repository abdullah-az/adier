# Data Layer Documentation

This directory contains the data layer implementation for the Flutter application, providing a clean abstraction for API communication, error handling, and data serialization.

## Architecture Overview

```
data/
├── api/                      # HTTP client configuration
│   ├── api_client.dart       # Dio client wrapper
│   ├── dio_interceptors.dart # Retry, error mapping, upload progress
│   └── logging_interceptor.dart # Request/response logging
├── errors/                   # Error types
│   └── api_failure.dart      # Sealed failure types
├── models/                   # Data models (Freezed)
│   ├── project.dart
│   ├── video_asset.dart
│   ├── scene_suggestion.dart
│   ├── subtitle_segment.dart
│   ├── timeline_clip.dart
│   └── export_job.dart
├── providers/                # Riverpod providers
│   └── environment_provider.dart
└── repositories/             # Data access layer
    ├── project_repository.dart
    └── processing_repository.dart
```

## Configuration

### Environment Setup

The application supports multiple environments (development, staging, production) configured via compile-time constants:

```dart
// Development (default)
flutter run

// Staging
flutter run --dart-define=API_ENV=staging

// Production
flutter run --dart-define=API_ENV=production

// Custom API URL
flutter run --dart-define=API_BASE_URL=https://custom-api.example.com/api
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_ENV` | Environment name (development/staging/production) | development |
| `API_BASE_URL` | Override base API URL | (environment-specific) |
| `API_CONNECT_TIMEOUT` | Connection timeout in milliseconds | 30000 |
| `API_RECEIVE_TIMEOUT` | Receive timeout in milliseconds | 30000 |
| `API_ENABLE_LOGGING` | Enable request/response logging | true (dev), false (prod) |
| `API_UPLOAD_RETRIES` | Max upload retry attempts | 3 |

### Example Configuration

```dart
// Access environment config via Riverpod
final config = ref.watch(environmentConfigProvider);
print(config.apiBaseUrl);
print(config.enableLogging);
```

## API Client

### Dio Setup

The API client is configured with the following features:

- **Automatic retries** for transient failures
- **Error mapping** to typed failure classes
- **Upload progress tracking**
- **Request/response logging** (development only)
- **Timeout handling**

### Interceptors

1. **LoggingInterceptor**: Logs requests and responses for debugging
2. **UploadProgressInterceptor**: Tracks upload progress
3. **FailureMappingInterceptor**: Maps HTTP errors to typed failures
4. **RetryInterceptor**: Automatically retries failed requests

### Usage

```dart
// Get API client via Riverpod
final apiClient = ref.watch(apiClientProvider);

// Make requests
final response = await apiClient.get('/projects');
final response = await apiClient.post('/projects', data: {...});
```

## Error Handling

All API errors are mapped to typed `ApiFailure` classes using Dart 3's sealed classes:

```dart
sealed class ApiFailure {
  NetworkFailure       // Network connectivity errors
  ServerFailure        // HTTP 5xx errors
  TimeoutFailure       // Request timeouts
  UnauthorizedFailure  // HTTP 401
  ForbiddenFailure     // HTTP 403
  NotFoundFailure      // HTTP 404
  ValidationFailure    // HTTP 422 with validation errors
  ParsingFailure       // JSON deserialization errors
  UploadFailure        // Upload-specific errors
  UnknownFailure       // Catch-all
}
```

### Error Pattern Matching

```dart
try {
  final project = await repository.getProject(id);
} catch (e) {
  final failure = mapDioError(e);
  failure.when(
    network: (f) => showError('No internet connection'),
    notFound: (f) => showError('Project not found'),
    server: (f) => showError('Server error: ${f.message}'),
    validation: (f) => showValidationErrors(f.errors),
    // ... handle other cases
    unknown: (f) => showError('Unexpected error'),
  );
}
```

## Data Models

All data models use Freezed for immutability and JSON serialization:

### Project

```dart
final project = Project(
  id: 'proj_123',
  name: 'My Project',
  description: 'A video editing project',
  createdAt: DateTime.now(),
  updatedAt: DateTime.now(),
);

// JSON serialization
final json = project.toJson();
final project = Project.fromJson(json);
```

### VideoAsset

```dart
final asset = VideoAsset(
  id: 'asset_123',
  projectId: 'proj_123',
  filename: 'video.mp4',
  originalFilename: 'my_video.mp4',
  relativePath: 'uploads/proj_123/video.mp4',
  checksum: 'abc123',
  sizeBytes: 1048576,
  mimeType: 'video/mp4',
  category: VideoAssetCategory.source,
  status: 'ready',
  createdAt: DateTime.now(),
  updatedAt: DateTime.now(),
);
```

### TimelineClip

```dart
final clip = TimelineClip(
  assetId: 'asset_123',
  inPoint: 0.0,
  outPoint: 10.0,
  includeAudio: true,
  transition: TransitionSpec(
    type: TransitionType.crossfade,
    duration: 1.0,
  ),
);
```

### ExportJob

```dart
final job = ExportJob(
  id: 'job_123',
  projectId: 'proj_123',
  jobType: 'export',
  status: ExportJobStatus.running,
  progress: 45.0,
  attempts: 1,
  maxAttempts: 3,
  retryDelaySeconds: 5.0,
  createdAt: DateTime.now(),
  updatedAt: DateTime.now(),
);
```

## Repositories

### ProjectRepository

Handles project and video asset management:

```dart
final repository = ref.watch(projectRepositoryProvider);

// Projects
final projects = await repository.getProjects();
final project = await repository.getProject(projectId);
final newProject = await repository.createProject(name: 'New Project');
await repository.updateProject(projectId, name: 'Updated Name');
await repository.deleteProject(projectId);

// Videos
final videos = await repository.getProjectVideos(projectId);
final uploadResponse = await repository.uploadVideo(
  projectId,
  filePath: '/path/to/video.mp4',
  fileName: 'video.mp4',
  onProgress: (progress) => print('Upload: ${(progress * 100).toInt()}%'),
);
await repository.deleteVideo(projectId, assetId);

// Storage
final stats = await repository.getProjectStorageStats(projectId);
await repository.clearProjectStorage(projectId);
```

### ProcessingRepository

Handles background job processing:

```dart
final repository = ref.watch(processingRepositoryProvider);

// Submit jobs
final job = await repository.submitIngestJob(
  projectId: 'proj_123',
  assetId: 'asset_123',
);

final job = await repository.submitSceneDetectionJob(
  projectId: 'proj_123',
  assetId: 'asset_123',
);

final job = await repository.submitTranscriptionJob(
  projectId: 'proj_123',
  assetId: 'asset_123',
  language: 'en',
);

final job = await repository.submitExportJob(
  projectId: 'proj_123',
  request: TimelineCompositionRequest(
    clips: [clip1, clip2],
    aspectRatio: AspectRatio.sixteenNine,
    resolution: ResolutionPreset.p1080,
  ),
);

// List and monitor jobs
final jobs = await repository.listJobs(projectId);
final job = await repository.getJob(projectId, jobId);

// Watch job progress
await for (final updatedJob in repository.watchJob(projectId, jobId)) {
  print('Progress: ${updatedJob.progress}%');
  if (updatedJob.status == ExportJobStatus.completed) {
    final result = await repository.getExportResult(updatedJob);
    print('Export complete: ${result?.timeline.name}');
    break;
  }
}
```

## Code Generation

Run code generation after modifying models:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

For watch mode during development:

```bash
flutter pub run build_runner watch
```

## Testing

The data layer includes comprehensive tests:

```bash
# Run all data layer tests
flutter test test/data/

# Run specific test suites
flutter test test/data/models/
flutter test test/data/repositories/
```

### Test Structure

- **Model tests**: Validate JSON serialization/deserialization
- **Repository tests**: Mock Dio responses and test API calls
- **Error tests**: Verify error mapping logic

### Example Test

```dart
test('getProject returns project on success', () async {
  final mockData = {
    'id': 'proj_1',
    'name': 'Project 1',
    'created_at': '2024-01-01T00:00:00Z',
    'updated_at': '2024-01-01T00:00:00Z',
  };

  dioAdapter.onGet('/projects/proj_1', (server) => server.reply(200, mockData));

  final project = await repository.getProject('proj_1');

  expect(project.id, 'proj_1');
  expect(project.name, 'Project 1');
});
```

## Best Practices

1. **Always use repositories** - Never call the API client directly from UI code
2. **Handle all error cases** - Use pattern matching on ApiFailure
3. **Show upload progress** - Use onProgress callbacks for user feedback
4. **Cancel requests** - Pass CancelToken for cancellable operations
5. **Validate data** - Models validate structure, but check business rules
6. **Test serialization** - Write tests for all model fromJson/toJson
7. **Mock API calls** - Use http_mock_adapter in tests

## Migration Guide

### From Old UserRepository

```dart
// Old pattern
final dio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
final response = await dio.get('/users/$id');
final user = UserModel.fromJson(response.data);

// New pattern
final repository = ref.watch(projectRepositoryProvider);
final project = await repository.getProject(id);
```

### Environment-specific URLs

```dart
// Old
static const apiBaseUrl = 'http://localhost:8000/api';

// New
final config = ref.watch(environmentConfigProvider);
final baseUrl = config.apiBaseUrl; // Configured per environment
```

## Troubleshooting

### "Build runner fails"

Run with `--delete-conflicting-outputs`:
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### "Freezed files not generated"

Ensure imports include the generated files:
```dart
part 'my_model.freezed.dart';
part 'my_model.g.dart';
```

### "API calls timing out"

Increase timeout in compile-time constants:
```bash
flutter run --dart-define=API_CONNECT_TIMEOUT=60000
```

### "Logging not working"

Enable explicitly:
```bash
flutter run --dart-define=API_ENABLE_LOGGING=true
```

## Future Enhancements

- [ ] WebSocket support for real-time job updates
- [ ] Offline caching with Hive/Drift
- [ ] Token refresh interceptor
- [ ] Certificate pinning
- [ ] Response caching
- [ ] Pagination helpers
- [ ] GraphQL support
