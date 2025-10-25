import { AlertCircle, CheckCircle, Clock, Loader2, RefreshCw } from 'lucide-react';
import { JobStatus } from '../types/preview';

interface PreviewStatusBarProps {
  jobStatus: JobStatus | null;
  onRefresh: () => void;
  className?: string;
}

export function PreviewStatusBar({ jobStatus, onRefresh, className = '' }: PreviewStatusBarProps) {
  if (!jobStatus) {
    return null;
  }

  const getStatusIcon = () => {
    switch (jobStatus.status) {
      case 'queued':
        return <Clock className="text-yellow-500" size={20} />;
      case 'running':
        return <Loader2 className="text-blue-500 animate-spin" size={20} />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'failed':
        return <AlertCircle className="text-red-500" size={20} />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (jobStatus.status) {
      case 'queued':
        return 'bg-yellow-50 border-yellow-200';
      case 'running':
        return 'bg-blue-50 border-blue-200';
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusText = () => {
    switch (jobStatus.status) {
      case 'queued':
        return 'Preview generation queued...';
      case 'running':
        return jobStatus.message || 'Generating preview...';
      case 'completed':
        return 'Preview ready!';
      case 'failed':
        return 'Preview generation failed';
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor()} ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <p className="font-medium text-gray-900">{getStatusText()}</p>
            {jobStatus.status === 'running' && (
              <div className="mt-2 w-64">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${jobStatus.progress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1">{jobStatus.progress.toFixed(0)}% complete</p>
              </div>
            )}
            {jobStatus.status === 'failed' && jobStatus.message && (
              <p className="text-sm text-red-600 mt-1">{jobStatus.message}</p>
            )}
          </div>
        </div>

        {jobStatus.status === 'failed' && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 transition"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
