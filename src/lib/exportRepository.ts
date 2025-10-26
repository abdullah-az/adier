import {
  CreateExportJobPayload,
  ExportJob,
  ExportJobEventPayload,
  ExportJobHistoryEntry,
  ExportStatus,
  ExportPresetPlatform,
} from '../types/export';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ExportJobApiHistoryEntry {
  status: ExportStatus;
  message?: string;
  progress?: number;
  timestamp: string;
}

interface ExportJobApiResult {
  url: string;
  filename?: string;
  filesize?: number;
  format?: string;
  relative_path?: string;
  thumbnail_url?: string;
  metadata?: Record<string, unknown> & {
    durationSeconds?: number;
    duration_seconds?: number;
    duration?: number;
  };
}

interface ExportJobApiResponse {
  job_id: string;
  preset_id: string;
  preset_name?: string;
  platform?: string;
  aspect_ratio?: string;
  resolution: string;
  status: ExportStatus;
  progress?: number;
  message?: string;
  created_at: string;
  updated_at: string;
  history?: ExportJobApiHistoryEntry[];
  result?: ExportJobApiResult;
  failure_reason?: string;
}

function normalizeResolution(value: string): '720p' | '1080p' | '4K' {
  switch (value?.toLowerCase()) {
    case '720p':
    case '720':
      return '720p';
    case '4k':
    case '2160p':
      return '4K';
    case '1080':
    case '1080p':
    default:
      return '1080p';
  }
}

function normalizePlatform(value?: string): ExportPresetPlatform {
  if (!value) {
    return 'instagram_reels';
  }
  const normalized = value.toLowerCase();
  if (normalized.includes('tiktok')) {
    return 'tiktok';
  }
  if (normalized.includes('youtube')) {
    return 'youtube_shorts';
  }
  return 'instagram_reels';
}

function sortHistory(history: ExportJobHistoryEntry[] = []): ExportJobHistoryEntry[] {
  return [...history].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
}

function ensureHistoryEntries(job: ExportJobApiResponse, history: ExportJobHistoryEntry[]): ExportJobHistoryEntry[] {
  const deduped = new Map<ExportStatus, ExportJobHistoryEntry>();
  history.forEach((entry) => {
    if (!entry.timestamp) {
      return;
    }
    const existing = deduped.get(entry.status);
    if (!existing || new Date(existing.timestamp).getTime() < new Date(entry.timestamp).getTime()) {
      deduped.set(entry.status, entry);
    }
  });

  if (!deduped.has('queued')) {
    deduped.set('queued', {
      status: 'queued',
      timestamp: job.created_at,
      message: job.message,
      progress: job.progress,
    });
  }

  const currentStatusEntry = deduped.get(job.status);
  if (!currentStatusEntry) {
    deduped.set(job.status, {
      status: job.status,
      timestamp: job.updated_at,
      message: job.message,
      progress: job.progress,
    });
  }

  return sortHistory(Array.from(deduped.values()));
}

function mapApiResult(result?: ExportJobApiResult) {
  if (!result) {
    return undefined;
  }

  const durationFromMetadata =
    (result.metadata?.durationSeconds as number | undefined) ??
    (result.metadata?.duration_seconds as number | undefined) ??
    (result.metadata?.duration as number | undefined);

  return {
    url: result.url,
    filename: result.filename ?? 'export.mp4',
    filesize: result.filesize ?? 0,
    format: result.format ?? 'mp4',
    relativePath: result.relative_path,
    thumbnailUrl: result.thumbnail_url,
    metadata: {
      ...result.metadata,
      durationSeconds: durationFromMetadata,
    },
  };
}

function mapExportJob(payload: ExportJobApiResponse): ExportJob {
  const historyEntries: ExportJobHistoryEntry[] = (payload.history ?? []).map((entry) => ({
    status: entry.status,
    message: entry.message,
    progress: entry.progress,
    timestamp: entry.timestamp,
  }));

  const history = ensureHistoryEntries(payload, historyEntries);

  return {
    id: payload.job_id,
    presetId: payload.preset_id,
    presetName: payload.preset_name ?? payload.preset_id,
    platform: normalizePlatform(payload.platform),
    aspectRatio: payload.aspect_ratio ?? '9:16',
    resolution: normalizeResolution(payload.resolution),
    status: payload.status,
    progress: typeof payload.progress === 'number' ? payload.progress : 0,
    message: payload.message,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
    history,
    result: mapApiResult(payload.result),
    failureReason: payload.failure_reason,
  };
}

async function requestJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = {
    Accept: 'application/json',
    ...(init.headers || {}),
  } as Record<string, string>;

  const response = await fetch(url, {
    ...init,
    headers: init.body ? { 'Content-Type': 'application/json', ...headers } : headers,
    credentials: 'include',
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = (isJson && (payload?.message || payload?.error)) || response.statusText;
    throw new Error(typeof message === 'string' ? message : 'Request failed');
  }

  return payload as T;
}

