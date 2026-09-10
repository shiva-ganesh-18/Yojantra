import React from 'react';
import { 
  X, CheckCircle2, XCircle, AlertCircle, IndianRupee, ShieldCheck, 
  ArrowRight, ExternalLink, Scale, Sparkles, Building, Landmark
} from 'lucide-react';

export default function SchemeCompareModal({ 
  compareData, 
  isOpen, 
  onClose,
  onSelectScheme
}) {
  if (!isOpen || !compareData || !compareData.schemes || compareData.schemes.length === 0) return null;

  const { schemes, common_criteria, differing_features, recommendation_summary } = compareData;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gov-navy-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 sm:py-8 animate-in fade-in duration-200">
      <div 
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden text-gov-navy-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-gov-navy-900 via-gov-navy-800 to-gov-navy-900 text-white p-5 sm:p-6 relative border-b border-gov-navy-700/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-2xl bg-gov-saffron-500/20 text-gov-saffron-400 border border-gov-saffron-400/30">
              <Scale size={24} />
            </span>
            <div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                Side-by-Side Scheme Comparison
              </h2>
              <p className="text-xs text-slate-300 mt-0.5">
                Comparing {schemes.length} schemes side-by-side with your personalized eligibility profile.
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            aria-label="Close dialog"
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Comparison Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6 custom-scrollbar text-left">
          
          {/* AI Recommendation Summary Box */}
          {recommendation_summary && (
            <div className="bg-gradient-to-r from-gov-saffron-50/80 to-amber-50/60 border border-gov-saffron-200 rounded-2xl p-4 sm:p-5 flex items-start gap-3.5">
              <Sparkles size={20} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-gov-saffron-900">
                  Yojantra AI Comparative Verdict
                </h4>
                <p className="text-xs sm:text-sm text-slate-800 mt-1 leading-relaxed">
                  {recommendation_summary}
                </p>
              </div>
            </div>
          )}

          {/* Scheme Cards Grid */}
          <div className={`grid grid-cols-1 md:grid-cols-${Math.min(schemes.length, 3)} gap-4`}>
            {schemes.map((item) => {
              const m = item.match_data || {};
              const s = item.scheme || {};
              const loan = m.loan_recommendation || {};
              const verdict = m.overall_verdict || 'PASS';

              const isPass = verdict === 'PASS';
              const isUnknown = verdict === 'UNKNOWN';

              return (
                <div 
                  key={s.id} 
                  className="bg-slate-50/70 border border-slate-200 rounded-3xl p-5 flex flex-col justify-between space-y-4 shadow-xs"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 truncate max-w-[180px]">
                        {s.ministry || 'Govt of India'}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-black border ${
                        isPass 
                          ? 'bg-gov-emerald-100 text-gov-emerald-800 border-gov-emerald-300' 
                          : isUnknown 
                          ? 'bg-amber-100 text-amber-900 border-amber-300' 
                          : 'bg-red-100 text-red-800 border-red-300'
                      }`}>
                        {verdict}
                      </span>
                    </div>

                    <h3 className="text-base font-extrabold text-gov-navy-950 line-clamp-2">
                      {s.name}
                    </h3>

                    {/* Score Bar */}
                    <div className="bg-white p-3 rounded-2xl border border-slate-200 flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-600">Match Score</span>
                      <span className="text-sm font-black text-gov-navy-950">
                        {m.match_score || 85}%
                      </span>
                    </div>

                    {/* Financial Metrics */}
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between border-b border-slate-200/60 pb-1.5">
                        <span className="text-slate-500 font-medium">Max Benefit</span>
                        <span className="font-bold text-slate-900">
                          {s.max_benefit_inr ? `₹${Number(s.max_benefit_inr).toLocaleString('en-IN')}` : 'Not Capped'}
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-slate-200/60 pb-1.5">
                        <span className="text-slate-500 font-medium">Subsidy Est.</span>
                        <span className="font-bold text-gov-emerald-700">
                          {loan.estimated_subsidy_amount ? `₹${Number(loan.estimated_subsidy_amount).toLocaleString('en-IN')} (${loan.subsidy_percentage}%)` : '0%'}
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-slate-200/60 pb-1.5">
                        <span className="text-slate-500 font-medium">Margin Money (5-10%)</span>
                        <span className="font-bold text-slate-800">
                          {loan.margin_money_required ? `₹${Number(loan.margin_money_required).toLocaleString('en-IN')}` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-slate-200/60 pb-1.5">
                        <span className="text-slate-500 font-medium">Monthly EMI Est.</span>
                        <span className="font-bold text-gov-saffron-700">
                          {loan.estimated_monthly_emi ? `₹${Number(loan.estimated_monthly_emi).toLocaleString('en-IN')}/mo` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between pb-1">
                        <span className="text-slate-500 font-medium">Collateral</span>
                        <span className="font-bold text-slate-800">
                          {s.collateral_required ? 'Required' : 'Collateral-Free (CGTMSE)'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      onClose();
                      if (onSelectScheme) onSelectScheme(m || s);
                    }}
                    className="w-full py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                  >
                    <span>View Scheme Details</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Detailed Criteria Audit Comparison Table */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
              <ShieldCheck size={16} className="text-gov-navy-700" />
              <span>Comparative Feature Breakdown</span>
            </h4>

            <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
                    <th className="p-3 sm:p-4 w-1/3">Feature / Parameter</th>
                    {schemes.map(it => (
                      <th key={it.scheme.id} className="p-3 sm:p-4 text-gov-navy-950 font-extrabold truncate max-w-[200px]">
                        {it.scheme.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {differing_features.map((feat, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="p-3 sm:p-4 font-semibold text-slate-700 bg-slate-50/30">
                        {feat.feature}
                      </td>
                      {schemes.map(it => (
                        <td key={it.scheme.id} className="p-3 sm:p-4 text-slate-800 font-medium">
                          {feat.values[strOrId(it.scheme.id)] || 'N/A'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Common Baseline Criteria */}
          {common_criteria && common_criteria.length > 0 && (
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Shared Eligibility Baseline
              </p>
              <div className="flex flex-wrap gap-2">
                {common_criteria.map((crit, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1.5 text-xs bg-white px-3 py-1.5 rounded-xl border border-slate-200 text-slate-700">
                    <CheckCircle2 size={13} className="text-gov-emerald-600" />
                    <span>{crit}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-4 sm:p-5 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs sm:text-sm transition-colors"
          >
            Close Comparison
          </button>
        </div>

      </div>
    </div>
  );
}

function strOrId(val) {
  return String(val);
}
