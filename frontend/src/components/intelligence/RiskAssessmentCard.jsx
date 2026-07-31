import React from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';

export default function RiskAssessmentCard({ riskAssessment }) {
  if (!riskAssessment) return null;

  const risks = [
    { label: 'Technical Debt Indicator', score: riskAssessment.technical_debt, desc: 'Uncontrolled churn and large diff size index' },
    { label: 'Architecture Stability', score: riskAssessment.architecture_stability, desc: 'Structural file modification balance', isPositive: true },
    { label: 'Maintenance Risk Level', score: riskAssessment.maintenance_risk, desc: 'Single contributor & ownership risk' },
    { label: 'Bug Propagation Risk', score: riskAssessment.bug_risk, desc: 'Critical hotspot overlap and churn density' },
  ];

  const getScoreColor = (val, isPositive) => {
    if (isPositive) {
      if (val >= 75) return 'bg-emerald-500 text-emerald-700 border-emerald-200';
      if (val >= 50) return 'bg-amber-500 text-amber-700 border-amber-200';
      return 'bg-rose-500 text-rose-700 border-rose-200';
    }
    if (val <= 35) return 'bg-emerald-500 text-emerald-700 border-emerald-200';
    if (val <= 65) return 'bg-amber-500 text-amber-700 border-amber-200';
    return 'bg-rose-500 text-rose-700 border-rose-200';
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-600" />
          <h3 className="text-base font-bold text-slate-900">Multi-Factor Risk Assessment Gauges</h3>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
          Bus Factor: {riskAssessment.bus_factor_score} Key Contributors
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {risks.map((item, idx) => (
          <div key={idx} className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800">{item.label}</h4>
              <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${getScoreColor(item.score, item.isPositive)}`}>
                {item.score}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-1000 ${
                  item.isPositive
                    ? item.score >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
                    : item.score >= 60 ? 'bg-rose-500' : 'bg-amber-500'
                }`}
                style={{ width: `${item.score}%` }}
              />
            </div>

            <p className="text-[11px] text-slate-500">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
