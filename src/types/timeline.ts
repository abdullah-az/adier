export interface AIScene {
  id: string;
  asset_id: string;
  start_time: number;
  end_time: number;
  confidence: number;
  quality_score: number;
  scene_type: string;
  thumbnail_url?: string;
  description?: string;
  keywords?: string[];
}

export interface TranscriptSegment {
  id: string;
  asset_id: string;
  start_time: number;
  end_time: number;
  text: string;
  speaker?: string;
  confidence?: number;
}

export interface TimelineClipExtended {
  id: string;
  asset_id: string;
  in_point: number;
  out_point: number;
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
  order: number;
  source_type: 'ai_scene' | 'transcript' | 'manual';
  source_id?: string;
  quality_score?: number;
  confidence?: number;
}

export interface Timeline {
  id: string;
  project_id: string;
  name: string;
  clips: TimelineClipExtended[];
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
  max_duration?: number;
  created_at: string;
  updated_at: string;
}

export interface TimelineConstraints {
  max_duration: number;
  min_clip_duration: number;
  max_clip_duration: number;
  allow_overlaps: boolean;
}

export interface DraggedClip {
  type: 'ai_scene' | 'transcript' | 'timeline_clip';
  data: AIScene | TranscriptSegment | TimelineClipExtended;
  index?: number;
}
