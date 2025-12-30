import { useMemo } from 'react';
import type { AdminProvider, ProviderModel } from '../types/api';

interface ProviderModelSelectorProps {
  providers: AdminProvider[];
  isLoading: boolean;
  selectedProvider: string | null;
  selectedModel: string | null;
  onProviderChange: (providerId: string | null) => void;
  onModelChange: (modelId: string | null) => void;
  disabled?: boolean;
}

const getStatusIndicator = (provider: AdminProvider): string => {
  if (!provider.enabled) return '⚫';
  if (provider.health.is_healthy) return '🟢';
  if (provider.health.consecutive_failures < 3) return '🟡';
  return '🔴';
};

const formatConcurrency = (provider: AdminProvider): string => {
  const { current_requests, max_concurrent } = provider.load;
  return `(${current_requests}/${max_concurrent})`;
};

const formatContextWindow = (model: ProviderModel): string => {
  if (!model.context_window) return '';
  const k = Math.round(model.context_window / 1024);
  return `${k}K ctx`;
};

export default function ProviderModelSelector({
  providers,
  isLoading,
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  disabled = false,
}: ProviderModelSelectorProps) {
  const availableModels = useMemo(() => {
    if (!selectedProvider) return [];
    const provider = providers.find(p => p.id === selectedProvider);
    return provider?.models || [];
  }, [providers, selectedProvider]);

  const currentProvider = useMemo(() => {
    if (!selectedProvider) return null;
    return providers.find(p => p.id === selectedProvider) || null;
  }, [providers, selectedProvider]);

  const sortedProviders = useMemo(() => {
    return [...providers].sort((a, b) => {
      if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
      if (a.health.is_healthy !== b.health.is_healthy) {
        return a.health.is_healthy ? -1 : 1;
      }
      return a.priority - b.priority;
    });
  }, [providers]);

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === 'auto') {
      onProviderChange(null);
      onModelChange(null);
    } else {
      onProviderChange(value);
      const provider = providers.find(p => p.id === value);
      const defaultModel = provider?.models.find(m => m.is_default) || provider?.models[0];
      onModelChange(defaultModel?.id || null);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onModelChange(value || null);
  };

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <label className="text-xs uppercase tracking-wider text-gray-500">
          Provider:
        </label>
        <select
          value={selectedProvider || 'auto'}
          onChange={handleProviderChange}
          disabled={disabled || isLoading}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed min-w-[200px]"
        >
          <option value="auto">🤖 Auto (Intelligent Routing)</option>
          {isLoading ? (
            <option disabled>Loading providers...</option>
          ) : (
            sortedProviders.map(provider => (
              <option
                key={provider.id}
                value={provider.id}
                disabled={!provider.enabled || !provider.health.is_healthy}
              >
                {getStatusIndicator(provider)} {provider.name} {formatConcurrency(provider)}
                {!provider.health.is_healthy ? ' (offline)' : ''}
              </option>
            ))
          )}
        </select>
      </div>

      {selectedProvider && currentProvider && (
        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wider text-gray-500">
            Model:
          </label>
          <select
            value={selectedModel || ''}
            onChange={handleModelChange}
            disabled={disabled || isLoading || availableModels.length === 0}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed min-w-[280px]"
          >
            {availableModels.length === 0 ? (
              <option disabled>No models available</option>
            ) : (
              availableModels.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                  {model.is_default ? ' ⭐' : ''}
                  {model.capabilities?.vision ? ' 👁️' : ''}
                  {formatContextWindow(model) ? ` • ${formatContextWindow(model)}` : ''}
                </option>
              ))
            )}
          </select>
        </div>
      )}

      {!selectedProvider && (
        <div className="text-xs text-gray-500">
          Router will select optimal provider automatically
        </div>
      )}
    </div>
  );
}
