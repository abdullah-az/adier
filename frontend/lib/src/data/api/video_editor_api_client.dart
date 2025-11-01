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

  Future<Clip> updateClipTrim({
    required String clipId,
    required int inPointMs,
    required int outPointMs,
  });

  Future<Clip> mergeClips({
    required String projectId,
    required List<String> clipIds,
    String? description,
  });

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
  Future<Clip> updateClipTrim({
    required String clipId,
    required int inPointMs,
    required int outPointMs,
  }) async {
    final index = _clips.indexWhere((c) => c.id == clipId);
    if (index == -1) {
      throw StateError('Clip $clipId not found');
    }
    final current = _clips[index];
    final boundedIn = inPointMs.clamp(0, current.duration.inMilliseconds);
    final boundedOut = outPointMs.clamp(0, current.duration.inMilliseconds);
    final normalizedIn = boundedIn is int ? boundedIn : boundedIn.toInt();
    final normalizedOut = boundedOut is int ? boundedOut : boundedOut.toInt();
    if (normalizedOut < normalizedIn) {
      throw StateError('outPoint must be >= inPoint');
    }
    final updated = current.copyWith(
      inPointMs: normalizedIn,
      outPointMs: normalizedOut,
    );
    _clips[index] = updated;
    return updated;
  }

  @override
  Future<Clip> mergeClips({
    required String projectId,
    required List<String> clipIds,
    String? description,
  }) async {
    if (clipIds.isEmpty) {
      throw ArgumentError('clipIds cannot be empty');
    }
    final selected = _clips.where((c) => clipIds.contains(c.id)).toList(growable: false);
    if (selected.isEmpty) {
      throw StateError('No clips found to merge');
    }
    selected.sort((a, b) => a.sequence.compareTo(b.sequence));

    int totalMs = 0;
    final mergedMarkers = <int>[];
    final transcripts = <String>[];
    double? avgQuality;
    int markerOffset = 0;

    for (final c in selected) {
      final inMs = c.inPointMs ?? 0;
      final outMs = c.outPointMs ?? c.duration.inMilliseconds;
      final effective = (outMs - inMs).clamp(0, c.duration.inMilliseconds);
      totalMs += effective;
      // Adjust markers by offset
      for (final m in c.markers) {
        if (m >= inMs && m <= outMs) {
          mergedMarkers.add(markerOffset + (m - inMs));
        }
      }
      markerOffset = totalMs;
      if (c.transcriptSnippet != null) transcripts.add(c.transcriptSnippet!);
      if (c.qualityScore != null) {
        avgQuality = (avgQuality == null) ? c.qualityScore : (avgQuality! + c.qualityScore!) / 2.0;
      }
    }

    final merged = Clip(
      id: _generateId('clip'),
      projectId: projectId,
      sequence: _nextSequenceForProject(projectId),
      duration: Duration(milliseconds: totalMs),
      playbackUrl: Uri.parse('https://stream.local/merged/${_idCounter.toString()}'),
      createdAt: DateTime.now().toUtc(),
      description: description ?? 'Merged clip (${clipIds.length})',
      inPointMs: 0,
      outPointMs: totalMs,
      transcriptSnippet: transcripts.isEmpty ? null : transcripts.join(' ... '),
      qualityScore: avgQuality,
      markers: mergedMarkers,
    );

    _clips.add(merged);
    return merged;
  }

  int _nextSequenceForProject(String projectId) {
    final projectClips = _clips.where((c) => c.projectId == projectId);
    if (projectClips.isEmpty) return 0;
    return projectClips.map((c) => c.sequence).reduce((a, b) => a > b ? a : b) + 1;
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
