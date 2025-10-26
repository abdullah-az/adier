import { useState, useEffect } from 'react';
import { Sparkles, Plus, TrendingUp, TrendingDown } from 'lucide-react';
import { AIScene } from '../types/timeline';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AIScenesListProps {
  projectId: string;
  onSelectScene: (scene: AIScene) => void;
  selectedSceneIds?: Set<string>;
  className?: string;
}

export function AIScenesList({
  projectId,
  onSelectScene,
  selectedSceneIds = new Set(),
  className = '',
}: AIScenesListProps) {
  const [scenes, setScenes] = useState<AIScene[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [minQuality, setMinQuality] = useState(0.5);

  useEffect(() => {
    fetchScenes();
  }, [projectId, minQuality]);

  const fetchScenes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/ai-scenes?min_quality=${minQuality}`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch AI scenes');
      }
      const data = await response.json();
      setScenes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load AI scenes');
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityIcon = (score: number) => {
    if (score >= 0.7) return <TrendingUp size={16} />;
    return <TrendingDown size={16} />;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`}>
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button
            onClick={fetchScenes}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`} dir="ltr">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Sparkles className="text-purple-600" size={20} />
          AI Suggestions
        </h3>
        <div className="flex items-center gap-2 text-sm">
          <label className="text-gray-600">Min Quality:</label>
          <select
            value={minQuality}
            onChange={(e) => setMinQuality(Number(e.target.value))}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value={0}>All</option>
            <option value={0.5}>50%+</option>
            <option value={0.7}>70%+</option>
            <option value={0.8}>80%+</option>
            <option value={0.9}>90%+</option>
          </select>
        </div>
      </div>

      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {scenes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Sparkles size={48} className="mx-auto mb-2 opacity-50" />
            <p>No AI scenes available</p>
            <p className="text-sm mt-1">Upload videos to get AI suggestions</p>
          </div>
        ) : (
          scenes.map((scene) => {
            const isSelected = selectedSceneIds.has(scene.id);
            const duration = scene.end_time - scene.start_time;

            return (
              <div
                key={scene.id}
                className={`border rounded-lg p-3 transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-blue-50 border-blue-500'
                    : 'hover:bg-gray-50 border-gray-200'
                }`}
                onClick={() => onSelectScene(scene)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm capitalize">
                        {scene.scene_type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {duration.toFixed(1)}s
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {scene.description || 'No description'}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectScene(scene);
                    }}
                    className={`p-1 rounded transition ${
                      isSelected
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                    title={isSelected ? 'Remove from timeline' : 'Add to timeline'}
                  >
                    <Plus size={16} />
                  </button>
                </div>

                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1">
                    <span className="text-gray-500">Quality:</span>
                    <span className={`font-medium ${getQualityColor(scene.quality_score)}`}>
                      {getQualityIcon(scene.quality_score)}
                      {(scene.quality_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-gray-500">Confidence:</span>
                    <span className="font-medium">
                      {(scene.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-gray-400">
                    {scene.start_time.toFixed(1)}s - {scene.end_time.toFixed(1)}s
                  </div>
                </div>

                {scene.keywords && scene.keywords.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {scene.keywords.slice(0, 3).map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
