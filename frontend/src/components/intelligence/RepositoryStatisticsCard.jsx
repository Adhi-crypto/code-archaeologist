import React from 'react';
import { GitCommit, Users, FileCode, Calendar, TrendingUp, Layers, Zap, Clock } from 'lucide-react';

export default function RepositoryStatisticsCard({ statistics }) {
  if (!statistics) return null;

  const statItems = [
    { label: 'Total Commits', value: statistics.total_commits, icon: GitCommit, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Total Contributors', value: statistics.total_authors, icon: Users, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Indexed Files', value: statistics.total_files, icon: FileCode, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Repository Lifespan', value: `${statistics.repo_age_months || 1} months`, icon: Calendar, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Avg Commits / Month', value: statistics.avg_commits_per_month, icon: TrendingUp, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Avg Commit Size', value: `+${statistics.avg_commit_size} lines`, icon: Zap, color: 'text-rose-600', bg: 'bg-rose-50' },
    { label: 'Avg Files / Commit', value: statistics.avg_files_modified, icon: Layers, color: 'text-teal-600', bg: 'bg-teal-50' },
    { label: 'Last Commit Activity', value: statistics.last_activity_date, icon: Clock, color: 'text-slate-600', bg: 'bg-slate-100' },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <h3 className="text-base font-bold text-slate-900 mb-4 border-b border-slate-100 pb-3">
        Repository Vital Statistics
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${item.bg} ${item.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider truncate">{item.label}</p>
                <p className="text-base font-bold text-slate-900 truncate">{item.value}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
