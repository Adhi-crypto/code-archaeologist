import React, { useState } from 'react';
import { Bug, Search, Loader2, Sparkles, AlertCircle, Clock, ShieldAlert, FileText, CheckCircle2, ChevronRight } from 'lucide-react';
import { useRepo } from '../store/repoStore';
import { bugOriginApi } from '../services/api';
import ConfidenceGauge from '../components/bug_origin/ConfidenceGauge';
import BugCommitCard from '../components/bug_origin/BugCommitCard';
import BugTimelineVisualizer from '../components/bug_origin/BugTimelineVisualizer';
import BugOriginSkeleton from '../components/bug_origin/BugOriginSkeleton';

export default function BugOriginPage() {
  const { activeRepo } = useRepo();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null); // { likely_commit, supporting_commits, llm_explanation, analysis_time }

  const sampleQueries = [
    "Authentication stopped working after route refactor",
    "JWT token validation fails during request handling",
    "Search API became slower or timing out",
    "Repository crashes on startup with initialization error",
    "Database migration issue or table schema change",
  ];

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || !activeRepo) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await bugOriginApi.analyze({
        repo_id: activeRepo.repo_id,
        query: query.trim(),
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setResult(res.data.data);
      } else {
        setError('Failed to analyze bug origin.');
      }
    } catch (err) {
      console.error('Bug origin API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to bug origin analysis API.');
    } finally {
      setLoading(false);
    }
  };

  const handleSampleClick = (sampleText) => {
    setQuery(sampleText);
  };

  if (!activeRepo) {
    return (
      <div className="p-8 max-w-4xl">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 flex items-start gap-4 shadow-sm">
          <div className="p-2 bg-amber-100 rounded-lg text-amber-700">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-amber-900">No Repository Selected</h2>
            <p className="text-sm text-amber-800 mt-1">
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to perform Bug Origin Forensic Analysis.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header Title */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-rose-600 uppercase tracking-wider mb-1">
          <Bug className="w-3.5 h-3.5" />
          <span>Forensic Bug Localization</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Bug Origin Analysis</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Pinpoint the exact historical commit responsible for introducing a bug or regression in <span className="font-semibold text-slate-800">{activeRepo.repo_name}</span>.
        </p>
      </div>

      {/* Query Input Card */}
      <form onSubmit={handleAnalyze} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div>
          <label className="block text-sm font-semibold text-slate-800 mb-1.5">
            Describe Bug, Error Message, or Affected Feature
          </label>
          <div className="relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Authentication started failing after login refactor, or paste stack trace / error message..."
              rows={3}
              required
              className="w-full px-4 py-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent leading-relaxed"
            />
          </div>
        </div>

        {/* Sample Queries */}
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Try Sample Queries:</p>
          <div className="flex flex-wrap gap-2">
            {sampleQueries.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSampleClick(sample)}
                className="text-xs bg-slate-50 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-300 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 transition text-left"
              >
                "{sample}"
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-medium py-3 rounded-lg transition shadow-sm text-sm"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Git Commits & Running Multi-Factor Localization...</span>
            </>
          ) : (
            <>
              <Bug className="w-4 h-4 text-rose-400" />
              <span>Run Bug Origin Analysis</span>
            </>
          )}
        </button>
      </form>

      {/* Loading State Skeleton */}
      {loading && <BugOriginSkeleton />}

      {/* Error Callout */}
      {!loading && error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 text-rose-800 flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm">Analysis Failed</h3>
            <p className="text-xs text-rose-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results Display */}
      {!loading && !error && result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Analysis Time Header */}
          <div className="flex items-center justify-between bg-slate-100 rounded-lg px-4 py-2 text-xs text-slate-600">
            <span className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Multi-Factor Vector & LLM Forensic Pipeline Complete
            </span>
            <span className="flex items-center gap-1 font-mono text-slate-500">
              <Clock className="w-3 h-3" />
              Execution time: {result.analysis_time}s
            </span>
          </div>

          {/* 1. Confidence Gauge */}
          <ConfidenceGauge score={result.likely_commit?.confidence} />

          {/* 2. Bug Timeline Propagation Flow */}
          <BugTimelineVisualizer
            likelyCommit={result.likely_commit}
            supportingCommits={result.supporting_commits}
          />

          {/* 3. Primary Suspected Bug Commit */}
          <div>
            <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              Most Likely Bug Origin Commit
            </h2>
            <BugCommitCard
              commit={result.likely_commit}
              repoUrl={activeRepo.repo_url}
              isPrimary={true}
            />
          </div>

          {/* 4. AI Forensic Reasoning Explanation */}
          <div className="bg-slate-900 text-white rounded-xl p-6 border border-slate-800 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 border-b border-slate-800 pb-3">
              <Sparkles className="w-5 h-5 animate-pulse" />
              <h3 className="text-base font-bold text-white">AI Forensic Reasoning & Evidence</h3>
            </div>
            <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {result.llm_explanation}
            </div>
          </div>

          {/* 5. Runner-Up Supporting Commits */}
          {result.supporting_commits && result.supporting_commits.length > 0 && (
            <div>
              <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-500" />
                Supporting / Runner-Up Candidate Commits ({result.supporting_commits.length})
              </h3>
              <div className="space-y-4">
                {result.supporting_commits.map((cand, idx) => (
                  <BugCommitCard
                    key={cand.sha || idx}
                    commit={cand}
                    repoUrl={activeRepo.repo_url}
                    isPrimary={false}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}