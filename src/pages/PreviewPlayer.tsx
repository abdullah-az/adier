import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, Download, Settings, Share2 } from 'lucide-react';
import { VideoPlayer } from '../components/VideoPlayer';
import { TimelineScrubber } from '../components/TimelineScrubber';
import { PreviewStatusBar } from '../components/PreviewStatusBar';
import { SubtitleEditor } from '../components/SubtitleEditor';
import { MusicLibrary } from '../components/MusicLibrary';
import { useEventSource } from '../hooks/useEventSource';
import { TimelinePreview, JobStatus, SubtitleCue } from '../types/preview';
import type { TimelineSubtitleSegment, TimelineMusicSettings, MusicTrack } from '../types/timeline';
import {
  API_BASE_URL,
  fetchTimelineSubtitles,
  updateTimelineSubtitles,
  fetchMusicTracks,
  fetchMusicSettings,
  updateMusicSettings,
} from '../lib/api/timeline';
import { loadSubtitles } from '../utils/subtitles';

const DEFAULT_MUSIC_SETTINGS: TimelineMusicSettings = {
  trackId: null,
  volume: 0.35,
  fadeIn: 1,
  fadeOut: 1,
  offset: 0,
  placement: 'full_timeline',
  clipId: null,
  loop: true,
  isEnabled: true,
};

