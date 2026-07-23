import React, { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bug, Search, Loader2, Sparkles, AlertCircle, Clock, ShieldAlert, FileText, CheckCircle2, ChevronRight, RefreshCw } from 'lucide-react';

import { useRepo } from '../store/repoStore';
import { bugOriginApi } from '../services/api';
import ConfidenceGauge from '../components/bug_origin/ConfidenceGauge';
import BugCommitCard from '../components/bug_origin/BugCommitCard';
import BugTimelineVisualizer from '../components/bug_origin/BugTimelineVisualizer';
import BugOriginSkeleton from '../components/bug_origin/BugOriginSkeleton';

export default function BugOriginPage() {
  const { activeRepo, bugOriginCache, setBugOriginCache } = useRepo();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const query = bugOriginCache.query;
  const result = bugOriginCache.repo_id === activeRepo?.repo_id ? bugOriginCache.result : null;

  const setQuery = (val) => {
    setBugOriginCache((prev) => ({ ...prev, query: val }));
  };

  const sampleQueries = [
    "Authentication stopped working after route refactor",
    "JWT token validation fails during request handling",
    "Search API became slower or timing out",
    "Repository crashes on startup with initialization error",
    "Database migration issue or table schema change",
  ];

  const handleAnalyze = useCallback(async (e, overrideQuery = null) => {
    if (e) e.preventDefault();
    const queryToUse = (overrideQuery || query).trim();
    if (!queryToUse || !activeRepo) return;

    setLoading(true);
    setError('');

    try {
      const res = await bugOriginApi.analyze({
        repo_id: activeRepo.repo_id,
        query: queryToUse,
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setBugOriginCache((prev) => ({
          ...prev,
          query: queryToUse,
          result: res.data.data,
          repo_id: activeRepo.repo_id,
        }));
      } else {
        setError('Failed to analyze bug origin.');
      }
    } catch (err) {
      console.error('Bug origin API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to bug origin analysis API.');
    } finally {
      setLoading(false);
    }
  }, [activeRepo, query, setBugOriginCache]);

  const handleSampleClick = (sample) => {
    setQuery(sample);
    handleAnalyze(null, sample);
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
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to perform forensic bug origin analysis.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900">Bug Origin Analysis</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              {activeRepo.repo_name}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Forensic commit identification and bug regression tracking powered by weighted confidence scoring
          </p>
        </div>

        {result && (
          <button
            onClick={(e) => handleAnalyze(e)}
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-4 py-2.5 rounded-xl text-xs font-semibold transition shadow-sm self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Re-analyze Bug</span>
          </button>
        )}
      </div>

      {/* Query Search Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <form onSubmit={handleAnalyze} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe the bug or issue (e.g. Authentication failed after router refactor)..."
              className="w-full pl-12 pr-4 py-3 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-6 py-3 rounded-xl transition flex items-center gap-2 text-sm font-semibold shadow-sm"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bug className="w-4 h-4" />}
            <span>{loading ? 'Analyzing...' : 'Find Bug Origin'}</span>
          </button>
        </form>

        {/* Sample Queries */}
        <div className="pt-3 border-t border-slate-100 flex items-center gap-2 flex-wrap text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Sample Forensic Queries:
          </span>
          {sampleQueries.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => handleSampleClick(sample)}
              className="bg-slate-50 hover:bg-emerald-50 text-slate-600 hover:text-emerald-700 border border-slate-200 hover:border-emerald-300 px-2.5 py-1 rounded-lg transition text-[11px] font-medium"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-semibold">{error}</p>
          </div>
          <button
            onClick={handleAnalyze}
            className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-900 rounded-lg text-xs font-semibold transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && <BugOriginSkeleton />}

      {/* Results View */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Analysis Header Metrics */}
          <div className="bg-emerald-900 text-white rounded-2xl p-5 border border-emerald-700 shadow-md flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-500/20 text-emerald-300 rounded-xl border border-emerald-500/30">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Forensic Analysis Complete</h3>
                <p className="text-xs text-emerald-200 mt-0.5">
                  Targeted commit identified across repository commit history
                </p>
              </div>
            </div>
            {result.analysis_time && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-200 bg-emerald-800/60 px-3 py-1.5 rounded-lg border border-emerald-700/60">
                <Clock className="w-3.5 h-3.5" />
                <span>Execution Time: <strong>{result.analysis_time}s</strong></span>
              </div>
            )}
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
            <div className="text-slate-300 text-sm leading-relaxed font-sans prose prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-xl font-bold text-emerald-400 mb-2 mt-4">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-lg font-bold text-emerald-300 mb-2 mt-3 border-b border-slate-800 pb-1">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-base font-bold text-emerald-200 mb-2 mt-3">{children}</h3>,
                  p: ({ children }) => <p className="mb-3 leading-relaxed text-slate-300">{children}</p>,
                  strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                  ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1 text-slate-300">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1 text-slate-300">{children}</ol>,
                  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                }}
              >
                {result.llm_explanation}
              </ReactMarkdown>
            </div>
          </div>

          {/* 5. Supporting Commits */}
          {result.supporting_commits && result.supporting_commits.length > 0 && (
            <div>
              <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
                <FileText className="w-5 h-5 text-slate-600" />
                Supporting Context Commits ({result.supporting_commits.length})
              </h2>
              <div className="space-y-3">
                {result.supporting_commits.map((commit, idx) => (
                  <BugCommitCard
                    key={commit.sha || idx}
                    commit={commit}
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