function unwrapJobResponse(payload: any): ExportJobApiResponse {
  if (!payload) {
    throw new Error('Missing export job payload');
  }
  if (Array.isArray(payload)) {
    return payload[0];
  }
  if (payload.job) {
    return payload.job as ExportJobApiResponse;
  }
  if (payload.data && !Array.isArray(payload.data)) {
    return payload.data as ExportJobApiResponse;
  }
  return payload as ExportJobApiResponse;
}

function unwrapJobList(payload: any): ExportJobApiResponse[] {
  if (!payload) {
    return [];
  }
  if (Array.isArray(payload)) {
    return payload as ExportJobApiResponse[];
  }
  if (Array.isArray(payload.data)) {
    return payload.data as ExportJobApiResponse[];
  }
  if (Array.isArray(payload.jobs)) {
    return payload.jobs as ExportJobApiResponse[];
  }
  return [];
}

export async function listExportJobs(projectId: string): Promise<ExportJob[]> {
  const payload = await requestJson<any>(`${API_BASE_URL}/projects/${projectId}/exports`);
  const jobs = unwrapJobList(payload);
  return jobs.map(mapExportJob);
}

export async function getExportJob(projectId: string, jobId: string): Promise<ExportJob> {
  const payload = await requestJson<any>(`${API_BASE_URL}/projects/${projectId}/exports/${jobId}`);
  return mapExportJob(unwrapJobResponse(payload));
}

export async function createExportJob(
  projectId: string,
  payload: CreateExportJobPayload
): Promise<ExportJob> {
  const body: Record<string, unknown> = {
    preset_id: payload.presetId,
    resolution: payload.resolution,
  };

  if (typeof payload.includeCaptions === 'boolean') {
    body.include_captions = payload.includeCaptions;
  }
  if (typeof payload.autoShare === 'boolean') {
    body.auto_share = payload.autoShare;
  }
  if (payload.fileName) {
    body.file_name = payload.fileName;
  }

  const response = await requestJson<any>(`${API_BASE_URL}/projects/${projectId}/exports`, {
    method: 'POST',
    body: JSON.stringify(body),
  });

  return mapExportJob(unwrapJobResponse(response));
}

export async function cancelExportJob(projectId: string, jobId: string): Promise<ExportJob | null> {
  const response = await requestJson<any>(`${API_BASE_URL}/projects/${projectId}/exports/${jobId}/cancel`, {
    method: 'POST',
  });

  if (!response) {
    return null;
  }

  return mapExportJob(unwrapJobResponse(response));
}

export async function retryExportJob(projectId: string, jobId: string): Promise<ExportJob> {
  const response = await requestJson<any>(`${API_BASE_URL}/projects/${projectId}/exports/${jobId}/retry`, {
    method: 'POST',
  });

  return mapExportJob(unwrapJobResponse(response));
}

export function mergeJobUpdate(job: ExportJob, update: ExportJobEventPayload): ExportJob {
  const nextStatus = update.status ?? job.status;
  const nextProgress = typeof update.progress === 'number' ? update.progress : job.progress;
  const nextMessage = update.message ?? job.message;
  const nextUpdatedAt = update.timestamp ?? new Date().toISOString();

  const mergedHistory: ExportJobHistoryEntry[] = [...job.history];

  if (update.history?.length) {
    update.history.forEach((entry) => {
      mergedHistory.push({
        status: entry.status,
        message: entry.message,
        progress: entry.progress,
        timestamp: entry.timestamp,
      });
    });
  }

  const nextHistory = ensureHistoryEntries(
    {
      job_id: job.id,
      preset_id: job.presetId,
      preset_name: job.presetName,
      platform: job.platform,
      aspect_ratio: job.aspectRatio,
      resolution: job.resolution,
      status: nextStatus,
      progress: nextProgress,
      message: nextMessage,
      created_at: job.createdAt,
      updated_at: nextUpdatedAt,
      failure_reason: update.failure_reason ?? job.failureReason,
      history: mergedHistory.map((entry) => ({
        status: entry.status,
        message: entry.message,
        progress: entry.progress,
        timestamp: entry.timestamp,
      })),
      result: update.result as ExportJobApiResult | undefined,
    },
    mergedHistory
  );

  const mappedResult = update.result ? mapApiResult(update.result as ExportJobApiResult) : job.result;

  return {
    ...job,
    status: nextStatus,
    progress: nextProgress,
    message: nextMessage,
    updatedAt: nextUpdatedAt,
    history: nextHistory,
    result: mappedResult,
    failureReason: update.failure_reason ?? job.failureReason,
  };
}
