import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { memoryAPI } from '../api/client';
import type { Conversation } from '../types/api';
import { RetroButton, RetroInput } from './ui';

interface ConversationSidebarProps {
  selectedConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

const getSourceBadge = (conv: { source?: string; project?: string }) => {
  const source = conv.source || conv.project || 'unknown';
  // Retro-styled badge colors
  const colors: Record<string, string> = {
    discord: 'bg-[rgba(179,136,255,0.2)] text-[var(--retro-accent-purple)] border-[var(--retro-accent-purple)]',
    'tayne-discord-bot': 'bg-[rgba(179,136,255,0.2)] text-[var(--retro-accent-purple)] border-[var(--retro-accent-purple)]',
    dashboard: 'bg-[rgba(96,165,250,0.15)] text-[var(--retro-accent-blue)] border-[var(--retro-accent-blue)]',
    testing: 'bg-[rgba(255,215,0,0.2)] text-[var(--retro-accent-yellow)] border-[var(--retro-accent-yellow)]',
    unknown: 'bg-[var(--retro-bg-light)] text-[var(--retro-text-muted)] border-[var(--retro-border)]',
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
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const queryClient = useQueryClient();

  const updateConversationMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      memoryAPI.updateConversation(id, { title }),
    onMutate: async ({ id, title }) => {
      await queryClient.cancelQueries({ queryKey: ['conversations'] });
      const previousConversations = queryClient.getQueryData(['conversations']);
      queryClient.setQueryData(['conversations'], (old: Conversation[] | undefined) =>
        old?.map(conv =>
          conv.id === id ? { ...conv, title } : conv
        )
      );
      return { previousConversations };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousConversations) {
        queryClient.setQueryData(['conversations'], context.previousConversations);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const handleStartEdit = (conversationId: string, currentTitle: string) => {
    setEditingId(conversationId);
    setEditValue(currentTitle);
  };

  const handleSaveEdit = () => {
    if (editingId && editValue.trim()) {
      updateConversationMutation.mutate({ id: editingId, title: editValue.trim() });
    }
    setEditingId(null);
    setEditValue('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

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
    <div className="flex flex-col flex-1 min-h-0 bg-[var(--retro-bg-medium)]">
      {/* Search */}
      <div className="p-3 sm:p-4 border-b-2 border-[var(--retro-border)]">
        <RetroInput
          type="text"
          placeholder="🔍 Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="text-sm"
        />
      </div>

      {/* New Chat Button */}
      <div className="p-3 sm:p-4 border-b-2 border-[var(--retro-border)]">
        <RetroButton
          variant="primary"
          fullWidth
          onClick={onNewChat}
          icon={<span>+</span>}
        >
          New Conversation
        </RetroButton>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3 sm:p-4 border-b border-[var(--retro-border)]">
          <div className="text-xs text-[var(--retro-text-secondary)] font-semibold">
            Conversations ({sortedConversations.length})
          </div>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-[var(--retro-text-muted)] text-sm retro-animate-pulse">
            Loading...
          </div>
        ) : sortedConversations.length === 0 ? (
          <div className="p-6 text-center text-[var(--retro-text-muted)] text-sm">
            {searchQuery.length > 2 ? 'No results found' : 'No conversations yet'}
          </div>
        ) : (
          <div className="divide-y divide-[var(--retro-border)]">
            {sortedConversations.map((item) => {
              const conv = item as Conversation;
              const badge = getSourceBadge(conv);
              const isEditing = editingId === conv.id;
              const isSelected = selectedConversationId === conv.id;

              return (
                <button
                  key={conv.id}
                  onClick={() => !isEditing && onSelectConversation(conv.id)}
                  className={`w-full p-3 sm:p-4 text-left transition-colors min-h-[var(--retro-touch-target)] ${
                    isSelected
                      ? 'bg-[var(--retro-bg-light)] border-l-2 border-[var(--retro-accent-green)]'
                      : 'hover:bg-[var(--retro-bg-light)] border-l-2 border-transparent'
                  }`}
                  style={{}}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 text-[10px] rounded border font-semibold ${badge.colorClass}`}>
                      {badge.label}
                    </span>
                    {conv.username && (
                      <span className="text-[10px] text-[var(--retro-text-muted)] truncate">@{conv.username}</span>
                    )}
                  </div>

                  {isEditing ? (
                    <div className="relative">
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onBlur={handleSaveEdit}
                        className="retro-input text-sm font-mono"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  ) : (
                    <div className="group flex items-center justify-between">
                      <div className="text-sm text-[var(--retro-text-primary)] truncate flex-1">
                        {conv.title || 'Untitled conversation'}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartEdit(conv.id, conv.title || '');
                        }}
                        className="ml-2 p-1 text-[var(--retro-text-muted)] hover:text-[var(--retro-accent-cyan)] opacity-0 group-hover:opacity-100 transition-all"
                        title="Rename conversation"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                    </div>
                  )}

                  <div className="flex items-center gap-3 mt-2 text-xs text-[var(--retro-text-muted)]">
                    <span className="text-[var(--retro-accent-cyan)]">▸ {conv.message_count || 0}</span>
                    <span>msgs</span>
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
