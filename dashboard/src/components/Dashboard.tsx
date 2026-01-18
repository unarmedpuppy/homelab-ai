import { useQuery } from '@tanstack/react-query';
import { metricsAPI } from '../api/client';
import ActivityHeatmap from './ActivityHeatmap';
import { RetroPanel, RetroStatCard } from './ui';

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: metricsAPI.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[var(--retro-text-muted)] retro-animate-pulse uppercase tracking-wider text-sm">
          Loading dashboard...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-[rgba(255,68,68,0.1)] border-2 border-[var(--retro-accent-red)] rounded">
        <p className="text-[var(--retro-accent-red)]">Error loading dashboard: {String(error)}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-[var(--retro-text-muted)]">No data available</div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-4">
      {/* Header */}
      <h1 className="text-xl sm:text-2xl font-bold text-[var(--retro-accent-green)] uppercase tracking-wider">
        Usage Statistics
      </h1>

      {/* Primary Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <RetroStatCard
          label="Total Messages"
          value={stats.total_messages?.toLocaleString() || 0}
          color="green"
        />
        <RetroStatCard
          label="Total Tokens"
          value={`${(stats.total_tokens / 1000000).toFixed(1)}M`}
          color="blue"
        />
        <RetroStatCard
          label="Days Active"
          value={stats.days_active || 0}
          color="default"
        />
        <RetroStatCard
          label="Streak"
          value={`${stats.longest_streak || 0}d`}
          color="yellow"
        />
      </div>

      {/* Activity Section */}
      <RetroPanel title="Activity" icon="📊">
        <div className="overflow-x-auto">
          <ActivityHeatmap data={stats.activity_chart || []} />
        </div>
      </RetroPanel>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Top Models */}
        {stats.top_models && stats.top_models.length > 0 && (
          <RetroPanel title="Top Models" icon="🤖">
            <div className="space-y-3">
              {stats.top_models.slice(0, 5).map((model, index) => (
                <div key={model.model} className="flex items-center gap-3">
                  <div className="text-lg sm:text-xl font-bold text-[var(--retro-text-muted)] w-6 sm:w-8">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[var(--retro-text-primary)] font-medium text-sm sm:text-base truncate">
                      {model.model}
                    </div>
                    <div className="text-xs text-[var(--retro-text-muted)]">
                      {model.count.toLocaleString()} uses
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </RetroPanel>
        )}

        {/* Providers */}
        {stats.providers_used && Object.keys(stats.providers_used).length > 0 && (
          <RetroPanel title="Providers" icon="⚡">
            <div className="space-y-3">
              {Object.entries(stats.providers_used).map(([provider, percentage], index) => (
                <div key={provider} className="flex items-center gap-3">
                  <div className="text-lg sm:text-xl font-bold text-[var(--retro-text-muted)] w-6 sm:w-8">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[var(--retro-text-primary)] font-medium capitalize text-sm sm:text-base">
                      {provider}
                    </div>
                    <div className="text-xs text-[var(--retro-text-muted)]">{percentage}%</div>
                  </div>
                  {/* Progress bar */}
                  <div className="w-20 sm:w-32 h-2 bg-[var(--retro-bg-dark)] rounded overflow-hidden">
                    <div
                      className="h-full bg-[var(--retro-accent-cyan)] transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </RetroPanel>
        )}
      </div>

      {/* Bottom Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
        <RetroStatCard
          label="Sessions"
          value={stats.total_sessions?.toLocaleString() || 0}
          color="default"
        />
        <RetroStatCard
          label="Projects"
          value={stats.unique_projects || 0}
          color="default"
        />
        <RetroStatCard
          label="Most Active Day"
          value={stats.most_active_day_count || 0}
          color="green"
          className="col-span-2 sm:col-span-1"
        />
      </div>
    </div>
  );
}
