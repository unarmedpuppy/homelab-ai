import { RetroInput, RetroSelect } from '../ui';
import type { ModelFilters } from '../../types/models';

interface ModelFilterBarProps {
  filters: ModelFilters;
  providers: string[];
  onFiltersChange: (filters: ModelFilters) => void;
}

export function ModelFilterBar({ filters, providers, onFiltersChange }: ModelFilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div className="flex-1 min-w-[200px]">
        <RetroInput
          placeholder="Search models..."
          value={filters.search}
          onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
        />
      </div>
      <div className="w-[140px]">
        <RetroSelect
          value={filters.type}
          onChange={(e) => onFiltersChange({ ...filters, type: e.target.value as ModelFilters['type'] })}
          options={[
            { value: 'all', label: 'All Types' },
            { value: 'text', label: 'Text' },
            { value: 'image', label: 'Image' },
            { value: 'tts', label: 'TTS' },
            { value: 'embedding', label: 'Embedding' },
          ]}
        />
      </div>
      <div className="w-[140px]">
        <RetroSelect
          value={filters.status}
          onChange={(e) => onFiltersChange({ ...filters, status: e.target.value as ModelFilters['status'] })}
          options={[
            { value: 'all', label: 'All Status' },
            { value: 'running', label: 'Running' },
            { value: 'stopped', label: 'Stopped' },
            { value: 'cached', label: 'Cached' },
            { value: 'unavailable', label: 'Unavailable' },
          ]}
        />
      </div>
      <div className="w-[160px]">
        <RetroSelect
          value={filters.provider}
          onChange={(e) => onFiltersChange({ ...filters, provider: e.target.value })}
          options={[
            { value: 'all', label: 'All Providers' },
            ...providers.map(p => ({ value: p, label: p })),
          ]}
        />
      </div>
    </div>
  );
}
