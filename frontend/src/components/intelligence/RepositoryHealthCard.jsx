import React from 'react';
import { HeartPulse, ShieldCheck, ShieldAlert, AlertTriangle, Lightbulb } from 'lucide-react';

export default function RepositoryHealthCard({ healthScore, riskLevel, recommendation }) {
  const score = Math.min(100, Math.max(0, healthScore || 0));

  const getTheme = (val) => {
    if (val >= 80) return { text: 'text-emerald-500', bg: 'bg-emerald-500', border: 'border-emerald-200', bgLight: 'bg-emerald-50', icon: ShieldCheck, label: 'Optimal Architecture' };
    if (val >= 60) return { text: 'text-amber-500', bg: 'bg-amber-500', border: 'border-amber-200', bgLight: 'bg-amber-50', icon: AlertTriangle, label: 'Moderate Maintenance Risk' };
    return { text: 'text-rose-500', bg: 'bg-rose-500', border: 'border-rose-200', bgLight: 'bg-rose-50', icon: ShieldAlert, label: 'High Technical Debt Risk' };
  };

  const theme = getTheme(score);
  const Icon = theme.icon;

  return (
    <div className={`bg-white rounded-xl border ${theme.border} p-6 shadow-sm flex flex-col justify-between`}>
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <HeartPulse className="w-5 h-5 text-rose-500" />
          <h3 className="text-base font-bold text-slate-900">Repository Health Index</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${theme.bgLight} ${theme.text} ${theme.border}`}>
          {riskLevel} Risk Level
        </span>
      </div>

      <div className="flex items-center gap-6 my-2">
        {/* Radial Meter */}
        <div className="relative w-24 h-24 flex-shrink-0 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-slate-100"
              strokeWidth="3.5"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className={`${theme.text} transition-all duration-1000 ease-out`}
              strokeDasharray={`${score}, 100`}
              strokeWidth="3.5"
              strokeLinecap="round"
              stroke="currentColor"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center">
            <span className={`text-2xl font-black font-mono ${theme.text}`}>{score}</span>
            <span className="text-[10px] text-slate-400 font-semibold uppercase">/100</span>
          </div>
        </div>

        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-1.5">
            <Icon className={`w-4 h-4 ${theme.text}`} />
            <h4 className="text-sm font-bold text-slate-800">{theme.label}</h4>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Evaluation factors include commit consistency, code churn, developer ownership balance, and structural hotspot stability.
          </p>
        </div>
      </div>

      {/* Recommendation Footer */}
      {recommendation && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-start gap-2 text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200">
          <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p><strong className="font-semibold text-slate-800">Recommendation: </strong>{recommendation}</p>
        </div>
      )}
    </div>
  );
}
