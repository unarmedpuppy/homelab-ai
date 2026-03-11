import { useState, useCallback, useEffect, lazy, Suspense, Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { Routes, Route, useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import { PageLoading, ErrorFallback } from './components/ui';
import { useIsDesktop } from './hooks/useMediaQuery';
import { CleanLayout } from './components/clean/CleanLayout';

class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorFallback
          error={this.state.error}
          resetErrorBoundary={() => this.setState({ error: null })}
        />
      );
    }
    return this.props.children;
  }
}

// Lazy-loaded components for code splitting
// Chat-related components are loaded immediately since Chat is a primary view
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';

// Heavy components are lazy-loaded to improve initial bundle size
const Dashboard = lazy(() => import('./components/Dashboard'));
const ProviderMonitoring = lazy(() => import('./components/ProviderMonitoring'));
const TasksDashboard = lazy(() => import('./components/tasks/TasksDashboard'));
const AgentsDashboard = lazy(() => import('./components/agents/AgentsDashboard'));

const ModelGardenDashboard = lazy(() => import('./components/models/ModelGardenDashboard'));
const TradingDashboard = lazy(() => import('./components/trading/TradingDashboard'));
const DocsPage = lazy(() => import('./pages/DocsPage'));
const CommandPage = lazy(() => import('./command/CommandPage'));
const SessionsPage = lazy(() => import('./pages/SessionsPage'));

// Clean pages (lazy)
const HomePage = lazy(() => import('./pages/HomePage'));
const EmailsPage = lazy(() => import('./pages/reference/EmailsPage'));
const GettingStartedPage = lazy(() => import('./pages/reference/GettingStartedPage'));
const TroubleshootingPage = lazy(() => import('./pages/reference/TroubleshootingPage'));
const SummaryPage = lazy(() => import('./pages/SummaryPage'));

type ViewName = 'chat' | 'tasks' | 'providers' | 'stats' | 'agents' | 'models' | 'trading' | 'docs' | 'command' | 'sessions';

function AppHeader() {
  return (
    <div className="px-5 py-4 border-b border-[var(--retro-border)]">
      <p className="text-[0.6rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)]">
        homelab
      </p>
      <h1 className="text-sm font-bold text-[var(--retro-text-primary)] mt-0.5 tracking-tight">
        AI Dashboard
      </h1>
    </div>
  );
}

// Minimal 15×15 SVG nav icons
const NAV_ICONS: Record<string, ReactNode> = {
  home: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M7.5 1L1 6.5V14h4.5V10h4v4H14V6.5L7.5 1z"/>
    </svg>
  ),
  chat: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M13 1H2a1 1 0 00-1 1v8a1 1 0 001 1h3.5l2 2 2-2H13a1 1 0 001-1V2a1 1 0 00-1-1z"/>
    </svg>
  ),
  tasks: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 4h2M6 4h7M2 7.5h2M6 7.5h7M2 11h2M6 11h5"/>
    </svg>
  ),
  providers: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4.5" y="6.5" width="6" height="5" rx="0.5"/>
      <path d="M6.5 6.5V4M8.5 6.5V4M4.5 11.5v1.5M10.5 11.5v1.5"/>
    </svg>
  ),
  stats: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1.5 13V8H5v5M5.5 13V4H9v9M9.5 13V7H13v6"/>
    </svg>
  ),
  agents: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="5.5" cy="4.5" r="2"/>
      <path d="M1 13c0-2.5 2-4.5 4.5-4.5"/>
      <circle cx="10" cy="4.5" r="2"/>
      <path d="M10 8.5c2.5 0 4.5 2 4.5 4.5"/>
    </svg>
  ),
  sessions: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M8.5 1L4 8H8.5L5.5 14.5 12.5 7H8L8.5 1z"/>
    </svg>
  ),
  trading: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1.5 12L5 8l3 3 5.5-7"/>
      <path d="M10.5 4H14v3.5"/>
    </svg>
  ),
  docs: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 1h6.5L12 3.5V14H3V1z"/>
      <path d="M9.5 1v3H12"/>
      <path d="M5.5 6.5h4M5.5 8.5h4M5.5 10.5h2.5"/>
    </svg>
  ),
  models: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M7.5 1C5 1 3 3 3 5.5c0 1.5.5 2.5 1.5 3.5L3 14h9l-1.5-5c1-1 1.5-2 1.5-3.5C12 3 10 1 7.5 1z"/>
      <path d="M5.5 5.5h4"/>
    </svg>
  ),
  command: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M7.5 1L13.5 4.5v6L7.5 14 1.5 10.5v-6L7.5 1z"/>
    </svg>
  ),
};

