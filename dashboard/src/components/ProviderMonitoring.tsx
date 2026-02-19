import { useEffect, useState } from 'react';
import { providersAPI } from '../api/client';
import type { AdminProvider } from '../types/api';
import { RetroCard, RetroStatCard, RetroBadge, RetroProgress, RetroButton, useIsMobile } from './ui';
import GamingModePanel from './GamingModePanel';

export default function ProviderMonitoring() {
  const [providers, setProviders] = useState<AdminProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalProviders, setTotalProviders] = useState(0);
  const [healthyProviders, setHealthyProviders] = useState(0);
  const isMobile = useIsMobile();

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

  // Get progress bar variant based on utilization
  const getUtilizationVariant = (utilization: number): 'success' | 'warning' | 'danger' => {
    if (utilization > 80) return 'danger';
    if (utilization > 50) return 'warning';
    return 'success';
  };

  if (loading && providers.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[var(--retro-text-muted)] retro-animate-pulse uppercase tracking-wider text-sm">
          Loading providers...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-[rgba(255,68,68,0.1)] border-2 border-[var(--retro-accent-red)] rounded">
        <h3 className="text-[var(--retro-accent-red)] font-bold mb-2 uppercase tracking-wider">
          Error Loading Providers
        </h3>
        <p className="text-[var(--retro-accent-red)] text-sm mb-3">{error}</p>
        <RetroButton variant="danger" onClick={fetchProviders} size="sm">
          Retry
        </RetroButton>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-4">
      {/* Header with refresh button */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl sm:text-2xl font-bold text-[var(--retro-accent-green)] uppercase tracking-wider">
          Provider Monitoring
        </h2>
        <RetroButton variant="primary" size="sm" onClick={fetchProviders}>
          Refresh
        </RetroButton>
      </div>

      {/* Gaming Mode */}
      <GamingModePanel />

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <RetroStatCard
          label="Total Providers"
          value={totalProviders}
          color="default"
        />
        <RetroStatCard
          label="Healthy"
          value={healthyProviders}
          color="green"
        />
        <RetroStatCard
          label="Offline"
          value={totalProviders - healthyProviders}
          color={totalProviders - healthyProviders > 0 ? 'red' : 'default'}
          className="col-span-2 md:col-span-1"
        />
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {providers.map((provider) => (
          <RetroCard
            key={provider.id}
            variant={provider.health.is_healthy ? 'default' : 'warning'}
            size="responsive"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4 gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg sm:text-xl font-semibold text-[var(--retro-text-primary)]">
                    {provider.name}
                  </h3>
                  <RetroBadge
                    variant={provider.health.is_healthy ? 'status-done' : 'status-blocked'}
                    size="sm"
                  >
                    {provider.health.is_healthy ? 'Online' : 'Offline'}
                  </RetroBadge>
                  <RetroBadge variant="label" size="sm">
                    {provider.type}
                  </RetroBadge>
                </div>
                <p className="text-[var(--retro-text-muted)] text-xs sm:text-sm mt-1 truncate">
                  {provider.description || provider.endpoint}
                </p>
              </div>
              <div className="text-right shrink-0">
                <div className="text-[0.625rem] sm:text-xs text-[var(--retro-text-muted)] uppercase tracking-wider">
                  Priority
                </div>
                <div className="text-lg sm:text-xl font-bold text-[var(--retro-accent-cyan)]">
                  {provider.priority}
                </div>
              </div>
            </div>

            {/* Health Status */}
            <div className="mb-4 p-2 sm:p-3 bg-[var(--retro-bg-dark)] rounded border border-[var(--retro-border)]">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs sm:text-sm font-medium text-[var(--retro-text-secondary)] uppercase tracking-wider">
                  Health Status
                </span>
                <span className="text-[0.625rem] sm:text-xs text-[var(--retro-text-muted)]">
                  {formatTimestamp(provider.health.checked_at)}
                </span>
              </div>
              {provider.health.is_healthy ? (
                <div className="space-y-1">
                  {provider.health.response_time_ms !== undefined && (
                    <div className="text-xs sm:text-sm text-[var(--retro-text-muted)]">
                      Response: <span className="text-[var(--retro-accent-green)]">{provider.health.response_time_ms}ms</span>
                    </div>
                  )}
                  <div className="text-xs sm:text-sm text-[var(--retro-text-muted)]">
                    Failures: <span className="text-[var(--retro-text-primary)]">{provider.health.consecutive_failures}</span>
                  </div>
                </div>
              ) : (
                <div className="text-xs sm:text-sm text-[var(--retro-accent-red)]">
                  {provider.health.error || 'Provider is not responding'}
                  <div className="text-[0.625rem] sm:text-xs text-[var(--retro-text-muted)] mt-1">
                    Consecutive failures: {provider.health.consecutive_failures}
                  </div>
                </div>
              )}
            </div>

            {/* Load/Utilization */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs sm:text-sm font-medium text-[var(--retro-text-secondary)] uppercase tracking-wider">
                  Load
                </span>
                <span className="text-[0.625rem] sm:text-xs text-[var(--retro-text-muted)]">
                  {provider.load.current_requests} / {provider.load.max_concurrent}
                </span>
              </div>
              <RetroProgress
                value={provider.load.utilization}
                variant={getUtilizationVariant(provider.load.utilization)}
                showLabel={!isMobile}
                size="sm"
              />
              {isMobile && (
                <div className="text-[0.625rem] text-[var(--retro-text-muted)] mt-1 text-right">
                  {provider.load.utilization.toFixed(1)}% utilized
                </div>
              )}
            </div>

            {/* Models */}
            <div>
              <div className="text-xs sm:text-sm font-medium text-[var(--retro-text-secondary)] mb-2 uppercase tracking-wider">
                Models ({provider.models.length})
              </div>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {provider.models.slice(0, isMobile ? 3 : 4).map((model) => (
                  <RetroBadge
                    key={model.id}
                    variant="label"
                    size="sm"
                    className="max-w-[120px] sm:max-w-none"
                  >
                    <span className="truncate" title={model.name}>
                      {model.name.length > (isMobile ? 15 : 20) ? model.name.slice(0, isMobile ? 15 : 20) + '...' : model.name}
                    </span>
                  </RetroBadge>
                ))}
                {provider.models.length > (isMobile ? 3 : 4) && (
                  <RetroBadge variant="label" size="sm">
                    +{provider.models.length - (isMobile ? 3 : 4)} more
                  </RetroBadge>
                )}
              </div>
            </div>
          </RetroCard>
        ))}
      </div>

      {providers.length === 0 && (
        <div className="text-center py-8 text-[var(--retro-text-muted)] uppercase tracking-wider">
          No providers found.
        </div>
      )}

      {/* Auto-refresh indicator */}
      <div className="text-center text-[0.625rem] sm:text-xs text-[var(--retro-text-muted)] uppercase tracking-wider">
        Auto-refreshing every 10 seconds
      </div>
    </div>
  );
}
