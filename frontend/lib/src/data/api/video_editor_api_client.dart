import 'dart:async';

import '../models/clip.dart';
import '../models/media_asset.dart';
import '../models/project.dart';
import '../models/preset.dart';
import '../models/upload_request.dart';

abstract class VideoEditorApiClient {
  Future<List<Project>> fetchProjects();

  Future<Project> getProjectById(String id);

  Future<Project> createProject(String name);

  Future<List<MediaAsset>> fetchMediaAssets(String projectId);

  Future<MediaAsset> initiateUpload({
    required String projectId,
    required UploadRequest request,
  });

  Future<List<Clip>> fetchClips(String projectId);

  Future<List<Preset>> fetchPresets();
}

class InMemoryVideoEditorApiClient implements VideoEditorApiClient {
  InMemoryVideoEditorApiClient({
    List<Project>? projects,
    List<MediaAsset>? mediaAssets,
    List<Clip>? clips,
    List<Preset>? presets,
  })  : _projects = List<Project>.from(projects ?? const <Project>[]),
        _mediaAssets = List<MediaAsset>.from(mediaAssets ?? const <MediaAsset>[]),
        _clips = List<Clip>.from(clips ?? const <Clip>[]),
        _presets = List<Preset>.from(presets ?? const <Preset>[]);

  final List<Project> _projects;
  final List<MediaAsset> _mediaAssets;
  final List<Clip> _clips;
  final List<Preset> _presets;
  int _idCounter = 0;

  @override
  Future<List<Project>> fetchProjects() async {
    return List<Project>.unmodifiable(_projects);
  }

  @override
  Future<Project> getProjectById(String id) async {
    final project = _projects.firstWhere(
      (item) => item.id == id,
      orElse: () => throw StateError('Project $id not found'),
    );
    return project;
  }

  @override
  Future<Project> createProject(String name) async {
    final project = Project(
      id: _generateId('project'),
      name: name,
      updatedAt: DateTime.now().toUtc(),
    );
    _projects.add(project);
    return project;
  }

  @override
  Future<List<MediaAsset>> fetchMediaAssets(String projectId) async {
    return List<MediaAsset>.unmodifiable(
      _mediaAssets.where((asset) => asset.projectId == projectId),
    );
  }

  @override
  Future<MediaAsset> initiateUpload({
    required String projectId,
    required UploadRequest request,
  }) async {
    final asset = MediaAsset(
      id: _generateId('asset'),
      projectId: projectId,
      fileName: request.fileName,
      status: MediaAssetStatus.uploading,
      createdAt: DateTime.now().toUtc(),
      uploadUrl: Uri.parse('https://uploads.example.com/${_idCounter.toString()}'),
      sizeBytes: request.fileSizeBytes,
      mimeType: request.mimeType,
    );
    _mediaAssets.add(asset);
    return asset;
  }

  @override
  Future<List<Clip>> fetchClips(String projectId) async {
    return List<Clip>.unmodifiable(
      _clips.where((clip) => clip.projectId == projectId),
    );
  }

  @override
  Future<List<Preset>> fetchPresets() async {
    return List<Preset>.unmodifiable(_presets);
  }

  String _generateId(String prefix) {
    _idCounter += 1;
    return '${prefix}_$_idCounter';
  }
}