function AppNavigation({ currentView }: { currentView: ViewName }) {
  const navItems: { to: string; view: ViewName; iconKey: string; label: string }[] = [
    { to: '/chat', view: 'chat', iconKey: 'chat', label: 'Chat' },
    { to: '/tasks', view: 'tasks', iconKey: 'tasks', label: 'Tasks' },
    { to: '/providers', view: 'providers', iconKey: 'providers', label: 'Providers' },
    { to: '/stats', view: 'stats', iconKey: 'stats', label: 'Stats' },
    { to: '/agents', view: 'agents', iconKey: 'agents', label: 'Agents' },
    { to: '/models', view: 'models', iconKey: 'models', label: 'Models' },
    { to: '/sessions', view: 'sessions', iconKey: 'sessions', label: 'Sessions' },
    { to: '/trading', view: 'trading', iconKey: 'trading', label: 'Trading' },
    { to: '/docs', view: 'docs', iconKey: 'docs', label: 'Docs' },
    { to: '/command', view: 'command', iconKey: 'command', label: 'Command' },
  ];

  const linkBase = 'flex items-center gap-2.5 w-full pl-[18px] pr-4 py-[7px] border-l-2 text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--retro-border-active)]';
  const linkActive = 'border-[var(--retro-border-active)] bg-[var(--retro-bg-light)] text-[var(--retro-text-primary)]';
  const linkInactive = 'border-transparent text-[var(--retro-text-secondary)] hover:bg-[var(--retro-bg-light)] hover:text-[var(--retro-text-primary)]';

  return (
    <nav className="py-2 border-b border-[var(--retro-border)]" aria-label="Main navigation">
      <Link
        to="/"
        className={`${linkBase} ${linkInactive}`}
        aria-label="Home"
      >
        {NAV_ICONS.home}
        <span>Home</span>
      </Link>
      <div className="pl-[20px] pr-4 pb-1 pt-3">
        <span className="text-[0.6rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)]">Views</span>
      </div>
      {navItems.map((item) => {
        const isActive = currentView === item.view;
        return (
          <Link
            key={item.view}
            to={item.to}
            className={`${linkBase} ${isActive ? linkActive : linkInactive}`}
            aria-current={isActive ? 'page' : undefined}
          >
            {NAV_ICONS[item.iconKey]}
            <span>{item.label}</span>
          </Link>
        );
      })}
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
                className="w-10 h-10 flex items-center justify-center bg-[var(--retro-bg-light)] border border-[var(--retro-border)] rounded transition-colors hover:border-[var(--retro-border-active)] text-[var(--retro-text-secondary)] hover:text-[var(--retro-text-primary)]"
                aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                aria-expanded={menuOpen}
              >
                {menuOpen ? (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                    <path d="M3 3l10 10M13 3L3 13"/>
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                    <path d="M2 4h12M2 8h12M2 12h12"/>
                  </svg>
                )}
              </button>
              <div className="flex flex-col items-center">
                <span className="text-[0.55rem] font-semibold tracking-[0.12em] uppercase text-[var(--retro-text-muted)] leading-none">homelab</span>
                <h1 className="text-sm font-bold text-[var(--retro-text-primary)] tracking-tight leading-tight">AI Dashboard</h1>
              </div>
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
  const [historyOpen, setHistoryOpen] = useState(false);

  const handleNewChat = () => {
    navigate('/chat');
    setHistoryOpen(false);
  };

  const handleSelectConversation = (id: string) => {
    navigate(`/chat/${id}`);
    setHistoryOpen(false);
  };

  return (
    <AppLayout currentView="chat">
      <div className="flex h-full overflow-hidden relative">
        {/* Chat pane */}
        <div className="flex-1 min-w-0 overflow-hidden">
          <ChatInterface
            conversationId={conversationId || null}
            onToggleHistory={() => setHistoryOpen(o => !o)}
            historyOpen={historyOpen}
          />
        </div>

        {/* Mobile backdrop */}
        {historyOpen && (
          <div
            className="lg:hidden fixed inset-0 z-20 bg-black/60 backdrop-blur-sm"
            onClick={() => setHistoryOpen(false)}
          />
        )}

        {/* Right history panel */}
        <div className={`chat-history-panel ${historyOpen ? 'open' : ''}`}>
          {/* Panel header — always visible */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--retro-border)] flex-shrink-0">
            <span className="text-xs font-semibold text-[var(--retro-text-secondary)] uppercase tracking-wide">
              Conversations
            </span>
            <button
              onClick={() => setHistoryOpen(false)}
              className="w-8 h-8 flex items-center justify-center text-[var(--retro-text-muted)] hover:text-[var(--retro-text-primary)] rounded transition-colors"
              aria-label="Close history panel"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                <path d="M2 2l10 10M12 2L2 12"/>
              </svg>
            </button>
          </div>
          {/* Sidebar content */}
          <div className="chat-history-panel-inner">
            <ConversationSidebar
              selectedConversationId={conversationId || null}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
            />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

function TasksView() {
  return (
    <AppLayout currentView="tasks">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Tasks" />}>
          <TasksDashboard />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function ProvidersView() {
  return (
    <AppLayout currentView="providers" scrollable withContainer>
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Providers" />}>
          <h2 className="text-3xl font-bold text-[var(--retro-text-primary)] mb-8">Provider Monitoring</h2>
          <ProviderMonitoring />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function StatsView() {
  return (
    <AppLayout currentView="stats" scrollable withContainer>
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Stats" />}>
          <Dashboard />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function AgentsView() {
  return (
    <AppLayout currentView="agents">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Agents" />}>
          <AgentsDashboard />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function ModelsView() {
  return (
    <AppLayout currentView="models">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Models" />}>
          <ModelGardenDashboard />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function SessionsView() {
  return (
    <AppLayout currentView="sessions">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Sessions" />}>
          <SessionsPage />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function TradingView() {
  return (
    <AppLayout currentView="trading">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Trading" />}>
          <TradingDashboard />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function DocsView() {
  return (
    <AppLayout currentView="docs">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Docs" />}>
          <DocsPage />
        </Suspense>
      </ErrorBoundary>
    </AppLayout>
  );
}

function CommandView() {
  return (
    <AppLayout currentView="command">
      <ErrorBoundary>
        <Suspense fallback={<PageLoading section="Command" />}>
          <CommandPage />
        </Suspense>
      </ErrorBoundary>
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
      <Route
        path="/summary"
        element={
          <CleanLayout noNav>
            <Suspense fallback={<div style={{ padding: '2rem', color: 'var(--clean-text-muted)' }}>Loading...</div>}>
              <SummaryPage />
            </Suspense>
          </CleanLayout>
        }
      />

      {/* Retro theme routes */}
      <Route path="/chat" element={<ChatView />} />
      <Route path="/chat/:conversationId" element={<ChatView />} />
      <Route path="/tasks" element={<TasksView />} />
      <Route path="/providers" element={<ProvidersView />} />
      <Route path="/stats" element={<StatsView />} />
      <Route path="/agents" element={<AgentsView />} />
      <Route path="/models" element={<ModelsView />} />
      <Route path="/sessions" element={<SessionsView />} />
      <Route path="/trading" element={<TradingView />} />
      <Route path="/docs" element={<DocsView />} />
      <Route path="/docs/:repo/:slug" element={<DocsView />} />
      <Route path="/command" element={<CommandView />} />
    </Routes>
  );
}

export default App;
