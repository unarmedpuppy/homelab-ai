import { RetroBadge, RetroButton } from '../ui';
import type { ModelCard as ModelCardType } from '../../types/models';

interface ModelCardProps {
  model: ModelCardType;
  onSelect: (model: ModelCardType) => void;
  onStart: (modelId: string) => void;
  onStop: (modelId: string) => void;
  onPrefetch: (modelId: string) => void;
  actionLoading: string | null;
}

function statusBadge(status: string) {
  switch (status) {
    case 'running':
      return <RetroBadge variant="status-done">Running</RetroBadge>;
    case 'stopped':
      return <RetroBadge variant="status-open">Stopped</RetroBadge>;
    case 'unavailable':
      return <RetroBadge variant="status-blocked">Unavailable</RetroBadge>;
    default:
      return <RetroBadge variant="label">{status}</RetroBadge>;
  }
}

function typeBadge(type: string) {
  const variants: Record<string, string> = {
    text: 'agent',
    image: 'priority-medium',
    tts: 'priority-low',
    embedding: 'label',
  };
  return (
    <RetroBadge variant={(variants[type] || 'label') as 'agent' | 'label' | 'priority-medium' | 'priority-low'}>
      {type}
    </RetroBadge>
  );
}

export function ModelCard({ model, onSelect, onStart, onStop, onPrefetch, actionLoading }: ModelCardProps) {
  const isLoading = actionLoading === model.id;

  return (
    <div
      className="p-4 bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded cursor-pointer hover:border-[var(--retro-border-active)] transition-colors"
      onClick={() => onSelect(model)}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-bold text-[var(--retro-text-primary)] truncate flex-1 mr-2">
          {model.name}
        </h3>
        {statusBadge(model.status)}
      </div>

      <p className="text-xs text-[var(--retro-text-muted)] mb-3 line-clamp-2 min-h-[2rem]">
        {model.description || 'No description'}
      </p>

      <div className="flex flex-wrap gap-1 mb-3">
        {typeBadge(model.type)}
        {model.source === 'custom' && <RetroBadge variant="priority-high">Custom</RetroBadge>}
        {model.is_default && <RetroBadge variant="status-progress">Default</RetroBadge>}
        {model.cached === true && <RetroBadge variant="label">Cached</RetroBadge>}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-[var(--retro-text-secondary)] mb-3">
        <span>Provider: {model.provider_name}</span>
        {model.vram_gb && <span>VRAM: {model.vram_gb}GB</span>}
        {model.context_window && <span>Context: {(model.context_window / 1024).toFixed(0)}K</span>}
        {model.quantization && <span>Quant: {model.quantization}</span>}
      </div>

      {model.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {model.tags.slice(0, 4).map(tag => (
            <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--retro-bg-light)] text-[var(--retro-text-muted)]">
              {tag}
            </span>
          ))}
        </div>
      )}

      {model.is_local && (
        <div className="flex gap-2 mt-2" onClick={(e) => e.stopPropagation()}>
          {model.status === 'running' ? (
            <RetroButton variant="danger" size="sm" onClick={() => onStop(model.id)} disabled={isLoading}>
              {isLoading ? 'Stopping...' : 'Stop'}
            </RetroButton>
          ) : model.status === 'stopped' && model.cached ? (
            <RetroButton variant="primary" size="sm" onClick={() => onStart(model.id)} disabled={isLoading}>
              {isLoading ? 'Starting...' : 'Start'}
            </RetroButton>
          ) : model.status === 'stopped' ? (
            <RetroButton variant="primary" size="sm" onClick={() => onPrefetch(model.id)} disabled={isLoading}>
              {isLoading ? 'Downloading...' : 'Download'}
            </RetroButton>
          ) : null}
        </div>
      )}
    </div>
  );
}
