import type { BeadsStats } from '../../types/beads';
import { RetroButton } from '../ui';
import { useIsMobile } from '../../hooks/useMediaQuery';

interface BeadsStatsHeaderProps {
  stats: BeadsStats | null;
  loading?: boolean;
  idleAgents?: number;
  systemLoad?: number; // 0-100
  onCreateTask: () => void;
  onRefresh: () => void;
  onAutoFill?: () => void; // Start Ralph for idle agents
}

type StatColor = 'default' | 'green' | 'yellow' | 'red' | 'blue' | 'cyan';

interface StatItem {
  label: string;
  value: string | number;
  color: StatColor;
  showOnMobile?: boolean;
}

const colorClasses: Record<StatColor, string> = {
  default: 'text-[var(--retro-accent-cyan)]',
  cyan: 'text-[var(--retro-accent-cyan)]',
  green: 'text-[var(--retro-accent-green)]',
  yellow: 'text-[var(--retro-accent-yellow)]',
  red: 'text-[var(--retro-accent-red)]',
  blue: 'text-[var(--retro-accent-blue)]',
};

const glowClasses: Record<StatColor, string> = {
  default: 'drop-shadow-[0_0_4px_var(--retro-accent-cyan)]',
  cyan: 'drop-shadow-[0_0_4px_var(--retro-accent-cyan)]',
  green: 'drop-shadow-[0_0_4px_var(--retro-accent-green)]',
  yellow: 'drop-shadow-[0_0_4px_var(--retro-accent-yellow)]',
  red: 'drop-shadow-[0_0_4px_var(--retro-accent-red)]',
  blue: 'drop-shadow-[0_0_4px_var(--retro-accent-blue)]',
};

export function BeadsStatsHeader({
  stats,
  loading = false,
  idleAgents,
  systemLoad,
  onCreateTask,
  onRefresh,
  onAutoFill,
}: BeadsStatsHeaderProps) {
  const isMobile = useIsMobile();

  // Build stat items based on available data
  const statItems: StatItem[] = stats
    ? [
        { label: 'TASKS', value: stats.total_tasks, color: 'cyan', showOnMobile: true },
        { label: 'BACKLOG', value: stats.backlog_count, color: 'blue', showOnMobile: false },
        { label: 'IN PROGRESS', value: stats.in_progress_count, color: 'yellow', showOnMobile: true },
        { label: 'DONE', value: stats.done_count, color: 'green', showOnMobile: false },
        { label: 'BLOCKED', value: stats.blocked_count, color: 'red', showOnMobile: false },
      ]
    : [];

  // Add idle agents and system load if provided
  if (idleAgents !== undefined) {
    statItems.push({
      label: 'IDLE',
      value: idleAgents,
      color: idleAgents > 0 ? 'green' : 'yellow',
      showOnMobile: false,
    });
  }

  if (systemLoad !== undefined) {
    statItems.push({
      label: 'LOAD',
      value: `${systemLoad}%`,
      color: systemLoad > 80 ? 'red' : systemLoad > 50 ? 'yellow' : 'green',
      showOnMobile: false,
    });
  }

  // Mobile: condensed layout
  // Desktop: full layout with all stats and buttons
  if (isMobile) {
    return (
      <div className="flex items-center justify-between gap-2 px-3 py-2 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        {/* Condensed Stats */}
        <div className="flex items-center gap-3 text-xs font-mono">
          {loading ? (
            <span className="text-[var(--retro-text-muted)] retro-animate-pulse">
              Loading...
            </span>
          ) : (
            statItems
              .filter((stat) => stat.showOnMobile)
              .map((stat, index) => (
                <div key={index} className="flex items-baseline gap-1">
                  <span className="text-[var(--retro-text-muted)]">{stat.label}:</span>
                  <span
                    className={`font-bold ${colorClasses[stat.color]} ${glowClasses[stat.color]}`}
                  >
                    {stat.value}
                  </span>
                </div>
              ))
          )}
        </div>

        {/* Mobile Actions - compact buttons */}
        <div className="flex gap-1">
          <RetroButton
            variant="ghost"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            aria-label="Refresh"
          >
            ⟳
          </RetroButton>
          <RetroButton
            variant="primary"
            size="sm"
            onClick={onCreateTask}
            aria-label="Create task"
          >
            +
          </RetroButton>
        </div>
      </div>
    );
  }

  // Desktop: full layout
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-3 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
      {/* Action Buttons */}
      <div className="flex gap-2 flex-shrink-0">
        <RetroButton
          variant="primary"
          size="sm"
          onClick={onCreateTask}
        >
          CREATE TASK
        </RetroButton>
        {onAutoFill && (
          <RetroButton
            variant="secondary"
            size="sm"
            onClick={onAutoFill}
            disabled={idleAgents === 0}
          >
            AUTO-FILL
          </RetroButton>
        )}
        <RetroButton
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={loading}
          aria-label="Refresh"
        >
          ⟳
        </RetroButton>
      </div>

      {/* Stats Display */}
      <div className="flex items-center gap-4 text-xs font-mono">
        {loading ? (
          <span className="text-[var(--retro-text-muted)] retro-animate-pulse">
            Loading stats...
          </span>
        ) : (
          statItems.map((stat, index) => (
            <div
              key={index}
              className="flex items-baseline gap-1.5 whitespace-nowrap"
            >
              <span className="text-[var(--retro-text-muted)] uppercase tracking-wider">
                {stat.label}:
              </span>
              <span
                className={`font-bold ${colorClasses[stat.color]} ${glowClasses[stat.color]}`}
              >
                {stat.value}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default BeadsStatsHeader;
