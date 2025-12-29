import { useQuery } from '@tanstack/react-query';
import { metricsAPI } from '../api/client';
import ActivityHeatmap from './ActivityHeatmap';

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: metricsAPI.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 border border-red-800 rounded-lg p-6">
        <p className="text-red-400">Error loading dashboard: {String(error)}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-gray-400">No data available</div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Total Messages</div>
          <div className="text-5xl font-bold text-white">
            {stats.total_messages?.toLocaleString() || 0}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Total Tokens</div>
          <div className="text-5xl font-bold text-white">
            {(stats.total_tokens / 1000000).toFixed(1)}M
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Days Active</div>
          <div className="text-5xl font-bold text-white">
            {stats.days_active || 0}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Streak</div>
          <div className="text-5xl font-bold text-white">
            {stats.longest_streak || 0}d
          </div>
        </div>
      </div>

      {/* Activity Section */}
      <div className="bg-gray-800 rounded-lg p-8">
        <h2 className="text-xs uppercase tracking-wider text-gray-400 mb-6">Activity</h2>
        <ActivityHeatmap data={stats.activity_chart || []} />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Models */}
        {stats.top_models && stats.top_models.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-8">
            <h2 className="text-xs uppercase tracking-wider text-gray-400 mb-6">Top Models</h2>
            <div className="space-y-4">
              {stats.top_models.slice(0, 5).map((model, index) => (
                <div key={model.model} className="flex items-center gap-4">
                  <div className="text-2xl font-bold text-gray-500 w-8">{index + 1}</div>
                  <div className="flex-1">
                    <div className="text-white font-medium">{model.model}</div>
                    <div className="text-sm text-gray-400">{model.count} uses</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Providers */}
        {stats.providers_used && Object.keys(stats.providers_used).length > 0 && (
          <div className="bg-gray-800 rounded-lg p-8">
            <h2 className="text-xs uppercase tracking-wider text-gray-400 mb-6">Providers</h2>
            <div className="space-y-4">
              {Object.entries(stats.providers_used).map(([provider, percentage], index) => (
                <div key={provider} className="flex items-center gap-4">
                  <div className="text-2xl font-bold text-gray-500 w-8">{index + 1}</div>
                  <div className="flex-1">
                    <div className="text-white font-medium capitalize">{provider}</div>
                    <div className="text-sm text-gray-400">{percentage}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Sessions</div>
          <div className="text-4xl font-bold text-white">
            {stats.total_sessions?.toLocaleString() || 0}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Projects</div>
          <div className="text-4xl font-bold text-white">
            {stats.unique_projects || 0}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Most Active Day</div>
          <div className="text-4xl font-bold text-white">
            {stats.most_active_day_count || 0}
          </div>
        </div>
      </div>
    </div>
  );
}
