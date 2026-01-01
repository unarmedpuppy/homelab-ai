import { useQuery } from '@tanstack/react-query';
import { statsAPI } from '../api/client';

export function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: statsAPI.get,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-zinc-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">Error loading stats: {(error as Error).message}</p>
      </div>
    );
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="text-zinc-400 text-sm">Total Posts</div>
          <div className="text-3xl font-bold mt-1">{stats?.total_posts ?? 0}</div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="text-zinc-400 text-sm">Total Runs</div>
          <div className="text-3xl font-bold mt-1">{stats?.total_runs ?? 0}</div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <div className="text-zinc-400 text-sm">Latest Run</div>
          <div className="text-lg font-medium mt-1">
            {stats?.latest_run ? (
              <span className={stats.latest_run.status === 'success' ? 'text-green-400' : 'text-red-400'}>
                {stats.latest_run.status}
              </span>
            ) : (
              'No runs yet'
            )}
          </div>
          {stats?.latest_run && (
            <div className="text-zinc-500 text-sm mt-1">
              {formatDate(stats.latest_run.timestamp)}
            </div>
          )}
        </div>
      </div>

      {stats?.posts_by_source && Object.keys(stats.posts_by_source).length > 0 && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Posts by Source</h3>
          <div className="space-y-2">
            {Object.entries(stats.posts_by_source).map(([source, count]) => (
              <div key={source} className="flex justify-between items-center">
                <span className="text-zinc-400 capitalize">{source}</span>
                <span className="font-mono">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
