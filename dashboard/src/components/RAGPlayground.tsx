import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ragAPI } from '../api/client';

// Format date safely
const formatDate = (dateInput: string | number | undefined | null): string => {
  if (!dateInput) return '—';
  try {
    let date: Date;
    if (typeof dateInput === 'number' || !isNaN(Number(dateInput))) {
      const timestamp = typeof dateInput === 'number' ? dateInput : Number(dateInput);
      date = new Date(timestamp < 10000000000 ? timestamp * 1000 : timestamp);
    } else {
      date = new Date(dateInput);
    }
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
};

export default function RAGPlayground() {
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(5);
  const [threshold, setThreshold] = useState(0.3);

  const searchMutation = useMutation({
    mutationFn: (searchQuery: string) =>
      ragAPI.search({
        query: searchQuery,
        limit,
        similarity_threshold: threshold,
      }),
  });

  const handleSearch = () => {
    if (query.trim()) {
      searchMutation.mutate(query);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-xs text-gray-400 mb-6">
          Text Search
        </div>

        <div className="space-y-6">
          {/* Query Input */}
          <div>
            <div className="text-xs text-gray-500 mb-2">
              Query
            </div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What are you looking for?"
              rows={3}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none font-mono text-sm"
            />
          </div>

          {/* Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Results</span>
                <span className="text-xl font-bold text-white">{limit}</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">Threshold</span>
                <span className="text-xl font-bold text-white">{threshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          </div>

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={!query.trim() || searchMutation.isPending}
            className="w-full px-6 py-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors text-sm"
          >
            {searchMutation.isPending ? '▸ Searching...' : '▸ Search'}
          </button>
        </div>
      </div>

      {/* Results */}
      {searchMutation.data && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <div className="text-xs text-gray-400">
              Results ({searchMutation.data.length})
            </div>
          </div>

          {searchMutation.data.length === 0 ? (
            <div className="p-12 text-center text-gray-500 text-sm">
              No results found
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {searchMutation.data.map((result, idx) => (
                <div key={idx} className="p-6">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="font-mono text-sm text-white">
                      {result.conversation.id}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-xs text-gray-400">
                        <span className="text-gray-500">relevance:</span> {(result.relevance_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-400">
                        <span className="text-gray-500">messages:</span> {result.conversation.message_count}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mb-4">
                    {formatDate(result.conversation.created_at)}
                  </div>

                  {/* Sample Messages */}
                  {result.messages && result.messages.length > 0 && (
                    <div className="space-y-2">
                      {result.messages.slice(0, 3).map((msg, msgIdx) => (
                        <div
                          key={msgIdx}
                          className="bg-gray-900 border border-gray-800 rounded p-3"
                        >
                          <div className={`text-xs font-mono uppercase mb-2 ${
                            msg.role === 'user' ? 'text-blue-400' : 'text-green-400'
                          }`}>
                            {msg.role === 'user' ? '▸ USER' : '◂ ASSISTANT'}
                          </div>
                          <div className="text-sm text-gray-300">
                            {msg.content.substring(0, 200)}
                            {msg.content.length > 200 ? '...' : ''}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {searchMutation.isError && (
        <div className="bg-gray-800 border border-red-800 rounded-lg p-6">
          <div className="text-xs text-red-400 mb-2">Error</div>
          <div className="text-red-300 text-sm">
            {String(searchMutation.error)}
          </div>
        </div>
      )}
    </div>
  );
}
