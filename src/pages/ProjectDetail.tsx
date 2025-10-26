import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Save, Play, AlertCircle, Info, Settings, Languages } from 'lucide-react';
import { AIScenesList } from '../components/AIScenesList';
import { TranscriptSearch } from '../components/TranscriptSearch';
import { TimelineBuilder } from '../components/TimelineBuilder';
import { useTimeline } from '../hooks/useTimeline';
import { AIScene, TranscriptSegment, TimelineClipExtended } from '../types/timeline';

export default function ProjectDetail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('project') || 'demo';
  const timelineId = searchParams.get('timeline') || undefined;

  const [selectedSceneIds, setSelectedSceneIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'ai' | 'transcript'>('ai');
  const [language, setLanguage] = useState<'en' | 'ar'>('en');

  const {
    timeline,
    loading,
    error,
    saving,
    updateClips,
    addClip,
    removeClip,
    updateClip,
    saveTimeline,
    validateTimeline,
  } = useTimeline({
    projectId,
    timelineId,
    autoSave: true,
    autoSaveDelay: 2000,
  });

  useEffect(() => {
    if (timeline) {
      const sceneIds = new Set(
        timeline.clips
          .filter((c) => c.source_type === 'ai_scene' && c.source_id)
          .map((c) => c.source_id!)
      );
      setSelectedSceneIds(sceneIds);
    }
  }, [timeline]);

  const handleSelectScene = (scene: AIScene) => {
    const isSelected = selectedSceneIds.has(scene.id);
    
    if (isSelected) {
      // Remove from timeline
      const clipToRemove = timeline?.clips.find(
        (c) => c.source_type === 'ai_scene' && c.source_id === scene.id
      );
      if (clipToRemove) {
        removeClip(clipToRemove.id);
      }
      setSelectedSceneIds((prev) => {
        const next = new Set(prev);
        next.delete(scene.id);
        return next;
      });
    } else {
      // Add to timeline
      const newClip: TimelineClipExtended = {
        id: `clip-${Date.now()}-${Math.random()}`,
        asset_id: scene.asset_id,
        in_point: scene.start_time,
        out_point: scene.end_time,
        transition: {
          type: 'cut',
          duration: 0,
        },
        include_audio: true,
        order: timeline?.clips.length || 0,
        source_type: 'ai_scene',
        source_id: scene.id,
        quality_score: scene.quality_score,
        confidence: scene.confidence,
      };
      addClip(newClip);
      setSelectedSceneIds((prev) => new Set(prev).add(scene.id));
    }
  };

  const handleSelectSegment = (segment: TranscriptSegment) => {
    const newClip: TimelineClipExtended = {
      id: `clip-${Date.now()}-${Math.random()}`,
      asset_id: segment.asset_id,
      in_point: segment.start_time,
      out_point: segment.end_time,
      transition: {
        type: 'cut',
        duration: 0,
      },
      include_audio: true,
      order: timeline?.clips.length || 0,
      source_type: 'transcript',
      source_id: segment.id,
      confidence: segment.confidence,
    };
    addClip(newClip);
  };

  const handleManualSave = async () => {
    await saveTimeline();
  };

  const handleExport = () => {
    const validation = validateTimeline();
    if (!validation.isValid) {
      alert(`Cannot export:\n${validation.errors.join('\n')}`);
      return;
    }
    // Navigate to export/preview
    if (timeline) {
      navigate(`/preview?project=${projectId}&timeline=${timeline.id}`);
    }
  };

  const isRtl = language === 'ar';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error && !timeline) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to Load Project</h2>
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

  const totalDuration = timeline?.clips.reduce(
    (sum, clip) => sum + (clip.out_point - clip.in_point),
    0
  ) || 0;

  return (
    <div className="min-h-screen bg-gray-50" dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="max-w-[1800px] mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {timeline?.name || 'New Timeline'}
              </h1>
              <p className="text-gray-600 mt-1">Project: {projectId}</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setLanguage(language === 'en' ? 'ar' : 'en')}
                className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition"
                title="Toggle language"
              >
                <Languages size={18} />
                {language.toUpperCase()}
              </button>

              <button
                onClick={handleManualSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 disabled:bg-gray-100 transition"
                title="Save timeline"
              >
                <Save size={18} />
                {saving ? 'Saving...' : 'Save'}
              </button>

              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                title="Preview timeline"
              >
                <Play size={18} />
                Preview
              </button>
            </div>
          </div>

          {saving && (
            <div className="text-sm text-blue-600 flex items-center gap-2">
              <div className="w-3 h-3 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
              Auto-saving...
            </div>
          )}

          {error && (
            <div className="mt-2 p-3 bg-red-50 text-red-600 rounded-lg text-sm flex items-start gap-2">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
        </div>

        {/* Metadata Overview */}
        <div className="mb-6 bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Info size={16} className="text-gray-400" />
              <span className="text-gray-600">Clips:</span>
              <span className="font-medium">{timeline?.clips.length || 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <Settings size={16} className="text-gray-400" />
              <span className="text-gray-600">Duration:</span>
              <span className="font-medium">{totalDuration.toFixed(2)}s</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Aspect Ratio:</span>
              <span className="font-medium">{timeline?.aspect_ratio || '16:9'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Resolution:</span>
              <span className="font-medium">{timeline?.resolution || '1080p'}</span>
            </div>
            {timeline?.max_duration && (
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Max Duration:</span>
                <span
                  className={`font-medium ${
                    totalDuration > timeline.max_duration ? 'text-red-600' : ''
                  }`}
                >
                  {timeline.max_duration}s
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Timeline Builder */}
          <div className="lg:col-span-2">
            <TimelineBuilder
              clips={timeline?.clips || []}
              onUpdateClips={updateClips}
              onRemoveClip={removeClip}
              onUpdateClip={updateClip}
              maxDuration={timeline?.max_duration}
              isRtl={isRtl}
            />
          </div>

          {/* Right Column - AI Scenes & Transcript Search */}
          <div className="space-y-6">
            {/* Tab Switcher */}
            <div className="bg-white rounded-lg shadow-sm">
              <div className="flex border-b">
                <button
                  onClick={() => setActiveTab('ai')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                    activeTab === 'ai'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  AI Suggestions
                </button>
                <button
                  onClick={() => setActiveTab('transcript')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                    activeTab === 'transcript'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Transcript Search
                </button>
              </div>
            </div>

            {/* Content based on active tab */}
            {activeTab === 'ai' ? (
              <AIScenesList
                projectId={projectId}
                onSelectScene={handleSelectScene}
                selectedSceneIds={selectedSceneIds}
              />
            ) : (
              <TranscriptSearch
                projectId={projectId}
                onSelectSegment={handleSelectSegment}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
