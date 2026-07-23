import React, { useState, useEffect } from 'react';
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
  const { activeRepo } = useRepo();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  const fetchIntelligence = async () => {
    if (!activeRepo) return;
    setLoading(true);
    setError('');
    try {
      const res = await repoIntelligenceApi.analyze({
        repo_id: activeRepo.repo_id,
        repo_name: activeRepo.repo_name,
      });

      if (res.data.success && res.data.data) {
        setData(res.data.data);
      } else {
        setError('Failed to generate repository intelligence.');
      }
    } catch (err) {
      console.error('Intelligence API error:', err);
      setError(err.response?.data?.detail || 'Failed to connect to repository intelligence API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeRepo) {
      fetchIntelligence();
    }
  }, [activeRepo?.repo_id]);

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
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to view its automated Repository Intelligence Dashboard.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Header Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Repository Intelligence Dashboard</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">
            {activeRepo.repo_name}
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Automated repository health, developer bus factor, file hotspots, logical coupling, and risk assessment.
          </p>
        </div>

        <button
          onClick={fetchIntelligence}
          disabled={loading}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition shadow-sm self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Re-analyze Intelligence</span>
        </button>
      </div>

      {/* Loading Skeleton */}
      {loading && <IntelligenceSkeleton />}

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

      {/* Main Dashboard Cards */}
      {!loading && !error && data && (
        <div className="space-y-6 animate-fadeIn">
          {/* 1. AI Executive Summary Banner */}
          <AIRepositorySummaryCard
            summary={data.summary}
            repoName={activeRepo.repo_name}
            healthScore={data.health_score}
            riskLevel={data.risk_level}
          />

          {/* 2. Health & Statistics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RepositoryHealthCard
              healthScore={data.health_score}
              riskLevel={data.risk_level}
              recommendation={data.recommendation}
            />
            <RepositoryStatisticsCard statistics={data.statistics} />
          </div>

          {/* 3. Developer Contribution Analytics (Recharts) */}
          <DeveloperAnalyticsCard developers={data.developers} />

          {/* 4. Code Hotspots & Churn Heatmap */}
          <HotspotCard hotspots={data.hotspots} />

          {/* 5. Co-Evolving Files & Risk Assessment Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <CoEvolvingFilesCard coEvolvingFiles={data.co_evolving_files} />
            <RiskAssessmentCard riskAssessment={data.risk_assessment} />
          </div>
        </div>
      )}
    </div>
  );
}
