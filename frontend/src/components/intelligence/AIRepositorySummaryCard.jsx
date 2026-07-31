import React from 'react';
import { Sparkles, Activity, ShieldCheck } from 'lucide-react';

export default function AIRepositorySummaryCard({ summary, repoName, healthScore, riskLevel }) {
  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 text-white rounded-xl border border-slate-700 shadow-xl overflow-hidden mb-6">
      <div className="p-6">
        <div className="flex flex-wrap items-center justify-between border-b border-slate-700/80 pb-4 mb-4 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-xl">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white">AI Executive Repository Report</h2>
              <p className="text-xs text-slate-300">Automated health & structural intelligence for <span className="font-semibold text-indigo-300">{repoName}</span></p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Health: {healthScore}/100
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
              riskLevel === 'Low'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : riskLevel === 'Medium'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
            }`}>
              {riskLevel} Risk
            </span>
          </div>
        </div>

        {/* Narrative Box */}
        <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
          {summary}
        </div>
      </div>
    </div>
  );
}
