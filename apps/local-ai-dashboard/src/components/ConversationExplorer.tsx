import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { memoryAPI } from '../api/client';

export default function ConversationExplorer() {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => memoryAPI.listConversations({ limit: 100 }),
  });

  const { data: selectedConv } = useQuery({
    queryKey: ['conversation', selectedConversation],
    queryFn: () => memoryAPI.getConversation(selectedConversation!),
    enabled: !!selectedConversation,
  });

  const { data: searchResults } = useQuery({
    queryKey: ['conversation-search', searchQuery],
    queryFn: () => memoryAPI.searchConversations(searchQuery),
    enabled: searchQuery.length > 2,
  });

  const displayedConversations = searchQuery.length > 2 ? searchResults : conversations;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading conversations...</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Conversation List */}
      <div className="lg:col-span-1 space-y-4">
        <div>
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
          {!displayedConversations || displayedConversations.length === 0 ? (
            <div className="p-4 text-gray-500 dark:text-gray-400 text-sm">
              No conversations found
            </div>
          ) : (
            displayedConversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedConversation(conv.id)}
                className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  selectedConversation === conv.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                }`}
              >
                <div className="font-medium text-gray-900 dark:text-white truncate">
                  {conv.id}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {conv.message_count || 0} messages
                </div>
                <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {new Date(conv.created_at).toLocaleString()}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Conversation Detail */}
      <div className="lg:col-span-2">
        {!selectedConv ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center text-gray-500 dark:text-gray-400">
            Select a conversation to view details
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {selectedConv.id}
              </h2>
              <div className="mt-2 space-y-1 text-sm text-gray-500 dark:text-gray-400">
                {selectedConv.user_id && <div>User: {selectedConv.user_id}</div>}
                {selectedConv.session_id && <div>Session: {selectedConv.session_id}</div>}
                {selectedConv.project && <div>Project: {selectedConv.project}</div>}
                <div>Created: {new Date(selectedConv.created_at).toLocaleString()}</div>
              </div>
            </div>

            <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto">
              {!selectedConv.messages || selectedConv.messages.length === 0 ? (
                <div className="text-gray-500 dark:text-gray-400 text-sm">
                  No messages in this conversation
                </div>
              ) : (
                selectedConv.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-4 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-50 dark:bg-blue-900/20 ml-8'
                        : msg.role === 'assistant'
                        ? 'bg-green-50 dark:bg-green-900/20 mr-8'
                        : 'bg-gray-50 dark:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                        {msg.role}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(msg.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    {(msg.model_used || msg.backend || msg.tokens_completion) && (
                      <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600 text-xs text-gray-500 dark:text-gray-400 space-y-1">
                        {msg.model_used && <div>Model: {msg.model_used}</div>}
                        {msg.backend && <div>Backend: {msg.backend}</div>}
                        {msg.tokens_completion && <div>Tokens: {msg.tokens_completion}</div>}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
