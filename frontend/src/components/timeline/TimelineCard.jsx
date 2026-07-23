import React, { useState } from 'react';
import { GitCommit, Calendar, User, ChevronDown, ChevronUp, FileCode, Layers, ShieldAlert, Sparkles } from 'lucide-react';

export default function TimelineCard({ event, isLast }) {
  const [expanded, setExpanded] = useState(false);

  const getImportanceBadge = (score) => {
    if (score >= 75) {
      return { label: 'High Impact', bg: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500' };
    } else if (score >= 45) {
      return { label: 'Medium Impact', bg: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500' };
    }
    return { label: 'Low Impact', bg: 'bg-slate-50 text-slate-600 border-slate-200', dot: 'bg-slate-400' };
  };

  const importanceInfo = getImportanceBadge(event.importance_score || 0);

  return (
    <div className="relative flex items-start gap-4 group">
      {/* Timeline Connecting Line */}
      {!isLast && (
        <div className="absolute left-5 top-10 bottom-0 w-0.5 bg-slate-200 group-hover:bg-emerald-300 transition-colors"></div>
      )}

      {/* Timeline Node Icon */}
      <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 shadow-sm ${
        event.is_architecture_change
          ? 'bg-amber-500 text-white border-amber-600 ring-4 ring-amber-100 group-hover:scale-110'
          : 'bg-white text-slate-700 border-slate-300 group-hover:border-emerald-500 group-hover:text-emerald-600 group-hover:scale-105'
      }`}>
        {event.is_architecture_change ? (
          <Layers className="w-5 h-5" />
        ) : (
          <GitCommit className="w-5 h-5" />
        )}
      </div>

      {/* Card Content Container */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 mb-6 overflow-hidden">
        {/* Card Header */}
        <div className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                {event.sha}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Calendar className="w-3.5 h-3.5" />
                <span>{event.date}</span>
              </div>
              <span className="text-xs text-slate-400">•</span>
              <div className="flex items-center gap-1 text-xs text-slate-600 font-medium">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>{event.author}</span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-2">
              {event.is_architecture_change && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                  <Sparkles className="w-3 h-3 text-amber-600" />
                  {event.impact_type || 'Arch Change'}
                </span>
              )}
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${importanceInfo.bg}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${importanceInfo.dot}`}></span>
                Score: {event.importance_score || 0}
              </span>
            </div>
          </div>

          {/* Commit Message */}
          <h3 className="text-base font-semibold text-slate-900 group-hover:text-emerald-600 transition-colors leading-snug">
            {event.message}
          </h3>

          {/* Diff Stats summary */}
          <div className="mt-3 flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
            <div className="flex items-center gap-3">
              <span className="text-slate-500">
                <strong className="text-slate-800">{event.files?.length || 0}</strong> files changed
              </span>
              <span className="text-emerald-600 font-medium">+{event.additions || 0}</span>
              <span className="text-rose-600 font-medium">-{event.deletions || 0}</span>
            </div>

            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 transition"
            >
              <span>{expanded ? 'Hide Details' : 'View Details & Files'}</span>
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Expandable Section */}
        {expanded && (
          <div className="bg-slate-50 p-5 border-t border-slate-200 text-xs space-y-4 animate-fadeIn">
            {/* Impact Explanation */}
            <div>
              <p className="font-semibold text-slate-700 mb-1">Impact Analysis:</p>
              <p className="text-slate-600 bg-white p-3 rounded-lg border border-slate-200 leading-relaxed">
                {event.explanation}
              </p>
            </div>

            {/* Changed Files List */}
            {event.files && event.files.length > 0 && (
              <div>
                <p className="font-semibold text-slate-700 mb-1.5">Modified Files ({event.files.length}):</p>
                <div className="bg-white rounded-lg border border-slate-200 p-2.5 space-y-1 max-h-48 overflow-y-auto">
                  {event.files.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-2 font-mono text-slate-700 py-0.5 hover:bg-slate-50 px-1 rounded">
                      <FileCode className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                      <span className="truncate">{file}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
