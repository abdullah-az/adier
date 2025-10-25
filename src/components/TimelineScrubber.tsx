import { TimelineClip } from '../types/preview';

interface TimelineScrubberProps {
  clips: TimelineClip[];
  currentTime: number;
  duration: number;
  onSeek: (time: number) => void;
  className?: string;
}

export function TimelineScrubber({ clips, currentTime, duration, onSeek, className = '' }: TimelineScrubberProps) {
  const getClipColor = (index: number) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-indigo-500',
      'bg-teal-500',
    ];
    return colors[index % colors.length];
  };

  const getClipDuration = (clip: TimelineClip, index: number): number => {
    if (clip.out_point !== undefined) {
      return clip.out_point - clip.in_point;
    }
    return 5;
  };

  const getClipPosition = (clipIndex: number): { start: number; width: number } => {
    let totalTime = 0;
    for (let i = 0; i < clipIndex; i++) {
      totalTime += getClipDuration(clips[i], i);
    }
    const clipDuration = getClipDuration(clips[clipIndex], clipIndex);
    const start = (totalTime / duration) * 100;
    const width = (clipDuration / duration) * 100;
    return { start, width };
  };

  const currentClipIndex = (() => {
    let accumulatedTime = 0;
    for (let i = 0; i < clips.length; i++) {
      const clipDuration = getClipDuration(clips[i], i);
      if (currentTime >= accumulatedTime && currentTime < accumulatedTime + clipDuration) {
        return i;
      }
      accumulatedTime += clipDuration;
    }
    return clips.length - 1;
  })();

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const time = percentage * duration;
    onSeek(time);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`${className}`}>
      <div className="mb-2 flex items-center justify-between text-sm text-gray-600">
        <span>Timeline</span>
        <span className="font-mono">{formatTime(currentTime)} / {formatTime(duration)}</span>
      </div>

      <div
        className="relative h-16 bg-gray-200 rounded-lg overflow-hidden cursor-pointer group"
        onClick={handleTimelineClick}
      >
        {clips.map((clip, index) => {
          const { start, width } = getClipPosition(index);
          const isActive = index === currentClipIndex;
          return (
            <div
              key={index}
              className={`absolute top-0 h-full ${getClipColor(index)} transition-all ${
                isActive ? 'opacity-100 ring-2 ring-white' : 'opacity-70 hover:opacity-90'
              }`}
              style={{
                left: `${start}%`,
                width: `${width}%`,
              }}
              title={`Clip ${index + 1} (${clip.asset_id})`}
            >
              <div className="h-full flex items-center justify-center text-white text-xs font-semibold">
                {index + 1}
              </div>
              {clip.transition.type !== 'cut' && (
                <div className="absolute top-0 right-0 h-full w-1 bg-white/50" title={`Transition: ${clip.transition.type}`} />
              )}
            </div>
          );
        })}

        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none z-10"
          style={{
            left: `${(currentTime / duration) * 100}%`,
          }}
        >
          <div className="absolute -top-1 -left-1.5 w-3 h-3 bg-red-500 rounded-full" />
        </div>
      </div>

      <div className="mt-3 flex gap-2 overflow-x-auto pb-2">
        {clips.map((clip, index) => {
          const isActive = index === currentClipIndex;
          return (
            <button
              key={index}
              onClick={() => {
                let accumulatedTime = 0;
                for (let i = 0; i < index; i++) {
                  accumulatedTime += getClipDuration(clips[i], i);
                }
                onSeek(accumulatedTime);
              }}
              className={`flex-shrink-0 px-3 py-2 rounded text-sm transition ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <div className="font-semibold">Clip {index + 1}</div>
              <div className="text-xs opacity-80 mt-1">
                {clip.in_point.toFixed(1)}s - {clip.out_point?.toFixed(1) || 'end'}s
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
