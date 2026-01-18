import type { BeadsStats } from '../../types/beads';
import { RetroButton } from '../ui';

interface BeadsStatsHeaderProps {
  stats: BeadsStats | null;
  loading: boolean;
  onCreateTask: () => void;
  onRefresh: () => void;
}

export function BeadsStatsHeader({
  stats,
  loading,
  onCreateTask,
  onRefresh,
}: BeadsStatsHeaderProps) {
  const statItems = stats
    ? [
        { label: 'TOTAL', value: stats.total_tasks, color: 'default' as const },
        { label: 'BACKLOG', value: stats.backlog_count, color: 'blue' as const },
        { label: 'IN PROGRESS', value: stats.in_progress_count, color: 'yellow' as const },
        { label: 'DONE', value: stats.done_count, color: 'green' as const },
        { label: 'BLOCKED', value: stats.blocked_count, color: 'red' as const },
      ]
    : [];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
      {/* Stats */}
      <div className="flex-1">
        {loading ? (
          <div className="text-sm text-[var(--retro-text-muted)] retro-animate-pulse">
            Loading stats...
          </div>
        ) : (
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {statItems.map((stat, index) => (
              <div key={index} className="flex items-baseline gap-1 text-xs">
                <span className="text-[var(--retro-text-muted)]">{stat.label}:</span>
                <span className={`font-bold ${
                  stat.color === 'green' ? 'text-[var(--retro-accent-green)]' :
                  stat.color === 'yellow' ? 'text-[var(--retro-accent-yellow)]' :
                  stat.color === 'red' ? 'text-[var(--retro-accent-red)]' :
                  stat.color === 'blue' ? 'text-[var(--retro-accent-blue)]' :
                  'text-[var(--retro-accent-cyan)]'
                }`}>
                  {stat.value}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <RetroButton
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
        >
          ↻
        </RetroButton>
        <RetroButton
          variant="primary"
          size="sm"
          onClick={onCreateTask}
        >
          + NEW TASK
        </RetroButton>
      </div>
    </div>
  );
}

export default BeadsStatsHeader;
