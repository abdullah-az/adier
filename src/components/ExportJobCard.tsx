import { useMemo } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  ExternalLink,
  Loader2,
  RotateCcw,
  Share2,
  XCircle,
} from 'lucide-react';
import { ExportJob, ExportJobHistoryEntry, ExportStatus } from '../types/export';
import { formatDuration, formatFileSize, formatLocalizedTimestamp } from '../utils/format';
import { useTranslation } from 'react-i18next';

interface ExportJobCardProps {
  job: ExportJob;
  onCancel: (job: ExportJob) => void;
  onRetry: (job: ExportJob) => void;
  onDownload: (job: ExportJob) => void;
  onShare: (job: ExportJob) => void;
  onOpen: (job: ExportJob) => void;
  actionState?: {
    canceling?: boolean;
    retrying?: boolean;
  };
}

const STATUS_FLOW: ExportStatus[] = ['queued', 'running', 'completed'];

function buildHistoryMap(history: ExportJobHistoryEntry[]) {
  return history.reduce<Record<ExportStatus, ExportJobHistoryEntry>>((acc, entry) => {
    acc[entry.status] = entry;
    return acc;
  }, {} as Record<ExportStatus, ExportJobHistoryEntry>);
}

export function ExportJobCard({
  job,
  onCancel,
  onRetry,
  onDownload,
  onShare,
  onOpen,
  actionState,
}: ExportJobCardProps) {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();

  const historyMap = useMemo(() => buildHistoryMap(job.history ?? []), [job.history]);

  const timelineStatuses = useMemo(() => {
    if (job.status === 'failed' || job.status === 'canceled') {
      return ['queued', 'running', job.status] as ExportStatus[];
    }
    return STATUS_FLOW;
  }, [job.status]);

  const statusBadgeClass = useMemo(() => {
    switch (job.status) {
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-emerald-100 text-emerald-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      case 'canceled':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  }, [job.status]);

  const canCancel = job.status === 'queued' || job.status === 'running';
  const canRetry = job.status === 'failed' || job.status === 'canceled';
  const canDownload = job.status === 'completed' && job.result?.url;

  const durationSeconds =
    job.result?.metadata?.durationSeconds ??
    job.result?.metadata?.duration ??
    (typeof job.result?.metadata?.duration_seconds === 'number' ? (job.result?.metadata as any).duration_seconds : undefined);

  const canceling = actionState?.canceling;
  const retrying = actionState?.retrying;

  const renderStatusIcon = (status: ExportStatus) => {
    if (status === 'failed') {
      return <AlertCircle className="h-4 w-4 text-red-500" aria-hidden="true" />;
    }
    if (status === 'canceled') {
      return <XCircle className="h-4 w-4 text-gray-500" aria-hidden="true" />;
    }
    if (status === 'completed') {
      return <CheckCircle2 className="h-4 w-4 text-emerald-500" aria-hidden="true" />;
    }
    if (status === 'running') {
      return <Loader2 className="h-4 w-4 animate-spin text-blue-500" aria-hidden="true" />;
    }
    return <Clock className="h-4 w-4 text-yellow-500" aria-hidden="true" />;
  };

  return (
    <div className="border border-gray-200 rounded-2xl bg-white shadow-sm p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">
            {job.presetName}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {job.platform.replace('_', ' ')} • {job.resolution} • {job.aspectRatio}
          </p>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${statusBadgeClass}`}>
          {renderStatusIcon(job.status)}
          {t(`preview.export.status.${job.status}`)}
        </span>
      </div>

      {(job.message || job.failureReason) && (
        <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50/70 px-4 py-3 text-xs text-gray-600">
          {job.failureReason ? job.failureReason : job.message}
        </div>
      )}

      {(job.status === 'running' || job.status === 'queued') && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{t('preview.export.progressLabel')}</span>
            <span className="font-semibold text-gray-700">{Math.round(job.progress)}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-indigo-600 transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, job.progress))}%` }}
            />
          </div>
        </div>
      )}

      <div className={`space-y-3 ${direction === 'rtl' ? 'text-right' : ''}`}>
        {timelineStatuses.map((status) => {
          const entry = historyMap[status];
          const isActive = job.status === status;
          const isComplete =
            status === 'completed' || status === 'failed' || status === 'canceled'
              ? job.status === status
              : !!entry && job.status !== status;
          const timestamp = entry?.timestamp ?? (isActive ? job.updatedAt : undefined);

          return (
            <div key={status} className="flex items-start gap-3">
              <span
                className={`mt-1 h-2.5 w-2.5 rounded-full ${
                  isActive
                    ? 'bg-indigo-500'
                    : isComplete
                    ? status === 'failed'
                      ? 'bg-red-500'
                      : status === 'canceled'
                      ? 'bg-gray-400'
                      : 'bg-emerald-500'
                    : 'bg-gray-300'
                }`}
              />
              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-800">
                  {t(`preview.export.status.${status}`)}
                </p>
                {entry?.message && (
                  <p className="text-xs text-gray-500 leading-relaxed">{entry.message}</p>
                )}
                {timestamp && (
                  <p className="text-[11px] text-gray-400">
                    {formatLocalizedTimestamp(timestamp, i18n.language)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {job.result && (
        <div className="rounded-xl bg-indigo-50/70 p-4 text-xs text-gray-700">
          <p className="text-sm font-semibold text-gray-900 mb-2">
            {t('preview.export.metadata.title')}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-wide text-gray-500">
                {t('preview.export.metadata.format')}
              </p>
              <p className="mt-1 font-medium text-gray-800">{job.result.format}</p>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide text-gray-500">
                {t('preview.export.metadata.duration')}
              </p>
              <p className="mt-1 font-medium text-gray-800">
                {durationSeconds ? formatDuration(durationSeconds) : '—'}
              </p>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide text-gray-500">
                {t('preview.export.metadata.size')}
              </p>
              <p className="mt-1 font-medium text-gray-800">
                {formatFileSize(job.result.filesize)}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className={`flex flex-wrap items-center gap-2 ${direction === 'rtl' ? 'justify-end' : ''}`}>
        {canCancel && (
          <button
            type="button"
            onClick={() => onCancel(job)}
            disabled={canceling}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {canceling ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {t('preview.export.actions.cancel')}
          </button>
        )}

        {canRetry && (
          <button
            type="button"
            onClick={() => onRetry(job)}
            disabled={retrying}
            className="inline-flex items-center gap-2 rounded-lg border border-indigo-200 bg-white px-3 py-2 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {retrying ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {t('preview.export.actions.retry')}
          </button>
        )}

        {canDownload && (
          <>
            <button
              type="button"
              onClick={() => onDownload(job)}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-indigo-500"
            >
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
              {t('preview.export.actions.download')}
            </button>
            <button
              type="button"
              onClick={() => onShare(job)}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <Share2 className="h-3.5 w-3.5" aria-hidden="true" />
              {t('preview.export.actions.share')}
            </button>
            <button
              type="button"
              onClick={() => onOpen(job)}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
              {t('preview.export.actions.open')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
