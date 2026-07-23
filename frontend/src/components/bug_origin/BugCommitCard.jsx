import React, { useState } from 'react';
import { GitCommit, Copy, Check, ExternalLink, Calendar, User, Layers, FileCode, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

export default function BugCommitCard({ commit, repoUrl, isPrimary = true }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopySha = () => {
    if (!commit.sha) return;
    navigator.clipboard.writeText(commit.sha);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Build GitHub Commit Link if public URL available
  const getGithubUrl = () => {
    if (!repoUrl) return null;
    const cleanUrl = repoUrl.replace(/\.git$/, '').replace(/\/$/, '');
    return `${cleanUrl}/commit/${commit.sha}`;
  };

  const githubUrl = getGithubUrl();

  return (
    <div className={`rounded-xl border shadow-sm transition-all overflow-hidden ${
      isPrimary
        ? 'bg-white border-rose-300 ring-2 ring-rose-100'
        : 'bg-white border-slate-200 hover:border-slate-300'
    }`}>
      {/* Primary Banner Header */}
      {isPrimary && (
        <div className="bg-gradient-to-r from-rose-600 to-amber-600 text-white px-5 py-2.5 flex items-center justify-between text-xs font-semibold">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-200 animate-pulse" />
            <span>PRIMARY SUSPECTED BUG ORIGIN COMMIT</span>
          </div>
          <span className="bg-white/20 backdrop-blur px-2.5 py-0.5 rounded-full font-mono text-white">
            Confidence: {commit.confidence}%
          </span>
        </div>
      )}

      <div className="p-5">
        {/* Commit Header Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-slate-100 text-slate-900 border border-slate-200">
              {commit.sha}
            </span>
            <button
              onClick={handleCopySha}
              className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded transition"
              title="Copy SHA"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
            {githubUrl && (
              <a
                href={githubUrl}
                target="_blank"
                rel="noreferrer"
                className="p-1 text-slate-400 hover:text-emerald-600 hover:bg-slate-100 rounded transition"
                title="View on GitHub"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <Calendar className="w-3.5 h-3.5" />
              <span>{commit.date}</span>
            </div>
            <span className="text-slate-300">•</span>
            <div className="flex items-center gap-1 text-xs text-slate-600 font-medium">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span>{commit.author}</span>
            </div>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2">
            {commit.architecture_change && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                <Layers className="w-3 h-3 text-amber-600" />
                Arch Impact
              </span>
            )}
            {!isPrimary && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                Score: {commit.confidence}%
              </span>
            )}
          </div>
        </div>

        {/* Commit Message */}
        <h3 className="text-base font-bold text-slate-900 leading-snug mb-2">
          {commit.message}
        </h3>

        {/* Reason snippet */}
        {commit.reason && (
          <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 mb-3">
            <strong className="text-slate-700 font-semibold">Forensic Finding: </strong>
            {commit.reason}
          </p>
        )}

        {/* Footer Diff Stats */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-3">
            <span className="text-slate-500">
              <strong className="text-slate-800">{commit.files?.length || 0}</strong> files changed
            </span>
            <span className="text-emerald-600 font-medium">+{commit.additions || 0}</span>
            <span className="text-rose-600 font-medium">-{commit.deletions || 0}</span>
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 font-medium text-emerald-600 hover:text-emerald-700 transition"
          >
            <span>{expanded ? 'Hide Scope' : 'Inspect File Scope'}</span>
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Expandable File List */}
        {expanded && commit.files && commit.files.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-700 mb-1.5">Affected File Paths:</p>
            <div className="bg-slate-50 rounded-lg p-2.5 space-y-1 max-h-40 overflow-y-auto border border-slate-200 font-mono text-xs">
              {commit.files.map((file, i) => (
                <div key={i} className="flex items-center gap-2 text-slate-700 py-0.5 px-1 hover:bg-white rounded">
                  <FileCode className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span className="truncate">{file}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
