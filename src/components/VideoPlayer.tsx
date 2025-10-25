import { Play, Pause, Volume2, VolumeX, Maximize, Settings } from 'lucide-react';
import { useState } from 'react';
import { useVideoPlayer } from '../hooks/useVideoPlayer';
import { SubtitleCue } from '../types/preview';

interface VideoPlayerProps {
  src: string;
  subtitles?: SubtitleCue[];
  onTimeUpdate?: (time: number) => void;
  className?: string;
}

export function VideoPlayer({ src, subtitles = [], onTimeUpdate, className = '' }: VideoPlayerProps) {
  const { videoRef, state, togglePlayPause, seek, setVolume } = useVideoPlayer();
  const [showControls, setShowControls] = useState(true);
  const [isMuted, setIsMuted] = useState(false);

  const currentSubtitle = subtitles.find(
    (sub) => state.currentTime >= sub.start && state.currentTime <= sub.end
  );

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    seek(time);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    setVolume(isMuted ? 1 : 0);
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  return (
    <div
      className={`relative bg-black rounded-lg overflow-hidden ${className}`}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(state.isPlaying ? false : true)}
    >
      <video
        ref={videoRef}
        src={src}
        className="w-full h-full object-contain"
        onClick={togglePlayPause}
        onTimeUpdate={() => onTimeUpdate?.(state.currentTime)}
      />

      {currentSubtitle && (
        <div className="absolute bottom-20 left-0 right-0 text-center px-4">
          <div className="inline-block bg-black/80 text-white px-4 py-2 rounded text-lg font-medium">
            {currentSubtitle.text}
          </div>
        </div>
      )}

      {state.isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin" />
        </div>
      )}

      {state.error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center text-white">
            <p className="text-lg mb-2">Failed to load video</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {showControls && !state.error && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
          <input
            type="range"
            min="0"
            max={state.duration || 0}
            value={state.currentTime}
            onChange={handleSeek}
            className="w-full mb-3 h-1 bg-white/30 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${
                (state.currentTime / state.duration) * 100
              }%, rgba(255,255,255,0.3) ${(state.currentTime / state.duration) * 100}%, rgba(255,255,255,0.3) 100%)`,
            }}
          />

          <div className="flex items-center justify-between text-white">
            <div className="flex items-center gap-3">
              <button
                onClick={togglePlayPause}
                className="p-2 hover:bg-white/20 rounded-full transition"
                aria-label={state.isPlaying ? 'Pause' : 'Play'}
              >
                {state.isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>

              <button
                onClick={toggleMute}
                className="p-2 hover:bg-white/20 rounded-full transition"
                aria-label={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>

              <span className="text-sm">
                {formatTime(state.currentTime)} / {formatTime(state.duration)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                className="p-2 hover:bg-white/20 rounded-full transition"
                aria-label="Settings"
              >
                <Settings size={20} />
              </button>

              <button
                onClick={toggleFullscreen}
                className="p-2 hover:bg-white/20 rounded-full transition"
                aria-label="Fullscreen"
              >
                <Maximize size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