export function PreviewPlayer() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project') || 'demo';
  const jobId = searchParams.get('job');

  const [preview, setPreview] = useState<TimelinePreview | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [quality, setQuality] = useState<'proxy' | 'timeline'>('proxy');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [subtitleSegments, setSubtitleSegments] = useState<TimelineSubtitleSegment[]>([]);
  const [isSavingSubtitles, setIsSavingSubtitles] = useState(false);
  const [subtitleError, setSubtitleError] = useState<string | null>(null);
  const subtitleSaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const subtitleInitialisedRef = useRef(false);
  const subtitleLatestRef = useRef<TimelineSubtitleSegment[]>([]);

  const [musicTracks, setMusicTracks] = useState<MusicTrack[]>([]);
  const [musicSettings, setMusicSettings] = useState<TimelineMusicSettings>(DEFAULT_MUSIC_SETTINGS);
  const [isSavingMusic, setIsSavingMusic] = useState(false);
  const [musicError, setMusicError] = useState<string | null>(null);
  const musicSaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const musicInitialisedRef = useRef(false);
  const musicLatestRef = useRef<TimelineMusicSettings>(DEFAULT_MUSIC_SETTINGS);
  const [isTimelineDataLoading, setIsTimelineDataLoading] = useState(false);

  const fetchJobStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/jobs/${jobId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }
      const data = await response.json();
      setJobStatus(data);

      if (data.status === 'completed' && data.result) {
        const previewData: TimelinePreview = {
          timeline: {
            ...data.result.timeline,
            url: `${API_BASE_URL}/storage/${data.result.timeline.relative_path}`,
          },
          proxy: data.result.proxy
            ? {
                ...data.result.proxy,
                url: `${API_BASE_URL}/storage/${data.result.proxy.relative_path}`,
              }
            : undefined,
          clips: data.result.clips || [],
          duration: data.result.timeline.metadata?.duration || 0,
          subtitles: [],
        };

        if (data.result.global_subtitles?.path) {
          const subtitleUrl = `${API_BASE_URL}/storage/${data.result.global_subtitles.path}`;
          loadSubtitles(subtitleUrl).then(subs => {
            previewData.subtitles = subs;
            setPreview({ ...previewData });
          }).catch(err => {
            console.error('Failed to load subtitles:', err);
            setPreview(previewData);
          });
        } else {
          setPreview(previewData);
        }
        
        setIsLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preview');
      setIsLoading(false);
    }
  }, [jobId, projectId]);

  const handleJobUpdate = useCallback((data: JobStatus) => {
    setJobStatus(data);
    if (data.status === 'completed') {
      fetchJobStatus();
    }
  }, [fetchJobStatus]);

  useEventSource(
    jobId ? `${API_BASE_URL}/projects/${projectId}/jobs/${jobId}/events` : null,
    {
      onMessage: handleJobUpdate,
      onError: (err) => {
        console.error('EventSource error:', err);
      },
      enabled: jobStatus?.status !== 'completed' && jobStatus?.status !== 'failed',
    }
  );

  useEffect(() => {
    if (jobId) {
      fetchJobStatus();
    } else {
      setError('No job ID provided');
      setIsLoading(false);
    }
  }, [jobId, fetchJobStatus]);

  useEffect(() => {
    if (!projectId) return;
    let ignore = false;

    const loadTimelineData = async () => {
      setIsTimelineDataLoading(true);
      try {
        const [subtitlesResult, tracksResult, musicResult] = await Promise.allSettled([
          fetchTimelineSubtitles(projectId),
          fetchMusicTracks(projectId),
          fetchMusicSettings(projectId),
        ]);

        if (ignore) return;

        if (subtitlesResult.status === 'fulfilled') {
          const segments = subtitlesResult.value.segments || [];
          if (segments.length > 0) {
            setSubtitleSegments(segments);
            subtitleLatestRef.current = segments;
            subtitleInitialisedRef.current = true;
            setSubtitleError(null);
          }
        } else if (!subtitleInitialisedRef.current) {
          setSubtitleError('Failed to load subtitles');
        }

        if (tracksResult.status === 'fulfilled') {
          setMusicTracks(tracksResult.value);
        }

        if (musicResult.status === 'fulfilled') {
          const mergedSettings = {
            ...DEFAULT_MUSIC_SETTINGS,
            ...musicResult.value.settings,
          };
          setMusicSettings(mergedSettings);
          musicLatestRef.current = mergedSettings;
          musicInitialisedRef.current = true;
          setMusicError(null);
        } else if (!musicInitialisedRef.current) {
          setMusicSettings(DEFAULT_MUSIC_SETTINGS);
          musicLatestRef.current = DEFAULT_MUSIC_SETTINGS;
          musicInitialisedRef.current = true;
          setMusicError('Failed to load music settings');
        }
      } catch (err) {
        if (!ignore) {
          setSubtitleError(prev => prev ?? 'Failed to load subtitles');
          setMusicError(prev => prev ?? 'Failed to load music settings');
        }
      } finally {
        if (!ignore) {
          setIsTimelineDataLoading(false);
        }
      }
    };

    loadTimelineData();

    return () => {
      ignore = true;
    };
  }, [projectId]);

  useEffect(() => {
    if (subtitleInitialisedRef.current) return;
    if (!preview?.subtitles || preview.subtitles.length === 0) return;

    const fallback = preview.subtitles.map((cue, index) => ({
      id: `cue-${index}`,
      start: cue.start,
      end: cue.end,
      text: cue.text,
      language: 'auto',
      isVisible: true,
    }));
    setSubtitleSegments(fallback);
    subtitleLatestRef.current = fallback;
    subtitleInitialisedRef.current = true;
  }, [preview?.subtitles]);

  const scheduleSubtitleSave = useCallback(
    (segments: TimelineSubtitleSegment[]) => {
      if (!projectId) return;
      setSubtitleError(null);
      setIsSavingSubtitles(true);
      if (subtitleSaveTimeoutRef.current) {
        window.clearTimeout(subtitleSaveTimeoutRef.current);
      }
      subtitleSaveTimeoutRef.current = window.setTimeout(async () => {
        try {
          const response = await updateTimelineSubtitles(projectId, segments);
          if (subtitleLatestRef.current !== segments) {
            return;
          }
          setSubtitleSegments(response.segments);
          subtitleLatestRef.current = response.segments;
          setSubtitleError(null);
        } catch (err) {
          if (subtitleLatestRef.current === segments) {
            setSubtitleError(err instanceof Error ? err.message : 'Failed to save subtitles');
          }
        } finally {
          subtitleSaveTimeoutRef.current = null;
          if (subtitleLatestRef.current === segments) {
            setIsSavingSubtitles(false);
          }
        }
      }, 600);
    },
    [projectId],
  );

  const handleSubtitleSegmentsChange = useCallback(
    (segments: TimelineSubtitleSegment[]) => {
      setSubtitleSegments(segments);
      subtitleLatestRef.current = segments;
      if (!subtitleInitialisedRef.current) {
        subtitleInitialisedRef.current = true;
      }
      scheduleSubtitleSave(segments);
    },
    [scheduleSubtitleSave],
  );

  const scheduleMusicSave = useCallback(
    (settings: TimelineMusicSettings) => {
      if (!projectId) return;
      setMusicError(null);
      setIsSavingMusic(true);
      if (musicSaveTimeoutRef.current) {
        window.clearTimeout(musicSaveTimeoutRef.current);
      }
      musicSaveTimeoutRef.current = window.setTimeout(async () => {
        try {
          const response = await updateMusicSettings(projectId, settings);
          if (musicLatestRef.current !== settings) {
            return;
          }
          const mergedSettings = {
            ...DEFAULT_MUSIC_SETTINGS,
            ...response.settings,
          };
          setMusicSettings(mergedSettings);
          musicLatestRef.current = mergedSettings;
          setMusicError(null);
        } catch (err) {
          if (musicLatestRef.current === settings) {
            setMusicError(err instanceof Error ? err.message : 'Failed to save music settings');
          }
        } finally {
          musicSaveTimeoutRef.current = null;
          if (musicLatestRef.current === settings) {
            setIsSavingMusic(false);
          }
        }
      }, 600);
    },
    [projectId],
  );

  const handleMusicSettingsChange = useCallback(
    (settings: TimelineMusicSettings) => {
      setMusicSettings(settings);
      musicLatestRef.current = settings;
      if (!musicInitialisedRef.current) {
        musicInitialisedRef.current = true;
      }
      scheduleMusicSave(settings);
    },
    [scheduleMusicSave],
  );

  const handleSeek = (time: number) => {
    setCurrentTime(time);
  };

  useEffect(() => {
    subtitleLatestRef.current = subtitleSegments;
  }, [subtitleSegments]);

  useEffect(() => {
    musicLatestRef.current = musicSettings;
  }, [musicSettings]);

  useEffect(() => {
    return () => {
      if (subtitleSaveTimeoutRef.current) {
        window.clearTimeout(subtitleSaveTimeoutRef.current);
      }
      if (musicSaveTimeoutRef.current) {
        window.clearTimeout(musicSaveTimeoutRef.current);
      }
    };
  }, []);

  const videoUrl = preview
    ? quality === 'proxy' && preview.proxy
      ? preview.proxy.url
      : preview.timeline.url
    : '';

  const subtitleCues: SubtitleCue[] = useMemo(() => {
    if (subtitleSegments.length > 0) {
      return subtitleSegments
        .filter(segment => segment.isVisible)
        .map(segment => ({
          start: segment.start,
          end: segment.end,
          text: segment.text,
        }));
    }
    return preview?.subtitles ?? [];
  }, [subtitleSegments, preview?.subtitles]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading preview...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to Load Preview</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Preview Not Ready</h2>
          <p className="text-gray-600 mb-4">
            The preview is being generated. Please wait...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Timeline Preview</h1>
            <p className="text-gray-600 mt-1">Project: {projectId}</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white border rounded-lg px-3 py-2">
              <span className="text-sm text-gray-600">Quality:</span>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value as 'proxy' | 'timeline')}
                className="text-sm font-medium bg-transparent border-none outline-none cursor-pointer"
                disabled={!preview.proxy}
              >
                <option value="proxy">Proxy (Fast)</option>
                <option value="timeline">Timeline (High Quality)</option>
              </select>
            </div>

            <button
              className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition"
              title="Share"
            >
              <Share2 size={18} />
              Share
            </button>

            <button
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              title="Download"
            >
              <Download size={18} />
              Download
            </button>
          </div>
        </div>

        {jobStatus && jobStatus.status !== 'completed' && (
          <PreviewStatusBar
            jobStatus={jobStatus}
            onRefresh={fetchJobStatus}
            className="mb-6"
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <VideoPlayer
              src={videoUrl}
              subtitles={preview.subtitles}
              onTimeUpdate={setCurrentTime}
              className="aspect-video"
            />

            <div className="mt-6 bg-white rounded-lg p-6 shadow-sm">
              <TimelineScrubber
                clips={preview.clips}
                currentTime={currentTime}
                duration={preview.duration}
                onSeek={handleSeek}
              />
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Settings size={20} />
                Timeline Info
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Clips:</span>
                  <span className="font-medium">{preview.clips.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="font-medium">{preview.duration.toFixed(2)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Resolution:</span>
                  <span className="font-medium">
                    {preview.timeline.metadata.width}x{preview.timeline.metadata.height}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Audio:</span>
                  <span className="font-medium">
                    {preview.timeline.metadata.has_audio ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-4">Clips</h3>
              <div className="space-y-2">
                {preview.clips.map((clip, index) => (
                  <div
                    key={index}
                    className="p-3 border rounded hover:bg-gray-50 cursor-pointer transition"
                    onClick={() => {
                      let time = 0;
                      for (let i = 0; i < index; i++) {
                        const clipDuration = preview.clips[i].out_point
                          ? preview.clips[i].out_point! - preview.clips[i].in_point
                          : 5;
                        time += clipDuration;
                      }
                      handleSeek(time);
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm">Clip {index + 1}</span>
                      <span className="text-xs text-gray-500">
                        {clip.transition.type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      {clip.in_point.toFixed(1)}s - {clip.out_point?.toFixed(1) || 'end'}s
                    </div>
                    {clip.subtitles && (
                      <div className="text-xs text-blue-600 mt-1">Has subtitles</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
