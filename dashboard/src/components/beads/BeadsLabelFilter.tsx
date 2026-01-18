import { useState, useEffect } from 'react';
import { RetroPanel, RetroCheckbox, RetroButton } from '../ui';
import { useIsMobile } from '../../hooks/useMediaQuery';

// Known repository labels for grouping
const KNOWN_REPO_LABELS = [
  'mercury', 'trading-bot', 'polyjuiced', 'home-server',
  'infrastructure', 'homelab-ai', 'ai-services', 'claude-harness',
  'pokedex', 'trading-journal', 'shua-ledger', 'beads-viewer',
  'maptapdat', 'bird', 'agent-gateway', 'smart-home-3d'
];

interface LabelWithCount {
  name: string;
  count: number;
}

interface BeadsLabelFilterProps {
  labels: LabelWithCount[];
  activeLabels: string[];
  onToggleLabel: (label: string) => void;
  onClearFilters: () => void;
  className?: string;
  // Mobile drawer control
  isOpen?: boolean;
  onClose?: () => void;
}

// Helper to check if a label is a known repo label
function isRepoLabel(label: string): boolean {
  // Check for repo: prefix
  if (label.startsWith('repo:')) {
    const repoName = label.replace('repo:', '');
    return KNOWN_REPO_LABELS.includes(repoName);
  }
  // Also check if the label itself matches a known repo
  return KNOWN_REPO_LABELS.includes(label);
}

// Helper to get display name for a label
function getDisplayName(label: string): string {
  return label.startsWith('repo:') ? label.replace('repo:', '') : label;
}

interface LabelItemProps {
  label: LabelWithCount;
  isActive: boolean;
  onToggle: () => void;
}

function LabelItem({ label, isActive, onToggle }: LabelItemProps) {
  return (
    <div
      className={`
        flex items-center justify-between py-1.5 px-2 rounded cursor-pointer transition-colors
        ${isActive
          ? 'bg-[rgba(0,255,255,0.1)] border border-[var(--retro-accent-cyan)]'
          : 'hover:bg-[rgba(255,255,255,0.05)] border border-transparent'
        }
      `}
      onClick={onToggle}
      role="checkbox"
      aria-checked={isActive}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onToggle();
        }
      }}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <RetroCheckbox
          label=""
          checked={isActive}
          onChange={onToggle}
          onClick={(e) => e.stopPropagation()}
          className="flex-shrink-0"
        />
        <span className={`
          text-sm truncate
          ${isActive ? 'text-[var(--retro-accent-cyan)]' : 'text-[var(--retro-text-primary)]'}
        `}>
          {getDisplayName(label.name)}
        </span>
      </div>
      <span className={`
        text-xs ml-2 flex-shrink-0
        ${isActive ? 'text-[var(--retro-accent-cyan)]' : 'text-[var(--retro-text-muted)]'}
      `}>
        ({label.count})
      </span>
    </div>
  );
}

// Mobile drawer component
function MobileDrawer({
  isOpen,
  onClose,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Drawer */}
      <div
        className={`
          absolute top-0 left-0 h-full w-72 max-w-[85vw]
          bg-[var(--retro-bg-dark)] border-r border-[var(--retro-border)]
          transform transition-transform duration-200 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {children}
      </div>
    </div>
  );
}

export function BeadsLabelFilter({
  labels,
  activeLabels,
  onToggleLabel,
  onClearFilters,
  className = '',
  isOpen = false,
  onClose,
}: BeadsLabelFilterProps) {
  const isMobile = useIsMobile();
  const [localOpen, setLocalOpen] = useState(isOpen);

  // Sync with external open state
  useEffect(() => {
    setLocalOpen(isOpen);
  }, [isOpen]);

  // Separate repo labels from other labels
  const repoLabels = labels.filter(l => isRepoLabel(l.name));
  const otherLabels = labels.filter(l => !isRepoLabel(l.name));

  // Sort by count descending
  const sortedRepoLabels = [...repoLabels].sort((a, b) => b.count - a.count);
  const sortedOtherLabels = [...otherLabels].sort((a, b) => b.count - a.count);

  const handleClose = () => {
    setLocalOpen(false);
    onClose?.();
  };

  const filterContent = (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--retro-border)]">
        <span className="text-sm font-bold uppercase tracking-wider text-[var(--retro-accent-cyan)]">
          Filters
        </span>
        {activeLabels.length > 0 && (
          <RetroButton
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            className="text-xs"
          >
            Clear ({activeLabels.length})
          </RetroButton>
        )}
        {isMobile && (
          <button
            onClick={handleClose}
            className="ml-2 p-1 text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] transition-colors"
            aria-label="Close filters"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Repository Labels */}
        {sortedRepoLabels.length > 0 && (
          <RetroPanel title="Repositories" collapsible defaultCollapsed={false}>
            <div className="space-y-1">
              {sortedRepoLabels.map(label => (
                <LabelItem
                  key={label.name}
                  label={label}
                  isActive={activeLabels.includes(label.name)}
                  onToggle={() => onToggleLabel(label.name)}
                />
              ))}
            </div>
          </RetroPanel>
        )}

        {/* Other Labels */}
        {sortedOtherLabels.length > 0 && (
          <RetroPanel title="Other Labels" collapsible defaultCollapsed={sortedRepoLabels.length > 0}>
            <div className="space-y-1">
              {sortedOtherLabels.map(label => (
                <LabelItem
                  key={label.name}
                  label={label}
                  isActive={activeLabels.includes(label.name)}
                  onToggle={() => onToggleLabel(label.name)}
                />
              ))}
            </div>
          </RetroPanel>
        )}

        {/* Empty state */}
        {labels.length === 0 && (
          <div className="text-sm text-[var(--retro-text-muted)] text-center py-4">
            No labels available
          </div>
        )}
      </div>

      {/* Active filters summary (mobile) */}
      {isMobile && activeLabels.length > 0 && (
        <div className="p-4 border-t border-[var(--retro-border)] bg-[var(--retro-bg-medium)]">
          <div className="text-xs text-[var(--retro-text-muted)] mb-2">
            Active filters:
          </div>
          <div className="flex flex-wrap gap-1">
            {activeLabels.map(label => (
              <span
                key={label}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-[rgba(0,255,255,0.15)] text-[var(--retro-accent-cyan)] border border-[var(--retro-accent-cyan)]"
              >
                {getDisplayName(label)}
                <button
                  onClick={() => onToggleLabel(label)}
                  className="hover:text-white transition-colors"
                  aria-label={`Remove ${label} filter`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Mobile: render in drawer
  if (isMobile) {
    return (
      <MobileDrawer isOpen={localOpen} onClose={handleClose}>
        {filterContent}
      </MobileDrawer>
    );
  }

  // Desktop: render inline
  return filterContent;
}

export default BeadsLabelFilter;
