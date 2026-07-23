import React from 'react';
import { GitCommit, AlertTriangle, ShieldCheck, ArrowRight, Layers } from 'lucide-react';

export default function BugTimelineVisualizer({ likelyCommit, supportingCommits = [] }) {
  if (!likelyCommit) return null;

  // Build timeline order (Chronological order)
  const allEvents = [...supportingCommits, likelyCommit].sort((a, b) => (a.timestamp_unix || 0) - (b.timestamp_unix || 0));

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-5">
        <div>
          <h3 className="text-base font-bold text-slate-900">Regression Timeline Propagation</h3>
          <p className="text-xs text-slate-500">Visual mapping from historical context to suspected bug introduction</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
          Flow Direction: Past → HEAD
        </span>
      </div>

      {/* Horizontal Flow Line Diagram */}
      <div className="flex items-center justify-between gap-2 overflow-x-auto py-4 px-2 scrollbar-thin">
        {allEvents.map((evt, idx) => {
          const isSuspected = evt.sha === likelyCommit.sha;
          return (
            <React.Fragment key={evt.sha || idx}>
              {/* Event Node Box */}
              <div className={`flex flex-col items-center flex-shrink-0 w-44 p-3 rounded-xl border transition-all ${
                isSuspected
                  ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-200 text-rose-950 scale-105 shadow-md'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 shadow-sm ${
                  isSuspected
                    ? 'bg-rose-600 text-white ring-4 ring-rose-100 animate-pulse'
                    : 'bg-white text-slate-600 border border-slate-300'
                }`}>
                  {isSuspected ? <AlertTriangle className="w-4 h-4" /> : <GitCommit className="w-4 h-4" />}
                </div>

                <span className="font-mono text-xs font-bold truncate max-w-full">
                  {evt.sha}
                </span>

                <span className="text-[10px] text-slate-400 mt-0.5">{evt.date}</span>

                <p className="text-xs font-medium text-center truncate max-w-full mt-1.5 font-sans">
                  {evt.message}
                </p>

                {isSuspected ? (
                  <span className="mt-2 text-[10px] font-bold bg-rose-600 text-white px-2 py-0.5 rounded-full">
                    Suspected Bug Origin
                  </span>
                ) : (
                  <span className="mt-2 text-[10px] font-medium text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                    Supporting Commit
                  </span>
                )}
              </div>

              {/* Arrow separator */}
              {idx < allEvents.length - 1 && (
                <ArrowRight className="w-5 h-5 text-slate-300 flex-shrink-0" />
              )}
            </React.Fragment>
          );
        })}

        {/* Arrow to HEAD */}
        <ArrowRight className="w-5 h-5 text-slate-400 flex-shrink-0" />

        {/* HEAD Node */}
        <div className="flex flex-col items-center flex-shrink-0 w-32 p-3 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-950">
          <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center mb-2 shadow-sm">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <span className="font-mono text-xs font-bold">Current HEAD</span>
          <span className="text-[10px] text-emerald-700 mt-0.5">Active Repository</span>
        </div>
      </div>
    </div>
  );
}
