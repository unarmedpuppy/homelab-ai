import { useState } from 'react';
import Dashboard from './components/Dashboard';
import ConversationExplorer from './components/ConversationExplorer';
import RAGPlayground from './components/RAGPlayground';

type TabType = 'dashboard' | 'conversations' | 'rag';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Local AI Dashboard
                </h1>
              </div>
              <div className="flex space-x-4 items-center">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'dashboard'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('conversations')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'conversations'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  Conversations
                </button>
                <button
                  onClick={() => setActiveTab('rag')}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === 'rag'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  RAG Search
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'conversations' && <ConversationExplorer />}
        {activeTab === 'rag' && <RAGPlayground />}
      </main>
    </div>
  );
}

export default App;
