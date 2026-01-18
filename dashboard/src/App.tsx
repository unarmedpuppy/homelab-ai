import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';
import ProviderMonitoring from './components/ProviderMonitoring';
import AgentRuns from './components/AgentRuns';
import { BeadsBoard } from './components/beads/BeadsBoard';
import { RalphDashboard } from './components/ralph/RalphDashboard';
import { MobileNav } from './components/ui';

type ViewName = 'chat' | 'beads' | 'ralph' | 'providers' | 'stats' | 'agents';

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
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="chat" />
        <ConversationSidebar
          selectedConversationId={conversationId || null}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-hidden retro-with-mobile-nav">
        <ChatInterface conversationId={conversationId || null} />
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function BeadsView() {
  return (
    <div className="flex h-screen bg-[var(--retro-bg-dark)]">
      {/* Sidebar */}
      <div className="w-80 bg-[var(--retro-bg-medium)] border-r border-[var(--retro-border)] flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="beads" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-hidden retro-with-mobile-nav">
        <BeadsBoard />
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function RalphView() {
  return (
    <div className="flex h-screen bg-[var(--retro-bg-dark)]">
      {/* Sidebar */}
      <div className="w-80 bg-[var(--retro-bg-medium)] border-r border-[var(--retro-border)] flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="ralph" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-hidden retro-with-mobile-nav">
        <RalphDashboard />
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function StatsView() {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="stats" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-auto retro-with-mobile-nav">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Dashboard />
        </div>
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function ProvidersView() {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="providers" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-auto retro-with-mobile-nav">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-3xl font-bold text-white mb-8">Provider Monitoring</h2>
          <ProviderMonitoring />
        </div>
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function AgentsView() {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex-col hidden sm:flex">
        <AppHeader />
        <AppNavigation currentView="agents" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-auto retro-with-mobile-nav">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <AgentRuns />
        </div>
      </div>

      {/* Mobile Nav */}
      <MobileNav />
    </div>
  );
}

function AppHeader() {
  return (
    <div className="p-6 border-b border-[var(--retro-border,#1f2937)]">
      <h1 className="text-xl font-bold text-[var(--retro-accent-green,#00ff41)] uppercase tracking-wider">
        Local AI Dashboard
      </h1>
    </div>
  );
}

function AppNavigation({ currentView }: { currentView: ViewName }) {
  const navItems: { to: string; view: ViewName; icon: string; label: string }[] = [
    { to: '/', view: 'chat', icon: '💬', label: 'Chat' },
    { to: '/beads', view: 'beads', icon: '📋', label: 'Beads Board' },
    { to: '/ralph', view: 'ralph', icon: '🔄', label: 'Ralph Loops' },
    { to: '/providers', view: 'providers', icon: '🔌', label: 'Providers' },
    { to: '/stats', view: 'stats', icon: '📊', label: 'Stats' },
    { to: '/agents', view: 'agents', icon: '🤖', label: 'Agent Runs' },
  ];

  return (
    <nav className="p-4 border-b border-[var(--retro-border,#1f2937)] space-y-2">
      {navItems.map((item) => (
        <Link
          key={item.view}
          to={item.to}
          className={`
            block w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left
            ${currentView === item.view
              ? 'bg-[var(--retro-bg-light,#1f2937)] text-[var(--retro-text-primary,#fff)] border border-[var(--retro-border-active,#5bc0be)]'
              : 'text-[var(--retro-text-secondary,#9ca3af)] hover:text-[var(--retro-text-primary,#fff)] hover:bg-[var(--retro-bg-light,#1f2937)]'
            }
          `}
        >
          {item.icon} {item.label}
        </Link>
      ))}
    </nav>
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
