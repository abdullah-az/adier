import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  ExternalLink,
  Film,
  Instagram,
  Loader2,
  MonitorPlay,
  Music2,
  RefreshCw,
  Share2,
  X,
  Youtube,
} from 'lucide-react';
import {
  ExportAspectRatio,
  ExportJob,
  ExportResolution,
  ExportStageKey,
  ExportStatus,
} from '../types/export';
import { UseExportQueueResult } from '../hooks/useExportQueue';
import { PreviewMedia } from '../types/preview';

interface ExportDrawerProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  timelineDuration?: number;
  timelineUrl?: string;
  existingExports?: PreviewMedia[];
  exportQueue: UseExportQueueResult;
}

type PresetDefinition = {
  id: 'youtube_shorts' | 'tiktok' | 'instagram_reels';
  colorClass: string;
  icon: typeof Youtube;
  nameKey: string;
  descriptionKey: string;
  recommendedResolution: ExportResolution;
  recommendedAspectRatio: ExportAspectRatio;
  maxDurationSeconds: number;
  supportedResolutions: ExportResolution[];
  supportedAspectRatios: ExportAspectRatio[];
};

const PRESET_DEFINITIONS: PresetDefinition[] = [
  {
    id: 'youtube_shorts',
    colorClass: 'bg-red-500/10 text-red-600 border border-red-500/30',
    icon: Youtube,
    nameKey: 'export.presets.youtube_shorts.name',
    descriptionKey: 'export.presets.youtube_shorts.description',
    recommendedResolution: '1080p',
    recommendedAspectRatio: '9:16',
    maxDurationSeconds: 60,
    supportedResolutions: ['720p', '1080p', '4k'],
    supportedAspectRatios: ['9:16', '1:1'],
  },
  {
    id: 'tiktok',
    colorClass: 'bg-fuchsia-500/10 text-fuchsia-600 border border-fuchsia-500/30',
    icon: Music2,
    nameKey: 'export.presets.tiktok.name',
    descriptionKey: 'export.presets.tiktok.description',
    recommendedResolution: '1080p',
    recommendedAspectRatio: '9:16',
    maxDurationSeconds: 180,
    supportedResolutions: ['720p', '1080p', '4k'],
    supportedAspectRatios: ['9:16', '1:1'],
  },
  {
    id: 'instagram_reels',
    colorClass: 'bg-orange-500/10 text-orange-600 border border-orange-500/30',
    icon: Instagram,
    nameKey: 'export.presets.instagram_reels.name',
    descriptionKey: 'export.presets.instagram_reels.description',
    recommendedResolution: '1080p',
    recommendedAspectRatio: '9:16',
    maxDurationSeconds: 90,
    supportedResolutions: ['720p', '1080p'],
    supportedAspectRatios: ['9:16', '1:1', '16:9'],
  },
];

const RESOLUTION_OPTIONS: ExportResolution[] = ['720p', '1080p', '4k'];
const ASPECT_RATIO_OPTIONS: ExportAspectRatio[] = ['9:16', '1:1', '16:9'];

