import { RetroBadge, RetroButton, RetroPanel } from '../ui';
import type { ModelCard } from '../../types/models';

interface ModelDetailPanelProps {
  model: ModelCard;
  onClose: () => void;
  onStart: (modelId: string) => void;
  onStop: (modelId: string) => void;
  onPrefetch: (modelId: string) => void;
  onDelete?: (modelId: string) => void;
  actionLoading: string | null;
}

export function ModelDetailPanel({
  model,
  onClose,
  onStart,
  onStop,
  onPrefetch,
  onDelete,
  actionLoading,
}: ModelDetailPanelProps) {
  const isLoading = actionLoading === model.id;

  return (
    <div className="h-full flex flex-col bg-[var(--retro-bg-dark)]">
      <div className="p-4 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <RetroButton variant="secondary" size="sm" onClick={onClose}>
            Back
          </RetroButton>
          <h2 className="text-lg font-bold text-[var(--retro-text-primary)]">
            {model.name}
          </h2>
        </div>
        <div className="flex gap-2">
          {model.is_local && model.status === 'running' && (
            <RetroButton variant="danger" size="sm" onClick={() => onStop(model.id)} disabled={isLoading}>
              {isLoading ? 'Stopping...' : 'Stop'}
            </RetroButton>
          )}
          {model.is_local && model.status === 'stopped' && (
            <RetroButton variant="primary" size="sm" onClick={() => onStart(model.id)} disabled={isLoading}>
              {isLoading ? 'Starting...' : 'Start'}
            </RetroButton>
          )}
          {model.is_local && model.cached !== true && model.status !== 'unavailable' && (
            <RetroButton variant="primary" size="sm" onClick={() => onPrefetch(model.id)} disabled={isLoading}>
              {isLoading ? 'Downloading...' : 'Download'}
            </RetroButton>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Status & Badges */}
        <RetroPanel>
          <div className="flex flex-wrap gap-2 mb-3">
            <RetroBadge variant={model.status === 'running' ? 'status-done' : model.status === 'stopped' ? 'status-open' : 'status-blocked'}>
              {model.status}
            </RetroBadge>
            <RetroBadge variant="agent">{model.type}</RetroBadge>
            {model.source === 'custom' && <RetroBadge variant="priority-high">Custom</RetroBadge>}
            {model.is_default && <RetroBadge variant="status-progress">Default</RetroBadge>}
            {model.cached === true && <RetroBadge variant="label">Cached</RetroBadge>}
          </div>
          {model.description && (
            <p className="text-sm text-[var(--retro-text-secondary)]">{model.description}</p>
          )}
        </RetroPanel>

        {/* Specs */}
        <RetroPanel>
          <h3 className="text-sm font-bold text-[var(--retro-text-primary)] mb-3">Specifications</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-[var(--retro-text-muted)]">Provider</span>
              <p className="text-[var(--retro-text-primary)]">{model.provider_name}</p>
            </div>
            {model.vram_gb && (
              <div>
                <span className="text-[var(--retro-text-muted)]">VRAM Required</span>
                <p className="text-[var(--retro-text-primary)]">{model.vram_gb} GB</p>
              </div>
            )}
            {model.context_window && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Context Window</span>
                <p className="text-[var(--retro-text-primary)]">{(model.context_window / 1024).toFixed(0)}K tokens</p>
              </div>
            )}
            {model.max_tokens && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Max Output</span>
                <p className="text-[var(--retro-text-primary)]">{(model.max_tokens / 1024).toFixed(0)}K tokens</p>
              </div>
            )}
            {model.quantization && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Quantization</span>
                <p className="text-[var(--retro-text-primary)]">{model.quantization}</p>
              </div>
            )}
            {model.architecture && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Architecture</span>
                <p className="text-[var(--retro-text-primary)]">{model.architecture}</p>
              </div>
            )}
            {model.license && (
              <div>
                <span className="text-[var(--retro-text-muted)]">License</span>
                <p className="text-[var(--retro-text-primary)]">{model.license}</p>
              </div>
            )}
            {model.cache_size_gb !== null && model.cache_size_gb !== undefined && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Cache Size</span>
                <p className="text-[var(--retro-text-primary)]">{model.cache_size_gb} GB</p>
              </div>
            )}
            {model.idle_seconds !== null && model.idle_seconds !== undefined && (
              <div>
                <span className="text-[var(--retro-text-muted)]">Idle Time</span>
                <p className="text-[var(--retro-text-primary)]">{Math.floor(model.idle_seconds / 60)}m {model.idle_seconds % 60}s</p>
              </div>
            )}
          </div>
        </RetroPanel>

        {/* Capabilities */}
        <RetroPanel>
          <h3 className="text-sm font-bold text-[var(--retro-text-primary)] mb-3">Capabilities</h3>
          <div className="flex flex-wrap gap-2">
            {model.capabilities.streaming && <RetroBadge variant="label">Streaming</RetroBadge>}
            {model.capabilities.function_calling && <RetroBadge variant="label">Function Calling</RetroBadge>}
            {model.capabilities.vision && <RetroBadge variant="label">Vision</RetroBadge>}
            {model.capabilities.json_mode && <RetroBadge variant="label">JSON Mode</RetroBadge>}
          </div>
        </RetroPanel>

        {/* Tags */}
        {model.tags.length > 0 && (
          <RetroPanel>
            <h3 className="text-sm font-bold text-[var(--retro-text-primary)] mb-3">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {model.tags.map(tag => (
                <span key={tag} className="text-xs px-2 py-1 rounded bg-[var(--retro-bg-light)] text-[var(--retro-text-secondary)] border border-[var(--retro-border)]">
                  {tag}
                </span>
              ))}
            </div>
          </RetroPanel>
        )}

        {/* References */}
        {(model.hf_model || model.harbor_ref) && (
          <RetroPanel>
            <h3 className="text-sm font-bold text-[var(--retro-text-primary)] mb-3">Source</h3>
            <div className="space-y-2 text-sm">
              {model.hf_model && (
                <div>
                  <span className="text-[var(--retro-text-muted)]">HuggingFace: </span>
                  <span className="text-[var(--retro-accent-blue)]">{model.hf_model}</span>
                </div>
              )}
              {model.harbor_ref && (
                <div>
                  <span className="text-[var(--retro-text-muted)]">Harbor: </span>
                  <span className="text-[var(--retro-accent-blue)]">{model.harbor_ref}</span>
                </div>
              )}
            </div>
          </RetroPanel>
        )}

        {/* Delete custom model */}
        {model.source === 'custom' && onDelete && (
          <div className="pt-2">
            <RetroButton variant="danger" size="sm" onClick={() => onDelete(model.id)}>
              Unregister Custom Model
            </RetroButton>
          </div>
        )}
      </div>
    </div>
  );
}
