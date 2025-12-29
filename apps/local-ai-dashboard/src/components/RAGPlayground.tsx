import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ragAPI } from '../api/client';

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

  const contextMutation = useMutation({
    mutationFn: (searchQuery: string) =>
      ragAPI.getContext({
        query: searchQuery,
        limit,
      }),
  });

  const handleSearch = () => {
    if (query.trim()) {
      searchMutation.mutate(query);
    }
  };

  const handleGetContext = () => {
    if (query.trim()) {
      contextMutation.mutate(query);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Semantic Search
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Search Query
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query..."
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Result Limit: {limit}
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Similarity Threshold: {threshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSearch}
              disabled={!query.trim() || searchMutation.isPending}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {searchMutation.isPending ? 'Searching...' : 'Search'}
            </button>
            <button
              onClick={handleGetContext}
              disabled={!query.trim() || contextMutation.isPending}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {contextMutation.isPending ? 'Loading...' : 'Get Context'}
            </button>
          </div>
        </div>
      </div>

      {/* Search Results */}
      {searchMutation.data && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Search Results ({searchMutation.data.count})
          </h2>
          <div className="space-y-4">
            {searchMutation.data.results.length === 0 ? (
              <div className="text-gray-500 dark:text-gray-400 text-sm">
                No results found
              </div>
            ) : (
              searchMutation.data.results.map((result, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {result.conversation_id}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                      <span>Similarity: {(result.similarity_score * 100).toFixed(1)}%</span>
                      <span>{result.message_count} messages</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mb-3">
                    Created: {new Date(result.conversation_created_at).toLocaleString()}
                  </div>
                  {result.sample_messages && result.sample_messages.length > 0 && (
                    <div className="space-y-2">
                      {result.sample_messages.map((msg, msgIdx) => (
                        <div
                          key={msgIdx}
                          className="bg-gray-50 dark:bg-gray-700 rounded p-3 text-sm"
                        >
                          <div className="font-medium text-gray-700 dark:text-gray-300 capitalize mb-1">
                            {msg.role}:
                          </div>
                          <div className="text-gray-600 dark:text-gray-400">
                            {msg.content.substring(0, 200)}
                            {msg.content.length > 200 ? '...' : ''}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Context Result */}
      {contextMutation.data && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Retrieved Context
          </h2>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
              {contextMutation.data.context}
            </pre>
          </div>
        </div>
      )}

      {/* Error Display */}
      {(searchMutation.isError || contextMutation.isError) && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Error: {String(searchMutation.error || contextMutation.error)}
          </p>
        </div>
      )}
    </div>
  );
}
