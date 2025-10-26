export type ExportResolution = '720p' | '1080p' | '4K';

export type ExportStatus = 'queued' | 'running' | 'completed' | 'failed' | 'canceled';

export type ExportPresetPlatform = 'youtube_shorts' | 'tiktok' | 'instagram_reels';

export interface ExportPreset {
  id: string;
  name: string;
  description: string;
  platform: ExportPresetPlatform;
  aspectRatio: '9:16' | '1:1' | '16:9';
  supportedResolutions: ExportResolution[];
  defaultFileName?: string;
  maxDurationSeconds?: number;
}

export interface ExportJobHistoryEntry {
  status: ExportStatus;
  message?: string;
  timestamp: string;
  progress?: number;
}

export interface ExportJobResultMetadata {
  durationSeconds?: number;
  frameRate?: number;
  audioChannels?: number;
  codec?: string;
  bitrate?: number;
  [key: string]: unknown;
}

export interface ExportJobResult {
  url: string;
  filename: string;
  filesize: number;
  format: string;
  relativePath?: string;
  thumbnailUrl?: string;
  metadata?: ExportJobResultMetadata;
}

export interface ExportJob {
  id: string;
  presetId: string;
  presetName: string;
  platform: ExportPresetPlatform;
  aspectRatio: string;
  resolution: ExportResolution;
  status: ExportStatus;
  progress: number;
  message?: string;
  createdAt: string;
  updatedAt: string;
  history: ExportJobHistoryEntry[];
  result?: ExportJobResult;
  failureReason?: string;
}

export interface CreateExportJobPayload {
  presetId: string;
  resolution: ExportResolution;
  includeCaptions?: boolean;
  autoShare?: boolean;
  fileName?: string;
}

export interface ExportJobEventPayload {
  job_id: string;
  status: ExportStatus;
  progress?: number;
  message?: string;
  timestamp?: string;
  result?: ExportJobResult;
  failure_reason?: string;
  history?: ExportJobHistoryEntry[];
}
