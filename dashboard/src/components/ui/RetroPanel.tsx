import type { ReactNode } from 'react';
import { useState } from 'react';

interface RetroPanelProps {
  children: ReactNode;
  title?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  className?: string;
  headerAction?: ReactNode;
}

export function RetroPanel({
  children,
  title,
  collapsible = false,
  defaultCollapsed = false,
  className = '',
  headerAction,
}: RetroPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div className={`retro-panel ${className}`.trim()}>
      {title && (
        <div className="retro-panel-header">
          <div className="flex items-center gap-2">
            {collapsible && (
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] transition-colors"
              >
                {isCollapsed ? '▸' : '▾'}
              </button>
            )}
            <span>{title}</span>
          </div>
          {headerAction && (
            <div className="flex items-center gap-2">
              {headerAction}
            </div>
          )}
        </div>
      )}
      {(!collapsible || !isCollapsed) && (
        <div className="retro-panel-content">
          {children}
        </div>
      )}
    </div>
  );
}

export default RetroPanel;
