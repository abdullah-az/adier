import { useEffect, useMemo, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Languages,
  Plus,
  Scissors,
  Trash2,
  WrapText,
} from 'lucide-react';

import type { TimelineSubtitleSegment } from '../types/timeline';

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const generateSegmentId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `seg-${Math.random().toString(36).slice(2, 10)}`;

const normaliseSegments = (segments: TimelineSubtitleSegment[]): TimelineSubtitleSegment[] =>
  segments
    .map(segment => {
      const startValue = Number(segment.start);
      const safeStart = Number.isFinite(startValue) ? startValue : 0;
      const endValue = Number(segment.end);
      const initialEnd = Number.isFinite(endValue) ? endValue : safeStart + 0.1;
      const safeEnd = initialEnd <= safeStart ? safeStart + 0.1 : initialEnd;

      return {
        ...segment,
        start: Number.parseFloat(safeStart.toFixed(3)),
        end: Number.parseFloat(safeEnd.toFixed(3)),
        text: segment.text ?? '',
        language: segment.language || 'en',
        isVisible: segment.isVisible ?? true,
      };
    })
    .sort((a, b) => a.start - b.start);

interface SubtitleEditorProps {
  segments: TimelineSubtitleSegment[];
  currentTime: number;
  onSegmentsChange: (segments: TimelineSubtitleSegment[]) => void;
  isSaving: boolean;
  error?: string | null;
}

