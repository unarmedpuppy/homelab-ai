import { useQuery } from '@tanstack/react-query';
import { runsAPI } from '../api/client';

export function RunList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['runs'],
    queryFn: () => runsAPI.list({ limit: 50 }),
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-400 bg-green-400/10';
      case 'error':
        return 'text-red-400 bg-red-400/10';
      case 'running':
        return 'text-yellow-400 bg-yellow-400/10';
      default:
        return 'text-zinc-400 bg-zinc-400/10';
    }
  };

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
        <p className="text-red-400">Error loading runs: {(error as Error).message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Processing Runs</h2>

      <div className="text-sm text-zinc-400">
        Total: {data?.total ?? 0} runs
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left px-4 py-3 text-sm font-medium text-zinc-400">Timestamp</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-zinc-400">Source</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-zinc-400">Status</th>
              <th className="text-right px-4 py-3 text-sm font-medium text-zinc-400">Posts</th>
            </tr>
          </thead>
          <tbody>
            {data?.runs.map((run) => (
              <tr key={run.id} className="border-b border-zinc-800 last:border-0 hover:bg-zinc-800/50">
                <td className="px-4 py-3 text-sm">{formatDate(run.timestamp)}</td>
                <td className="px-4 py-3 text-sm capitalize">{run.source}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(run.status)}`}>
                    {run.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono">{run.post_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data?.runs.length === 0 && (
        <div className="text-center text-zinc-500 py-8">
          No processing runs yet
        </div>
      )}
    </div>
  );
}
