import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import { PostList } from './components/PostList';
import { RunList } from './components/RunList';

function App() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/posts', label: 'Posts' },
    { path: '/runs', label: 'Runs' },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <nav className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold text-white">Bird Viewer</h1>
              <div className="flex gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'bg-zinc-800 text-white'
                        : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/posts" element={<PostList />} />
          <Route path="/runs" element={<RunList />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
