import { useEffect, useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AlertCircle, CheckCircle2, Download, Film, Settings, Share2 } from 'lucide-react';
import { VideoPlayer } from '../components/VideoPlayer';
import { TimelineScrubber } from '../components/TimelineScrubber';
import { PreviewStatusBar } from '../components/PreviewStatusBar';
import { useEventSource } from '../hooks/useEventSource';
import { useExportQueue } from '../hooks/useExportQueue';
import ExportDrawer from '../components/ExportDrawer';
import { TimelinePreview, JobStatus, SubtitleCue, PreviewMedia } from '../types/preview';
import { loadSubtitles } from '../utils/subtitles';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function PreviewPlayer() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project') || 'demo';
  const jobId = searchParams.get('job');
  const { t } = useTranslation();
  const exportQueue = useExportQueue();
  const [isExportOpen, setIsExportOpen] = useState(false);

  const [preview, setPreview] = useState<TimelinePreview | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [quality, setQuality] = useState<'proxy' | 'timeline'>('proxy');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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
        const transformMedia = (media: any): PreviewMedia => {
          const metadata = media.metadata ?? {};
          return {
            ...media,
            asset_id: media.asset_id ?? media.id ?? media.relative_path,
            name: media.name ?? metadata.label ?? media.filename ?? media.asset_id ?? 'Export',
            category: media.category ?? 'export',
            relative_path: media.relative_path,
            url: `${API_BASE_URL}/storage/${media.relative_path}`,
            metadata,
          };
        };

        const mappedExports = Array.isArray(data.result.exports)
          ? (data.result.exports as any[]).map(transformMedia)
          : [];

        const previewData: TimelinePreview = {
          timeline: transformMedia(data.result.timeline),
          proxy: data.result.proxy ? transformMedia(data.result.proxy) : undefined,
          clips: data.result.clips || [],
          duration: data.result.timeline.metadata?.duration || 0,
          subtitles: [],
          exports: mappedExports,
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

  const handleSeek = (time: number) => {
    setCurrentTime(time);
  };

  const existingExports = useMemo<PreviewMedia[]>(() => {
    if (preview?.exports?.length) {
      return preview.exports;
    }

    const raw = (jobStatus?.result?.exports ?? []) as any[];
    if (!raw.length) {
      return [];
    }

    return raw.map((media: any) => {
      const metadata = media.metadata ?? {};
      return {
        ...media,
        asset_id: media.asset_id ?? media.id ?? media.relative_path,
        name: media.name ?? metadata.label ?? media.filename ?? media.asset_id ?? 'Export',
        category: media.category ?? 'export',
        relative_path: media.relative_path,
        url: `${API_BASE_URL}/storage/${media.relative_path}`,
        metadata,
      } as PreviewMedia;
    });
  }, [preview?.exports, jobStatus]);

  const videoUrl = preview
    ? quality === 'proxy' && preview.proxy
      ? preview.proxy.url
      : preview.timeline.url
    : '';

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
    <>
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
                onClick={() => setIsExportOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                title={t('export.actions.openDrawer')}
              >
                <Film size={18} />
                {t('export.actions.openDrawer')}
              </button>

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

      <ExportDrawer
        open={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        projectId={projectId}
        timelineDuration={preview.duration}
        timelineUrl={preview.timeline.url}
        existingExports={existingExports}
        exportQueue={exportQueue}
      />

      {exportQueue.notifications.length > 0 && (
        <div className="fixed bottom-6 right-6 z-50 flex w-full max-w-sm flex-col gap-3 px-4 md:px-0">
          {exportQueue.notifications.map(notification => {
            const title = t(notification.titleKey, notification.titleParams);
            const messageParams = notification.messageParams
              ? {
                  ...notification.messageParams,
                  reason:
                    typeof notification.messageParams.reason === 'string'
                      ? t(notification.messageParams.reason)
                      : notification.messageParams.reason,
                }
              : undefined;
            const description = t(notification.messageKey, messageParams);

            return (
              <div
                key={notification.id}
                className={`rounded-xl border shadow-lg ring-1 ring-black/5 backdrop-blur ${
                  notification.type === 'success'
                    ? 'border-emerald-200 bg-emerald-50/90 text-emerald-900'
                    : 'border-rose-200 bg-rose-50/90 text-rose-900'
                }`}
              >
                <div className="flex items-start gap-3 p-4">
                  {notification.type === 'success' ? (
                    <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-500" />
                  ) : (
                    <AlertCircle className="mt-0.5 h-5 w-5 text-rose-500" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-semibold">{title}</p>
                    <p className="mt-1 text-xs text-slate-600">{description}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => exportQueue.dismissNotification(notification.id)}
                        className="text-xs font-semibold text-slate-500 hover:text-slate-700"
                      >
                        {t('export.buttons.dismiss')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
