export type ExportPlatform = 'youtube_shorts' | 'tiktok' | 'instagram_reels';

export type ExportResolution = '720p' | '1080p' | '4k';

export type ExportAspectRatio = '9:16' | '1:1' | '16:9';

export type ExportStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';

export type ExportStageKey =
  | 'queued'
  | 'preparing'
  | 'rendering'
  | 'encoding'
  | 'uploading'
  | 'finalising'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface ExportJobEvent {
  stage: ExportStageKey;
  timestamp: string;
  progress: number;
  messageKey: string;
}

export interface ExportJobSimulation {
  shouldFail: boolean;
  failReason?: string;
  failEmitted?: boolean;
}

export interface ExportRequest {
  projectId: string;
  platform: ExportPlatform;
  resolution: ExportResolution;
  aspectRatio: ExportAspectRatio;
  presetLabel: string;
  durationSeconds?: number;
  sourceJobId?: string;
  displayName?: string;
  downloadBaseUrl?: string;
  attempt?: number;
}

export interface ExportJobMetadata {
  estimatedDurationSeconds: number;
  maxDurationSeconds?: number;
  recommendedResolution?: ExportResolution;
  recommendedAspectRatio?: ExportAspectRatio;
}

export interface ExportJob {
  id: string;
  projectId: string;
  status: ExportStatus;
  platform: ExportPlatform;
  resolution: ExportResolution;
  aspectRatio: ExportAspectRatio;
  progress: number;
  format: string;
  createdAt: string;
  updatedAt: string;
  etaSeconds?: number;
  durationSeconds?: number;
  fileSizeMB?: number;
  downloadUrl?: string;
  shareUrl?: string;
  openUrl?: string;
  errorMessage?: string;
  attempt: number;
  presetLabel: string;
  displayName: string;
  events: ExportJobEvent[];
  simulation?: ExportJobSimulation;
  metadata: ExportJobMetadata;
  request: ExportRequest;
}

export interface ExportNotification {
  id: string;
  jobId: string;
  type: 'success' | 'error';
  titleKey: string;
  messageKey: string;
  titleParams?: Record<string, string | number>;
  messageParams?: Record<string, string | number>;
}
