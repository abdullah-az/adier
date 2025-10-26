import { useState, useRef, useEffect } from 'react';
import { Trash2, GripVertical, Scissors, Volume2, VolumeX } from 'lucide-react';
import { TimelineClipExtended } from '../types/timeline';

interface TimelineBuilderProps {
  clips: TimelineClipExtended[];
  onUpdateClips: (clips: TimelineClipExtended[]) => void;
  onRemoveClip: (clipId: string) => void;
  onUpdateClip: (clipId: string, updates: Partial<TimelineClipExtended>) => void;
  maxDuration?: number;
  className?: string;
  isRtl?: boolean;
}

export function TimelineBuilder({
  clips,
  onUpdateClips,
  onRemoveClip,
  onUpdateClip,
  maxDuration,
  className = '',
  isRtl = false,
}: TimelineBuilderProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [resizingClip, setResizingClip] = useState<{ id: string; edge: 'start' | 'end' } | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  const totalDuration = clips.reduce(
    (sum, clip) => sum + (clip.out_point - clip.in_point),
    0
  );

  const handleDragStart = (index: number) => (e: React.DragEvent) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (index: number) => (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverIndex(index);
  };

  const handleDrop = (index: number) => (e: React.DragEvent) => {
    e.preventDefault();
    if (draggedIndex === null) return;

    const newClips = [...clips];
    const [removed] = newClips.splice(draggedIndex, 1);
    newClips.splice(index, 0, removed);
    
    onUpdateClips(newClips.map((clip, idx) => ({ ...clip, order: idx })));
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleResizeStart = (clipId: string, edge: 'start' | 'end') => (e: React.MouseEvent) => {
    e.preventDefault();
    setResizingClip({ id: clipId, edge });
  };

  useEffect(() => {
    if (!resizingClip) return;

    const handleMouseMove = (e: MouseEvent) => {
      const clip = clips.find((c) => c.id === resizingClip.id);
      if (!clip || !timelineRef.current) return;

      const rect = timelineRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = x / rect.width;
      const time = percentage * totalDuration;

      if (resizingClip.edge === 'start') {
        const newInPoint = Math.max(0, Math.min(time, clip.out_point - 0.5));
        onUpdateClip(clip.id, { in_point: newInPoint });
      } else {
        const newOutPoint = Math.max(clip.in_point + 0.5, time);
        onUpdateClip(clip.id, { out_point: newOutPoint });
      }
    };

    const handleMouseUp = () => {
      setResizingClip(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizingClip, clips, totalDuration]);

  const getQualityColor = (score?: number) => {
    if (!score) return 'bg-gray-400';
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`} dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Timeline</h3>
        <div className="text-sm text-gray-600">
          <span className="font-medium">{clips.length}</span> clips
          {maxDuration && (
            <span className="ml-2">
              ({totalDuration.toFixed(1)}s / {maxDuration}s)
            </span>
          )}
        </div>
      </div>

      {maxDuration && totalDuration > maxDuration && (
        <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
          ⚠ Timeline exceeds maximum duration
        </div>
      )}

      <div 
        ref={timelineRef}
        className="space-y-2 min-h-[200px] max-h-[600px] overflow-y-auto"
      >
        {clips.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Scissors size={48} className="mx-auto mb-2 opacity-30" />
            <p>No clips in timeline</p>
            <p className="text-sm mt-1">Add AI scenes or search transcript to get started</p>
          </div>
        ) : (
          clips.map((clip, index) => {
            const duration = clip.out_point - clip.in_point;
            const isDragging = draggedIndex === index;
            const isDragOver = dragOverIndex === index;

            return (
              <div
                key={clip.id}
                draggable
                onDragStart={handleDragStart(index)}
                onDragOver={handleDragOver(index)}
                onDrop={handleDrop(index)}
                onDragEnd={handleDragEnd}
                className={`border rounded-lg p-3 transition-all ${
                  isDragging ? 'opacity-50' : ''
                } ${
                  isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                } hover:bg-gray-50 cursor-move`}
              >
                <div className="flex items-center gap-3">
                  <div className="cursor-grab active:cursor-grabbing text-gray-400">
                    <GripVertical size={20} />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">Clip {index + 1}</span>
                        <span
                          className={`px-2 py-0.5 text-xs rounded ${
                            clip.source_type === 'ai_scene'
                              ? 'bg-purple-100 text-purple-700'
                              : clip.source_type === 'transcript'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {clip.source_type.replace('_', ' ')}
                        </span>
                        {clip.quality_score !== undefined && (
                          <div
                            className={`w-2 h-2 rounded-full ${getQualityColor(
                              clip.quality_score
                            )}`}
                            title={`Quality: ${(clip.quality_score * 100).toFixed(0)}%`}
                          />
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onUpdateClip(clip.id, { include_audio: !clip.include_audio })}
                          className="p-1 text-gray-600 hover:text-gray-900 transition"
                          title={clip.include_audio ? 'Mute audio' : 'Enable audio'}
                        >
                          {clip.include_audio ? <Volume2 size={16} /> : <VolumeX size={16} />}
                        </button>
                        <button
                          onClick={() => onRemoveClip(clip.id)}
                          className="p-1 text-red-600 hover:text-red-800 transition"
                          title="Remove clip"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <div className="flex items-center gap-1">
                        <button
                          onMouseDown={handleResizeStart(clip.id, 'start')}
                          className="px-1 py-0.5 bg-blue-100 hover:bg-blue-200 rounded cursor-ew-resize"
                        >
                          ◀
                        </button>
                        <span>{clip.in_point.toFixed(2)}s</span>
                      </div>
                      <span className="text-gray-400">→</span>
                      <div className="flex items-center gap-1">
                        <span>{clip.out_point.toFixed(2)}s</span>
                        <button
                          onMouseDown={handleResizeStart(clip.id, 'end')}
                          className="px-1 py-0.5 bg-blue-100 hover:bg-blue-200 rounded cursor-ew-resize"
                        >
                          ▶
                        </button>
                      </div>
                      <span className="text-gray-500">
                        (Duration: {duration.toFixed(2)}s)
                      </span>
                    </div>

                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs text-gray-500">Transition:</span>
                      <select
                        value={clip.transition.type}
                        onChange={(e) =>
                          onUpdateClip(clip.id, {
                            transition: {
                              ...clip.transition,
                              type: e.target.value as any,
                            },
                          })
                        }
                        className="text-xs border rounded px-2 py-1"
                      >
                        <option value="cut">Cut</option>
                        <option value="crossfade">Crossfade</option>
                        <option value="fade_to_black">Fade to Black</option>
                        <option value="fade_to_white">Fade to White</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
