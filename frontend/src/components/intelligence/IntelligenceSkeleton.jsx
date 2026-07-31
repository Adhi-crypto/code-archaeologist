import React from 'react';

export default function IntelligenceSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Executive Summary Skeleton */}
      <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 space-y-4">
        <div className="h-6 bg-slate-700 rounded w-1/3"></div>
        <div className="h-4 bg-slate-800 rounded w-full"></div>
        <div className="h-4 bg-slate-800 rounded w-5/6"></div>
      </div>

      {/* Health & Statistics Row Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm h-48"></div>
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm h-48"></div>
      </div>

      {/* Developer & Hotspots Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm h-64"></div>
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm h-64"></div>
      </div>
    </div>
  );
}
