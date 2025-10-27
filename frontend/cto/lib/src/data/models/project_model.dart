enum ProjectStatus {
  uploading,
  queued,
  processing,
  completed,
  failed,
  cancelled,
}

extension ProjectStatusX on ProjectStatus {
  String get value {
    switch (this) {
      case ProjectStatus.uploading:
        return 'uploading';
      case ProjectStatus.queued:
        return 'queued';
      case ProjectStatus.processing:
        return 'processing';
      case ProjectStatus.completed:
        return 'completed';
      case ProjectStatus.failed:
        return 'failed';
      case ProjectStatus.cancelled:
        return 'cancelled';
    }
  }

  bool get isActive =>
      this == ProjectStatus.uploading || this == ProjectStatus.processing;

  static ProjectStatus fromValue(String? value) {
    if (value == null || value.isEmpty) {
      return ProjectStatus.processing;
    }

    final normalized = value.toLowerCase();
    for (final status in ProjectStatus.values) {
      if (status.value == normalized) {
        return status;
      }
    }

    return ProjectStatus.processing;
  }
}

class ProjectModel {
  const ProjectModel({
    required this.id,
    required this.name,
    required this.updatedAt,
    required this.status,
    this.thumbnailUrl,
    this.description,
    this.progress,
    this.durationSeconds,
    this.fileSizeBytes,
  });

  final String id;
  final String name;
  final DateTime updatedAt;
  final ProjectStatus status;
  final String? thumbnailUrl;
  final String? description;
  final double? progress;
  final int? durationSeconds;
  final int? fileSizeBytes;

  ProjectModel copyWith({
    String? id,
    String? name,
    DateTime? updatedAt,
    ProjectStatus? status,
    String? thumbnailUrl,
    String? description,
    double? progress,
    int? durationSeconds,
    int? fileSizeBytes,
  }) {
    return ProjectModel(
      id: id ?? this.id,
      name: name ?? this.name,
      updatedAt: updatedAt ?? this.updatedAt,
      status: status ?? this.status,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      description: description ?? this.description,
      progress: progress ?? this.progress,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      fileSizeBytes: fileSizeBytes ?? this.fileSizeBytes,
    );
  }

  factory ProjectModel.fromJson(Map<String, dynamic> json) {
    return ProjectModel(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? json['title']?.toString() ?? '',
      updatedAt: _parseDate(json['updatedAt'] ?? json['updated_at']),
      status: ProjectStatusX.fromValue(json['status']?.toString()),
      thumbnailUrl: json['thumbnailUrl']?.toString() ?? json['thumbnail_url']?.toString(),
      description: json['description']?.toString(),
      progress: _parseProgress(json['progress']),
      durationSeconds: _parseInt(json['durationSeconds'] ?? json['duration_seconds']),
      fileSizeBytes: _parseInt(json['fileSizeBytes'] ?? json['file_size_bytes']),
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'name': name,
      'updatedAt': updatedAt.toIso8601String(),
      'status': status.value,
      if (thumbnailUrl != null) 'thumbnailUrl': thumbnailUrl,
      if (description != null) 'description': description,
      if (progress != null) 'progress': progress,
      if (durationSeconds != null) 'durationSeconds': durationSeconds,
      if (fileSizeBytes != null) 'fileSizeBytes': fileSizeBytes,
    };
  }

  static DateTime _parseDate(dynamic value) {
    if (value is DateTime) {
      return value;
    }

    if (value is String) {
      return DateTime.tryParse(value) ?? DateTime.now();
    }

    if (value is int) {
      return DateTime.fromMillisecondsSinceEpoch(value);
    }

    return DateTime.now();
  }

  static double? _parseProgress(dynamic value) {
    if (value == null) {
      return null;
    }

    if (value is int) {
      return value / 100;
    }

    if (value is double) {
      return value > 1 ? value / 100 : value;
    }

    if (value is String) {
      final parsed = double.tryParse(value);
      if (parsed == null) {
        return null;
      }
      return parsed > 1 ? parsed / 100 : parsed;
    }

    return null;
  }

  static int? _parseInt(dynamic value) {
    if (value == null) {
      return null;
    }

    if (value is int) {
      return value;
    }

    if (value is double) {
      return value.round();
    }

    if (value is String) {
      return int.tryParse(value);
    }

    return null;
  }
}
