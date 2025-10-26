import { useEffect, useMemo, useRef, useState } from 'react';
import {
  CheckCircle2,
  Headphones,
  Loader2,
  Music2,
  Pause,
  Play,
  Radio,
  RefreshCcw,
  Volume2,
} from 'lucide-react';

import { buildStorageUrl } from '../lib/api/timeline';
import type { MusicTrack, TimelineMusicSettings } from '../types/timeline';

interface MusicLibraryProps {
  tracks: MusicTrack[];
  value: TimelineMusicSettings;
  onChange: (settings: TimelineMusicSettings) => void;
  isSaving: boolean;
  error?: string | null;
}

const defaultSettings: TimelineMusicSettings = {
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

const clamp = (value: number, min: number, max: number) => {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.min(Math.max(value, min), max);
};

const toNumber = (value: unknown, fallback = 0) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
};

export function MusicLibrary({ tracks, value, onChange, isSaving, error }: MusicLibraryProps) {
  const settings = useMemo(() => ({ ...defaultSettings, ...value }), [value]);
  const [previewTrackId, setPreviewTrackId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  useEffect(() => {
    if (!previewTrackId) return;
    if (!tracks.some(track => track.trackId === previewTrackId)) {
      audioRef.current?.pause();
      setPreviewTrackId(null);
    }
  }, [tracks, previewTrackId]);

  useEffect(() => {
    const currentTrackId = value.trackId ?? null;
    if (!currentTrackId) return;
    if (!tracks.some(track => track.trackId === currentTrackId)) {
      onChange({ ...defaultSettings, ...value, trackId: null });
    }
  }, [tracks, value, onChange]);

  const handlePreview = async (track: MusicTrack) => {
    setPreviewError(null);
    if (!audioRef.current) {
      audioRef.current = new Audio();
    }

    if (previewTrackId === track.trackId) {
      audioRef.current.pause();
      setPreviewTrackId(null);
      return;
    }

    audioRef.current.pause();
    audioRef.current.src = buildStorageUrl(track.relativePath);
    audioRef.current.currentTime = 0;
    audioRef.current.volume = 1;

    try {
      await audioRef.current.play();
      setPreviewTrackId(track.trackId);
      audioRef.current.onended = () => setPreviewTrackId(null);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : 'Unable to play preview');
      setPreviewTrackId(null);
    }
  };

  const handleSettingsChange = (update: Partial<TimelineMusicSettings>) => {
    onChange({ ...settings, ...update });
  };

  const isTrackSelected = (trackId: string) => settings.trackId === trackId;

  return (
    <div className="bg-white border rounded-lg shadow-sm">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2 text-gray-800">
          <Music2 size={18} />
          <span className="font-semibold">Background Music</span>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          {isSaving && (
            <span className="inline-flex items-center gap-1">
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving…
            </span>
          )}
          <span className="hidden md:inline-flex items-center gap-1">
            <Headphones size={16} /> Preview tracks
          </span>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        {previewError && (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
            {previewError}
          </div>
        )}

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Select a track to bed under the timeline or assign it to a specific clip.</span>
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-gray-500 hover:bg-gray-100"
              onClick={() => handleSettingsChange({ isEnabled: !settings.isEnabled })}
            >
              {settings.isEnabled ? 'Disable' : 'Enable'} music
            </button>
          </div>

          <div className="space-y-2 max-h-[240px] overflow-y-auto pr-1">
            {tracks.length === 0 && (
              <div className="rounded-md border border-dashed border-gray-300 p-5 text-center text-sm text-gray-500">
                Your project music library is empty. Upload tracks to <code className="font-mono">storage/music/{'{project}'}</code> to populate this list.
              </div>
            )}

            {tracks.map(track => {
              const active = isTrackSelected(track.trackId);
              return (
                <div
                  key={track.trackId}
                  className={`flex items-center justify-between rounded-md border px-3 py-2 text-sm transition ${
                    active ? 'border-blue-300 bg-blue-50/60' : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-gray-800">{track.displayName}</span>
                    <span className="text-xs text-gray-500">
                      {track.duration ? `${track.duration.toFixed(0)}s • ` : ''}
                      {(track.sizeBytes / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className={`inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs ${
                        active
                          ? 'border-blue-400 bg-blue-100 text-blue-700'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                      }`}
                      onClick={() => handleSettingsChange({ trackId: track.trackId })}
                      disabled={!settings.isEnabled}
                    >
                      {active ? (
                        <span className="inline-flex items-center gap-1">
                          <CheckCircle2 size={14} /> Selected
                        </span>
                      ) : (
                        'Select'
                      )}
                    </button>
                    <button
                      type="button"
                      className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs ${
                        previewTrackId === track.trackId
                          ? 'border-emerald-400 bg-emerald-50 text-emerald-700'
                          : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                      }`}
                      onClick={() => handlePreview(track)}
                    >
                      {previewTrackId === track.trackId ? (
                        <>
                          <Pause size={14} /> Stop
                        </>
                      ) : (
                        <>
                          <Play size={14} /> Preview
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
          <div className="flex items-center justify-between text-xs uppercase tracking-wide text-gray-500">
            <span>Mix Controls</span>
            {!settings.isEnabled && <span className="text-red-500">Music disabled</span>}
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <label className="flex flex-col gap-2">
              <span>Volume</span>
              <div className="flex items-center gap-3">
                <Volume2 className="h-4 w-4 text-gray-400" />
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={settings.volume}
                  onChange={event => {
                    const nextVolume = clamp(toNumber(event.target.value, settings.volume), 0, 1);
                    handleSettingsChange({ volume: nextVolume });
                    if (audioRef.current) {
                      audioRef.current.volume = nextVolume;
                    }
                  }}
                  className="flex-1 accent-blue-500"
                  disabled={!settings.isEnabled}
                />
                <span className="w-12 text-right font-mono text-xs text-gray-600">
                  {(settings.volume * 100).toFixed(0)}%
                </span>
              </div>
            </label>

            <label className="flex flex-col gap-2">
              <span>Offset (s)</span>
              <input
                type="number"
                min={0}
                step={0.25}
                value={settings.offset}
                onChange={event => {
                  const nextOffset = Math.max(0, toNumber(event.target.value, settings.offset));
                  handleSettingsChange({ offset: nextOffset });
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                disabled={!settings.isEnabled}
              />
            </label>

            <label className="flex flex-col gap-2">
              <span>Fade in (s)</span>
              <input
                type="number"
                min={0}
                step={0.25}
                value={settings.fadeIn}
                onChange={event => {
                  const nextFadeIn = Math.max(0, toNumber(event.target.value, settings.fadeIn));
                  handleSettingsChange({ fadeIn: nextFadeIn });
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                disabled={!settings.isEnabled}
              />
            </label>

            <label className="flex flex-col gap-2">
              <span>Fade out (s)</span>
              <input
                type="number"
                min={0}
                step={0.25}
                value={settings.fadeOut}
                onChange={event => {
                  const nextFadeOut = Math.max(0, toNumber(event.target.value, settings.fadeOut));
                  handleSettingsChange({ fadeOut: nextFadeOut });
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                disabled={!settings.isEnabled}
              />
            </label>
          </div>

          <div className="space-y-2">
            <span className="text-xs uppercase tracking-wide text-gray-500">Placement</span>
            <div className="grid gap-2 md:grid-cols-2">
              <button
                type="button"
                className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition ${
                  settings.placement === 'full_timeline'
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
                onClick={() => handleSettingsChange({ placement: 'full_timeline', clipId: null })}
                disabled={!settings.isEnabled}
              >
                <Radio size={16} /> Full timeline
              </button>

              <button
                type="button"
                className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition ${
                  settings.placement === 'clip_specific'
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
                onClick={() => handleSettingsChange({ placement: 'clip_specific' })}
                disabled={!settings.isEnabled}
              >
                <RefreshCcw size={16} /> Clip specific
              </button>
            </div>

            {settings.placement === 'clip_specific' && (
              <label className="flex flex-col gap-2 text-sm">
                <span>Clip reference</span>
                <input
                  type="text"
                  value={settings.clipId ?? ''}
                  onChange={event => handleSettingsChange({ clipId: event.target.value || null })}
                  className="rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                  placeholder="e.g. clip-02"
                  disabled={!settings.isEnabled}
                />
              </label>
            )}

            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={settings.loop}
                onChange={event => handleSettingsChange({ loop: event.target.checked })}
                className="h-4 w-4"
                disabled={!settings.isEnabled}
              />
              Loop track to cover placement duration
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
