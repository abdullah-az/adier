import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  Download,
  Plus,
  RefreshCw,
  Settings,
  Share2,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { VideoPlayer } from '../components/VideoPlayer';
import { TimelineScrubber } from '../components/TimelineScrubber';
import { PreviewStatusBar } from '../components/PreviewStatusBar';
import { useEventSource } from '../hooks/useEventSource';
import { TimelinePreview, JobStatus } from '../types/preview';
import { loadSubtitles } from '../utils/subtitles';
import { ExportDrawer, QueueExportSelection } from '../components/ExportDrawer';
import { ExportJobCard } from '../components/ExportJobCard';
import { NotificationStack, NotificationItem, NotificationType } from '../components/NotificationStack';
import {
  ExportJob,
  ExportJobEventPayload,
  ExportPreset,
  ExportResolution,
} from '../types/export';
import {
  listExportJobs,
  createExportJob,
  cancelExportJob,
  retryExportJob,
  getExportJob,
  mergeJobUpdate,
} from '../lib/exportRepository';
import { sanitizeFileNameSegment } from '../utils/format';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EXPORT_PRESET_DEFINITIONS = [
  {
    id: 'youtube_shorts_vertical',
    platform: 'youtube_shorts',
    aspectRatio: '9:16' as const,
    supportedResolutions: ['720p', '1080p'] as ExportResolution[],
    nameKey: 'preview.export.presets.youtubeShortsVertical.name',
    descriptionKey: 'preview.export.presets.youtubeShortsVertical.description',
    fileNameSegment: 'yt-shorts',
  },
  {
    id: 'tiktok_vertical',
    platform: 'tiktok',
    aspectRatio: '9:16' as const,
    supportedResolutions: ['720p', '1080p'] as ExportResolution[],
    nameKey: 'preview.export.presets.tiktokVertical.name',
    descriptionKey: 'preview.export.presets.tiktokVertical.description',
    fileNameSegment: 'tiktok',
  },
  {
    id: 'instagram_reels_vertical',
    platform: 'instagram_reels',
    aspectRatio: '9:16' as const,
    supportedResolutions: ['720p', '1080p'] as ExportResolution[],
    nameKey: 'preview.export.presets.instagramVertical.name',
    descriptionKey: 'preview.export.presets.instagramVertical.description',
    fileNameSegment: 'reels-vertical',
  },
  {
    id: 'instagram_reels_square',
    platform: 'instagram_reels',
    aspectRatio: '1:1' as const,
    supportedResolutions: ['720p', '1080p'] as ExportResolution[],
    nameKey: 'preview.export.presets.instagramSquare.name',
    descriptionKey: 'preview.export.presets.instagramSquare.description',
    fileNameSegment: 'reels-square',
  },
  {
    id: 'instagram_reels_landscape',
    platform: 'instagram_reels',
    aspectRatio: '16:9' as const,
    supportedResolutions: ['1080p', '4K'] as ExportResolution[],
    nameKey: 'preview.export.presets.instagramLandscape.name',
    descriptionKey: 'preview.export.presets.instagramLandscape.description',
    fileNameSegment: 'reels-landscape',
  },
] as const;

const ACTIVE_EXPORT_STATUSES = new Set<ExportJob['status']>(['queued', 'running']);

function ensureExtension(fileName: string, extension = 'mp4'): string {
  const ext = extension.startsWith('.') ? extension : `.${extension}`;
  return fileName.toLowerCase().endsWith(ext.toLowerCase()) ? fileName : `${fileName}${ext}`;
}

function buildDefaultExportFileName(
  projectId: string,
  preset: ExportPreset,
  resolution: ExportResolution
): string {
  const baseSegments = [
    sanitizeFileNameSegment(projectId),
    sanitizeFileNameSegment(preset.defaultFileName ?? preset.name),
    sanitizeFileNameSegment(preset.aspectRatio.replace(':', '-')),
    sanitizeFileNameSegment(resolution),
  ].filter(Boolean);

  const baseName = baseSegments.join('-') || 'export';
  return ensureExtension(baseName, 'mp4');
}

function sortExportJobs(jobs: ExportJob[]): ExportJob[] {
  const priority: Record<ExportJob['status'], number> = {
    running: 0,
    queued: 1,
    failed: 2,
    canceled: 3,
    completed: 4,
  } as const;

  return [...jobs].sort((a, b) => {
    const priorityDiff = (priority[a.status] ?? 99) - (priority[b.status] ?? 99);
    if (priorityDiff !== 0) {
      return priorityDiff;
    }
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });
}

