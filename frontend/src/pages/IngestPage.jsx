import { useState } from 'react';
import { GitBranch, Loader2, CheckCircle2, XCircle, Search } from 'lucide-react';
import { repoApi } from '../services/api';
import { useRepo } from '../store/repoStore';

export default function IngestPage() {
  const { setActiveRepo } = useRepo();
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [maxCommits, setMaxCommits] = useState(100);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // { repo_id, status, message }
  const [error, setError] = useState('');

  const handleIngest = async (e) => {
    e.preventDefault();
    setError('');
    setStatus(null);
    setLoading(true);

    try {
      const res = await repoApi.ingest({
        repo_url: repoUrl,
        branch,
        max_commits: Number(maxCommits),
        include_prs: false,
        include_issues: false,
      });
      const repoId = res.data.data.repo_id;
      pollStatus(repoId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start ingestion');
      setLoading(false);
    }
  };

 const pollStatus = (repoId) => {
  let stopped = false;
  const interval = setInterval(async () => {
    if (stopped) return;
    try {
      const res = await repoApi.status(repoId);
      const data = res.data;
      setStatus(data);

      if (data.status === 'complete') {
        stopped = true;
        clearInterval(interval);
        setLoading(false);
        const repoName = repoUrl.replace(/\.git$/, '').split('/').pop();
        setActiveRepo({ repo_id: repoId, repo_name: repoName });
      } else if (data.status === 'failed') {
        stopped = true;
        clearInterval(interval);
        setLoading(false);
        setError(data.message);
      }
    } catch (err) {
      stopped = true;
      clearInterval(interval);
      setLoading(false);
    }
  }, 1500);
};

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Ingest Repository</h1>
        <p className="text-slate-500 mt-1">
          Provide a public GitHub repository URL to extract commit history and build the temporal knowledge base.
        </p>
      </div>

      <form onSubmit={handleIngest} className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Repository URL</label>
          <div className="relative">
            <GitBranch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              required
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/tiangolo/fastapi"
              className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Max Commits</label>
            <input
              type="number"
              value={maxCommits}
              onChange={(e) => setMaxCommits(e.target.value)}
              min="10"
              max="2000"
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white font-medium py-2.5 rounded-lg transition"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Ingest Repository
            </>
          )}
        </button>
      </form>

      {status && (
        <div className="mt-6 bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center gap-3">
            {status.status === 'complete' && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
            {status.status === 'running' && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
            {status.status === 'failed' && <XCircle className="w-5 h-5 text-red-500" />}
            <div>
              <p className="text-sm font-medium text-slate-900 capitalize">{status.status}</p>
              <p className="text-sm text-slate-500">{status.message}</p>
            </div>
          </div>
          {status.status === 'running' && status.total > 0 && (
            <div className="mt-3 w-full bg-slate-100 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${(status.progress / status.total) * 100}%` }}
              />
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-4">
          {error}
        </div>
      )}

      {status?.status === 'complete' && (
        <div className="mt-6 bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <p className="text-sm text-emerald-800">
            Repository ingested successfully. Head to the <b>Chat</b> tab to start asking questions, or <b>Evolution</b> to see the architectural timeline.
          </p>
        </div>
      )}
    </div>
  );
}