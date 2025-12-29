import { useQuery } from '@tanstack/react-query';
import { metricsAPI } from '../api/client';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
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
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Requests</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.total_requests.toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Tokens</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.total_tokens.toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Success Rate</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {(stats.success_rate * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Duration</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
            {stats.avg_duration_ms.toFixed(0)}ms
          </p>
        </div>
      </div>

      {/* Activity Heatmap */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Activity</h2>
        <ActivityHeatmap data={stats.activity_by_day} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Usage Pie Chart */}
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

        {/* Backend Distribution Pie Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Backend Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.top_backends}
                dataKey="count"
                nameKey="backend"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {stats.top_backends.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Metrics Bar Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Daily Requests (Last 30 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stats.daily_metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="request_count" fill="#3B82F6" name="Requests" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Token Usage Bar Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Daily Token Usage</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stats.daily_metrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="total_tokens" fill="#10B981" name="Tokens" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
