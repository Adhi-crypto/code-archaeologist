import React from 'react';
import { Flame, FileCode, Layers, AlertCircle } from 'lucide-react';

export default function HotspotCard({ hotspots = [] }) {
  if (!hotspots || hotspots.length === 0) return null;

  const getRiskBadge = (level) => {
    switch (level) {
      case 'Critical':
        return 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
      case 'High':
        return 'bg-amber-100 text-amber-800 border-amber-300 font-bold';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300 font-medium';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200 font-medium';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-amber-500" />
          <h3 className="text-base font-bold text-slate-900">Code Hotspot & Churn Risk Heatmap</h3>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
          Ranked by Churn & Change Frequency
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider bg-slate-50/50">
              <th className="py-2.5 px-3">File Path</th>
              <th className="py-2.5 px-3">Revisions</th>
              <th className="py-2.5 px-3">Contributors</th>
              <th className="py-2.5 px-3">Line Churn</th>
              <th className="py-2.5 px-3">Risk Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {hotspots.map((item, idx) => (
              <tr key={idx} className="hover:bg-slate-50/80 transition">
                <td className="py-2.5 px-3 font-mono text-slate-800 flex items-center gap-2 max-w-md truncate">
                  <FileCode className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span className="truncate" title={item.file}>{item.file}</span>
                  {item.is_architecture && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 flex-shrink-0">
                      Arch Core
                    </span>
                  )}
                </td>
                <td className="py-2.5 px-3 font-bold text-slate-900">{item.change_count}</td>
                <td className="py-2.5 px-3 text-slate-600">{item.authors_count} authors</td>
                <td className="py-2.5 px-3 font-mono text-slate-700">+{item.total_churn} lines</td>
                <td className="py-2.5 px-3">
                  <span className={`px-2.5 py-0.5 rounded-full border text-[11px] ${getRiskBadge(item.risk_level)}`}>
                    {item.risk_level}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
