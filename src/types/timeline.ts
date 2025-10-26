export type TimelineSubtitleSegment = {
  id: string;
  start: number;
  end: number;
  text: string;
  language: string;
  isVisible: boolean;
};

export type TimelineMusicPlacement = 'full_timeline' | 'clip_specific';

export type TimelineMusicSettings = {
  trackId: string | null;
  volume: number;
  fadeIn: number;
  fadeOut: number;
  offset: number;
  placement: TimelineMusicPlacement;
  clipId?: string | null;
  loop: boolean;
  isEnabled: boolean;
};

export type MusicTrack = {
  trackId: string;
  filename: string;
  displayName: string;
  relativePath: string;
  sizeBytes: number;
  duration?: number | null;
};

export type TimelineSettingsPayload = {
  subtitles: TimelineSubtitleSegment[];
  music: TimelineMusicSettings;
  updatedAt: string;
};
