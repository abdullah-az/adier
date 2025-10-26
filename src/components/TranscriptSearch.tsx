import { useState } from 'react';
import { Search, Plus } from 'lucide-react';
import { TranscriptSegment } from '../types/timeline';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TranscriptSearchProps {
  projectId: string;
  onSelectSegment: (segment: TranscriptSegment) => void;
  className?: string;
}

export function TranscriptSearch({
  projectId,
  onSelectSegment,
  className = '',
}: TranscriptSearchProps) {
  const [query, setQuery] = useState('');
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/projects/${projectId}/transcript/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: query.trim() }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to search transcript');
      }

      const data = await response.json();
      setSegments(data.segments || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className={`bg-white rounded-lg p-6 shadow-sm ${className}`} dir="ltr">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Search size={20} />
        Transcript Search
      </h3>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search for keywords..."
          className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {loading && (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto"></div>
            <p className="text-gray-600 mt-2 text-sm">Searching...</p>
          </div>
        )}

        {!loading && searched && segments.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Search size={48} className="mx-auto mb-2 opacity-50" />
            <p>No results found</p>
            <p className="text-sm mt-1">Try different keywords</p>
          </div>
        )}

        {!loading && !searched && (
          <div className="text-center py-8 text-gray-400">
            <Search size={48} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">Search transcript to find specific segments</p>
          </div>
        )}

        {!loading &&
          segments.map((segment) => {
            const duration = segment.end_time - segment.start_time;
            const highlightText = (text: string) => {
              if (!query) return text;
              const parts = text.split(new RegExp(`(${query})`, 'gi'));
              return (
                <>
                  {parts.map((part, i) =>
                    part.toLowerCase() === query.toLowerCase() ? (
                      <mark key={i} className="bg-yellow-200">
                        {part}
                      </mark>
                    ) : (
                      part
                    )
                  )}
                </>
              );
            };

            return (
              <div
                key={segment.id}
                className="border rounded-lg p-3 hover:bg-gray-50 transition"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {segment.speaker && (
                        <span className="text-xs font-medium text-blue-600">
                          {segment.speaker}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {duration.toFixed(1)}s
                      </span>
                      <span className="text-xs text-gray-400">
                        {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">
                      {highlightText(segment.text)}
                    </p>
                  </div>
                  <button
                    onClick={() => onSelectSegment(segment)}
                    className="ml-2 p-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                    title="Add to timeline"
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {segment.confidence !== undefined && (
                  <div className="text-xs text-gray-500">
                    Confidence: {(segment.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
