import type { ReactNode } from 'react';
import { useState, useRef, useEffect } from 'react';

export interface RetroPanelProps {
  children: ReactNode;
  title: string;
  icon?: ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  className?: string;
  actions?: ReactNode;
}

export function RetroPanel({
  children,
  title,
  icon,
  collapsible = false,
  defaultCollapsed = false,
  className = '',
  actions,
}: RetroPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [contentHeight, setContentHeight] = useState<number | undefined>(undefined);
  const contentRef = useRef<HTMLDivElement>(null);

  // Measure content height for animation (offsetHeight includes padding)
  useEffect(() => {
    if (contentRef.current) {
      const resizeObserver = new ResizeObserver(() => {
        if (contentRef.current) {
          setContentHeight(contentRef.current.offsetHeight);
        }
      });
      resizeObserver.observe(contentRef.current);
      return () => resizeObserver.disconnect();
    }
  }, []);

  const handleToggle = () => {
    if (collapsible) {
      setIsCollapsed(!isCollapsed);
    }
  };

  return (
    <div className={`retro-panel retro-panel--stepped ${className}`.trim()}>
      <div
        className={`retro-panel-header ${collapsible ? 'retro-panel-header--collapsible' : ''}`}
        onClick={collapsible ? handleToggle : undefined}
        role={collapsible ? 'button' : undefined}
        tabIndex={collapsible ? 0 : undefined}
        onKeyDown={collapsible ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleToggle();
          }
        } : undefined}
        aria-expanded={collapsible ? !isCollapsed : undefined}
      >
        <div className="retro-panel-header__left">
          {collapsible && (
            <span
              className={`retro-panel-chevron ${isCollapsed ? 'retro-panel-chevron--collapsed' : ''}`}
              aria-hidden="true"
            >
              ▾
            </span>
          )}
          {icon && (
            <span className="retro-panel-icon" aria-hidden="true">
              {icon}
            </span>
          )}
          <span className="retro-panel-title">{title}</span>
        </div>
        {actions && (
          <div
            className="retro-panel-actions"
            onClick={(e) => e.stopPropagation()}
          >
            {actions}
          </div>
        )}
      </div>
      <div
        className={`retro-panel-body ${isCollapsed ? 'retro-panel-body--collapsed' : ''}`}
        style={{
          height: collapsible
            ? (isCollapsed ? 0 : contentHeight !== undefined ? contentHeight : 'auto')
            : 'auto'
        }}
      >
        <div ref={contentRef} className="retro-panel-content">
          {children}
        </div>
      </div>
    </div>
  );
}

export default RetroPanel;
