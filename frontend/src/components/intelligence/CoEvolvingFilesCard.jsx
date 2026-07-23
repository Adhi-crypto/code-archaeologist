import React from 'react';
import { GitMerge, ArrowRight, FileCode } from 'lucide-react';

export default function CoEvolvingFilesCard({ coEvolvingFiles = [] }) {
  if (!coEvolvingFiles || coEvolvingFiles.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <GitMerge className="w-5 h-5 text-indigo-600" />
          <h3 className="text-base font-bold text-slate-900">Co-Evolving Files (Logical Coupling Graph)</h3>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
          Implicit Module Dependencies
        </span>
      </div>

      <p className="text-xs text-slate-500 mb-4">
        Files that frequently change together across historical commits represent strong architectural coupling.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {coEvolvingFiles.map((pair, idx) => (
          <div key={idx} className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-1 overflow-hidden font-mono text-xs text-slate-800">
              <FileCode className="w-3.5 h-3.5 text-indigo-500 flex-shrink-0" />
              <span className="truncate" title={pair.source}>{pair.source}</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate" title={pair.target}>{pair.target}</span>
            </div>

            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold">
                {pair.co_commit_count} shared commits
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
