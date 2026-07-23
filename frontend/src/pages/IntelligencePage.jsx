import React, { useState, useEffect, useCallback } from 'react';
import { BarChart3, AlertCircle, RefreshCw, GitBranch } from 'lucide-react';
import { useRepo } from '../store/repoStore';
import { repoIntelligenceApi } from '../services/api';
import AIRepositorySummaryCard from '../components/intelligence/AIRepositorySummaryCard';
import RepositoryHealthCard from '../components/intelligence/RepositoryHealthCard';
import RepositoryStatisticsCard from '../components/intelligence/RepositoryStatisticsCard';
import DeveloperAnalyticsCard from '../components/intelligence/DeveloperAnalyticsCard';
import HotspotCard from '../components/intelligence/HotspotCard';
import CoEvolvingFilesCard from '../components/intelligence/CoEvolvingFilesCard';
import RiskAssessmentCard from '../components/intelligence/RiskAssessmentCard';
import IntelligenceSkeleton from '../components/intelligence/IntelligenceSkeleton';

export default function IntelligencePage() {
  const { activeRepo, intelligenceCache, setIntelligenceCache } = useRepo();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const cachedData = intelligenceCache.repo_id === activeRepo?.repo_id ? intelligenceCache.data : null;

  const fetchIntelligence = useCallback(async (force = false) => {
    if (!activeRepo) return;

    if (!force && intelligenceCache.repo_id === activeRepo.repo_id && intelligenceCache.data) {
      return; // Reuse cache
    }

    setLoading(true);
    setError('');
    try {
      const res = await repoIntelligenceApi.analyze({
        repo_id: activeRepo.repo_id,
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setIntelligenceCache((prev) => ({
          ...prev,
          data: res.data.data,
          repo_id: activeRepo.repo_id,
        }));
      } else {
        setError('Failed to generate repository intelligence.');
      }
    } catch (err) {
      console.error('Intelligence API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to repository intelligence API.');
    } finally {
      setLoading(false);
    }
  }, [activeRepo, intelligenceCache.data, intelligenceCache.repo_id, setIntelligenceCache]);

  useEffect(() => {
    if (activeRepo && (!intelligenceCache.data || intelligenceCache.repo_id !== activeRepo.repo_id)) {
      fetchIntelligence(false);
    }
  }, [activeRepo?.repo_id, intelligenceCache.data, intelligenceCache.repo_id, fetchIntelligence]);

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
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to view intelligence reports.
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
            <h1 className="text-2xl font-bold text-slate-900">Repository Intelligence Dashboard</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              {activeRepo.repo_name}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Automated repository health assessment, developer analytics, hotspot detection, and multi-factor risk gauges
          </p>
        </div>

        <button
          onClick={() => fetchIntelligence(true)}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-4 py-2.5 rounded-xl text-xs font-semibold transition shadow-sm self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Analyzing...' : 'Refresh Intelligence'}</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-semibold">{error}</p>
          </div>
          <button
            onClick={() => fetchIntelligence(true)}
            className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-900 rounded-lg text-xs font-semibold transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Skeleton Loading */}
      {loading && !cachedData && <IntelligenceSkeleton />}

      {/* Main Dashboard Layout */}
      {cachedData && (
        <div className="space-y-6">
          {/* Top AI Executive Summary Banner */}
          <AIRepositorySummaryCard
            summary={cachedData.summary}
            repoName={activeRepo.repo_name}
            healthScore={cachedData.health_score}
            riskLevel={cachedData.risk_level}
          />

          {/* Health Score Dial & Multi-Factor Risk Gauges Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <RepositoryHealthCard
              healthScore={cachedData.health_score}
              riskLevel={cachedData.risk_level}
              recommendation={cachedData.recommendation}
            />

            <div className="lg:col-span-2">
              <RiskAssessmentCard risk={cachedData.risk_assessment} />
            </div>
          </div>

          {/* Vital Statistics 8-Card Grid */}
          <RepositoryStatisticsCard stats={cachedData.statistics} />

          {/* Developer Analytics (Recharts Bar & Pie Charts) */}
          <DeveloperAnalyticsCard developers={cachedData.developers} />

          {/* Hotspots & Co-Evolving Files Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <HotspotCard hotspots={cachedData.hotspots} />
            <CoEvolvingFilesCard coEvolvingFiles={cachedData.co_evolving_files} />
          </div>
        </div>
      )}
    </div>
  );
}
