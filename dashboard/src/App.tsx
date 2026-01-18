import { useState, useCallback, lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { MobileNav, PageLoading } from './components/ui';
import { useIsMobile } from './hooks/useMediaQuery';

// Lazy-loaded components for code splitting
// Chat-related components are loaded immediately since Chat is the default view
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';

// Heavy components are lazy-loaded to improve initial bundle size
const Dashboard = lazy(() => import('./components/Dashboard'));
const ProviderMonitoring = lazy(() => import('./components/ProviderMonitoring'));
const AgentRuns = lazy(() => import('./components/AgentRuns'));
const BeadsBoard = lazy(() => import('./components/beads/BeadsBoard'));
const RalphDashboard = lazy(() => import('./components/ralph/RalphDashboard'));

type ViewName = 'chat' | 'beads' | 'ralph' | 'providers' | 'stats' | 'agents';

/**
 * Shared application header with retro styling.
 */
function AppHeader() {
  return (
    <div className="p-6 border-b border-[var(--retro-border)]">
      <h1 className="text-xl font-bold text-[var(--retro-accent-green)] uppercase tracking-wider">
        LOCAL AI DASHBOARD
      </h1>
    </div>
  );
}

/**
 * Desktop sidebar navigation with retro styling.
 */
function AppNavigation({ currentView }: { currentView: ViewName }) {
  const navItems: { to: string; view: ViewName; icon: string; label: string }[] = [
    { to: '/', view: 'chat', icon: '💬', label: 'Chat' },
    { to: '/beads', view: 'beads', icon: '📋', label: 'Beads' },
    { to: '/ralph', view: 'ralph', icon: '🔄', label: 'Ralph' },
    { to: '/providers', view: 'providers', icon: '🔌', label: 'Providers' },
    { to: '/stats', view: 'stats', icon: '📊', label: 'Stats' },
    { to: '/agents', view: 'agents', icon: '🤖', label: 'Agents' },
  ];

  return (
    <nav className="p-4 border-b border-[var(--retro-border)] space-y-2">
      {navItems.map((item) => (
        <Link
          key={item.view}
          to={item.to}
          className={`
            block w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left
            ${currentView === item.view
              ? 'bg-[var(--retro-bg-light)] text-[var(--retro-text-primary)] border border-[var(--retro-border-active)]'
              : 'text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)] hover:bg-[var(--retro-bg-light)]'
            }
          `}
        >
          {item.icon} {item.label}
        </Link>
      ))}
    </nav>
  );
}

interface AppLayoutProps {
  children: ReactNode;
  currentView: ViewName;
  /** Additional sidebar content (e.g., ConversationSidebar for chat view) */
  sidebarContent?: ReactNode;
  /** Whether to use overflow-auto (scrollable) or overflow-hidden for main content */
  scrollable?: boolean;
  /** Whether to wrap content in a max-width container with padding */
  withContainer?: boolean;
}

/**
 * Shared layout component with responsive sidebar and mobile navigation.
 *
 * Desktop (>= 640px): Shows sidebar with header, navigation, and optional content
 * Mobile (< 640px): Shows mobile header with hamburger menu + bottom MobileNav
 */
function AppLayout({
  children,
  currentView,
  sidebarContent,
  scrollable = false,
  withContainer = false,
}: AppLayoutProps) {
  const isMobile = useIsMobile();
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = useCallback(() => {
    setMenuOpen((prev) => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setMenuOpen(false);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[var(--retro-bg-dark)]">
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <div className="w-80 bg-[var(--retro-bg-medium)] border-r border-[var(--retro-border)] flex flex-col flex-shrink-0">
            <AppHeader />
            <AppNavigation currentView={currentView} />
            {sidebarContent && (
              <div className="flex-1 overflow-hidden">
                {sidebarContent}
              </div>
            )}
          </div>
        )}

        {/* Mobile Header */}
        {isMobile && (
          <div className="fixed top-0 left-0 right-0 z-20 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]">
            <div className="flex items-center justify-between p-4">
              <button
                onClick={toggleMenu}
                className="w-10 h-10 flex items-center justify-center text-xl bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded transition-colors hover:border-[var(--retro-border-active)]"
                aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                aria-expanded={menuOpen}
              >
                {menuOpen ? '✕' : '☰'}
              </button>
              <h1 className="text-lg font-bold text-[var(--retro-accent-green)] uppercase tracking-wider">
                Local AI Dashboard
              </h1>
              <div className="w-10" aria-hidden="true" />
            </div>
          </div>
        )}

        {/* Mobile Slide-out Menu Overlay */}
        {isMobile && menuOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
            onClick={closeMenu}
            aria-hidden="true"
          />
        )}

        {/* Mobile Slide-out Menu */}
        {isMobile && (
          <div
            className={`
              fixed top-0 left-0 h-full w-[85%] max-w-[320px] z-40
              bg-[var(--retro-bg-medium)] border-r border-[var(--retro-border)]
              transform transition-transform duration-300 ease-out
              ${menuOpen ? 'translate-x-0' : '-translate-x-full'}
            `}
          >
            <div className="flex flex-col h-full">
              <AppHeader />
              <AppNavigation currentView={currentView} />
              {sidebarContent && (
                <div className="flex-1 overflow-hidden" onClick={closeMenu}>
                  {sidebarContent}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Content */}
        <div
          className={`
            flex-1
            ${scrollable ? 'overflow-auto' : 'overflow-hidden'}
            ${isMobile ? 'pt-[72px] retro-with-mobile-nav' : ''}
          `}
        >
          {withContainer ? (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
              {children}
            </div>
          ) : (
            children
          )}
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobile && <MobileNav currentView={currentView} />}
    </div>
  );
}

/**
 * Chat view with conversation sidebar.
 */
function ChatView() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();

  const handleNewChat = () => {
    navigate('/');
  };

  const handleSelectConversation = (id: string) => {
    navigate(`/chat/${id}`);
  };

  return (
    <AppLayout
      currentView="chat"
      sidebarContent={
        <ConversationSidebar
          selectedConversationId={conversationId || null}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      }
    >
      <ChatInterface conversationId={conversationId || null} />
    </AppLayout>
  );
}

/**
 * Beads kanban board view.
 */
function BeadsView() {
  return (
    <AppLayout currentView="beads">
      <Suspense fallback={<PageLoading section="Beads" />}>
        <BeadsBoard />
      </Suspense>
    </AppLayout>
  );
}

/**
 * Ralph Wiggum autonomous agent loops dashboard.
 */
function RalphView() {
  return (
    <AppLayout currentView="ralph">
      <Suspense fallback={<PageLoading section="Ralph" />}>
        <RalphDashboard />
      </Suspense>
    </AppLayout>
  );
}

/**
 * Provider monitoring view.
 */
function ProvidersView() {
  return (
    <AppLayout currentView="providers" scrollable withContainer>
      <Suspense fallback={<PageLoading section="Providers" />}>
        <h2 className="text-3xl font-bold text-[var(--retro-text-primary)] mb-8">Provider Monitoring</h2>
        <ProviderMonitoring />
      </Suspense>
    </AppLayout>
  );
}

/**
 * Stats/metrics dashboard view.
 */
function StatsView() {
  return (
    <AppLayout currentView="stats" scrollable withContainer>
      <Suspense fallback={<PageLoading section="Stats" />}>
        <Dashboard />
      </Suspense>
    </AppLayout>
  );
}

/**
 * Agent runs history view.
 */
function AgentsView() {
  return (
    <AppLayout currentView="agents" scrollable withContainer>
      <Suspense fallback={<PageLoading section="Agents" />}>
        <AgentRuns />
      </Suspense>
    </AppLayout>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      <Route path="/chat/:conversationId" element={<ChatView />} />
      <Route path="/beads" element={<BeadsView />} />
      <Route path="/ralph" element={<RalphView />} />
      <Route path="/providers" element={<ProvidersView />} />
      <Route path="/stats" element={<StatsView />} />
      <Route path="/agents" element={<AgentsView />} />
    </Routes>
  );
}

export default App;
