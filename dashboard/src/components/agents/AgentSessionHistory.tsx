import { useState, useEffect, useCallback } from 'react';
import type { Agent } from '../../types/agents';
import { agentsAPI } from '../../api/client';
import { RetroButton, RetroBadge } from '../ui';

interface AgentSessionHistoryProps {
  agent: Agent;
}

interface Session {
  id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  task_id: string | null;
  task_title: string | null;
  turns: number;
  tokens_used: number | null;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // If less than 24 hours ago, show relative time
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    if (hours === 0) {
      const mins = Math.floor(diff / 60000);
      return mins <= 1 ? 'Just now' : `${mins}m ago`;
    }
    return `${hours}h ago`;
  }

  // If this year, show date without year
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function getStatusVariant(status: Session['status']): 'status-done' | 'status-blocked' | 'status-progress' | 'label' {
  switch (status) {
    case 'running':
      return 'status-progress';
    case 'completed':
      return 'status-done';
    case 'failed':
      return 'status-blocked';
    case 'cancelled':
      return 'label';
    default:
      return 'label';
  }
}

export function AgentSessionHistory({ agent }: AgentSessionHistoryProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const isOnline = agent.health.status === 'online';

  const fetchSessions = useCallback(async () => {
    if (!isOnline) {
      setLoading(false);
      setError('Agent is offline - cannot fetch session history');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await agentsAPI.getSessions(agent.id);
      setSessions(data.sessions);
      setHasMore(data.has_more);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch sessions');
      console.error('Failed to fetch sessions:', e);
    } finally {
      setLoading(false);
    }
  }, [agent.id, isOnline]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-[var(--retro-text-muted)] retro-animate-pulse uppercase tracking-wider text-sm">
          Loading session history...
        </div>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-[var(--retro-text-muted)] uppercase tracking-wider mb-2">
          Agent Offline
        </div>
        <p className="text-sm text-[var(--retro-text-muted)] text-center max-w-md">
          Session history cannot be viewed while the agent is offline.
          The agent must be running to retrieve its session data.
        </p>
      </div>
    );
  }

  if (error && sessions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-[var(--retro-accent-red)] uppercase tracking-wider mb-2">
          Error Loading Sessions
        </div>
        <p className="text-sm text-[var(--retro-text-muted)] text-center max-w-md mb-4">
          {error}
        </p>
        <RetroButton variant="ghost" size="sm" onClick={fetchSessions}>
          Retry
        </RetroButton>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-[var(--retro-text-muted)] uppercase tracking-wider mb-2">
          No Sessions Found
        </div>
        <p className="text-sm text-[var(--retro-text-muted)] text-center max-w-md">
          This agent has no recorded session history yet.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Sessions Header */}
      <div className="p-3 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)] flex items-center justify-between">
        <span className="text-xs text-[var(--retro-text-muted)] uppercase tracking-wider">
          {sessions.length} Sessions {hasMore && '(showing recent)'}
        </span>
        <RetroButton variant="ghost" size="sm" onClick={fetchSessions}>
          Refresh
        </RetroButton>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-2 bg-[rgba(255,68,68,0.1)] border-b border-[var(--retro-accent-red)] text-xs text-[var(--retro-accent-red)]">
          {error}
        </div>
      )}

      {/* Sessions List */}
      <div className="flex-1 overflow-auto">
        <div className="divide-y divide-[var(--retro-border)]">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="p-4 hover:bg-[var(--retro-bg-light)] transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <RetroBadge variant={getStatusVariant(session.status)} size="sm">
                    {session.status.toUpperCase()}
                  </RetroBadge>
                  <span className="text-xs text-[var(--retro-text-muted)]">
                    {formatTimestamp(session.started_at)}
                  </span>
                </div>
                <span className="text-xs text-[var(--retro-text-muted)] font-mono">
                  {session.id.slice(0, 8)}
                </span>
              </div>

              {session.task_title && (
                <div className="mb-2">
                  <span className="text-sm text-[var(--retro-text-primary)]">
                    {session.task_title}
                  </span>
                  {session.task_id && (
                    <span className="ml-2 text-xs text-[var(--retro-accent-cyan)] font-mono">
                      #{session.task_id}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center gap-4 text-xs text-[var(--retro-text-muted)]">
                <div>
                  <span className="uppercase tracking-wider">Duration:</span>{' '}
                  <span className="font-mono text-[var(--retro-text-primary)]">
                    {formatDuration(session.duration_seconds)}
                  </span>
                </div>
                <div>
                  <span className="uppercase tracking-wider">Turns:</span>{' '}
                  <span className="font-mono text-[var(--retro-text-primary)]">
                    {session.turns}
                  </span>
                </div>
                {session.tokens_used !== null && (
                  <div>
                    <span className="uppercase tracking-wider">Tokens:</span>{' '}
                    <span className="font-mono text-[var(--retro-text-primary)]">
                      {session.tokens_used.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AgentSessionHistory;
