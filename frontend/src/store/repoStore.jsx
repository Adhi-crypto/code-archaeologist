import { useState, useEffect, createContext, useContext, useCallback } from 'react';

const RepoContext = createContext(null);

const ACTIVE_REPO_KEY = 'code_archaeologist_active_repo';

export function RepoProvider({ children }) {
  // Global Active Repo State (hydrated from localStorage)
  const [activeRepo, setActiveRepoState] = useState(() => {
    try {
      const saved = localStorage.getItem(ACTIVE_REPO_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [repos, setRepos] = useState([]);

  // Centralized Module Caches
  const [chatState, setChatState] = useState({
    messages: [],
    input: '',
    mode: 'causal',
  });

  const [evolutionCache, setEvolutionCache] = useState({
    data: null,
    repo_id: null,
    filters: {
      search: '',
      author: '',
      file: '',
      archOnly: false,
      sort: 'oldest',
    },
    scrollPos: 0,
  });

  const [bugOriginCache, setBugOriginCache] = useState({
    query: '',
    result: null,
    repo_id: null,
  });

  const [intelligenceCache, setIntelligenceCache] = useState({
    data: null,
    repo_id: null,
  });

  // Clear all cached responses when active repo changes
  const clearModuleCaches = useCallback(() => {
    setChatState({ messages: [], input: '', mode: 'causal' });
    setEvolutionCache({
      data: null,
      repo_id: null,
      filters: { search: '', author: '', file: '', archOnly: false, sort: 'oldest' },
      scrollPos: 0,
    });
    setBugOriginCache({ query: '', result: null, repo_id: null });
    setIntelligenceCache({ data: null, repo_id: null });
  }, []);

  const setActiveRepo = useCallback((repo) => {
    setActiveRepoState((prev) => {
      if (prev?.repo_id !== repo?.repo_id) {
        clearModuleCaches();
      }
      try {
        if (repo) {
          localStorage.setItem(ACTIVE_REPO_KEY, JSON.stringify(repo));
        } else {
          localStorage.removeItem(ACTIVE_REPO_KEY);
        }
      } catch (e) {
        console.error('Failed to persist active repo:', e);
      }
      return repo;
    });
  }, [clearModuleCaches]);

  return (
    <RepoContext.Provider
      value={{
        activeRepo,
        setActiveRepo,
        repos,
        setRepos,
        chatState,
        setChatState,
        evolutionCache,
        setEvolutionCache,
        bugOriginCache,
        setBugOriginCache,
        intelligenceCache,
        setIntelligenceCache,
        clearModuleCaches,
      }}
    >
      {children}
    </RepoContext.Provider>
  );
}

export function useRepo() {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error('useRepo must be used within RepoProvider');
  return ctx;
}