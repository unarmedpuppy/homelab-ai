import { Link, useLocation } from 'react-router-dom';

interface NavItem {
  to: string;
  icon: string;
  label: string;
  view: string;
}

const navItems: NavItem[] = [
  { to: '/', icon: '💬', label: 'Chat', view: 'chat' },
  { to: '/beads', icon: '📋', label: 'Beads', view: 'beads' },
  { to: '/ralph', icon: '🔄', label: 'Ralph', view: 'ralph' },
  { to: '/providers', icon: '🔌', label: 'Providers', view: 'providers' },
  { to: '/stats', icon: '📊', label: 'Stats', view: 'stats' },
];

interface MobileNavProps {
  className?: string;
}

export function MobileNav({ className = '' }: MobileNavProps) {
  const location = useLocation();

  const getCurrentView = () => {
    const path = location.pathname;
    if (path === '/' || path.startsWith('/chat')) return 'chat';
    if (path.startsWith('/beads')) return 'beads';
    if (path.startsWith('/ralph')) return 'ralph';
    if (path.startsWith('/providers')) return 'providers';
    if (path.startsWith('/stats')) return 'stats';
    if (path.startsWith('/agents')) return 'agents';
    return 'chat';
  };

  const currentView = getCurrentView();

  return (
    <nav className={`retro-mobile-nav retro-hide-desktop ${className}`.trim()}>
      {navItems.map((item) => (
        <Link
          key={item.view}
          to={item.to}
          className={`retro-mobile-nav-item ${currentView === item.view ? 'retro-mobile-nav-item-active' : ''}`}
        >
          <span>{item.icon}</span>
          <span>{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}

export default MobileNav;
