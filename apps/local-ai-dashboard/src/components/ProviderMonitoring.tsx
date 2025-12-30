import { useEffect, useState } from 'react';
import { providersAPI } from '../api/client';
import type { AdminProvider } from '../types/api';

export default function ProviderMonitoring() {
  const [providers, setProviders] = useState<AdminProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalProviders, setTotalProviders] = useState(0);
  const [healthyProviders, setHealthyProviders] = useState(0);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await providersAPI.listAdmin();
      setProviders(data.providers);
      setTotalProviders(data.total_providers);
      setHealthyProviders(data.healthy_providers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch providers');
      console.error('Error fetching providers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchProviders, 10000);
    return () => clearInterval(interval);
  }, []);

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  if (loading && providers.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading providers...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <h3 className="text-red-400 font-semibold mb-2">Error Loading Providers</h3>
        <p className="text-red-300">{error}</p>
        <button
          onClick={fetchProviders}
          className="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 rounded text-white text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Total Providers</div>
          <div className="text-3xl font-bold text-white mt-1">{totalProviders}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Healthy Providers</div>
          <div className="text-3xl font-bold text-green-400 mt-1">{healthyProviders}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Offline Providers</div>
          <div className="text-3xl font-bold text-red-400 mt-1">
            {totalProviders - healthyProviders}
          </div>
        </div>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map((provider) => (
          <div
            key={provider.id}
            className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-xl font-semibold text-white">{provider.name}</h3>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      provider.health.is_healthy
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}
                  >
                    {provider.health.is_healthy ? 'Online' : 'Offline'}
                  </span>
                  <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                    {provider.type}
                  </span>
                </div>
                <p className="text-gray-400 text-sm mt-1">{provider.description || provider.endpoint}</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-500">Priority</div>
                <div className="text-lg font-bold text-white">{provider.priority}</div>
              </div>
            </div>

            {/* Health Status */}
            <div className="mb-4 p-3 bg-gray-900 rounded border border-gray-700">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-300">Health Status</span>
                <span className="text-xs text-gray-500">
                  {formatTimestamp(provider.health.checked_at)}
                </span>
              </div>
              {provider.health.is_healthy ? (
                <div className="space-y-1">
                  {provider.health.response_time_ms !== undefined && (
                    <div className="text-sm text-gray-400">
                      Response: <span className="text-green-400">{provider.health.response_time_ms}ms</span>
                    </div>
                  )}
                  <div className="text-sm text-gray-400">
                    Failures: <span className="text-gray-300">{provider.health.consecutive_failures}</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-red-400">
                  {provider.health.error || 'Provider is not responding'}
                  <div className="text-xs text-gray-500 mt-1">
                    Consecutive failures: {provider.health.consecutive_failures}
                  </div>
                </div>
              )}
            </div>

            {/* Load/Utilization */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-300">Load</span>
                <span className="text-xs text-gray-400">
                  {provider.load.current_requests} / {provider.load.max_concurrent}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    provider.load.utilization > 80
                      ? 'bg-red-500'
                      : provider.load.utilization > 50
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(provider.load.utilization, 100)}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">{provider.load.utilization.toFixed(1)}% utilized</div>
            </div>

            {/* Models */}
            <div>
              <div className="text-sm font-medium text-gray-300 mb-2">
                Models ({provider.models.length})
              </div>
              <div className="flex flex-wrap gap-2">
                {provider.models.slice(0, 4).map((model) => (
                  <span
                    key={model.id}
                    className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
                    title={model.name}
                  >
                    {model.name.length > 20 ? model.name.slice(0, 20) + '...' : model.name}
                  </span>
                ))}
                {provider.models.length > 4 && (
                  <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                    +{provider.models.length - 4} more
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Auto-refresh indicator */}
      <div className="text-center text-xs text-gray-500">
        Auto-refreshing every 10 seconds
      </div>
    </div>
  );
}
