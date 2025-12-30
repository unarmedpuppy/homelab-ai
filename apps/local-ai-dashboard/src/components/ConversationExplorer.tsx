import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { memoryAPI } from '../api/client';
import type { Conversation } from '../types/api';

const getSourceBadge = (conv: Conversation) => {
  const source = conv.source || conv.project || 'unknown';
  const colors: Record<string, string> = {
    discord: 'bg-indigo-900/50 text-indigo-300 border-indigo-700',
    'tayne-discord-bot': 'bg-indigo-900/50 text-indigo-300 border-indigo-700',
    dashboard: 'bg-emerald-900/50 text-emerald-300 border-emerald-700',
    testing: 'bg-amber-900/50 text-amber-300 border-amber-700',
    unknown: 'bg-gray-800 text-gray-400 border-gray-600',
  };
  const label = source.replace('tayne-discord-bot', 'discord').replace('-', ' ');
  const colorClass = colors[source] || colors.unknown;
  return { label, colorClass };
};

// Format date safely - handles multiple formats
const formatDate = (dateInput: string | number | undefined | null): string => {
  if (!dateInput) {
    console.log('formatDate: no input', dateInput);
    return '—';
  }

  try {
    let date: Date;

    // Handle Unix timestamp (number or string number)
    if (typeof dateInput === 'number' || !isNaN(Number(dateInput))) {
      const timestamp = typeof dateInput === 'number' ? dateInput : Number(dateInput);
      // Check if it's in seconds (< year 3000 in milliseconds)
      date = new Date(timestamp < 10000000000 ? timestamp * 1000 : timestamp);
    } else {
      // Handle ISO string or other date string
      date = new Date(dateInput);
    }

    if (isNaN(date.getTime())) {
      console.log('formatDate: invalid date', dateInput);
      return '—';
    }

    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    console.error('formatDate error:', error, dateInput);
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
              {displayedConversations.map((conv) => {
                const badge = getSourceBadge(conv);
                return (
                  <button
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv.id)}
                    className={`w-full p-4 text-left hover:bg-gray-700 transition-colors ${
                      selectedConversation === conv.id ? 'bg-gray-700 border-l-2 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-xs rounded border ${badge.colorClass}`}>
                        {badge.label}
                      </span>
                      {conv.username && (
                        <span className="text-xs text-gray-500">@{conv.username}</span>
                      )}
                    </div>
                    <div className="font-mono text-sm text-white truncate mt-1">
                      {conv.title || conv.id}
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span>▸ {conv.message_count || 0} msgs</span>
                      <span>•</span>
                      <span>{formatDate(conv.created_at)}</span>
                      {conv.total_tokens && (
                        <>
                          <span>•</span>
                          <span>{conv.total_tokens.toLocaleString()} tokens</span>
                        </>
                      )}
                    </div>
                  </button>
                );
              })}
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
              <div className="flex items-center gap-3 mb-2">
                <div className="text-xs uppercase tracking-wider text-gray-400">
                  Conversation
                </div>
                {(() => {
                  const badge = getSourceBadge(selectedConv);
                  return (
                    <span className={`px-2 py-0.5 text-xs rounded border ${badge.colorClass}`}>
                      {badge.label}
                    </span>
                  );
                })()}
              </div>
              <h2 className="text-lg font-mono text-white truncate">
                {selectedConv.title || selectedConv.id}
              </h2>
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-400">
                {(selectedConv.username || selectedConv.display_name) && (
                  <div>
                    <span className="text-gray-500">User:</span>{' '}
                    {selectedConv.display_name || `@${selectedConv.username}`}
                  </div>
                )}
                {selectedConv.source && (
                  <div>
                    <span className="text-gray-500">Source:</span> {selectedConv.source}
                  </div>
                )}
                {selectedConv.project && (
                  <div>
                    <span className="text-gray-500">Project:</span> {selectedConv.project}
                  </div>
                )}
                {selectedConv.session_id && (
                  <div>
                    <span className="text-gray-500">Session:</span> {selectedConv.session_id}
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Created:</span> {formatDate(selectedConv.created_at)}
                </div>
                {selectedConv.total_tokens && (
                  <div>
                    <span className="text-gray-500">Tokens:</span> {selectedConv.total_tokens.toLocaleString()}
                  </div>
                )}
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
                        {formatDate(msg.timestamp)}
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
