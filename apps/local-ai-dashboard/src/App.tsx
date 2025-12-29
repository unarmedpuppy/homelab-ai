import { useState } from 'react';
import Dashboard from './components/Dashboard';
import ConversationExplorer from './components/ConversationExplorer';
import RAGPlayground from './components/RAGPlayground';

type TabType = 'dashboard' | 'conversations' | 'rag';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  return (
    <div className="min-h-screen bg-black">
      <nav className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20">
            <div className="flex space-x-8">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-white">
                  Local AI Dashboard
                </h1>
              </div>
              <div className="flex space-x-2 items-center ml-8">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'dashboard'
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('conversations')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'conversations'
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Conversations
                </button>
                <button
                  onClick={() => setActiveTab('rag')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'rag'
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  Search
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'conversations' && <ConversationExplorer />}
        {activeTab === 'rag' && <RAGPlayground />}
      </main>
    </div>
  );
}

export default App;
