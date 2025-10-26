import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ExportJob,
  ExportNotification,
  ExportRequest,
  ExportStageKey,
  ExportStatus,
} from '../types/export';

const EXPORT_STAGE_SEQUENCE: Array<{
  key: ExportStageKey;
  threshold: number;
  messageKey: string;
}> = [
  { key: 'queued', threshold: 0, messageKey: 'export.job.stage.queued' },
  { key: 'preparing', threshold: 15, messageKey: 'export.job.stage.preparing' },
  { key: 'rendering', threshold: 40, messageKey: 'export.job.stage.rendering' },
  { key: 'encoding', threshold: 65, messageKey: 'export.job.stage.encoding' },
  { key: 'uploading', threshold: 85, messageKey: 'export.job.stage.uploading' },
  { key: 'finalising', threshold: 95, messageKey: 'export.job.stage.finalising' },
  { key: 'completed', threshold: 100, messageKey: 'export.job.stage.completed' },
];

const RESOLUTION_SPEED_MULTIPLIER: Record<ExportRequest['resolution'], number> = {
  '720p': 0.8,
  '1080p': 1,
  '4k': 1.6,
};

const RESOLUTION_SIZE_MULTIPLIER: Record<ExportRequest['resolution'], number> = {
  '720p': 0.65,
  '1080p': 1,
  '4k': 2.5,
};

const randomBetween = (min: number, max: number) => Math.random() * (max - min) + min;

const nowIso = () => new Date().toISOString();

type IntervalId = ReturnType<typeof setInterval>;

export interface UseExportQueueResult {
  jobs: ExportJob[];
  activeJobs: ExportJob[];
  completedJobs: ExportJob[];
  failedJobs: ExportJob[];
  cancelledJobs: ExportJob[];
  startExport: (request: ExportRequest) => void;
  cancelJob: (jobId: string) => void;
  retryJob: (jobId: string) => void;
  removeJob: (jobId: string) => void;
  notifications: ExportNotification[];
  dismissNotification: (id: string) => void;
  stageDefinitions: typeof EXPORT_STAGE_SEQUENCE;
}

const buildJobDisplayName = (request: ExportRequest) => {
  if (request.displayName) return request.displayName;
  return `${request.presetLabel} • ${request.resolution} • ${request.aspectRatio}`;
};

