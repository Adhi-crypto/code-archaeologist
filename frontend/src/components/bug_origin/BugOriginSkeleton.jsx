import React from 'react';

export default function BugOriginSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Gauge skeleton */}
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-center gap-5">
        <div className="w-20 h-20 bg-slate-200 rounded-full flex-shrink-0"></div>
        <div className="flex-1 space-y-2">
          <div className="h-5 bg-slate-200 rounded w-1/3"></div>
          <div className="h-4 bg-slate-100 rounded w-3/4"></div>
        </div>
      </div>

      {/* Timeline flow skeleton */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="h-5 bg-slate-200 rounded w-1/4"></div>
        <div className="flex items-center gap-4 overflow-hidden py-2">
          <div className="w-40 h-28 bg-slate-100 rounded-xl flex-shrink-0"></div>
          <div className="w-40 h-28 bg-slate-100 rounded-xl flex-shrink-0"></div>
          <div className="w-40 h-28 bg-slate-200 rounded-xl flex-shrink-0"></div>
          <div className="w-32 h-28 bg-slate-100 rounded-xl flex-shrink-0"></div>
        </div>
      </div>

      {/* Primary Bug Commit Skeleton */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="h-6 bg-slate-200 rounded w-1/3"></div>
        <div className="h-5 bg-slate-200 rounded w-2/3"></div>
        <div className="h-16 bg-slate-100 rounded-lg"></div>
      </div>

      {/* LLM Reasoning Skeleton */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-3">
        <div className="h-5 bg-slate-200 rounded w-1/4"></div>
        <div className="h-4 bg-slate-100 rounded w-full"></div>
        <div className="h-4 bg-slate-100 rounded w-5/6"></div>
        <div className="h-4 bg-slate-100 rounded w-4/6"></div>
      </div>
    </div>
  );
}
