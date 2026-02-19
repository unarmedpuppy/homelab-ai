import type { Agent, AgentStatus } from '../../types/agents';
import { RetroCard, RetroBadge, RetroButton } from '../ui';

interface AgentCardProps {
  agent: Agent;
  onForceCheck?: (agentId: string) => void;
  isChecking?: boolean;
  onClick?: () => void;
}

function getStatusColor(status: AgentStatus): string {
  switch (status) {
    case 'online':
      return 'var(--retro-accent-green)';
    case 'offline':
      return 'var(--retro-text-muted)';
    case 'degraded':
      return 'var(--retro-accent-yellow)';
    case 'unknown':
    default:
      return 'var(--retro-text-muted)';
  }
}

function getStatusVariant(status: AgentStatus): 'status-done' | 'status-blocked' | 'status-open' | 'label' {
  switch (status) {
    case 'online':
      return 'status-done';
    case 'offline':
      return 'label'; // Gray for offline (not an error)
    case 'degraded':
      return 'status-open';
    case 'unknown':
    default:
      return 'label';
  }
}

function formatLastSeen(lastCheck: string | null, lastSuccess: string | null): string {
  const timestamp = lastSuccess || lastCheck;
  if (!timestamp) return 'Never';

  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return date.toLocaleDateString();
}

function formatResponseTime(ms: number | null): string {
  if (ms === null) return '-';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function AgentCard({ agent, onForceCheck, isChecking, onClick }: AgentCardProps) {
  const { health } = agent;
  const statusColor = getStatusColor(health.status);

  return (
    <RetroCard
      className={`relative overflow-hidden ${onClick ? 'hover:border-[var(--retro-accent-cyan)] transition-colors' : ''}`}
      onClick={onClick}
    >
      {/* Status indicator bar at top */}
      <div
        className="absolute top-0 left-0 right-0 h-1"
        style={{ backgroundColor: statusColor }}
      />

      <div className="pt-2">
        {/* Header: Name and Status */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="text-lg font-bold text-[var(--retro-text-primary)]">
              {agent.name}
            </h3>
            <p className="text-xs text-[var(--retro-text-muted)] mt-0.5">
              {agent.description}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: statusColor }}
            />
            <RetroBadge variant={getStatusVariant(health.status)} size="sm">
              {health.status.toUpperCase()}
            </RetroBadge>
          </div>
        </div>

        {/* Tags */}
        {agent.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {agent.tags.map((tag) => (
              <span
                key={tag}
                className="text-[0.625rem] px-1.5 py-0.5 bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded text-[var(--retro-text-muted)] uppercase tracking-wide"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="bg-[var(--retro-bg-light)] rounded p-2 border border-[var(--retro-border)]">
            <div className="text-[0.625rem] text-[var(--retro-text-muted)] mb-0.5">
              Last Seen
            </div>
            <div className="text-sm text-[var(--retro-text-primary)]">
              {formatLastSeen(health.last_check, health.last_success)}
            </div>
          </div>
          <div className="bg-[var(--retro-bg-light)] rounded p-2 border border-[var(--retro-border)]">
            <div className="text-[0.625rem] text-[var(--retro-text-muted)] mb-0.5">
              Response Time
            </div>
            <div className="text-sm text-[var(--retro-text-primary)]">
              {formatResponseTime(health.response_time_ms)}
            </div>
          </div>
        </div>

        {/* Version */}
        {health.version && (
          <div className="text-xs text-[var(--retro-text-muted)] mb-3">
            Version: <span className="font-mono text-[var(--retro-accent-cyan)]">{health.version}</span>
          </div>
        )}

        {/* Error message */}
        {health.error && health.status !== 'online' && (
          <div className="text-xs text-[var(--retro-text-muted)] bg-[var(--retro-bg-dark)] p-2 rounded border border-[var(--retro-border)] mb-3 font-mono">
            {health.error}
          </div>
        )}

        {/* Expected online indicator */}
        {agent.expected_online && health.status === 'offline' && (
          <div className="text-xs text-[var(--retro-accent-yellow)] mb-3">
            This agent is expected to be online
          </div>
        )}

        {/* Force check button */}
        {onForceCheck && (
          <div onClick={(e) => e.stopPropagation()}>
            <RetroButton
              variant="ghost"
              size="sm"
              onClick={() => onForceCheck(agent.id)}
              disabled={isChecking}
              loading={isChecking}
              className="w-full"
            >
              Force Health Check
            </RetroButton>
          </div>
        )}
      </div>
    </RetroCard>
  );
}

export default AgentCard;