export function useExportQueue(): UseExportQueueResult {
  const [jobs, setJobs] = useState<ExportJob[]>([]);
  const timers = useRef<Record<string, IntervalId>>({});
  const [notifications, setNotifications] = useState<ExportNotification[]>([]);

  const clearTimer = useCallback((jobId: string) => {
    const timer = timers.current[jobId];
    if (timer) {
      clearInterval(timer);
      delete timers.current[jobId];
    }
  }, []);

  useEffect(() => () => {
    Object.values(timers.current).forEach(clearInterval);
    timers.current = {};
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const pushNotification = useCallback(
    (notification: ExportNotification) => {
      setNotifications(prev => [...prev, notification]);
      if (typeof window !== 'undefined') {
        window.setTimeout(() => dismissNotification(notification.id), 6000);
      }
    },
    [dismissNotification],
  );

  const startProgressSimulation = useCallback(
    (jobId: string) => {
      if (typeof window === 'undefined') {
        return;
      }

      const interval = window.setInterval(() => {
        let lifecycleEvent: { type: 'completed' | 'failed'; job: ExportJob } | null = null;

        setJobs(prevJobs =>
          prevJobs.map(job => {
            if (job.id !== jobId) return job;

            if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
              clearTimer(jobId);
              return job;
            }

            const nextStatus: ExportStatus = job.status === 'queued' ? 'processing' : job.status;
            const incrementBase = job.status === 'queued' ? 8 : 12;
            const progressIncrement = randomBetween(incrementBase - 4, incrementBase + 6);
            const multiplier = RESOLUTION_SPEED_MULTIPLIER[job.resolution] ?? 1;
            let nextProgress = Math.min(100, job.progress + progressIncrement / multiplier);
            const timestamp = nowIso();

            let nextEvents = job.events.slice();

            EXPORT_STAGE_SEQUENCE.forEach(stage => {
              if (nextProgress >= stage.threshold && !nextEvents.some(event => event.stage === stage.key)) {
                nextEvents = [
                  ...nextEvents,
                  {
                    stage: stage.key,
                    timestamp,
                    progress: Math.min(100, stage.threshold),
                    messageKey: stage.messageKey,
                  },
                ];
              }
            });

            let nextJob: ExportJob = {
              ...job,
              status: nextStatus,
              progress: Number(nextProgress.toFixed(1)),
              events: nextEvents,
              updatedAt: timestamp,
            };

            if (job.simulation?.shouldFail && !job.simulation.failEmitted && nextProgress > 58) {
              const failureTimestamp = nowIso();
              nextJob = {
                ...nextJob,
                status: 'failed',
                progress: Number(Math.min(nextProgress, 96).toFixed(1)),
                errorMessage: job.simulation.failReason,
                events: [
                  ...nextEvents,
                  {
                    stage: 'failed',
                    timestamp: failureTimestamp,
                    progress: Number(Math.min(nextProgress, 96).toFixed(1)),
                    messageKey: 'export.job.stage.failed',
                  },
                ],
                simulation: {
                  ...job.simulation,
                  failEmitted: true,
                },
              };

              lifecycleEvent = { type: 'failed', job: nextJob };
              clearTimer(jobId);
              return nextJob;
            }

            if (nextProgress >= 100) {
              const baseDuration = nextJob.request.durationSeconds ?? nextJob.metadata.estimatedDurationSeconds;
              const sizeMultiplier = RESOLUTION_SIZE_MULTIPLIER[nextJob.resolution] ?? 1;
              const computedFileSize = Math.round(baseDuration * 0.55 * sizeMultiplier + randomBetween(8, 25));

              let downloadUrl = nextJob.request.downloadBaseUrl;
              if (downloadUrl) {
                const delimiter = downloadUrl.includes('?') ? '&' : '?';
                downloadUrl = `${downloadUrl}${delimiter}export=${nextJob.id}`;
              }

              nextJob = {
                ...nextJob,
                status: 'completed',
                progress: 100,
                downloadUrl,
                shareUrl: downloadUrl,
                openUrl: downloadUrl,
                durationSeconds: baseDuration,
                fileSizeMB: computedFileSize,
                events: nextEvents.some(event => event.stage === 'completed')
                  ? nextEvents
                  : [
                      ...nextEvents,
                      {
                        stage: 'completed',
                        timestamp,
                        progress: 100,
                        messageKey: 'export.job.stage.completed',
                      },
                    ],
              };

              lifecycleEvent = { type: 'completed', job: nextJob };
              clearTimer(jobId);
              return nextJob;
            }

            return nextJob;
          }),
        );

        if (lifecycleEvent) {
          const { job, type } = lifecycleEvent;
          pushNotification({
            id: `${type}-${job.id}`,
            jobId: job.id,
            type: type === 'completed' ? 'success' : 'error',
            titleKey:
              type === 'completed' ? 'export.notifications.completedTitle' : 'export.notifications.failedTitle',
            messageKey:
              type === 'completed' ? 'export.notifications.completedDescription' : 'export.notifications.failedDescription',
            titleParams: { preset: job.presetLabel },
            messageParams:
              type === 'completed'
                ? undefined
                : {
                    reason: job.errorMessage ?? 'export.job.error.default',
                  },
          });
        }
      }, 1200);

      timers.current[jobId] = interval;
    },
    [pushNotification, clearTimer],
  );

  const startExport = useCallback(
    (request: ExportRequest) => {
      const jobId = `export-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
      const timestamp = nowIso();
      const estimatedDuration = Math.max(45, Math.round((request.durationSeconds ?? 60) * 0.9));

      const shouldFail =
        request.resolution === '4k' &&
        Math.random() < 0.32 &&
        !request.presetLabel.toLowerCase().includes('fallback');

      const job: ExportJob = {
        id: jobId,
        projectId: request.projectId,
        status: 'queued',
        platform: request.platform,
        resolution: request.resolution,
        aspectRatio: request.aspectRatio,
        progress: 0,
        format: 'mp4',
        createdAt: timestamp,
        updatedAt: timestamp,
        etaSeconds: estimatedDuration,
        presetLabel: request.presetLabel,
        displayName: buildJobDisplayName(request),
        attempt: request.attempt ?? 1,
        metadata: {
          estimatedDurationSeconds: estimatedDuration,
          recommendedAspectRatio: request.aspectRatio,
          recommendedResolution: request.resolution,
        },
        events: [
          {
            stage: 'queued',
            timestamp,
            progress: 0,
            messageKey: 'export.job.stage.queued',
          },
        ],
        simulation: shouldFail
          ? {
              shouldFail: true,
              failReason: 'export.job.error.default',
            }
          : undefined,
        request,
      };

      setJobs(prev => [job, ...prev]);
      startProgressSimulation(job.id);
    },
    [startProgressSimulation],
  );

  const cancelJob = useCallback(
    (jobId: string) => {
      clearTimer(jobId);
      setJobs(prev =>
        prev.map(job => {
          if (job.id !== jobId) return job;
          if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
            return job;
          }
          const timestamp = nowIso();
          return {
            ...job,
            status: 'cancelled',
            updatedAt: timestamp,
            events: [
              ...job.events,
              {
                stage: 'cancelled',
                timestamp,
                progress: job.progress,
                messageKey: 'export.job.stage.cancelled',
              },
            ],
          };
        }),
      );
    },
    [clearTimer],
  );

  const retryJob = useCallback(
    (jobId: string) => {
      const job = jobs.find(entry => entry.id === jobId);
      if (!job) return;
      const updatedLabel = `${job.presetLabel}`;
      startExport({
        ...job.request,
        attempt: job.attempt + 1,
        presetLabel: updatedLabel,
      });
    },
    [jobs, startExport],
  );

  const removeJob = useCallback((jobId: string) => {
    clearTimer(jobId);
    setJobs(prev => prev.filter(job => job.id !== jobId));
  }, [clearTimer]);

  const activeJobs = useMemo(
    () => jobs.filter(job => job.status === 'queued' || job.status === 'processing'),
    [jobs],
  );

  const completedJobs = useMemo(
    () => jobs.filter(job => job.status === 'completed'),
    [jobs],
  );

  const failedJobs = useMemo(
    () => jobs.filter(job => job.status === 'failed'),
    [jobs],
  );

  const cancelledJobs = useMemo(
    () => jobs.filter(job => job.status === 'cancelled'),
    [jobs],
  );

  return {
    jobs,
    activeJobs,
    completedJobs,
    failedJobs,
    cancelledJobs,
    startExport,
    cancelJob,
    retryJob,
    removeJob,
    notifications,
    dismissNotification,
    stageDefinitions: EXPORT_STAGE_SEQUENCE,
  };
}
