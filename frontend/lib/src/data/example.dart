import 'dart:io';
import 'package:ai_video_editor_frontend/src/data/index.dart';
import 'package:ai_video_editor_frontend/src/data/config.dart';

/// Example usage of the Data Layer
/// 
/// This file demonstrates how to use the networking stack
/// to communicate with the FastAPI backend.
class DataLayerExample {
  late DataLayer _dataLayer;

  /// Initialize the data layer
  void initialize() {
    _dataLayer = DataLayer(
      baseUrl: DataConfig.getBaseUrlForEnvironment('development'),
      enableLogging: true,
    );
  }

  /// Example: Check backend health
  Future<void> checkHealth() async {
    try {
      final health = await _dataLayer.healthService.checkHealth();
      print('Backend health: ${health.status}');
      print('App: ${health.app}');
      print('Environment: ${health.environment}');
    } catch (e) {
      print('Health check failed: $e');
    }
  }

  /// Example: Get detailed diagnostics
  Future<void> checkDiagnostics() async {
    try {
      final diagnostics = await _dataLayer.healthService.checkDiagnostics();
      print('Diagnostics status: ${diagnostics.status}');
      print('Queue connected: ${diagnostics.queue.connected}');
      if (diagnostics.queue.redisVersion != null) {
        print('Redis version: ${diagnostics.queue.redisVersion}');
      }
    } catch (e) {
      print('Diagnostics check failed: $e');
    }
  }

  /// Example: Create a new project
  Future<void> createProject() async {
    try {
      final request = const ProjectCreateRequest(
        name: 'My Video Project',
        description: 'A test project for video editing',
        status: ProjectStatus.active,
      );

      final project = await _dataLayer.projectsService.createProject(request);
      print('Created project: ${project.name} (ID: ${project.id})');
      
      // Later, update the project
      final updateRequest = ProjectUpdateRequest(
        description: 'Updated project description',
      );
      
      final updatedProject = await _dataLayer.projectsService.updateProject(
        project.id,
        updateRequest,
      );
      print('Updated project description: ${updatedProject.description}');
      
    } catch (e) {
      print('Project creation failed: $e');
    }
  }

  /// Example: List projects
  Future<void> listProjects() async {
    try {
      final projects = await _dataLayer.projectsService.getProjects(
        page: 1,
        limit: 10,
      );
      
      print('Found ${projects.length} projects:');
      for (final project in projects) {
        print('- ${project.name} (${project.status.value})');
      }
    } catch (e) {
      print('Failed to list projects: $e');
    }
  }

  /// Example: Create and track a processing job
  Future<void> createAndTrackJob() async {
    try {
      // Create a job
      final job = await _dataLayer.jobsService.createJob(
        jobType: ProcessingJobType.render,
        payload: {
          'format': 'mp4',
          'resolution': '1920x1080',
          'quality': 'high',
        },
        priority: 5,
      );
      
      print('Created job: ${job.id} (${job.jobType.value})');
      
      // Monitor job progress via WebSocket
      _dataLayer.webSocketClient.messages.listen((message) {
        if (message.type == 'job_progress' && 
            message.data!['job_id'] == job.id) {
          final progress = message.data!['progress'] as int;
          final status = message.data!['status'] as String;
          print('Job progress: $progress% (Status: $status)');
        }
      });
      
      // Connect to WebSocket for real-time updates
      await _dataLayer.webSocketClient.connect();
      
      // Poll job status as fallback
      await _monitorJobProgress(job.id);
      
    } catch (e) {
      print('Job creation/monitoring failed: $e');
    }
  }

  /// Example: Upload a media asset
  Future<void> uploadAsset(String projectId, String filePath) async {
    try {
      final file = File(filePath);
      final asset = await _dataLayer.assetsService.uploadAsset(
        projectId: projectId,
        type: MediaAssetType.source,
        filename: 'video.mp4',
        file: file,
        mimeType: 'video/mp4',
      );
      
      print('Uploaded asset: ${asset.filename} (ID: ${asset.id})');
      print('Size: ${asset.sizeBytes} bytes');
      if (asset.durationSeconds != null) {
        print('Duration: ${asset.durationSeconds} seconds');
      }
    } catch (e) {
      print('Asset upload failed: $e');
    }
  }

  /// Example: Create a clip from an asset
  Future<void> createClip(String projectId, String assetId) async {
    try {
      final clip = await _dataLayer.clipsService.createClip(
        projectId: projectId,
        title: 'My First Clip',
        description: 'A short clip from the source video',
        sourceAssetId: assetId,
        startTime: 10.0,
        endTime: 30.0,
        status: ClipStatus.draft,
      );
      
      print('Created clip: ${clip.title} (ID: ${clip.id})');
      print('Time range: ${clip.startTime}s - ${clip.endTime}s');
      
      // Create a version of the clip
      final version = await _dataLayer.clipsService.createClipVersion(
        clipId: clip.id,
        notes: 'First version for review',
      );
      
      print('Created version: ${version.versionNumber} (ID: ${version.id})');
      
    } catch (e) {
      print('Clip creation failed: $e');
    }
  }

  /// Example: Get available presets
  Future<void> getExportPresets() async {
    try {
      final presets = await _dataLayer.presetsService.getPresets(
        category: PresetCategory.export,
      );
      
      print('Available export presets:');
      for (final preset in presets) {
        print('- ${preset.name} (${preset.key})');
        if (preset.description != null) {
          print('  ${preset.description}');
        }
      }
    } catch (e) {
      print('Failed to get presets: $e');
    }
  }

  /// Example: Monitor job progress
  Future<void> _monitorJobProgress(String jobId) async {
    try {
      var lastStatus = '';
      
      // Poll every 2 seconds
      while (true) {
        final job = await _dataLayer.jobsService.getJob(jobId);
        
        if (job.status != lastStatus) {
          print('Job status changed: ${job.status.value}');
          lastStatus = job.status.value;
        }
        
        if (job.status == ProcessingJobStatus.completed) {
          print('Job completed successfully!');
          if (job.resultPayload != null) {
            print('Result: ${job.resultPayload}');
          }
          break;
        } else if (job.status == ProcessingJobStatus.failed) {
          print('Job failed: ${job.errorMessage ?? 'Unknown error'}');
          break;
        } else if (job.status == ProcessingJobStatus.cancelled) {
          print('Job was cancelled');
          break;
        }
        
        await Future.delayed(const Duration(seconds: 2));
      }
    } catch (e) {
      print('Job monitoring failed: $e');
    }
  }

  /// Example: Handle authentication
  void setAuthentication(String token) {
    _dataLayer.setAuthToken(token);
    print('Authentication token set');
  }

  void clearAuthentication() {
    _dataLayer.clearAuthToken();
    print('Authentication token cleared');
  }

  /// Clean up resources
  void dispose() {
    _dataLayer.dispose();
    print('Data layer disposed');
  }
}

/// Main example function
void main() async {
  final example = DataLayerExample();
  
  try {
    // Initialize
    example.initialize();
    
    // Check if backend is available
    await example.checkHealth();
    await example.checkDiagnostics();
    
    // Set authentication (if needed)
    // example.setAuthentication('your-auth-token');
    
    // Work with projects
    await example.listProjects();
    await example.createProject();
    
    // Get export presets
    await example.getExportPresets();
    
    // Create and track a job
    await example.createAndTrackJob();
    
    // Clean up
    example.clearAuthentication();
    
  } catch (e) {
    print('Example failed: $e');
  } finally {
    example.dispose();
  }
}