const formatDuration = (duration?: number) => {
  if (!duration || Number.isNaN(duration)) {
    return '00:00';
  }
  const rounded = Math.max(0, Math.round(duration));
  const hours = Math.floor(rounded / 3600);
  const minutes = Math.floor((rounded % 3600) / 60);
  const seconds = rounded % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

const formatFileSize = (sizeBytes?: number, sizeMbFallback?: number) => {
  if (sizeMbFallback && sizeMbFallback > 0) {
    return `${sizeMbFallback.toFixed(1)} MB`;
  }
  if (!sizeBytes || Number.isNaN(sizeBytes)) {
    return '—';
  }
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = sizeBytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
};

const statusBadgeClasses: Record<ExportStatus, string> = {
  queued: 'bg-blue-100 text-blue-700 border border-blue-200',
  processing: 'bg-sky-100 text-sky-700 border border-sky-200',
  completed: 'bg-green-100 text-green-700 border border-green-200',
  failed: 'bg-rose-100 text-rose-700 border border-rose-200',
  cancelled: 'bg-gray-100 text-gray-700 border border-gray-200',
};

const stageStatusForJob = (job: ExportJob, stageKey: ExportStageKey) => {
  if (job.status === 'failed' && stageKey === 'failed') return 'current';
  const hasStage = job.events.some(event => event.stage === stageKey);
  if (!hasStage) return 'upcoming';
  const lastStage = job.events[job.events.length - 1]?.stage;
  if (stageKey === lastStage && job.status !== 'completed') {
    return 'current';
  }
  return 'done';
};

const isStageVisible = (stageKey: ExportStageKey, job: ExportJob) => {
  if (stageKey === 'failed') {
    return job.status === 'failed';
  }
  if (stageKey === 'cancelled') {
    return job.status === 'cancelled';
  }
  return true;
};

const jobStatusTranslationKey = (status: ExportStatus) => {
  switch (status) {
    case 'queued':
      return 'export.job.status.queued';
    case 'processing':
      return 'export.job.status.processing';
    case 'completed':
      return 'export.job.status.completed';
    case 'failed':
      return 'export.job.status.failed';
    case 'cancelled':
      return 'export.job.status.cancelled';
    default:
      return 'export.job.status.queued';
  }
};

const ExportDrawer = ({
  open,
  onClose,
  projectId,
  timelineDuration,
  timelineUrl,
  existingExports,
  exportQueue,
}: ExportDrawerProps) => {
  const { t } = useTranslation();
  const [selectedPresetId, setSelectedPresetId] = useState<PresetDefinition['id']>('youtube_shorts');
  const selectedPreset = useMemo(
    () => PRESET_DEFINITIONS.find(preset => preset.id === selectedPresetId) ?? PRESET_DEFINITIONS[0],
    [selectedPresetId],
  );

  const [selectedResolution, setSelectedResolution] = useState<ExportResolution>(selectedPreset.recommendedResolution);
  const [selectedAspectRatio, setSelectedAspectRatio] = useState<ExportAspectRatio>(selectedPreset.recommendedAspectRatio);

  const { activeJobs, completedJobs, failedJobs, stageDefinitions } = exportQueue;

  const startExport = () => {
    const presetLabel = t(selectedPreset.nameKey);
    exportQueue.startExport({
      projectId,
      platform: selectedPreset.id,
      resolution: selectedResolution,
      aspectRatio: selectedAspectRatio,
      presetLabel,
      durationSeconds: timelineDuration,
      downloadBaseUrl: timelineUrl,
    });
  };

  const renderedExistingExports = useMemo(() => {
    if (!existingExports?.length) return [];
    return existingExports.map(asset => {
      const duration = asset.metadata?.duration ?? timelineDuration;
      const sizeBytes = asset.metadata?.size_bytes ?? asset.metadata?.sizeBytes;
      const format = asset.metadata?.format ?? (asset.name?.split('.').pop() ?? 'mp4');
      return {
        id: asset.asset_id ?? asset.name ?? asset.relative_path,
        label: asset.metadata?.label ?? asset.name ?? t('export.generated.defaultLabel'),
        duration,
        sizeBytes,
        format: format?.toUpperCase(),
        resolution: asset.metadata?.width && asset.metadata?.height
          ? `${asset.metadata.width}×${asset.metadata.height}`
          : undefined,
        aspect: asset.metadata?.aspect_ratio ?? asset.metadata?.aspectRatio,
        url: asset.url,
      };
    });
  }, [existingExports, timelineDuration, t]);

  const timelineSummary = useMemo(() => {
    if (!timelineDuration) return null;
    return {
      duration: formatDuration(timelineDuration),
    };
  }, [timelineDuration]);

  const disableStart = !projectId || !timelineUrl;

  const openLink = (url?: string, target: '_blank' | '_self' = '_blank') => {
    if (!url || typeof window === 'undefined') return;
    const features = target === '_blank' ? 'noopener' : undefined;
    window.open(url, target, features);
  };

  const shareJob = async (job: ExportJob) => {
    const link = job.shareUrl ?? job.downloadUrl;
    if (!link || typeof navigator === 'undefined') return;

    if (navigator.share) {
      try {
        await navigator.share({
          title: job.displayName,
          text: t('export.share.copyFallback'),
          url: link,
        });
        return;
      } catch (error) {
        // fallback to clipboard when share fails
      }
    }

    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(link);
      } catch (error) {
        // ignore clipboard errors gracefully
      }
    }
  };

  return (
    <div className={`fixed inset-0 z-40 transition ${open ? 'pointer-events-auto' : 'pointer-events-none'}`}>
      <div
        className={`absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />

      <div
        className={`absolute right-0 top-0 h-full w-full max-w-5xl bg-white shadow-2xl transform transition-transform duration-300 ease-out flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{t('export.title')}</h2>
            <p className="text-sm text-slate-500 mt-1">{t('export.subtitle')}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-transparent p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          <section className="grid gap-6 lg:grid-cols-[2fr,3fr]">
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-slate-700 uppercase tracking-wide">
                  {t('export.sections.preset')}
                </h3>
                <div className="mt-3 grid grid-cols-1 gap-3">
                  {PRESET_DEFINITIONS.map(preset => {
                    const Icon = preset.icon;
                    const isActive = preset.id === selectedPreset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() => {
                          setSelectedPresetId(preset.id);
                          setSelectedResolution(preset.recommendedResolution);
                          setSelectedAspectRatio(preset.recommendedAspectRatio);
                        }}
                        className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${isActive ? 'border-blue-500 shadow-sm bg-blue-50/60' : 'border-slate-200 hover:border-blue-400/70 hover:bg-blue-50/40'}`}
                      >
                        <div className={`mt-1 flex h-10 w-10 items-center justify-center rounded-full ${preset.colorClass}`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="grow">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-900">{t(preset.nameKey)}</span>
                            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                              {t('export.preset.maxDuration', {
                                value: formatDuration(preset.maxDurationSeconds),
                              })}
                            </span>
                          </div>
                          <p className="text-sm text-slate-500 mt-1">
                            {t(preset.descriptionKey)}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <h4 className="text-sm font-medium text-slate-700">
                  {t('export.summary.heading')}
                </h4>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <dt className="text-slate-500">{t('export.summary.preset')}</dt>
                    <dd className="font-medium text-slate-700">{t(selectedPreset.nameKey)}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-slate-500">{t('export.summary.recommendation')}</dt>
                    <dd className="font-medium text-slate-700">
                      {selectedPreset.recommendedResolution} · {selectedPreset.recommendedAspectRatio}
                    </dd>
                  </div>
                  {timelineSummary && (
                    <div className="flex items-center justify-between">
                      <dt className="text-slate-500">{t('export.summary.timelineDuration')}</dt>
                      <dd className="font-medium text-slate-700">{timelineSummary.duration}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>

            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-slate-600 uppercase tracking-wide">
                    {t('export.sections.resolution')}
                  </h4>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {RESOLUTION_OPTIONS.map(option => {
                      const isDisabled = !selectedPreset.supportedResolutions.includes(option);
                      const isActive = selectedResolution === option;
                      return (
                        <button
                          key={option}
                          type="button"
                          onClick={() => setSelectedResolution(option)}
                          disabled={isDisabled}
                          className={`rounded-lg border px-3 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${isActive ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:border-blue-400/70 hover:text-blue-600'} ${isDisabled ? 'cursor-not-allowed opacity-40 hover:border-slate-200' : ''}`}
                        >
                          {t(`export.resolutions.${option}`)}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-slate-600 uppercase tracking-wide">
                    {t('export.sections.aspectRatio')}
                  </h4>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {ASPECT_RATIO_OPTIONS.map(option => {
                      const isDisabled = !selectedPreset.supportedAspectRatios.includes(option);
                      const isActive = selectedAspectRatio === option;
                      return (
                        <button
                          key={option}
                          type="button"
                          onClick={() => setSelectedAspectRatio(option)}
                          disabled={isDisabled}
                          className={`rounded-lg border px-3 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${isActive ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600 hover:border-blue-400/70 hover:text-blue-600'} ${isDisabled ? 'cursor-not-allowed opacity-40 hover:border-slate-200' : ''}`}
                        >
                          {option}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={startExport}
                disabled={disableStart}
                className={`inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${disableStart ? 'cursor-not-allowed bg-slate-200 text-slate-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
              >
                <MonitorPlay className="h-5 w-5" />
                {t('export.actions.start')}
              </button>
            </div>
          </section>

          <section className="space-y-4">
            <header className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{t('export.sections.activeJobs')}</h3>
                <p className="text-sm text-slate-500">
                  {t('export.queueCount', { count: activeJobs.length })}
                </p>
              </div>
            </header>

            {activeJobs.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/80 p-8 text-center">
                <MonitorPlay className="mx-auto h-10 w-10 text-slate-400" />
                <p className="mt-2 text-sm text-slate-500">{t('export.emptyActive')}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeJobs.map(job => (
                  <JobCard
                    key={job.id}
                    job={job}
                    stageDefinitions={stageDefinitions}
                    onCancel={() => exportQueue.cancelJob(job.id)}
                    shareJob={() => shareJob(job)}
                    onDownload={() => openLink(job.downloadUrl)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <h3 className="text-base font-semibold text-slate-900">{t('export.sections.completed')}</h3>
            {completedJobs.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
                {t('export.emptyCompleted')}
              </div>
            ) : (
              <div className="space-y-3">
                {completedJobs.map(job => (
                  <CompletedJobCard
                    key={job.id}
                    job={job}
                    t={t}
                    onDownload={() => openLink(job.downloadUrl)}
                    onOpen={() => openLink(job.openUrl)}
                    onShare={() => shareJob(job)}
                    onDismiss={() => exportQueue.removeJob(job.id)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <h3 className="text-base font-semibold text-slate-900">{t('export.sections.failed')}</h3>
            {failedJobs.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
                {t('export.emptyFailed')}
              </div>
            ) : (
              <div className="space-y-3">
                {failedJobs.map(job => (
                  <FailedJobCard
                    key={job.id}
                    job={job}
                    t={t}
                    onRetry={() => exportQueue.retryJob(job.id)}
                    onDismiss={() => exportQueue.removeJob(job.id)}
                  />
                ))}
              </div>
            )}
          </section>

          {renderedExistingExports.length > 0 && (
            <section className="space-y-4">
              <h3 className="text-base font-semibold text-slate-900">{t('export.sections.generated')}</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {renderedExistingExports.map(item => (
                  <div key={item.id} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-slate-800">{item.label}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {item.format || 'MP4'} · {item.resolution || '—'} · {item.aspect || '—'}
                        </p>
                      </div>
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                        <Film className="h-4 w-4" />
                        {formatDuration(item.duration)}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
                      <span>{t('export.metadata.size')}</span>
                      <span className="font-medium text-slate-700">{formatFileSize(item.sizeBytes)}</span>
                    </div>
                    <div className="mt-4 flex items-center gap-2">
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:border-slate-300 hover:bg-slate-50"
                        onClick={() => openLink(item.url)}
                      >
                        <Download className="h-4 w-4" />
                        {t('export.buttons.download')}
                      </button>
                      <button
                        type="button"
                        className="inline-flex items-center gap-1 rounded-lg border border-transparent px-3 py-2 text-sm font-medium text-slate-600 hover:text-blue-600"
                        onClick={() => openLink(item.url)}
                      >
                        <ExternalLink className="h-4 w-4" />
                        {t('export.buttons.open')}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

interface JobCardProps {
  job: ExportJob;
  stageDefinitions: UseExportQueueResult['stageDefinitions'];
  onCancel: () => void;
  onDownload: () => void;
  shareJob: () => Promise<void> | void;
}

const JobCard = ({ job, stageDefinitions, onCancel, onDownload, shareJob }: JobCardProps) => {
  const { t } = useTranslation();

  const progressLabel = useMemo(
    () => `${job.progress.toFixed(0)}%`,
    [job.progress],
  );

  const currentStage = job.events[job.events.length - 1]?.stage;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-900">{job.displayName}</p>
          <p className="text-xs text-slate-500 mt-1">
            {t(jobStatusTranslationKey(job.status))}
          </p>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClasses[job.status]}`}>
          {job.status === 'processing' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
          {progressLabel}
        </span>
      </div>

      <div className="mt-3">
        <div className="h-2 rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-blue-500 via-blue-600 to-violet-500 transition-all"
            style={{ width: `${Math.min(100, Math.max(0, job.progress))}%` }}
          />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-6 md:items-start">
        {stageDefinitions.map((stage, index) => {
          const visible = isStageVisible(stage.key, job);
          if (!visible) return null;
          const status = stageStatusForJob(job, stage.key);
          const isCurrent = currentStage === stage.key;
          return (
            <div key={stage.key} className="space-y-1">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full border text-xs font-medium transition ${
                  status === 'done'
                    ? 'border-green-500 bg-green-50 text-green-600'
                    : status === 'current'
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-slate-200 bg-white text-slate-400'
                }`}
              >
                {status === 'done' ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : status === 'current' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span className="font-semibold">{index + 1}</span>
                )}
              </div>
              <p className={`text-xs font-medium leading-tight ${isCurrent ? 'text-blue-600' : 'text-slate-500'}`}>
                {t(stage.messageKey)}
              </p>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
        >
          <RefreshCw className="h-4 w-4" />
          {t('export.buttons.cancel')}
        </button>
        <button
          type="button"
          onClick={shareJob}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600"
        >
          <Share2 className="h-4 w-4" />
          {t('export.buttons.share')}
        </button>
        <button
          type="button"
          onClick={onDownload}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:border-green-200 hover:bg-green-50 hover:text-green-600"
        >
          <Download className="h-4 w-4" />
          {t('export.buttons.download')}
        </button>
      </div>
    </div>
  );
};

interface CompletedJobCardProps {
  job: ExportJob;
  t: ReturnType<typeof useTranslation>['t'];
  onDownload: () => void;
  onOpen: () => void;
  onShare: () => void;
  onDismiss: () => void;
}

const CompletedJobCard = ({ job, t, onDownload, onOpen, onShare, onDismiss }: CompletedJobCardProps) => (
  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-2">
      <div>
        <p className="text-sm font-semibold text-slate-900">{job.displayName}</p>
        <p className="text-xs text-slate-500 mt-1">{t(jobStatusTranslationKey(job.status))}</p>
      </div>
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${statusBadgeClasses[job.status]}`}>
        <CheckCircle2 className="h-3.5 w-3.5" />
        {t('export.job.completedAt', { time: new Date(job.updatedAt).toLocaleTimeString() })}
      </span>
    </div>

    <div className="mt-4 grid gap-3 text-xs text-slate-500 md:grid-cols-4">
      <div>
        <p className="font-medium text-slate-600">{t('export.metadata.duration')}</p>
        <p className="text-slate-900">{formatDuration(job.durationSeconds)}</p>
      </div>
      <div>
        <p className="font-medium text-slate-600">{t('export.metadata.size')}</p>
        <p className="text-slate-900">{formatFileSize(undefined, job.fileSizeMB)}</p>
      </div>
      <div>
        <p className="font-medium text-slate-600">{t('export.metadata.resolution')}</p>
        <p className="text-slate-900">{job.resolution}</p>
      </div>
      <div>
        <p className="font-medium text-slate-600">{t('export.metadata.aspect')}</p>
        <p className="text-slate-900">{job.aspectRatio}</p>
      </div>
    </div>

    <div className="mt-4 flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={onDownload}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-slate-300 hover:bg-slate-50"
      >
        <Download className="h-4 w-4" />
        {t('export.buttons.download')}
      </button>
      <button
        type="button"
        onClick={onOpen}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600"
      >
        <ExternalLink className="h-4 w-4" />
        {t('export.buttons.open')}
      </button>
      <button
        type="button"
        onClick={onShare}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-600"
      >
        <Share2 className="h-4 w-4" />
        {t('export.buttons.share')}
      </button>
      <button
        type="button"
        onClick={onDismiss}
        className="inline-flex items-center gap-1 rounded-lg border border-transparent px-3 py-2 text-xs font-semibold text-slate-400 hover:text-slate-600"
      >
        <X className="h-4 w-4" />
        {t('export.buttons.dismiss')}
      </button>
    </div>
  </div>
);

interface FailedJobCardProps {
  job: ExportJob;
  t: ReturnType<typeof useTranslation>['t'];
  onRetry: () => void;
  onDismiss: () => void;
}

const FailedJobCard = ({ job, t, onRetry, onDismiss }: FailedJobCardProps) => (
  <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-4">
    <div className="flex flex-wrap items-start justify-between gap-2">
      <div>
        <p className="text-sm font-semibold text-rose-700">{job.displayName}</p>
        <p className="text-xs text-rose-500 mt-1">{t(jobStatusTranslationKey(job.status))}</p>
      </div>
      <span className="inline-flex items-center gap-1 rounded-full bg-white/80 px-2.5 py-1 text-xs font-medium text-rose-600">
        <AlertCircle className="h-3.5 w-3.5" />
        {t('export.job.failedLabel')}
      </span>
    </div>

    {job.errorMessage && (
      <p className="mt-3 text-sm text-rose-700 flex items-center gap-2">
        <AlertCircle className="h-4 w-4" />
        {t(job.errorMessage)}
      </p>
    )}

    <div className="mt-4 flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-white px-3 py-2 text-xs font-semibold text-rose-600 hover:border-rose-300 hover:bg-rose-100"
      >
        <RefreshCw className="h-4 w-4" />
        {t('export.buttons.retry')}
      </button>
      <button
        type="button"
        onClick={onDismiss}
        className="inline-flex items-center gap-1 rounded-lg border border-transparent px-3 py-2 text-xs font-semibold text-rose-400 hover:text-rose-600"
      >
        <X className="h-4 w-4" />
        {t('export.buttons.dismiss')}
      </button>
    </div>
  </div>
);

export default ExportDrawer;
