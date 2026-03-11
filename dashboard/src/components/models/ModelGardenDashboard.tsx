import { useState, useCallback } from 'react';
import type { ModelCard as ModelCardType, ModelFilters, ModelGardenResponse } from '../../types/models';
import { modelGardenAPI } from '../../api/client';
import { RetroButton, RetroPanel } from '../ui';
import { useVisibilityPolling } from '../../hooks/useDocumentVisibility';
import { ModelCard } from './ModelCard';
import { ModelDetailPanel } from './ModelDetailPanel';
import { ModelFilterBar } from './ModelFilterBar';
import { RegisterModelModal } from './RegisterModelModal';

const POLL_INTERVAL = 30000;

const DEFAULT_FILTERS: ModelFilters = {
  search: '',
  type: 'all',
  status: 'all',
  provider: 'all',
};

function filterModels(models: ModelCardType[], filters: ModelFilters): ModelCardType[] {
  return models.filter((m) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const match =
        m.name.toLowerCase().includes(q) ||
        m.id.toLowerCase().includes(q) ||
        m.description?.toLowerCase().includes(q) ||
        m.tags.some((t) => t.toLowerCase().includes(q));
      if (!match) return false;
    }
    if (filters.type !== 'all' && m.type !== filters.type) return false;
    if (filters.status !== 'all') {
      if (filters.status === 'cached') {
        if (m.cached !== true) return false;
      } else if (m.status !== filters.status) {
        return false;
      }
    }
    if (filters.provider !== 'all' && m.provider_name !== filters.provider) return false;
    return true;
  });
}

export function ModelGardenDashboard() {
  const [data, setData] = useState<ModelGardenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ModelFilters>(DEFAULT_FILTERS);
  const [selectedModel, setSelectedModel] = useState<ModelCardType | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showRegister, setShowRegister] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const result = await modelGardenAPI.getModels();
      setData(result);
      setError(null);

      // Update selected model if still in list
      if (selectedModel) {
        const updated = result.models.find((m) => m.id === selectedModel.id);
        if (updated) setSelectedModel(updated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch model garden');
      console.error('Failed to fetch model garden:', e);
    } finally {
      setLoading(false);
    }
  }, [selectedModel]);

  useVisibilityPolling({
    callback: fetchData,
    interval: POLL_INTERVAL,
    enabled: true,
    immediate: true,
  });

  const handleStart = async (modelId: string) => {
    setActionLoading(modelId);
    try {
      await modelGardenAPI.startModel(modelId);
      await fetchData();
    } catch (e) {
      console.error('Failed to start model:', e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async (modelId: string) => {
    setActionLoading(modelId);
    try {
      await modelGardenAPI.stopModel(modelId);
      await fetchData();
    } catch (e) {
      console.error('Failed to stop model:', e);
    } finally {
      setActionLoading(null);
    }
  };

  const handlePrefetch = async (modelId: string) => {
    setActionLoading(modelId);
    try {
      await modelGardenAPI.prefetchModel(modelId);
      await fetchData();
    } catch (e) {
      console.error('Failed to prefetch model:', e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (modelId: string) => {
    setActionLoading(modelId);
    try {
      await modelGardenAPI.deleteCustom(modelId);
      if (selectedModel?.id === modelId) setSelectedModel(null);
      await fetchData();
    } catch (e) {
      console.error('Failed to delete custom model:', e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchData();
  };

  // Detail panel view
  if (selectedModel) {
    return (
      <ModelDetailPanel
        model={selectedModel}
        onClose={() => setSelectedModel(null)}
        onStart={handleStart}
        onStop={handleStop}
        onPrefetch={handlePrefetch}
        onDelete={handleDelete}
        actionLoading={actionLoading}
      />
    );
  }

  // Loading state
  if (loading && !data) {
    return (
      <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
        <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
          <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">Model Garden</h1>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-[var(--retro-text-muted)] retro-animate-pulse text-sm">
            Loading model garden...
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
        <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
          <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">Model Garden</h1>
        </div>
        <div className="flex-1 p-4">
          <div className="p-4 bg-[rgba(255,68,68,0.1)] border border-[var(--retro-accent-red)] rounded">
            <h3 className="text-[var(--retro-accent-red)] font-bold mb-2">Connection Error</h3>
            <p className="text-[var(--retro-text-muted)] text-sm mb-3">{error}</p>
            <RetroButton variant="danger" onClick={handleRefresh} size="sm">
              Retry
            </RetroButton>
          </div>
        </div>
      </div>
    );
  }

  const models = data?.models || [];
  const summary = data?.summary || { total: 0, running: 0, cached: 0, available: 0 };
  const filtered = filterModels(models, filters);
  const providers = [...new Set(models.map((m) => m.provider_name))];

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)] overflow-y-auto">
      {/* Header */}
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">Model Garden</h1>
            <p className="text-xs text-[var(--retro-text-muted)] mt-1">
              {summary.total} models &middot; {summary.running} running &middot; {summary.cached} cached
            </p>
          </div>
          <div className="flex gap-2">
            <RetroButton variant="primary" size="sm" onClick={() => setShowRegister(true)}>
              Register Model
            </RetroButton>
            <RetroButton variant="ghost" size="sm" onClick={handleRefresh}>
              Refresh
            </RetroButton>
          </div>
        </div>
      </div>

      <div className="flex-1 p-4 space-y-4 max-w-6xl">
        {/* Stats */}
        <RetroPanel>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-[var(--retro-text-primary)]">{summary.total}</div>
              <div className="text-xs text-[var(--retro-text-muted)]">Total Models</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--retro-accent-green)]">{summary.running}</div>
              <div className="text-xs text-[var(--retro-text-muted)]">Running</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--retro-accent-blue)]">{summary.cached}</div>
              <div className="text-xs text-[var(--retro-text-muted)]">Cached</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[var(--retro-text-secondary)]">{summary.available}</div>
              <div className="text-xs text-[var(--retro-text-muted)]">Available</div>
            </div>
          </div>
        </RetroPanel>

        {/* Filters */}
        <ModelFilterBar filters={filters} providers={providers} onFiltersChange={setFilters} />

        {/* Model Grid */}
        {filtered.length === 0 ? (
          <RetroPanel>
            <div className="text-center py-8 text-[var(--retro-text-muted)]">
              {models.length === 0 ? 'No models available' : 'No models match filters'}
            </div>
          </RetroPanel>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                onSelect={setSelectedModel}
                onStart={handleStart}
                onStop={handleStop}
                onPrefetch={handlePrefetch}
                actionLoading={actionLoading}
              />
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="text-xs text-[var(--retro-text-muted)] text-center">
          Showing {filtered.length} of {models.length} models
          <span className="mx-2">|</span>
          Auto-refresh every 30s (paused when tab hidden)
        </div>
      </div>

      {/* Register Modal */}
      <RegisterModelModal
        isOpen={showRegister}
        onClose={() => setShowRegister(false)}
        onSubmit={async (model) => {
          await modelGardenAPI.registerCustom(model);
          await fetchData();
        }}
      />
    </div>
  );
}

export default ModelGardenDashboard;
