import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AlertCircle, RefreshCw, Layers, GitBranch, ArrowLeft } from 'lucide-react';
import { useRepo } from '../store/repoStore';
import { evolutionApi } from '../services/api';
import NarrativeCard from '../components/timeline/NarrativeCard';
import TimelineFilters from '../components/timeline/TimelineFilters';
import TimelineCard from '../components/timeline/TimelineCard';
import TimelineSkeleton from '../components/timeline/TimelineSkeleton';

export default function EvolutionPage() {
  const { activeRepo, evolutionCache, setEvolutionCache } = useRepo();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const cachedData = evolutionCache.repo_id === activeRepo?.repo_id ? evolutionCache.data : null;
  const filters = evolutionCache.filters || { search: '', author: '', file: '', archOnly: false, sort: 'oldest' };

  const setSearchTerm = (val) => setEvolutionCache((prev) => ({ ...prev, filters: { ...prev.filters, search: val } }));
  const setSelectedAuthor = (val) => setEvolutionCache((prev) => ({ ...prev, filters: { ...prev.filters, author: val } }));
  const setSelectedFile = (val) => setEvolutionCache((prev) => ({ ...prev, filters: { ...prev.filters, file: val } }));
  const setArchOnly = (val) => setEvolutionCache((prev) => ({ ...prev, filters: { ...prev.filters, archOnly: typeof val === 'function' ? val(prev.filters.archOnly) : val } }));
  const setSortOrder = (val) => setEvolutionCache((prev) => ({ ...prev, filters: { ...prev.filters, sort: val } }));

  const fetchEvolution = useCallback(async (force = false) => {
    if (!activeRepo) return;

    if (!force && evolutionCache.repo_id === activeRepo.repo_id && evolutionCache.data) {
      return; // Reuse cache
    }

    setLoading(true);
    setError('');
    try {
      const res = await evolutionApi.analyze({
        repo_id: activeRepo.repo_id,
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setEvolutionCache((prev) => ({
          ...prev,
          data: res.data.data,
          repo_id: activeRepo.repo_id,
        }));
      } else {
        setError('Failed to analyze repository evolution.');
      }
    } catch (err) {
      console.error('Evolution API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to evolution analysis API.');
    } finally {
      setLoading(false);
    }
  }, [activeRepo, evolutionCache.repo_id, evolutionCache.data, setEvolutionCache]);

  useEffect(() => {
    if (activeRepo && (!evolutionCache.data || evolutionCache.repo_id !== activeRepo.repo_id)) {
      fetchEvolution(false);
    }
  }, [activeRepo?.repo_id, evolutionCache.data, evolutionCache.repo_id, fetchEvolution]);

  const authorsList = useMemo(() => {
    if (!cachedData?.timeline) return [];
    const authors = new Set(cachedData.timeline.map((t) => t.author).filter(Boolean));
    return Array.from(authors).sort();
  }, [cachedData?.timeline]);

  const filteredTimeline = useMemo(() => {
    if (!cachedData?.timeline) return [];

    return cachedData.timeline
      .filter((event) => {
        if (filters.search) {
          const q = filters.search.toLowerCase();
          const matchesMsg = event.message.toLowerCase().includes(q);
          const matchesSha = event.sha.toLowerCase().includes(q);
          const matchesFile = event.files?.some((f) => f.toLowerCase().includes(q));
          if (!matchesMsg && !matchesSha && !matchesFile) return false;
        }

        if (filters.author && event.author !== filters.author) {
          return false;
        }

        if (filters.file) {
          const qFile = filters.file.toLowerCase();
          const matchesFile = event.files?.some((f) => f.toLowerCase().includes(qFile));
          if (!matchesFile) return false;
        }

        if (filters.archOnly && !event.is_architecture_change) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        const timeA = a.timestamp_unix || 0;
        const timeB = b.timestamp_unix || 0;
        return filters.sort === 'desc' ? timeB - timeA : timeA - timeB;
      });
  }, [cachedData?.timeline, filters]);

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
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to view its evolution timeline.
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
            <h1 className="text-2xl font-bold text-slate-900">Evolution Timeline</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              {activeRepo.repo_name}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Chronological milestone analysis and macro-architectural evolution narrative
          </p>
        </div>

        <button
          onClick={() => fetchEvolution(true)}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-4 py-2.5 rounded-xl text-xs font-semibold transition shadow-sm self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Re-analyzing...' : 'Refresh Timeline'}</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-semibold">{error}</p>
          </div>
          <button
            onClick={() => fetchEvolution(true)}
            className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-900 rounded-lg text-xs font-semibold transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !cachedData && <TimelineSkeleton />}

      {/* Evolution Content */}
      {cachedData && (
        <div className="space-y-6">
          <NarrativeCard
            narrative={cachedData.narrative}
            repoName={activeRepo.repo_name}
            totalCommits={cachedData.commits_analyzed}
            sampledCommits={cachedData.commits_sampled}
            archCount={cachedData.timeline?.filter((t) => t.is_architecture_change).length || 0}
          />

          <TimelineFilters
            searchTerm={filters.search}
            setSearchTerm={setSearchTerm}
            selectedAuthor={filters.author}
            setSelectedAuthor={setSelectedAuthor}
            authorsList={authorsList}
            selectedFile={filters.file}
            setSelectedFile={setSelectedFile}
            archOnly={filters.archOnly}
            setArchOnly={setArchOnly}
            sortOrder={filters.sort}
            setSortOrder={setSortOrder}
            totalCount={cachedData.timeline?.length || 0}
            filteredCount={filteredTimeline.length}
          />

          <div className="space-y-4 relative before:absolute before:left-[17px] before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
            {filteredTimeline.length > 0 ? (
              filteredTimeline.map((event, idx) => (
                <TimelineCard key={event.sha || idx} event={event} index={idx} />
              ))
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 ml-8">
                No commits match the selected filters.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}