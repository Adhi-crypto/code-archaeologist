import React from 'react';
import { Search, Filter, ArrowUpDown, User, FileText, Layers, RotateCcw } from 'lucide-react';

export default function TimelineFilters({
  searchTerm,
  setSearchTerm,
  selectedAuthor,
  setSelectedAuthor,
  authorsList,
  selectedFile,
  setSelectedFile,
  archOnly,
  setArchOnly,
  sortOrder,
  setSortOrder,
  totalCount,
  filteredCount,
  onResetFilters,
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6 space-y-3">
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search commits by message, SHA, or keywords..."
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {/* Sort order toggle */}
        <button
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="flex items-center justify-center gap-2 px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 transition bg-white"
        >
          <ArrowUpDown className="w-4 h-4 text-emerald-600" />
          <span>Order: {sortOrder === 'asc' ? 'Oldest → Newest' : 'Newest → Oldest'}</span>
        </button>

        {/* Architecture change toggle button */}
        <button
          onClick={() => setArchOnly(!archOnly)}
          className={`flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium border transition ${
            archOnly
              ? 'bg-amber-500 text-white border-amber-600 shadow-sm'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Arch Changes Only</span>
        </button>
      </div>

      {/* Second Row: Filters for Author & File */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
        {/* Author filter */}
        <div className="relative">
          <User className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedAuthor}
            onChange={(e) => setSelectedAuthor(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
          >
            <option value="">All Authors ({authorsList.length})</option>
            {authorsList.map((author) => (
              <option key={author} value={author}>
                {author}
              </option>
            ))}
          </select>
        </div>

        {/* File filter input */}
        <div className="relative">
          <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            placeholder="Filter by file path (e.g. routes, main)..."
            className="w-full pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {/* Result Counter & Reset Button */}
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-slate-500 font-medium">
            Showing <strong className="text-slate-900">{filteredCount}</strong> of {totalCount} events
          </span>
          {(searchTerm || selectedAuthor || selectedFile || archOnly) && (
            <button
              onClick={onResetFilters}
              className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium transition"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Filters
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
