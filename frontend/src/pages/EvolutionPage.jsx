import React, { useState, useEffect, useMemo } from 'react';
import { AlertCircle, RefreshCw, Layers, GitBranch, ArrowLeft } from 'lucide-react';
import { useRepo } from '../store/repoStore';
import { evolutionApi } from '../services/api';
import NarrativeCard from '../components/timeline/NarrativeCard';
import TimelineFilters from '../components/timeline/TimelineFilters';
import TimelineCard from '../components/timeline/TimelineCard';
import TimelineSkeleton from '../components/timeline/TimelineSkeleton';

export default function EvolutionPage() {
  const { activeRepo } = useRepo();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null); // { narrative, timeline, commits_analyzed, commits_sampled }

  // Filter & Sort States
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAuthor, setSelectedAuthor] = useState('');
  const [selectedFile, setSelectedFile] = useState('');
  const [archOnly, setArchOnly] = useState(false);
  const [sortOrder, setSortOrder] = useState('desc'); // 'desc' = Newest first, 'asc' = Oldest first

  const fetchEvolution = async () => {
    if (!activeRepo) return;
    setLoading(true);
    setError('');
    try {
      const res = await evolutionApi.analyze({
        repo_id: activeRepo.repo_id,
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setData(res.data.data);
      } else {
        setError('Failed to analyze repository evolution.');
      }
    } catch (err) {
      console.error('Evolution API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to evolution analysis API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeRepo) {
      fetchEvolution();
    }
  }, [activeRepo?.repo_id]);

  // Unique list of authors for the dropdown filter
  const authorsList = useMemo(() => {
    if (!data?.timeline) return [];
    const authors = new Set(data.timeline.map((t) => t.author).filter(Boolean));
    return Array.from(authors).sort();
  }, [data?.timeline]);

  // Filtered & Sorted Timeline events
  const filteredTimeline = useMemo(() => {
    if (!data?.timeline) return [];

    let result = [...data.timeline];

    // Filter by search query (message, sha)
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      result = result.filter(
        (t) =>
          t.message.toLowerCase().includes(term) ||
          t.sha.toLowerCase().includes(term) ||
          t.author.toLowerCase().includes(term)
      );
    }

    // Filter by author
    if (selectedAuthor) {
      result = result.filter((t) => t.author === selectedAuthor);
    }

    // Filter by file path
    if (selectedFile.trim()) {
      const fileTerm = selectedFile.toLowerCase().trim();
      result = result.filter(
        (t) => t.files && t.files.some((f) => f.toLowerCase().includes(fileTerm))
      );
    }

    // Filter by architecture changes only
    if (archOnly) {
      result = result.filter((t) => t.is_architecture_change);
    }

    // Sort order: 'desc' = newest first (default), 'asc' = oldest first
    result.sort((a, b) => {
      const tA = a.timestamp_unix || 0;
      const tB = b.timestamp_unix || 0;
      return sortOrder === 'desc' ? tB - tA : tA - tB;
    });

    return result;
  }, [data?.timeline, searchTerm, selectedAuthor, selectedFile, archOnly, sortOrder]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedAuthor('');
    setSelectedFile('');
    setArchOnly(false);
    setSortOrder('desc');
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
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to view its architectural evolution timeline.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Page Title & Subtitle */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Evolution Intelligence</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">
            Repository Evolution: {activeRepo.repo_name}
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Chronological architectural timeline, milestone impact scores, and AI evolutionary synthesis.
          </p>
        </div>

        <button
          onClick={fetchEvolution}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition shadow-sm self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Re-analyze Evolution</span>
        </button>
      </div>

      {/* Loading Skeleton */}
      {loading && <TimelineSkeleton />}

      {/* Error Callout */}
      {!loading && error && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 text-rose-800 flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm">Analysis Failed</h3>
            <p className="text-xs text-rose-700 mt-1">{error}</p>
            <button
              onClick={fetchEvolution}
              className="mt-3 text-xs font-semibold bg-rose-100 hover:bg-rose-200 text-rose-800 px-3 py-1.5 rounded-md transition"
            >
              Retry Analysis
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {!loading && !error && data && (
        <>
          {/* AI Narrative Component */}
          <NarrativeCard
            narrative={data.narrative}
            repoName={data.repo_name}
            totalCommits={data.commits_analyzed}
            sampledCommits={data.commits_sampled}
            archCount={data.timeline.filter((t) => t.is_architecture_change).length}
          />

          {/* Interactive Filtering Controls */}
          <TimelineFilters
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            selectedAuthor={selectedAuthor}
            setSelectedAuthor={setSelectedAuthor}
            authorsList={authorsList}
            selectedFile={selectedFile}
            setSelectedFile={setSelectedFile}
            archOnly={archOnly}
            setArchOnly={setArchOnly}
            sortOrder={sortOrder}
            setSortOrder={setSortOrder}
            totalCount={data.timeline.length}
            filteredCount={filteredTimeline.length}
            onResetFilters={handleResetFilters}
          />

          {/* Timeline Events List */}
          {filteredTimeline.length > 0 ? (
            <div className="pl-2 pt-2">
              {filteredTimeline.map((event, index) => (
                <TimelineCard
                  key={event.sha || index}
                  event={event}
                  isLast={index === filteredTimeline.length - 1}
                />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
              <Layers className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-slate-800">No matching timeline events</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                No commit events matched your filter criteria. Try resetting search parameters or unchecking "Arch Changes Only".
              </p>
              <button
                onClick={handleResetFilters}
                className="mt-4 text-xs font-semibold bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}