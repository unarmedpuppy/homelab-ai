import type { FleetStats } from '../../types/agents';
import { RetroStatCard } from '../ui';

interface FleetOverviewProps {
  stats: FleetStats | null;
  loading?: boolean;
}

function formatResponseTime(ms: number | null): string {
  if (ms === null) return '-';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function FleetOverview({ stats, loading }: FleetOverviewProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-20 bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded retro-animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
      <RetroStatCard
        label="Total Agents"
        value={stats.total_agents}
        color="default"
      />
      <RetroStatCard
        label="Online"
        value={stats.online_count}
        color="green"
      />
      <RetroStatCard
        label="Offline"
        value={stats.offline_count}
        color="default"
      />
      <RetroStatCard
        label="Avg Response"
        value={formatResponseTime(stats.avg_response_time_ms)}
        color="blue"
      />
    </div>
  );
}

export default FleetOverview;
