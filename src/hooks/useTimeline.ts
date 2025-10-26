import { useState, useCallback, useEffect, useRef } from 'react';
import { Timeline, TimelineClipExtended, TimelineConstraints } from '../types/timeline';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface UseTimelineOptions {
  projectId: string;
  timelineId?: string;
  autoSave?: boolean;
  autoSaveDelay?: number;
}

interface UseTimelineReturn {
  timeline: Timeline | null;
  loading: boolean;
  error: string | null;
  saving: boolean;
  updateClips: (clips: TimelineClipExtended[]) => void;
  addClip: (clip: TimelineClipExtended) => void;
  removeClip: (clipId: string) => void;
  reorderClip: (fromIndex: number, toIndex: number) => void;
  updateClip: (clipId: string, updates: Partial<TimelineClipExtended>) => void;
  saveTimeline: () => Promise<void>;
  validateTimeline: () => { isValid: boolean; errors: string[] };
}

export function useTimeline({
  projectId,
  timelineId,
  autoSave = true,
  autoSaveDelay = 1000,
}: UseTimelineOptions): UseTimelineReturn {
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingChangesRef = useRef(false);

  // Fetch timeline on mount
  useEffect(() => {
    if (timelineId) {
      fetchTimeline();
    } else {
      setLoading(false);
    }
  }, [projectId, timelineId]);

  // Auto-save effect
  useEffect(() => {
    if (autoSave && pendingChangesRef.current && timeline) {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      saveTimeoutRef.current = setTimeout(() => {
        saveTimeline();
      }, autoSaveDelay);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [timeline, autoSave, autoSaveDelay]);

  const fetchTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/timelines/${timelineId}`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }
      const data = await response.json();
      setTimeline(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
    } finally {
      setLoading(false);
    }
  };

  const saveTimeline = useCallback(async () => {
    if (!timeline) return;

    setSaving(true);
    setError(null);
    try {
      const url = timeline.id
        ? `${API_BASE_URL}/projects/${projectId}/timelines/${timeline.id}`
        : `${API_BASE_URL}/projects/${projectId}/timelines`;
      
      const method = timeline.id ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(timeline),
      });

      if (!response.ok) {
        throw new Error('Failed to save timeline');
      }

      const savedTimeline = await response.json();
      setTimeline(savedTimeline);
      pendingChangesRef.current = false;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save timeline');
    } finally {
      setSaving(false);
    }
  }, [timeline, projectId]);

  const updateClips = useCallback((clips: TimelineClipExtended[]) => {
    setTimeline((prev) => {
      if (!prev) return prev;
      pendingChangesRef.current = true;
      return {
        ...prev,
        clips: clips.map((clip, index) => ({ ...clip, order: index })),
        updated_at: new Date().toISOString(),
      };
    });
  }, []);

  const addClip = useCallback((clip: TimelineClipExtended) => {
    setTimeline((prev) => {
      if (!prev) return prev;
      pendingChangesRef.current = true;
      const newClips = [...prev.clips, { ...clip, order: prev.clips.length }];
      return {
        ...prev,
        clips: newClips,
        updated_at: new Date().toISOString(),
      };
    });
  }, []);

  const removeClip = useCallback((clipId: string) => {
    setTimeline((prev) => {
      if (!prev) return prev;
      pendingChangesRef.current = true;
      const newClips = prev.clips
        .filter((c) => c.id !== clipId)
        .map((clip, index) => ({ ...clip, order: index }));
      return {
        ...prev,
        clips: newClips,
        updated_at: new Date().toISOString(),
      };
    });
  }, []);

  const reorderClip = useCallback((fromIndex: number, toIndex: number) => {
    setTimeline((prev) => {
      if (!prev) return prev;
      pendingChangesRef.current = true;
      const newClips = [...prev.clips];
      const [movedClip] = newClips.splice(fromIndex, 1);
      newClips.splice(toIndex, 0, movedClip);
      return {
        ...prev,
        clips: newClips.map((clip, index) => ({ ...clip, order: index })),
        updated_at: new Date().toISOString(),
      };
    });
  }, []);

  const updateClip = useCallback(
    (clipId: string, updates: Partial<TimelineClipExtended>) => {
      setTimeline((prev) => {
        if (!prev) return prev;
        pendingChangesRef.current = true;
        const newClips = prev.clips.map((clip) =>
          clip.id === clipId ? { ...clip, ...updates } : clip
        );
        return {
          ...prev,
          clips: newClips,
          updated_at: new Date().toISOString(),
        };
      });
    },
    []
  );

  const validateTimeline = useCallback(() => {
    const errors: string[] = [];
    
    if (!timeline) {
      errors.push('No timeline loaded');
      return { isValid: false, errors };
    }

    if (timeline.clips.length === 0) {
      errors.push('Timeline must have at least one clip');
    }

    // Check for overlaps
    const sortedClips = [...timeline.clips].sort((a, b) => a.order - b.order);
    for (let i = 0; i < sortedClips.length - 1; i++) {
      const currentClip = sortedClips[i];
      const nextClip = sortedClips[i + 1];
      
      if (currentClip.out_point > nextClip.in_point) {
        errors.push(`Clip ${i + 1} overlaps with clip ${i + 2}`);
      }
    }

    // Check max duration if specified
    if (timeline.max_duration) {
      const totalDuration = timeline.clips.reduce(
        (sum, clip) => sum + (clip.out_point - clip.in_point),
        0
      );
      if (totalDuration > timeline.max_duration) {
        errors.push(
          `Timeline duration (${totalDuration.toFixed(2)}s) exceeds maximum (${timeline.max_duration}s)`
        );
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, [timeline]);

  return {
    timeline,
    loading,
    error,
    saving,
    updateClips,
    addClip,
    removeClip,
    reorderClip,
    updateClip,
    saveTimeline,
    validateTimeline,
  };
}