export function SubtitleEditor({
  segments,
  currentTime,
  onSegmentsChange,
  isSaving,
  error,
}: SubtitleEditorProps) {
  const [expanded, setExpanded] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!segments.length) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !segments.some(segment => segment.id === selectedId)) {
      setSelectedId(segments[0]?.id ?? null);
    }
  }, [segments, selectedId]);

  const activeSegmentId = useMemo(() => {
    return (
      segments.find(segment => currentTime >= segment.start && currentTime <= segment.end)?.id ?? null
    );
  }, [segments, currentTime]);

  const handleSegmentUpdate = (segmentId: string, update: Partial<TimelineSubtitleSegment>) => {
    const nextSegments = segments.map(segment =>
      segment.id === segmentId ? { ...segment, ...update } : segment,
    );
    onSegmentsChange(normaliseSegments(nextSegments));
  };

  const handleSplit = (segmentId: string) => {
    const target = segments.find(segment => segment.id === segmentId);
    if (!target) return;

    const splitPoint = clamp(currentTime, target.start + 0.05, target.end - 0.05);
    const effectiveSplit = Number.isFinite(splitPoint)
      ? splitPoint
      : target.start + (target.end - target.start) / 2;

    if (!(effectiveSplit > target.start && effectiveSplit < target.end)) {
      return;
    }

    const first: TimelineSubtitleSegment = {
      ...target,
      end: Number(effectiveSplit.toFixed(3)),
    };

    const second: TimelineSubtitleSegment = {
      ...target,
      id: generateSegmentId(),
      start: Number(effectiveSplit.toFixed(3)),
      text: '',
    };

    const updated = segments.flatMap(segment => (segment.id === segmentId ? [first, second] : [segment]));
    onSegmentsChange(normaliseSegments(updated));
    setSelectedId(second.id);
  };

  const handleMerge = (segmentId: string, direction: 'previous' | 'next') => {
    const index = segments.findIndex(segment => segment.id === segmentId);
    if (index === -1) return;

    const targetIndex = direction === 'previous' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= segments.length) return;

    const current = segments[index];
    const other = segments[targetIndex];
    const [firstSegment, secondSegment] =
      direction === 'previous' ? [other, current] : [current, other];

    const combinedText = [firstSegment.text, secondSegment.text]
      .map(value => (value ?? '').trim())
      .filter(Boolean)
      .join('\n');

    const merged: TimelineSubtitleSegment = {
      ...firstSegment,
      id: firstSegment.id,
      start: Math.min(firstSegment.start, secondSegment.start),
      end: Math.max(firstSegment.end, secondSegment.end),
      text: combinedText,
      language:
        firstSegment.language === 'auto' && secondSegment.language
          ? secondSegment.language
          : firstSegment.language,
      isVisible: firstSegment.isVisible && secondSegment.isVisible,
    };

    const candidate = segments.filter((_, idx) => idx !== index && idx !== targetIndex);
    candidate.push(merged);
    onSegmentsChange(normaliseSegments(candidate));
    setSelectedId(merged.id);
  };

  const handleAddSegment = () => {
    const baseStart = Number.isFinite(currentTime) ? currentTime : segments.at(-1)?.end ?? 0;
    const newSegment: TimelineSubtitleSegment = {
      id: generateSegmentId(),
      start: Number(baseStart.toFixed(2)),
      end: Number((baseStart + 2).toFixed(2)),
      text: '',
      language: 'en',
      isVisible: true,
    };
    onSegmentsChange(normaliseSegments([...segments, newSegment]));
    setSelectedId(newSegment.id);
  };

  const handleRemoveSegment = (segmentId: string) => {
    const updated = segments.filter(segment => segment.id !== segmentId);
    onSegmentsChange(normaliseSegments(updated));
    if (selectedId === segmentId) {
      setSelectedId(updated[0]?.id ?? null);
    }
  };

  return (
    <div className="bg-white border rounded-lg shadow-sm">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 border-b hover:bg-gray-50 transition"
        onClick={() => setExpanded(prev => !prev)}
      >
        <span className="flex items-center gap-2 font-semibold text-gray-800">
          <WrapText size={18} />
          Subtitle Editor
        </span>
        <span className="flex items-center gap-3 text-sm text-gray-500">
          {isSaving && <span className="animate-pulse">Saving…</span>}
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </span>
      </button>

      {expanded && (
        <div className="p-4 space-y-4">
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Manage transcript segments, adjust timing, and toggle visibility. Changes auto-save to your project.
            </p>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
              onClick={handleAddSegment}
            >
              <Plus size={16} />
              Add Segment
            </button>
          </div>

          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {segments.length === 0 ? (
              <div className="rounded-md border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500">
                No subtitles yet. Click “Add Segment” to begin.
              </div>
            ) : (
              segments.map((segment, index) => {
                const isSelected = selectedId === segment.id;
                const isActive = activeSegmentId === segment.id;
                const direction = segment.language === 'ar' ? 'rtl' : 'ltr';

                return (
                  <div
                    key={segment.id}
                    className={`rounded-lg border transition ${
                      isSelected ? 'border-blue-400 bg-blue-50/40' : 'border-gray-200 bg-white'
                    } ${isActive ? 'ring-1 ring-blue-400' : ''}`}
                  >
                    <div className="flex items-center justify-between border-b px-3 py-2 text-xs text-gray-500">
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-gray-700">Segment {index + 1}</span>
                        <span>{segment.start.toFixed(2)}s → {segment.end.toFixed(2)}s</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100"
                          onClick={() => setSelectedId(segment.id)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="text-gray-400 hover:text-gray-600"
                          onClick={() => handleRemoveSegment(segment.id)}
                          title="Delete segment"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    {isSelected && (
                      <div className="space-y-3 p-4">
                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <label className="flex flex-col gap-1">
                            <span className="text-gray-600">Start (s)</span>
                            <input
                              type="number"
                              step="0.05"
                              value={segment.start}
                              onChange={event =>
                                handleSegmentUpdate(segment.id, {
                                  start: Number(event.target.value),
                                })
                              }
                              className="w-full rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                            />
                          </label>
                          <label className="flex flex-col gap-1">
                            <span className="text-gray-600">End (s)</span>
                            <input
                              type="number"
                              step="0.05"
                              value={segment.end}
                              onChange={event =>
                                handleSegmentUpdate(segment.id, {
                                  end: Number(event.target.value),
                                })
                              }
                              className="w-full rounded-md border border-gray-300 px-3 py-1.5 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                            />
                          </label>
                          <label className="flex flex-col gap-1">
                            <span className="text-gray-600">Language</span>
                            <div className="relative">
                              <select
                                value={segment.language}
                                onChange={event =>
                                  handleSegmentUpdate(segment.id, {
                                    language: event.target.value,
                                  })
                                }
                                className="w-full appearance-none rounded-md border border-gray-300 px-3 py-1.5 pr-8 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                              >
                                <option value="en">English</option>
                                <option value="ar">العربية</option>
                                <option value="auto">Auto</option>
                              </select>
                              <Languages className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                            </div>
                          </label>
                        </div>

                        <label className="flex flex-col gap-2 text-sm">
                          <span className="text-gray-600">Subtitle Text</span>
                          <textarea
                            value={segment.text}
                            onChange={event =>
                              handleSegmentUpdate(segment.id, {
                                text: event.target.value,
                              })
                            }
                            dir={direction as 'rtl' | 'ltr'}
                            className="min-h-[96px] w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-300"
                          />
                        </label>

                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            className={`inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm ${
                              segment.isVisible
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                                : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-100'
                            }`}
                            onClick={() =>
                              handleSegmentUpdate(segment.id, { isVisible: !segment.isVisible })
                            }
                          >
                            {segment.isVisible ? <Eye size={16} /> : <EyeOff size={16} />}
                            {segment.isVisible ? 'Visible' : 'Hidden'}
                          </button>

                          <button
                            type="button"
                            className="inline-flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm text-blue-700 hover:bg-blue-100"
                            onClick={() => handleSplit(segment.id)}
                          >
                            <Scissors size={16} />
                            Split at playhead
                          </button>

                          <button
                            type="button"
                            className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => handleMerge(segment.id, 'previous')}
                            disabled={index === 0}
                          >
                            Merge prev
                          </button>
                          <button
                            type="button"
                            className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => handleMerge(segment.id, 'next')}
                            disabled={index === segments.length - 1}
                          >
                            Merge next
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