interface ExportJobEventListenerProps {
  projectId: string;
  job: ExportJob;
  onEvent: (event: ExportJobEventPayload) => void;
}

function ExportJobEventListener({ projectId, job, onEvent }: ExportJobEventListenerProps) {
  const isActive = ACTIVE_EXPORT_STATUSES.has(job.status);
  const url = isActive
    ? `${API_BASE_URL}/projects/${projectId}/exports/${job.id}/events`
    : null;

  useEventSource(url, {
    onMessage: (payload) => {
      const event: ExportJobEventPayload = {
        ...payload,
        job_id: payload.job_id ?? job.id,
      };
      onEvent(event);
    },
    enabled: isActive,
    onError: (error) => {
      console.error('Export SSE connection error:', error);
    },
  });

  return null;
}

export function PreviewPlayer() {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();

  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project') || 'demo';
  const jobId = searchParams.get('job');

  const [preview, setPreview] = useState<TimelinePreview | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [quality, setQuality] = useState<'proxy' | 'timeline'>('proxy');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [exportsLoading, setExportsLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [isExportDrawerOpen, setIsExportDrawerOpen] = useState(false);
  const [isQueueingExport, setIsQueueingExport] = useState(false);
  const [jobActionState, setJobActionState] = useState<Record<string, { canceling?: boolean; retrying?: boolean }>>({});
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const exportPresets = useMemo<ExportPreset[]>(
    () =>
      EXPORT_PRESET_DEFINITIONS.map((definition) => ({
        id: definition.id,
        name: t(definition.nameKey),
        description: t(definition.descriptionKey),
        platform: definition.platform,
        aspectRatio: definition.aspectRatio,
        supportedResolutions: definition.supportedResolutions,
        defaultFileName: definition.fileNameSegment,
      })),
    [t]
  );

  const pushNotification = useCallback(
    (type: NotificationType, title: string, message?: string) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const notification: NotificationItem = {
        id,
        type,
        title,
        message,
        createdAt: Date.now(),
      };
      setNotifications((prev) => [...prev, notification]);

      if (typeof window !== 'undefined') {
        window.setTimeout(() => {
          setNotifications((prev) => prev.filter((item) => item.id !== id));
        }, 6000);
      }
    },
    []
  );

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));
  }, []);

  const fetchPreviewJobStatus = useCallback(async () => {
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
          loadSubtitles(subtitleUrl)
            .then((subs) => {
              previewData.subtitles = subs;
              setPreview({ ...previewData });
            })
            .catch((err) => {
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

  const handlePreviewJobUpdate = useCallback(
    (data: JobStatus) => {
      setJobStatus(data);
      if (data.status === 'completed') {
        fetchPreviewJobStatus();
      }
    },
    [fetchPreviewJobStatus]
  );

  useEventSource(
    jobId ? `${API_BASE_URL}/projects/${projectId}/jobs/${jobId}/events` : null,
    {
      onMessage: handlePreviewJobUpdate,
      onError: (err) => {
        console.error('EventSource error:', err);
      },
      enabled: jobStatus?.status !== 'completed' && jobStatus?.status !== 'failed',
    }
  );

  useEffect(() => {
    if (jobId) {
      fetchPreviewJobStatus();
    } else {
      setError('No job ID provided');
      setIsLoading(false);
    }
  }, [jobId, fetchPreviewJobStatus]);

  const fetchExportJobs = useCallback(async () => {
    try {
      setExportsLoading(true);
      setExportError(null);
      const jobs = await listExportJobs(projectId);
      setExportJobs(sortExportJobs(jobs));
    } catch (err) {
      console.error('Failed to load exports:', err);
      setExportError(err instanceof Error ? err.message : 'Failed to load exports');
    } finally {
      setExportsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchExportJobs();
  }, [fetchExportJobs]);

  const handleQueueExport = useCallback(
    async (selection: QueueExportSelection) => {
      const preset = exportPresets.find((item) => item.id === selection.presetId);
      if (!preset) {
        pushNotification('error', t('preview.export.notifications.queueErrorTitle'));
        return;
      }

      setIsQueueingExport(true);
      try {
        const baseFileName = selection.fileName
          ? sanitizeFileNameSegment(selection.fileName)
          : buildDefaultExportFileName(projectId, preset, selection.resolution);
        const fileName = ensureExtension(baseFileName || buildDefaultExportFileName(projectId, preset, selection.resolution));

        const job = await createExportJob(projectId, {
          presetId: selection.presetId,
          resolution: selection.resolution,
          includeCaptions: selection.includeCaptions,
          autoShare: selection.autoShare,
          fileName,
        });

        setExportJobs((prev) => sortExportJobs([...prev, job]));
        pushNotification(
          'info',
          t('preview.export.notifications.queuedTitle', { preset: job.presetName }),
          t('preview.export.notifications.queuedBody', { resolution: job.resolution })
        );
        setIsExportDrawerOpen(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : undefined;
        pushNotification(
          'error',
          t('preview.export.notifications.queueErrorTitle'),
          message ?? t('preview.export.notifications.queueErrorBody')
        );
      } finally {
        setIsQueueingExport(false);
      }
    },
    [exportPresets, projectId, pushNotification, t]
  );

  const refreshExportJob = useCallback(
    async (jobIdToRefresh: string) => {
      try {
        const latest = await getExportJob(projectId, jobIdToRefresh);
        setExportJobs((prev) => sortExportJobs(prev.map((job) => (job.id === jobIdToRefresh ? latest : job))));
      } catch (err) {
        console.error('Failed to refresh export job:', err);
      }
    },
    [projectId]
  );

  const handleExportJobEvent = useCallback(
    (event: ExportJobEventPayload) => {
      const jobIdFromEvent = event.job_id;
      let nextNotification: { type: NotificationType; title: string; message?: string } | null = null;

      setExportJobs((prev) => {
        let found = false;
        const updatedJobs = prev.map((job) => {
          if (job.id !== jobIdFromEvent) {
            return job;
          }

          found = true;
          const previousStatus = job.status;
          const updatedJob = mergeJobUpdate(job, event);

          if (previousStatus !== updatedJob.status) {
            if (updatedJob.status === 'completed') {
              nextNotification = {
                type: 'success',
                title: t('preview.export.notifications.completedTitle', { preset: updatedJob.presetName }),
                message: t('preview.export.notifications.completedBody'),
              };
            } else if (updatedJob.status === 'failed') {
              nextNotification = {
                type: 'error',
                title: t('preview.export.notifications.failedTitle', { preset: updatedJob.presetName }),
                message: updatedJob.failureReason ?? updatedJob.message ?? t('preview.export.notifications.failedBody'),
              };
            } else if (updatedJob.status === 'canceled') {
              nextNotification = {
                type: 'info',
                title: t('preview.export.notifications.canceledTitle', { preset: updatedJob.presetName }),
                message: t('preview.export.notifications.canceledBody'),
              };
            }
          }

          return updatedJob;
        });

        if (!found) {
          return prev;
        }

        return sortExportJobs(updatedJobs);
      });

      if (event.status === 'completed' || event.status === 'failed') {
        void refreshExportJob(jobIdFromEvent);
      }

      if (nextNotification) {
        pushNotification(nextNotification.type, nextNotification.title, nextNotification.message);
      }
    },
    [pushNotification, refreshExportJob, t]
  );

  const setJobAction = useCallback((jobIdToUpdate: string, updates: { canceling?: boolean; retrying?: boolean }) => {
    setJobActionState((prev) => {
      const next = { ...prev };
      const current = next[jobIdToUpdate] ?? {};
      const updated = { ...current, ...updates };
      if (!updated.canceling && !updated.retrying) {
        delete next[jobIdToUpdate];
      } else {
        next[jobIdToUpdate] = updated;
      }
      return next;
    });
  }, []);

  const handleCancelJob = useCallback(
    async (job: ExportJob) => {
      setJobAction(job.id, { canceling: true });
      try {
        const updated = await cancelExportJob(projectId, job.id);
        if (updated) {
          setExportJobs((prev) => sortExportJobs(prev.map((item) => (item.id === job.id ? updated : item))));
        } else {
          setExportJobs((prev) =>
            sortExportJobs(
              prev.map((item) =>
                item.id === job.id
                  ? {
                      ...item,
                      status: 'canceled',
                      message: t('preview.export.statusMessages.canceled'),
                      failureReason: undefined,
                    }
                  : item
              )
            )
          );
        }
        pushNotification(
          'info',
          t('preview.export.notifications.canceledTitle', { preset: job.presetName }),
          t('preview.export.notifications.canceledBody')
        );
      } catch (err) {
        pushNotification(
          'error',
          t('preview.export.notifications.cancelErrorTitle'),
          err instanceof Error ? err.message : t('preview.export.notifications.cancelErrorBody')
        );
      } finally {
        setJobAction(job.id, { canceling: false });
      }
    },
    [projectId, pushNotification, setJobAction, t]
  );

  const handleRetryJob = useCallback(
    async (job: ExportJob) => {
      setJobAction(job.id, { retrying: true });
      try {
        const retried = await retryExportJob(projectId, job.id);
        setExportJobs((prev) => {
          const filtered = prev.filter((item) => item.id !== job.id && item.id !== retried.id);
          return sortExportJobs([...filtered, retried]);
        });
        pushNotification(
          'info',
          t('preview.export.notifications.retryTitle', { preset: retried.presetName }),
          t('preview.export.notifications.retryBody')
        );
      } catch (err) {
        pushNotification(
          'error',
          t('preview.export.notifications.retryErrorTitle'),
          err instanceof Error ? err.message : t('preview.export.notifications.retryErrorBody')
        );
      } finally {
        setJobAction(job.id, { retrying: false });
      }
    },
    [projectId, pushNotification, setJobAction, t]
  );

  const handleDownloadJob = useCallback(
    (job: ExportJob) => {
      const downloadUrl = job.result?.url;
      if (!downloadUrl) {
        pushNotification('error', t('preview.export.notifications.downloadErrorTitle'));
        return;
      }

      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.download = job.result?.filename || `export-${job.id}.mp4`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
    },
    [pushNotification, t]
  );

  const handleShareJob = useCallback(
    async (job: ExportJob) => {
      const shareUrl = job.result?.url;
      if (!shareUrl) {
        pushNotification('error', t('preview.export.notifications.shareErrorTitle'));
        return;
      }

      try {
        if (typeof navigator !== 'undefined' && navigator.share) {
          await navigator.share({
            title: job.result?.filename ?? job.presetName,
            url: shareUrl,
          });
          pushNotification('success', t('preview.export.notifications.shareSuccessTitle'));
          return;
        }

        if (
          typeof navigator !== 'undefined' &&
          navigator.clipboard &&
          typeof window !== 'undefined' &&
          window.isSecureContext
        ) {
          await navigator.clipboard.writeText(shareUrl);
          pushNotification('success', t('preview.export.notifications.copySuccessTitle'), shareUrl);
          return;
        }

        if (typeof window !== 'undefined') {
          window.open(shareUrl, '_blank');
        }
        pushNotification('info', t('preview.export.notifications.openFallbackTitle'));
      } catch (err) {
        if ((err as Error)?.name === 'AbortError') {
          return;
        }
        pushNotification(
          'error',
          t('preview.export.notifications.shareErrorTitle'),
          err instanceof Error ? err.message : undefined
        );
      }
    },
    [pushNotification, t]
  );

  const handleOpenJob = useCallback(
    (job: ExportJob) => {
      const targetUrl = job.result?.url;
      if (!targetUrl) {
        pushNotification('error', t('preview.export.notifications.openErrorTitle'));
        return;
      }
      if (typeof window !== 'undefined') {
        window.open(targetUrl, '_blank', 'noopener');
      }
    },
    [pushNotification, t]
  );

  const handleSeek = (time: number) => {
    setCurrentTime(time);
  };

  const videoUrl = preview
    ? quality === 'proxy' && preview.proxy
      ? preview.proxy.url
      : preview.timeline.url
    : '';

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
          <p className="text-gray-600">{t('preview.loading.message')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md space-y-4">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
          <h2 className="text-2xl font-bold text-gray-900">{t('preview.error.title')}</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            {t('preview.error.retry')}
          </button>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md space-y-4">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto" />
          <h2 className="text-2xl font-bold text-gray-900">{t('preview.notReady.title')}</h2>
          <p className="text-gray-600">{t('preview.notReady.description')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" dir={direction}>
      <NotificationStack
        notifications={notifications}
        onDismiss={dismissNotification}
        direction={direction as 'ltr' | 'rtl'}
        dismissLabel={t('preview.export.notifications.dismiss')}
      />

      <div className="max-w-7xl mx-auto px-4 py-6" data-testid="preview-player">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t('preview.header.title')}</h1>
            <p className="text-gray-600 mt-1">
              {t('preview.header.projectLabel', { projectId })}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-white border rounded-lg px-3 py-2">
              <span className="text-sm text-gray-600">{t('preview.quality.label')}</span>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value as 'proxy' | 'timeline')}
                className="text-sm font-medium bg-transparent border-none outline-none cursor-pointer"
                disabled={!preview.proxy}
              >
                <option value="proxy">{t('preview.quality.proxy')}</option>
                <option value="timeline">{t('preview.quality.timeline')}</option>
              </select>
            </div>

            <button
              className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition"
              title={t('preview.actions.share')}
            >
              <Share2 size={18} />
              {t('preview.actions.share')}
            </button>

            <button
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              title={t('preview.actions.download')}
            >
              <Download size={18} />
              {t('preview.actions.download')}
            </button>

            <button
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition"
              onClick={() => setIsExportDrawerOpen(true)}
            >
              <Plus size={18} />
              {t('preview.export.newExport')}
            </button>
          </div>
        </div>

        {jobStatus && jobStatus.status !== 'completed' && (
          <PreviewStatusBar
            jobStatus={jobStatus}
            onRefresh={fetchPreviewJobStatus}
            className="mb-6"
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <VideoPlayer
              src={videoUrl}
              subtitles={preview.subtitles}
              onTimeUpdate={setCurrentTime}
              className="aspect-video"
            />

            <div className="bg-white rounded-lg p-6 shadow-sm">
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
                {t('preview.sidebar.timelineInfo.title')}
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">{t('preview.sidebar.timelineInfo.clips')}</span>
                  <span className="font-medium">{preview.clips.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{t('preview.sidebar.timelineInfo.duration')}</span>
                  <span className="font-medium">{preview.duration.toFixed(2)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{t('preview.sidebar.timelineInfo.resolution')}</span>
                  <span className="font-medium">
                    {preview.timeline.metadata.width}x{preview.timeline.metadata.height}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{t('preview.sidebar.timelineInfo.audio')}</span>
                  <span className="font-medium">
                    {preview.timeline.metadata.has_audio ? t('preview.sidebar.timelineInfo.audioYes') : t('preview.sidebar.timelineInfo.audioNo')}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{t('preview.export.panelTitle')}</h3>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => fetchExportJobs()}
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    {t('preview.export.refresh')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsExportDrawerOpen(true)}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    {t('preview.export.newExportCompact')}
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                {t('preview.export.panelSubtitle')}
              </p>

              {exportsLoading ? (
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  {t('preview.export.loading')}
                </div>
              ) : exportError ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                  {exportError}
                </div>
              ) : exportJobs.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50/70 p-6 text-center space-y-3">
                  <p className="text-sm font-semibold text-gray-800">
                    {t('preview.export.empty.title')}
                  </p>
                  <p className="text-sm text-gray-600">
                    {t('preview.export.empty.description')}
                  </p>
                  <button
                    onClick={() => setIsExportDrawerOpen(true)}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                  >
                    <Plus className="h-4 w-4" />
                    {t('preview.export.empty.action')}
                  </button>
                </div>
              ) : (
                <div className="space-y-5">
                  {exportJobs.map((job) => (
                    <ExportJobCard
                      key={job.id}
                      job={job}
                      onCancel={handleCancelJob}
                      onRetry={handleRetryJob}
                      onDownload={handleDownloadJob}
                      onShare={handleShareJob}
                      onOpen={handleOpenJob}
                      actionState={jobActionState[job.id]}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-4">{t('preview.sidebar.clips.title')}</h3>
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
                      <span className="font-medium text-sm">
                        {t('preview.sidebar.clips.clipTitle', { index: index + 1 })}
                      </span>
                      <span className="text-xs text-gray-500">{clip.transition.type}</span>
                    </div>
                    <div className="text-xs text-gray-600">
                      {clip.in_point.toFixed(1)}s - {clip.out_point?.toFixed(1) || t('preview.sidebar.clips.endLabel')}
                    </div>
                    {clip.subtitles && (
                      <div className="text-xs text-blue-600 mt-1">
                        {t('preview.sidebar.clips.hasSubtitles')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <ExportDrawer
        isOpen={isExportDrawerOpen}
        onClose={() => setIsExportDrawerOpen(false)}
        presets={exportPresets}
        onQueueExport={handleQueueExport}
        isSubmitting={isQueueingExport}
      />

      {exportJobs.map((job) => (
        <ExportJobEventListener key={job.id} projectId={projectId} job={job} onEvent={handleExportJobEvent} />
      ))}
    </div>
  );
}
