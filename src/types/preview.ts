export interface TimelineClip {
  asset_id: string;
  in_point: number;
  out_point?: number;
  transition: {
    type: 'cut' | 'crossfade' | 'fade_to_black' | 'fade_to_white';
    duration: number;
    style?: string;
  };
  subtitles?: {
    path: string;
    encoding?: string;
    force_style?: string;
  };
  include_audio: boolean;
}

export interface TimelineComposition {
  clips: TimelineClip[];
  aspect_ratio: '16:9' | '9:16' | '1:1';
  resolution: '540p' | '720p' | '1080p';
  proxy_resolution: '540p' | '720p' | '1080p';
  background_music?: {
    track: string;
    volume: number;
    offset: number;
    fade_in: number;
    fade_out: number;
    loop: boolean;
  };
  global_subtitles?: {
    path: string;
    encoding?: string;
    force_style?: string;
  };
}

export interface SubtitleCue {
  start: number;
  end: number;
  text: string;
}

export interface PreviewMedia {
  asset_id: string;
  name: string;
  category: string;
  relative_path: string;
  url: string;
  metadata: {
    duration?: number;
    width?: number;
    height?: number;
    has_audio?: boolean;
  };
}

export interface TimelinePreview {
  timeline: PreviewMedia;
  proxy?: PreviewMedia;
  clips: TimelineClip[];
  duration: number;
  subtitles: SubtitleCue[];
}

export interface JobStatus {
  job_id: string;
  job_type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  logs: string[];
  result?: any;
  created_at: string;
  updated_at: string;
}

export interface PreviewPlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  quality: string;
  isLoading: boolean;
  error?: string;
}
