import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { memoryAPI } from '../api/client';

// Format date safely
const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
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
        <div className="text-gray-400">Loading conversations...</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Conversation List */}
      <div className="lg:col-span-1 space-y-4">
        {/* Search Box */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-2">Search</div>
          <input
            type="text"
            placeholder="Filter conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Conversation List */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 max-h-[600px] overflow-y-auto">
          <div className="p-4 border-b border-gray-700">
            <div className="text-xs uppercase tracking-wider text-gray-400">
              Conversations ({displayedConversations?.length || 0})
            </div>
          </div>
          {!displayedConversations || displayedConversations.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">
              No conversations found
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {displayedConversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv.id)}
                  className={`w-full p-4 text-left hover:bg-gray-700 transition-colors ${
                    selectedConversation === conv.id ? 'bg-gray-700 border-l-2 border-blue-500' : ''
                  }`}
                >
                  <div className="font-mono text-sm text-white truncate">
                    {conv.id}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>▸ {conv.message_count || 0} msgs</span>
                    <span>•</span>
                    <span>{formatDate(conv.created_at)}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Conversation Detail */}
      <div className="lg:col-span-2">
        {!selectedConv ? (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-12 text-center">
            <div className="text-gray-500 text-sm">
              ▸ Select a conversation to view messages
            </div>
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            {/* Header */}
            <div className="p-6 border-b border-gray-700">
              <div className="text-xs uppercase tracking-wider text-gray-400 mb-2">
                Conversation
              </div>
              <h2 className="text-lg font-mono text-white truncate">
                {selectedConv.id}
              </h2>
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-400">
                {selectedConv.user_id && (
                  <div>
                    <span className="text-gray-500">User:</span> {selectedConv.user_id}
                  </div>
                )}
                {selectedConv.session_id && (
                  <div>
                    <span className="text-gray-500">Session:</span> {selectedConv.session_id}
                  </div>
                )}
                {selectedConv.project && (
                  <div>
                    <span className="text-gray-500">Project:</span> {selectedConv.project}
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Created:</span> {formatDate(selectedConv.created_at)}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="p-6 space-y-3 max-h-[600px] overflow-y-auto">
              {!selectedConv.messages || selectedConv.messages.length === 0 ? (
                <div className="text-gray-500 text-sm text-center py-8">
                  No messages in this conversation
                </div>
              ) : (
                selectedConv.messages.map((msg, idx) => (
                  <div key={msg.id} className="group">
                    {/* Message Header */}
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`text-xs font-mono uppercase ${
                        msg.role === 'user' ? 'text-blue-400' : 'text-green-400'
                      }`}>
                        {msg.role === 'user' ? '▸ USER' : '◂ ASSISTANT'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(msg.created_at)}
                      </div>
                      {idx === 0 && (
                        <div className="text-xs text-gray-600 uppercase">First</div>
                      )}
                    </div>

                    {/* Message Content */}
                    <div className={`p-4 rounded border ${
                      msg.role === 'user'
                        ? 'bg-gray-900 border-blue-900/30 ml-6'
                        : 'bg-gray-900 border-green-900/30 mr-6'
                    }`}>
                      <div className="text-gray-300 whitespace-pre-wrap text-sm">
                        {msg.content}
                      </div>

                      {/* Metadata */}
                      {(msg.model_used || msg.backend || msg.tokens_completion) && (
                        <div className="mt-3 pt-3 border-t border-gray-800 flex flex-wrap gap-4 text-xs text-gray-500">
                          {msg.model_used && (
                            <div>
                              <span className="text-gray-600">model:</span> {msg.model_used}
                            </div>
                          )}
                          {msg.backend && (
                            <div>
                              <span className="text-gray-600">backend:</span> {msg.backend}
                            </div>
                          )}
                          {msg.tokens_completion && (
                            <div>
                              <span className="text-gray-600">tokens:</span> {msg.tokens_completion.toLocaleString()}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
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
