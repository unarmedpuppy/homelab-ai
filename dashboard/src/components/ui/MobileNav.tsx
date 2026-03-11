import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

export type MobileNavView = 'chat' | 'tasks' | 'ralph' | 'providers' | 'stats' | 'agents' | 'docs';

// Minimal inline SVG icons for mobile nav
function IconChat() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M13 1H2a1 1 0 00-1 1v8a1 1 0 001 1h3.5l2 2 2-2H13a1 1 0 001-1V2a1 1 0 00-1-1z"/>
    </svg>
  );
}
function IconTasks() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 4h2M6 4h7M2 7.5h2M6 7.5h7M2 11h2M6 11h5"/>
    </svg>
  );
}
function IconRalph() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M13 7.5A5.5 5.5 0 002 7.5"/>
      <path d="M13 7.5L11 5M13 7.5L11 10"/>
    </svg>
  );
}
function IconAgents() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="5.5" cy="4.5" r="2"/>
      <path d="M1 13c0-2.5 2-4.5 4.5-4.5"/>
      <circle cx="10" cy="4.5" r="2"/>
      <path d="M10 8.5c2.5 0 4.5 2 4.5 4.5"/>
    </svg>
  );
}
function IconProviders() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4.5" y="6.5" width="6" height="5" rx="0.5"/>
      <path d="M6.5 6.5V4M8.5 6.5V4M4.5 11.5v1.5M10.5 11.5v1.5"/>
    </svg>
  );
}
function IconStats() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1.5 13V8H5v5M5.5 13V4H9v9M9.5 13V7H13v6"/>
    </svg>
  );
}
function IconDocs() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 1h6.5L12 3.5V14H3V1z"/>
      <path d="M9.5 1v3H12"/>
      <path d="M5.5 6.5h4M5.5 8.5h4M5.5 10.5h2.5"/>
    </svg>
  );
}
function IconMore() {
  return (
    <svg width="18" height="18" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" aria-hidden="true">
      <circle cx="3.5" cy="7.5" r="1" fill="currentColor" stroke="none"/>
      <circle cx="7.5" cy="7.5" r="1" fill="currentColor" stroke="none"/>
      <circle cx="11.5" cy="7.5" r="1" fill="currentColor" stroke="none"/>
    </svg>
  );
}

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  view: MobileNavView;
}

const primaryNavItems: NavItem[] = [
  { to: '/chat', icon: <IconChat />, label: 'Chat', view: 'chat' },
  { to: '/tasks', icon: <IconTasks />, label: 'Tasks', view: 'tasks' },
  { to: '/ralph', icon: <IconRalph />, label: 'Ralph', view: 'ralph' },
  { to: '/agents', icon: <IconAgents />, label: 'Agents', view: 'agents' },
];

const overflowNavItems: NavItem[] = [
  { to: '/providers', icon: <IconProviders />, label: 'Providers', view: 'providers' },
  { to: '/stats', icon: <IconStats />, label: 'Stats', view: 'stats' },
  { to: '/docs', icon: <IconDocs />, label: 'Docs', view: 'docs' },
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
          <span className="retro-mobile-nav-icon" aria-hidden="true">
            <IconMore />
          </span>
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
                      ? 'bg-[var(--retro-bg-light)] text-[var(--retro-accent-blue)]'
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
