import React, { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp, Layers, GitCommit, ShieldCheck, Zap } from 'lucide-react';

export default function NarrativeCard({ narrative, repoName, totalCommits, sampledCommits, archCount }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 text-white rounded-xl border border-slate-700 shadow-xl overflow-hidden mb-6">
      <div className="p-6">
        <div className="flex items-center justify-between border-b border-slate-700/80 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight text-white">AI Repository Evolution Narrative</h2>
              <p className="text-xs text-slate-300">Synthesized architectural milestones for <span className="font-semibold text-emerald-300">{repoName}</span></p>
            </div>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600 transition"
          >
            {expanded ? (
              <>
                <span>Collapse Narrative</span>
                <ChevronUp className="w-4 h-4" />
              </>
            ) : (
              <>
                <span>Expand Narrative</span>
                <ChevronDown className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/60 rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase font-medium tracking-wider">Total Commits</p>
              <p className="text-lg font-bold text-white">{totalCommits}</p>
            </div>
          </div>

          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/60 rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase font-medium tracking-wider">Arch Milestones</p>
              <p className="text-lg font-bold text-amber-300">{archCount}</p>
            </div>
          </div>

          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/60 rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase font-medium tracking-wider">Sampled Points</p>
              <p className="text-lg font-bold text-purple-300">{sampledCommits}</p>
            </div>
          </div>

          <div className="bg-slate-800/60 backdrop-blur border border-slate-700/60 rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase font-medium tracking-wider">Analysis Status</p>
              <p className="text-sm font-semibold text-emerald-400">Complete</p>
            </div>
          </div>
        </div>

        {/* Narrative Text */}
        {expanded && (
          <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
            {narrative}
          </div>
        )}
      </div>
    </div>
  );
}
