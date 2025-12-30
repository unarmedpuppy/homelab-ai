import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { memoryAPI } from '../api/client';
import type { Conversation } from '../types/api';

interface ConversationSidebarProps {
  selectedConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

const getSourceBadge = (conv: { source?: string; project?: string }) => {
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

    // Format as relative time
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'just now';
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '—';
  }
};

export default function ConversationSidebar({
  selectedConversationId,
  onSelectConversation,
  onNewChat,
}: ConversationSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all conversations
  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => memoryAPI.listConversations({ limit: 100 }),
  });

  // Search conversations
  const { data: searchResults } = useQuery({
    queryKey: ['searchConversations', searchQuery],
    queryFn: () => memoryAPI.searchConversations(searchQuery, 20),
    enabled: searchQuery.length > 2,
  });

  const displayedConversations = searchQuery.length > 2 ? searchResults : conversations;

  // Sort by most recent first
  const sortedConversations = displayedConversations
    ? [...displayedConversations].sort((a, b) => {
        const dateA = new Date(('updated_at' in a ? a.updated_at : undefined) || a.created_at).getTime();
        const dateB = new Date(('updated_at' in b ? b.updated_at : undefined) || b.created_at).getTime();
        return dateB - dateA;
      })
    : [];

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Search */}
      <div className="p-4 border-b border-gray-800">
        <input
          type="text"
          placeholder="🔍 Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm placeholder-gray-500 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* New Chat Button */}
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={onNewChat}
          className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 transition-colors uppercase tracking-wider text-sm"
        >
          + New Chat
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 border-b border-gray-800">
          <div className="text-xs uppercase tracking-wider text-gray-500">
            Conversations ({sortedConversations.length})
          </div>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500 text-sm">
            Loading...
          </div>
        ) : sortedConversations.length === 0 ? (
          <div className="p-6 text-center text-gray-500 text-sm">
            {searchQuery.length > 2 ? 'No results found' : 'No conversations yet'}
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {sortedConversations.map((item) => {
              const conv = item as Conversation;
              const badge = getSourceBadge(conv);
              return (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full p-4 text-left hover:bg-gray-800 transition-colors ${
                    selectedConversationId === conv.id
                      ? 'bg-gray-800 border-l-2 border-blue-500'
                      : 'border-l-2 border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 text-[10px] rounded border ${badge.colorClass}`}>
                      {badge.label}
                    </span>
                    {conv.username && (
                      <span className="text-[10px] text-gray-500 truncate">@{conv.username}</span>
                    )}
                  </div>
                  <div className="font-mono text-sm text-white truncate">
                    {conv.title || conv.id}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span>▸ {conv.message_count || 0} msgs</span>
                    <span>•</span>
                    <span>{formatDate(conv.updated_at || conv.created_at)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
