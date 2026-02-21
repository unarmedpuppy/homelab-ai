import { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Routes, Route, useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { PageLoading } from './components/ui';
import { useIsDesktop } from './hooks/useMediaQuery';
import { CleanLayout } from './components/clean/CleanLayout';

// Lazy-loaded components for code splitting
// Chat-related components are loaded immediately since Chat is a primary view
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';

// Heavy components are lazy-loaded to improve initial bundle size
const Dashboard = lazy(() => import('./components/Dashboard'));
const ProviderMonitoring = lazy(() => import('./components/ProviderMonitoring'));
const RalphDashboard = lazy(() => import('./components/ralph/RalphDashboard'));
const TasksDashboard = lazy(() => import('./components/tasks/TasksDashboard'));
const AgentsDashboard = lazy(() => import('./components/agents/AgentsDashboard'));

const TradingDashboard = lazy(() => import('./components/trading/TradingDashboard'));
const DocsPage = lazy(() => import('./pages/DocsPage'));

// Clean pages (lazy)
const HomePage = lazy(() => import('./pages/HomePage'));
const EmailsPage = lazy(() => import('./pages/reference/EmailsPage'));
const GettingStartedPage = lazy(() => import('./pages/reference/GettingStartedPage'));
const TroubleshootingPage = lazy(() => import('./pages/reference/TroubleshootingPage'));

type ViewName = 'chat' | 'ralph' | 'tasks' | 'providers' | 'stats' | 'agents' | 'trading' | 'docs';

function AppHeader() {
  return (
    <div className="p-6 border-b border-[var(--retro-border)]">
      <h1 className="text-xl font-bold text-[var(--retro-text-primary)]">
        Local AI Dashboard
      </h1>
    </div>
  );
}

function AppNavigation({ currentView }: { currentView: ViewName }) {
  const navItems: { to: string; view: ViewName; icon: string; label: string }[] = [
    { to: '/chat', view: 'chat', icon: '💬', label: 'Chat' },
    { to: '/tasks', view: 'tasks', icon: '📋', label: 'Tasks' },
    { to: '/ralph', view: 'ralph', icon: '🔄', label: 'Ralph' },
    { to: '/providers', view: 'providers', icon: '🔌', label: 'Providers' },
    { to: '/stats', view: 'stats', icon: '📊', label: 'Stats' },
    { to: '/agents', view: 'agents', icon: '🤖', label: 'Agents' },
    { to: '/trading', view: 'trading', icon: '📈', label: 'Trading' },
    { to: '/docs', view: 'docs', icon: '📄', label: 'Docs' },
  ];

  return (
    <nav className="p-4 border-b border-[var(--retro-border)] space-y-2">
      <Link
        to="/"
        className="block w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)] hover:bg-[var(--retro-bg-light)]"
      >
        🏠 Home
      </Link>
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
  sidebarContent?: ReactNode;
  scrollable?: boolean;
  withContainer?: boolean;
}

function AppLayout({
  children,
  currentView,
  sidebarContent,
  scrollable = false,
  withContainer = false,
}: AppLayoutProps) {
  const isDesktop = useIsDesktop();
  const useMobileLayout = !isDesktop;
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = useCallback(() => {
    setMenuOpen((prev) => !prev);
  }, []);

  const closeMenu = useCallback(() => {
    setMenuOpen(false);
  }, []);

  // Close menu on any navigation
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="theme-retro flex flex-col h-screen bg-[var(--retro-bg-dark)]">
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        {!useMobileLayout && (
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

        {/* Mobile/Tablet Header */}
        {useMobileLayout && (
          <div
            className="fixed top-0 left-0 right-0 z-20 bg-[var(--retro-bg-medium)] border-b border-[var(--retro-border)]"
            style={{ paddingTop: 'var(--safe-area-top)' }}
          >
            <div className="flex items-center justify-between p-4">
              <button
                onClick={toggleMenu}
                className="w-10 h-10 flex items-center justify-center text-xl bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded transition-colors hover:border-[var(--retro-border-active)]"
                aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                aria-expanded={menuOpen}
              >
                {menuOpen ? '✕' : '☰'}
              </button>
              <h1 className="text-lg font-bold text-[var(--retro-text-primary)]">
                Local AI Dashboard
              </h1>
              <div className="w-10" aria-hidden="true" />
            </div>
          </div>
        )}

        {/* Mobile/Tablet Slide-out Menu Overlay */}
        {useMobileLayout && menuOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
            onClick={closeMenu}
            aria-hidden="true"
          />
        )}

        {/* Mobile/Tablet Slide-out Menu */}
        {useMobileLayout && (
          <div
            className={`
              fixed top-0 left-0 h-full w-[85%] max-w-[320px] z-40
              bg-[var(--retro-bg-medium)] border-r border-[var(--retro-border)]
              transform transition-transform duration-300 ease-out
              ${menuOpen ? 'translate-x-0' : '-translate-x-full'}
            `}
            style={{ paddingTop: 'var(--safe-area-top)' }}
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
          `}
          style={useMobileLayout ? { paddingTop: 'var(--mobile-header-height)' } : undefined}
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
    </div>
  );
}

function ChatView() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();

  const handleNewChat = () => {
    navigate('/chat');
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

function TasksView() {
  return (
    <AppLayout currentView="tasks">
      <Suspense fallback={<PageLoading section="Tasks" />}>
        <TasksDashboard />
      </Suspense>
    </AppLayout>
  );
}

function RalphView() {
  return (
    <AppLayout currentView="ralph">
      <Suspense fallback={<PageLoading section="Ralph" />}>
        <RalphDashboard />
      </Suspense>
    </AppLayout>
  );
}

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

function StatsView() {
  return (
    <AppLayout currentView="stats" scrollable withContainer>
      <Suspense fallback={<PageLoading section="Stats" />}>
        <Dashboard />
      </Suspense>
    </AppLayout>
  );
}

function AgentsView() {
  return (
    <AppLayout currentView="agents">
      <Suspense fallback={<PageLoading section="Agents" />}>
        <AgentsDashboard />
      </Suspense>
    </AppLayout>
  );
}

function TradingView() {
  return (
    <AppLayout currentView="trading">
      <Suspense fallback={<PageLoading section="Trading" />}>
        <TradingDashboard />
      </Suspense>
    </AppLayout>
  );
}

function DocsView() {
  return (
    <AppLayout currentView="docs">
      <Suspense fallback={<PageLoading section="Docs" />}>
        <DocsPage />
      </Suspense>
    </AppLayout>
  );
}

function CleanPage({ children }: { children: ReactNode }) {
  return (
    <CleanLayout>
      <Suspense fallback={<div style={{ padding: '2rem', color: 'var(--clean-text-muted)' }}>Loading...</div>}>
        {children}
      </Suspense>
    </CleanLayout>
  );
}

function App() {
  return (
    <Routes>
      {/* Clean theme routes */}
      <Route path="/" element={<CleanPage><HomePage /></CleanPage>} />
      <Route path="/reference/emails" element={<CleanPage><EmailsPage /></CleanPage>} />
      <Route path="/reference/getting-started" element={<CleanPage><GettingStartedPage /></CleanPage>} />
      <Route path="/reference/troubleshooting" element={<CleanPage><TroubleshootingPage /></CleanPage>} />

      {/* Retro theme routes */}
      <Route path="/chat" element={<ChatView />} />
      <Route path="/chat/:conversationId" element={<ChatView />} />
      <Route path="/tasks" element={<TasksView />} />
      <Route path="/ralph" element={<RalphView />} />
      <Route path="/providers" element={<ProvidersView />} />
      <Route path="/stats" element={<StatsView />} />
      <Route path="/agents" element={<AgentsView />} />
      <Route path="/trading" element={<TradingView />} />
      <Route path="/docs" element={<DocsView />} />
      <Route path="/docs/:repo/:slug" element={<DocsView />} />
    </Routes>
  );
}

export default App;
