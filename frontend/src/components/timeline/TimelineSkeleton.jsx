import React from 'react';

export default function TimelineSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="h-6 bg-slate-200 rounded w-1/3"></div>
        <div className="h-4 bg-slate-100 rounded w-2/3"></div>
        <div className="grid grid-cols-4 gap-4 pt-2">
          <div className="h-16 bg-slate-100 rounded-lg"></div>
          <div className="h-16 bg-slate-100 rounded-lg"></div>
          <div className="h-16 bg-slate-100 rounded-lg"></div>
          <div className="h-16 bg-slate-100 rounded-lg"></div>
        </div>
      </div>

      {/* Filter bar skeleton */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex items-center justify-between gap-4">
        <div className="h-10 bg-slate-100 rounded-lg flex-1"></div>
        <div className="h-10 bg-slate-100 rounded-lg w-36"></div>
        <div className="h-10 bg-slate-100 rounded-lg w-36"></div>
      </div>

      {/* Timeline item skeletons */}
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex items-start gap-4">
            <div className="w-10 h-10 bg-slate-200 rounded-full flex-shrink-0"></div>
            <div className="flex-1 space-y-3">
              <div className="flex items-center justify-between">
                <div className="h-5 bg-slate-200 rounded w-1/4"></div>
                <div className="h-4 bg-slate-150 rounded w-20"></div>
              </div>
              <div className="h-4 bg-slate-100 rounded w-3/4"></div>
              <div className="flex items-center gap-3">
                <div className="h-6 bg-slate-100 rounded-full w-24"></div>
                <div className="h-6 bg-slate-100 rounded-full w-20"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
