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

  const serverCount = stats.online_count + stats.offline_count + stats.degraded_count + stats.unknown_count;
  const cliCount = stats.total_agents - serverCount;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
      <RetroStatCard
        label="Server Agents"
        value={`${stats.online_count}/${serverCount}`}
        color="green"
      />
      <RetroStatCard
        label="CLI Agents"
        value={cliCount}
        color="blue"
      />
      <RetroStatCard
        label="Avg Response"
        value={formatResponseTime(stats.avg_response_time_ms)}
        color="default"
      />
      {stats.unexpected_offline_count > 0 ? (
        <RetroStatCard
          label="Unexpected Down"
          value={stats.unexpected_offline_count}
          color="red"
        />
      ) : (
        <RetroStatCard
          label="Fleet Status"
          value="OK"
          color="green"
        />
      )}
    </div>
  );
}

export default FleetOverview;
