import { useState } from 'react';
import Dashboard from './components/Dashboard';
import ChatInterface from './components/ChatInterface';
import ConversationSidebar from './components/ConversationSidebar';

type ViewType = 'chat' | 'stats';

function App() {
  const [activeView, setActiveView] = useState<ViewType>('chat');
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  const handleNewChat = () => {
    setSelectedConversationId(null);
    setActiveView('chat');
  };

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
    setActiveView('chat');
  };

  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">
            Local AI Dashboard
          </h1>
        </div>

        {/* Navigation */}
        <div className="p-4 border-b border-gray-800 space-y-2">
          <button
            onClick={() => setActiveView('chat')}
            className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left ${
              activeView === 'chat'
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setActiveView('stats')}
            className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors text-left ${
              activeView === 'stats'
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            📊 Stats Overview
          </button>
        </div>

        {/* Conversation Sidebar (only show in chat view) */}
        {activeView === 'chat' && (
          <ConversationSidebar
            selectedConversationId={selectedConversationId}
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
          />
        )}
      </div>

      {/* Main Panel */}
      <div className="flex-1 overflow-hidden">
        {activeView === 'chat' ? (
          <ChatInterface conversationId={selectedConversationId} />
        ) : (
          <div className="h-screen overflow-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
              <Dashboard />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
