import { RetroPanel, RetroCheckbox } from '../ui';

interface BeadsLabelFilterProps {
  labels: string[];
  selectedLabels: string[];
  onToggleLabel: (label: string) => void;
  onClearFilters: () => void;
  className?: string;
}

export function BeadsLabelFilter({
  labels,
  selectedLabels,
  onToggleLabel,
  onClearFilters,
  className = '',
}: BeadsLabelFilterProps) {
  // Separate repo labels from other labels
  const repoLabels = labels.filter(l => l.startsWith('repo:'));
  const otherLabels = labels.filter(l => !l.startsWith('repo:'));

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Repo Labels */}
      {repoLabels.length > 0 && (
        <RetroPanel title="Repositories" collapsible defaultCollapsed={false}>
          <div className="space-y-1">
            {repoLabels.map(label => (
              <RetroCheckbox
                key={label}
                label={label.replace('repo:', '')}
                checked={selectedLabels.includes(label)}
                onChange={() => onToggleLabel(label)}
              />
            ))}
          </div>
        </RetroPanel>
      )}

      {/* Other Labels */}
      {otherLabels.length > 0 && (
        <RetroPanel title="Labels" collapsible defaultCollapsed={true}>
          <div className="space-y-1">
            {otherLabels.map(label => (
              <RetroCheckbox
                key={label}
                label={label}
                checked={selectedLabels.includes(label)}
                onChange={() => onToggleLabel(label)}
              />
            ))}
          </div>
        </RetroPanel>
      )}

      {/* Clear Filters */}
      {selectedLabels.length > 0 && (
        <button
          onClick={onClearFilters}
          className="w-full text-xs text-[var(--retro-accent-cyan)] hover:text-[var(--retro-text-primary)] transition-colors py-2"
        >
          Clear filters ({selectedLabels.length})
        </button>
      )}
    </div>
  );
}

export default BeadsLabelFilter;
