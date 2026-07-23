import { useState, useEffect, createContext, useContext } from 'react';

const RepoContext = createContext(null);

export function RepoProvider({ children }) {
  const [activeRepo, setActiveRepo] = useState(null); // { repo_id, repo_name }
  const [repos, setRepos] = useState([]);

  return (
    <RepoContext.Provider value={{ activeRepo, setActiveRepo, repos, setRepos }}>
      {children}
    </RepoContext.Provider>
  );
}

export function useRepo() {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error('useRepo must be used within RepoProvider');
  return ctx;
}