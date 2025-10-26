import type {
  MusicTrack,
  TimelineMusicSettings,
  TimelineMusicPlacement,
  TimelineSubtitleSegment,
  TimelineSettingsPayload,
} from '../../types/timeline';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const buildTimelineUrl = (projectId: string, path: string) =>
  `${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/timeline${path}`;

const mapSubtitleFromApi = (segment: any): TimelineSubtitleSegment => ({
  id: segment.id,
  start: Number(segment.start) || 0,
  end: Number(segment.end) || 0,
  text: segment.text ?? '',
  language: segment.language ?? 'en',
  isVisible: segment.is_visible ?? true,
});

const mapSubtitleToApi = (segment: TimelineSubtitleSegment) => ({
  id: segment.id,
  start: segment.start,
  end: segment.end,
  text: segment.text,
  language: segment.language,
  is_visible: segment.isVisible,
});

const mapMusicSettingsFromApi = (payload: any): TimelineMusicSettings => ({
  trackId: payload.track_id ?? null,
  volume: payload.volume ?? 0.35,
  fadeIn: payload.fade_in ?? 1,
  fadeOut: payload.fade_out ?? 1,
  offset: payload.offset ?? 0,
  placement: (payload.placement ?? 'full_timeline') as TimelineMusicPlacement,
  clipId: payload.clip_id ?? null,
  loop: payload.loop ?? true,
  isEnabled: payload.is_enabled ?? true,
});

const mapMusicSettingsToApi = (settings: TimelineMusicSettings) => ({
  track_id: settings.trackId,
  volume: settings.volume,
  fade_in: settings.fadeIn,
  fade_out: settings.fadeOut,
  offset: settings.offset,
  placement: settings.placement,
  clip_id: settings.clipId,
  loop: settings.loop,
  is_enabled: settings.isEnabled,
});

const mapTrackFromApi = (payload: any): MusicTrack => ({
  trackId: payload.track_id,
  filename: payload.filename,
  displayName: payload.display_name,
  relativePath: payload.relative_path,
  sizeBytes: payload.size_bytes ?? 0,
  duration: payload.duration ?? null,
});

export const buildStorageUrl = (relativePath: string) =>
  `${API_BASE_URL}/storage/${relativePath
    .split('/')
    .map(encodeURIComponent)
    .join('/')}`;

export async function fetchTimelineSettings(projectId: string): Promise<TimelineSettingsPayload> {
  const response = await fetch(buildTimelineUrl(projectId, ''));
  if (!response.ok) {
    throw new Error('Failed to load timeline settings');
  }
  const data = await response.json();
  return {
    subtitles: (data.subtitles ?? []).map(mapSubtitleFromApi),
    music: mapMusicSettingsFromApi(data.music ?? {}),
    updatedAt: data.updated_at ?? new Date().toISOString(),
  };
}

export async function fetchTimelineSubtitles(projectId: string): Promise<{
  segments: TimelineSubtitleSegment[];
  updatedAt: string;
}> {
  const response = await fetch(buildTimelineUrl(projectId, '/subtitles'));
  if (!response.ok) {
    throw new Error('Failed to load subtitles');
  }
  const data = await response.json();
  return {
    segments: (data.segments ?? []).map(mapSubtitleFromApi),
    updatedAt: data.updated_at ?? new Date().toISOString(),
  };
}

export async function updateTimelineSubtitles(
  projectId: string,
  segments: TimelineSubtitleSegment[],
): Promise<{
  segments: TimelineSubtitleSegment[];
  updatedAt: string;
}> {
  const response = await fetch(buildTimelineUrl(projectId, '/subtitles'), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ segments: segments.map(mapSubtitleToApi) }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Failed to update subtitles');
  }

  const data = await response.json();
  return {
    segments: (data.segments ?? []).map(mapSubtitleFromApi),
    updatedAt: data.updated_at ?? new Date().toISOString(),
  };
}

export async function fetchMusicTracks(projectId: string): Promise<MusicTrack[]> {
  const response = await fetch(buildTimelineUrl(projectId, '/music/tracks'));
  if (!response.ok) {
    throw new Error('Failed to load music tracks');
  }
  const data = await response.json();
  return (data.tracks ?? []).map(mapTrackFromApi);
}

export async function fetchMusicSettings(projectId: string): Promise<{
  settings: TimelineMusicSettings;
  updatedAt: string;
}> {
  const response = await fetch(buildTimelineUrl(projectId, '/music'));
  if (!response.ok) {
    throw new Error('Failed to load music settings');
  }
  const data = await response.json();
  return {
    settings: mapMusicSettingsFromApi(data),
    updatedAt: data.updated_at ?? new Date().toISOString(),
  };
}

export async function updateMusicSettings(
  projectId: string,
  settings: TimelineMusicSettings,
): Promise<{
  settings: TimelineMusicSettings;
  updatedAt: string;
}> {
  const response = await fetch(buildTimelineUrl(projectId, '/music'), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(mapMusicSettingsToApi(settings)),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || 'Failed to update music settings');
  }

  const data = await response.json();
  return {
    settings: mapMusicSettingsFromApi(data),
    updatedAt: data.updated_at ?? new Date().toISOString(),
  };
}
