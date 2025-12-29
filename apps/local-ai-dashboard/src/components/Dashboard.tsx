import { useQuery } from '@tanstack/react-query';
import { metricsAPI } from '../api/client';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import ActivityHeatmap from './ActivityHeatmap';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: metricsAPI.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">Error loading dashboard: {String(error)}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-gray-500 dark:text-gray-400">No data available</div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Messages</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.total_messages?.toLocaleString() || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Tokens</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.total_tokens?.toLocaleString() || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Days Active</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.days_active || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Longest Streak</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.longest_streak || 0} days
          </p>
        </div>
      </div>

      {/* Activity Heatmap */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Activity</h2>
        <ActivityHeatmap data={stats.activity_chart || []} />
      </div>

      {/* Model Usage Pie Chart */}
      {stats.top_models && stats.top_models.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Model Usage</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.top_models}
                dataKey="count"
                nameKey="model"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {stats.top_models.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Provider Distribution */}
      {stats.providers_used && Object.keys(stats.providers_used).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Provider Distribution</h2>
          <div className="space-y-4">
            {Object.entries(stats.providers_used).map(([provider, percentage]) => (
              <div key={provider}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">{provider}</span>
                  <span className="text-gray-500 dark:text-gray-400">{percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
