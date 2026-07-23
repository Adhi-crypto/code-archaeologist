import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function ConfidenceGauge({ score }) {
  // Score percentage 0 - 100
  const normalizedScore = Math.min(100, Math.max(0, score || 0));
  
  const getScoreColor = (val) => {
    if (val >= 75) return { text: 'text-emerald-500', bg: 'bg-emerald-500', ring: 'ring-emerald-100', border: 'border-emerald-200', icon: ShieldCheck, label: 'High Grounding Confidence' };
    if (val >= 50) return { text: 'text-amber-500', bg: 'bg-amber-500', ring: 'ring-amber-100', border: 'border-amber-200', icon: AlertTriangle, label: 'Moderate Confidence' };
    return { text: 'text-rose-500', bg: 'bg-rose-500', ring: 'ring-rose-100', border: 'border-rose-200', icon: ShieldAlert, label: 'Low Confidence (Multiple Candidates)' };
  };

  const status = getScoreColor(normalizedScore);
  const Icon = status.icon;

  return (
    <div className={`bg-white rounded-xl border ${status.border} p-5 shadow-sm flex items-center gap-5`}>
      {/* Circular Meter SVG */}
      <div className="relative w-20 h-20 flex-shrink-0 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-slate-100"
            strokeWidth="3.5"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            className={`${status.text} transition-all duration-1000 ease-out`}
            strokeDasharray={`${normalizedScore}, 100`}
            strokeWidth="3.5"
            strokeLinecap="round"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className={`text-xl font-bold font-mono ${status.text}`}>{normalizedScore}%</span>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-1.5 mb-1">
          <Icon className={`w-4 h-4 ${status.text}`} />
          <h4 className="text-sm font-bold text-slate-900">{status.label}</h4>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed max-w-sm">
          Quantitative multi-factor score evaluated across semantic similarity (40%), file scope match (20%), recency (15%), architecture impact (10%), commit churn (10%), and developer activity (5%).
        </p>
      </div>
    </div>
  );
}
