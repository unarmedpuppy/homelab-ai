import { Link, useLocation } from 'react-router-dom';

export type MobileNavView = 'chat' | 'ralph' | 'providers' | 'stats' | 'agents';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  view: MobileNavView;
}

const defaultNavItems: NavItem[] = [
  { to: '/', icon: '💬', label: 'Chat', view: 'chat' },
  { to: '/ralph', icon: '🔄', label: 'Ralph', view: 'ralph' },
  { to: '/providers', icon: '🔌', label: 'Prov', view: 'providers' },
  { to: '/agents', icon: '🤖', label: 'Agents', view: 'agents' },
];

export interface MobileNavProps {
  /** Currently active view - auto-detected from URL if not provided */
  currentView?: MobileNavView;
  /** Custom navigation items - uses default if not provided */
  items?: NavItem[];
  /** Additional CSS classes */
  className?: string;
  /** Whether to show the navigation (defaults to true) */
  visible?: boolean;
}

/**
 * Mobile-only bottom navigation bar.
 * Displays a sticky bottom bar with navigation icons.
 * Hidden on desktop (>= 640px) via CSS class.
 *
 * Layout:
 * ┌─────────────────────────────────────┐
 * │  💬   🔄   🔌   🤖                 │
 * │ Chat Ralph Prov Agents             │
 * └─────────────────────────────────────┘
 */
export function MobileNav({
  currentView,
  items = defaultNavItems,
  className = '',
  visible = true,
}: MobileNavProps) {
  const location = useLocation();

  // Auto-detect current view from URL if not provided
  const getCurrentView = (): MobileNavView => {
    if (currentView) return currentView;

    const path = location.pathname;
    if (path === '/' || path.startsWith('/chat')) return 'chat';
    if (path.startsWith('/ralph')) return 'ralph';
    if (path.startsWith('/providers')) return 'providers';
    if (path.startsWith('/stats')) return 'stats';
    if (path.startsWith('/agents')) return 'agents';
    return 'chat';
  };

  const activeView = getCurrentView();

  if (!visible) return null;

  return (
    <nav
      className={`retro-mobile-nav retro-hide-desktop ${className}`.trim()}
      role="navigation"
      aria-label="Mobile navigation"
    >
      {items.map((item) => {
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
    </nav>
  );
}

export type { NavItem as MobileNavItem };
export default MobileNav;
