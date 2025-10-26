class TimelineClip {
  const TimelineClip({
    required this.id,
    required this.startTime,
    required this.duration,
    required this.sourceFile,
    this.label,
    this.color,
  });

  final String id;
  final double startTime;
  final double duration;
  final String sourceFile;
  final String? label;
  final String? color;

  double get endTime => startTime + duration;

  factory TimelineClip.fromJson(Map<String, dynamic> json) {
    return TimelineClip(
      id: json['id'] as String,
      startTime: (json['start_time'] as num).toDouble(),
      duration: (json['duration'] as num).toDouble(),
      sourceFile: json['source_file'] as String,
      label: json['label'] as String?,
      color: json['color'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'start_time': startTime,
      'duration': duration,
      'source_file': sourceFile,
      if (label != null) 'label': label,
      if (color != null) 'color': color,
    };
  }
}

class SubtitleCue {
  const SubtitleCue({
    required this.startTime,
    required this.endTime,
    required this.text,
  });

  final double startTime;
  final double endTime;
  final String text;

  factory SubtitleCue.fromJson(Map<String, dynamic> json) {
    return SubtitleCue(
      startTime: (json['start_time'] as num).toDouble(),
      endTime: (json['end_time'] as num).toDouble(),
      text: json['text'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'start_time': startTime,
      'end_time': endTime,
      'text': text,
    };
  }
}

class TimelineComposition {
  const TimelineComposition({
    required this.id,
    required this.clips,
    required this.duration,
    this.resolution,
    this.fps,
  });

  final String id;
  final List<TimelineClip> clips;
  final double duration;
  final String? resolution;
  final int? fps;

  factory TimelineComposition.fromJson(Map<String, dynamic> json) {
    return TimelineComposition(
      id: json['id'] as String,
      clips: (json['clips'] as List<dynamic>)
          .map((e) => TimelineClip.fromJson(e as Map<String, dynamic>))
          .toList(),
      duration: (json['duration'] as num).toDouble(),
      resolution: json['resolution'] as String?,
      fps: json['fps'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'clips': clips.map((e) => e.toJson()).toList(),
      'duration': duration,
      if (resolution != null) 'resolution': resolution,
      if (fps != null) 'fps': fps,
    };
  }
}

enum JobStatus {
  queued,
  running,
  completed,
  failed,
  cancelled;

  factory JobStatus.fromString(String status) {
    switch (status.toLowerCase()) {
      case 'queued':
        return JobStatus.queued;
      case 'running':
        return JobStatus.running;
      case 'completed':
        return JobStatus.completed;
      case 'failed':
        return JobStatus.failed;
      case 'cancelled':
        return JobStatus.cancelled;
      default:
        return JobStatus.queued;
    }
  }

  String toJson() => name;
}

class PreviewJob {
  const PreviewJob({
    required this.id,
    required this.projectId,
    required this.status,
    this.proxyVideoUrl,
    this.subtitleUrl,
    this.timeline,
    this.progress,
    this.errorMessage,
  });

  final String id;
  final String projectId;
  final JobStatus status;
  final String? proxyVideoUrl;
  final String? subtitleUrl;
  final TimelineComposition? timeline;
  final double? progress;
  final String? errorMessage;

  bool get isReady => status == JobStatus.completed && proxyVideoUrl != null;
  bool get isProcessing => status == JobStatus.queued || status == JobStatus.running;
  bool get hasFailed => status == JobStatus.failed;

  factory PreviewJob.fromJson(Map<String, dynamic> json) {
    return PreviewJob(
      id: json['id'] as String,
      projectId: json['project_id'] as String,
      status: JobStatus.fromString(json['status'] as String),
      proxyVideoUrl: json['proxy_video_url'] as String?,
      subtitleUrl: json['subtitle_url'] as String?,
      timeline: json['timeline'] != null
          ? TimelineComposition.fromJson(json['timeline'] as Map<String, dynamic>)
          : null,
      progress: json['progress'] != null ? (json['progress'] as num).toDouble() : null,
      errorMessage: json['error_message'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'project_id': projectId,
      'status': status.toJson(),
      if (proxyVideoUrl != null) 'proxy_video_url': proxyVideoUrl,
      if (subtitleUrl != null) 'subtitle_url': subtitleUrl,
      if (timeline != null) 'timeline': timeline!.toJson(),
      if (progress != null) 'progress': progress,
      if (errorMessage != null) 'error_message': errorMessage,
    };
  }

  PreviewJob copyWith({
    String? id,
    String? projectId,
    JobStatus? status,
    String? proxyVideoUrl,
    String? subtitleUrl,
    TimelineComposition? timeline,
    double? progress,
    String? errorMessage,
  }) {
    return PreviewJob(
      id: id ?? this.id,
      projectId: projectId ?? this.projectId,
      status: status ?? this.status,
      proxyVideoUrl: proxyVideoUrl ?? this.proxyVideoUrl,
      subtitleUrl: subtitleUrl ?? this.subtitleUrl,
      timeline: timeline ?? this.timeline,
      progress: progress ?? this.progress,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class VideoPlayerState {
  const VideoPlayerState({
    this.isPlaying = false,
    this.currentPosition = Duration.zero,
    this.duration = Duration.zero,
    this.volume = 1.0,
    this.isBuffering = false,
    this.error,
  });

  final bool isPlaying;
  final Duration currentPosition;
  final Duration duration;
  final double volume;
  final bool isBuffering;
  final String? error;

  VideoPlayerState copyWith({
    bool? isPlaying,
    Duration? currentPosition,
    Duration? duration,
    double? volume,
    bool? isBuffering,
    String? error,
  }) {
    return VideoPlayerState(
      isPlaying: isPlaying ?? this.isPlaying,
      currentPosition: currentPosition ?? this.currentPosition,
      duration: duration ?? this.duration,
      volume: volume ?? this.volume,
      isBuffering: isBuffering ?? this.isBuffering,
      error: error ?? this.error,
    );
  }
}
