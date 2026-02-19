import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

export type MobileNavView = 'chat' | 'tasks' | 'ralph' | 'providers' | 'stats' | 'agents' | 'docs';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  view: MobileNavView;
}

const primaryNavItems: NavItem[] = [
  { to: '/chat', icon: '💬', label: 'Chat', view: 'chat' },
  { to: '/tasks', icon: '📋', label: 'Tasks', view: 'tasks' },
  { to: '/ralph', icon: '🔄', label: 'Ralph', view: 'ralph' },
  { to: '/agents', icon: '🤖', label: 'Agents', view: 'agents' },
];

const overflowNavItems: NavItem[] = [
  { to: '/providers', icon: '🔌', label: 'Providers', view: 'providers' },
  { to: '/stats', icon: '📊', label: 'Stats', view: 'stats' },
  { to: '/docs', icon: '📄', label: 'Docs', view: 'docs' },
];

const overflowViews = new Set<MobileNavView>(overflowNavItems.map(i => i.view));

export interface MobileNavProps {
  currentView?: MobileNavView;
  className?: string;
  visible?: boolean;
}

export function MobileNav({
  currentView,
  className = '',
  visible = true,
}: MobileNavProps) {
  const location = useLocation();
  const [moreOpen, setMoreOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const getCurrentView = (): MobileNavView => {
    if (currentView) return currentView;

    const path = location.pathname;
    if (path.startsWith('/chat')) return 'chat';
    if (path.startsWith('/tasks')) return 'tasks';
    if (path.startsWith('/ralph')) return 'ralph';
    if (path.startsWith('/providers')) return 'providers';
    if (path.startsWith('/stats')) return 'stats';
    if (path.startsWith('/agents')) return 'agents';
    if (path.startsWith('/docs')) return 'docs';
    return 'chat';
  };

  const activeView = getCurrentView();
  const isMoreActive = overflowViews.has(activeView);

  // Close popover on outside tap
  useEffect(() => {
    if (!moreOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [moreOpen]);

  // Close popover on navigation
  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  if (!visible) return null;

  return (
    <nav
      className={`retro-mobile-nav retro-hide-desktop ${className}`.trim()}
      role="navigation"
      aria-label="Mobile navigation"
    >
      {primaryNavItems.map((item) => {
        const isActive = activeView === item.view;
        return (
          <Link
            key={item.view}
            to={item.to}
            className={`retro-mobile-nav-item ${isActive ? 'retro-mobile-nav-item-active' : ''}`}
            aria-current={isActive ? 'page' : undefined}
          >
            <span className="retro-mobile-nav-icon" aria-hidden="true">
              {item.icon}
            </span>
            <span className="retro-mobile-nav-label">{item.label}</span>
          </Link>
        );
      })}

      {/* More tab */}
      <div className="relative" ref={popoverRef}>
        <button
          onClick={() => setMoreOpen((prev) => !prev)}
          className={`retro-mobile-nav-item ${isMoreActive ? 'retro-mobile-nav-item-active' : ''}`}
          aria-expanded={moreOpen}
          aria-haspopup="true"
        >
          <span className="retro-mobile-nav-icon" aria-hidden="true">•••</span>
          <span className="retro-mobile-nav-label">More</span>
        </button>

        {moreOpen && (
          <div
            className="absolute bottom-full right-0 mb-2 w-44 bg-[var(--retro-bg-medium)] border border-[var(--retro-border)] rounded-lg shadow-lg overflow-hidden"
            role="menu"
          >
            {overflowNavItems.map((item) => {
              const isActive = activeView === item.view;
              return (
                <Link
                  key={item.view}
                  to={item.to}
                  role="menuitem"
                  className={`
                    flex items-center gap-3 px-4 py-3 text-sm transition-colors
                    ${isActive
                      ? 'bg-[var(--retro-bg-light)] text-[var(--retro-accent-cyan)]'
                      : 'text-[var(--retro-text-secondary)] hover:bg-[var(--retro-bg-light)] hover:text-[var(--retro-text-primary)]'
                    }
                  `}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}

export type { NavItem as MobileNavItem };
export default MobileNav;
