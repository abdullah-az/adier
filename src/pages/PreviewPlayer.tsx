import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertCircle, Download, Settings, Share2 } from 'lucide-react';
import { VideoPlayer } from '../components/VideoPlayer';
import { TimelineScrubber } from '../components/TimelineScrubber';
import { PreviewStatusBar } from '../components/PreviewStatusBar';
import { useEventSource } from '../hooks/useEventSource';
import { TimelinePreview, JobStatus, SubtitleCue } from '../types/preview';
import { loadSubtitles } from '../utils/subtitles';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
