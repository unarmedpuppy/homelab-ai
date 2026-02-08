import { Link, useLocation } from 'react-router-dom';

export type MobileNavView = 'chat' | 'tasks' | 'ralph' | 'providers' | 'stats' | 'agents';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  view: MobileNavView;
}

const defaultNavItems: NavItem[] = [
  { to: '/chat', icon: '💬', label: 'Chat', view: 'chat' },
  { to: '/tasks', icon: '📋', label: 'Tasks', view: 'tasks' },
  { to: '/ralph', icon: '🔄', label: 'Ralph', view: 'ralph' },
  { to: '/agents', icon: '🤖', label: 'Agents', view: 'agents' },
];

export interface MobileNavProps {
  currentView?: MobileNavView;
  items?: NavItem[];
  className?: string;
  visible?: boolean;
}

export function MobileNav({
  currentView,
  items = defaultNavItems,
  className = '',
  visible = true,
}: MobileNavProps) {
  const location = useLocation();

  const getCurrentView = (): MobileNavView => {
    if (currentView) return currentView;

    const path = location.pathname;
    if (path.startsWith('/chat')) return 'chat';
    if (path.startsWith('/tasks')) return 'tasks';
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
