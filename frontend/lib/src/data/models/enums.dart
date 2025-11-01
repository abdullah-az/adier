enum ProjectStatus {
  active('active'),
  archived('archived');

  const ProjectStatus(this.value);
  final String value;

  static ProjectStatus fromString(String value) {
    return ProjectStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ProjectStatus.active,
    );
  }
}

enum MediaAssetType {
  source('source'),
  generated('generated'),
  thumbnail('thumbnail'),
  transcript('transcript');

  const MediaAssetType(this.value);
  final String value;

  static MediaAssetType fromString(String value) {
    return MediaAssetType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => MediaAssetType.source,
    );
  }
}

enum ClipStatus {
  draft('draft'),
  inReview('in_review'),
  approved('approved'),
  archived('archived');

  const ClipStatus(this.value);
  final String value;

  static ClipStatus fromString(String value) {
    return ClipStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ClipStatus.draft,
    );
  }
}

enum ClipVersionStatus {
  draft('draft'),
  rendering('rendering'),
  ready('ready'),
  failed('failed');

  const ClipVersionStatus(this.value);
  final String value;

  static ClipVersionStatus fromString(String value) {
    return ClipVersionStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ClipVersionStatus.draft,
    );
  }
}

enum ProcessingJobStatus {
  pending('pending'),
  queued('queued'),
  inProgress('in_progress'),
  completed('completed'),
  failed('failed'),
  cancelled('cancelled');

  const ProcessingJobStatus(this.value);
  final String value;

  static ProcessingJobStatus fromString(String value) {
    return ProcessingJobStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ProcessingJobStatus.pending,
    );
  }
}

enum ProcessingJobType {
  ingest('ingest'),
  transcribe('transcribe'),
  generateClip('generate_clip'),
  render('render'),
  export('export');

  const ProcessingJobType(this.value);
  final String value;

  static ProcessingJobType fromString(String value) {
    return ProcessingJobType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => ProcessingJobType.ingest,
    );
  }
}

enum PresetCategory {
  export('export'),
  style('style'),
  audio('audio');

  const PresetCategory(this.value);
  final String value;

  static PresetCategory fromString(String value) {
    return PresetCategory.values.firstWhere(
      (category) => category.value == value,
      orElse: () => PresetCategory.export,
    );
  }
}