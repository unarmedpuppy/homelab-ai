import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';
import ProviderMonitoring from './components/ProviderMonitoring';

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
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
        <AppHeader />
        <AppNavigation currentView="chat" />
        <ConversationSidebar
          selectedConversationId={conversationId || null}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface conversationId={conversationId || null} />
      </div>
    </div>
  );
}

function StatsView() {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
        <AppHeader />
        <AppNavigation currentView="stats" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Dashboard />
        </div>
      </div>
    </div>
  );
}

function ProvidersView() {
  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
        <AppHeader />
        <AppNavigation currentView="providers" />
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-3xl font-bold text-white mb-8">Provider Monitoring</h2>
          <ProviderMonitoring />
        </div>
      </div>
    </div>
  );
}

function AppHeader() {
  return (
    <div className="p-6 border-b border-gray-800">
      <h1 className="text-xl font-bold text-white">
        Local AI Dashboard
      </h1>
    </div>
  );
}

function AppNavigation({ currentView }: { currentView: 'chat' | 'stats' | 'providers' }) {
  return (
    <div className="p-4 border-b border-gray-800 space-y-2">
      <Link
        to="/"
        className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left block ${
          currentView === 'chat'
            ? 'bg-gray-800 text-white'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`}
      >
        💬 Chat
      </Link>
      <Link
        to="/providers"
        className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left block ${
          currentView === 'providers'
            ? 'bg-gray-800 text-white'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`}
      >
        🔌 Providers
      </Link>
      <Link
        to="/stats"
        className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left block ${
          currentView === 'stats'
            ? 'bg-gray-800 text-white'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`}
      >
        📊 Stats Overview
      </Link>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      <Route path="/chat/:conversationId" element={<ChatView />} />
      <Route path="/providers" element={<ProvidersView />} />
      <Route path="/stats" element={<StatsView />} />
    </Routes>
  );
}

export default App;
