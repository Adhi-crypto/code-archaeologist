import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { GitBranch, MessageSquare, TrendingUp, Bug, Home, BarChart3, Loader2 } from 'lucide-react';
import { RepoProvider, useRepo } from './store/repoStore';

const IngestPage = lazy(() => import('./pages/IngestPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const EvolutionPage = lazy(() => import('./pages/EvolutionPage'));
const BugOriginPage = lazy(() => import('./pages/BugOriginPage'));
const IntelligencePage = lazy(() => import('./pages/IntelligencePage'));

function RouteLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[60vh] text-slate-500 gap-2">
      <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
      <span className="text-sm font-medium">Loading view...</span>
    </div>
  );
}

function Sidebar() {
  const { activeRepo } = useRepo();

  const navItems = [
    { to: '/', icon: Home, label: 'Repository' },
    { to: '/intelligence', icon: BarChart3, label: 'Intelligence' },
    { to: '/chat', icon: MessageSquare, label: 'Chat' },
    { to: '/evolution', icon: TrendingUp, label: 'Evolution' },
    { to: '/bug-origin', icon: Bug, label: 'Bug Origin' },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col h-screen sticky top-0">
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <GitBranch className="w-6 h-6 text-emerald-400" />
          <span className="font-bold text-lg">Code Archaeologist</span>
        </div>
        <p className="text-xs text-slate-400 mt-1">Software Evolution Intelligence</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-300 hover:bg-slate-800'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        {activeRepo ? (
          <div className="bg-slate-800 rounded-lg p-3">
            <p className="text-xs text-slate-400">Active Repository</p>
            <p className="text-sm font-semibold truncate">{activeRepo.repo_name}</p>
          </div>
        ) : (
          <p className="text-xs text-slate-500">No repository selected</p>
        )}
      </div>
    </aside>
  );
}

function AppShell() {
  return (
    <div className="flex bg-slate-50 min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Suspense fallback={<RouteLoadingFallback />}>
          <Routes>
            <Route path="/" element={<IngestPage />} />
            <Route path="/intelligence" element={<IntelligencePage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/evolution" element={<EvolutionPage />} />
            <Route path="/bug-origin" element={<BugOriginPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <RepoProvider>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </RepoProvider>
  );
}