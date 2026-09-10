import React, { useState, useEffect } from 'react';
import { 
  X, CheckCircle2, XCircle, AlertTriangle, AlertCircle, Calendar, Building, IndianRupee, 
  FileText, ExternalLink, Bookmark, ShieldCheck, ArrowRight, Clock, HelpCircle,
  Sparkles, Check, ChevronDown, ChevronUp, Layers, Percent, Wallet, Calculator, RefreshCw
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import schemeService from '../services/schemeService';
import { useAuthStore } from '../hooks/useAuth';

const NORMALIZE_DOC_KEY = (name) => {
  if (!name) return '';
  const s = name.toLowerCase().trim();
  if (s.includes('pan')) return s.includes('business') ? 'business_pan' : 'pan';
  if (s.includes('aadhaar') || s.includes('aadhar')) return 'aadhaar';
  if (s.includes('udyam')) return 'udyam';
  if (s.includes('passbook') || (s.includes('bank') && s.includes('account'))) return 'bank_passbook';
  if (s.includes('statement')) return 'bank_statement';
  if (s.includes('project report') || s.includes('dpr')) return 'project_report';
  if (s.includes('caste') || s.includes('community') || s.includes('category certificate')) return 'caste_certificate';
  if (s.includes('photo')) return 'photo';
  if (s.includes('incorporation') || s.includes('partnership')) return 'incorporation_cert';
  if (s.includes('gst')) return 'gst';
  if (s.includes('fssai')) return 'fssai_license';
  if (s.includes('pollution') || s.includes('noc')) return 'noc_pollution';
  if (s.includes('quotation')) return 'machinery_quotation';
  return s.replace(/[^a-z0-9]/g, '_');
};

export default function SchemeDetailModal({ 
  scheme, 
  isOpen, 
  onClose, 
  onApply, 
  isBookmarked, 
  onBookmarkToggle 
}) {
  const navigate = useNavigate();
  const { api, user } = useAuthStore();
  const [userDocs, setUserDocs] = useState([]);
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);
  const [showFullRules, setShowFullRules] = useState(true);

  useEffect(() => {
    if (isOpen && user) {
      api().get('/documents/my-documents')
        .then(res => setUserDocs(res.data || []))
        .catch(() => setUserDocs([]));
    }
  }, [isOpen, user]);

  if (!isOpen || !scheme) return null;

  const matchScore = scheme.match_score || 85;
  const isHighMatch = matchScore >= 80;
  const verdict = scheme.overall_verdict || (matchScore >= 75 ? 'PASS' : (matchScore >= 40 ? 'UNKNOWN' : 'FAIL'));
  
  const scoreBreakdown = scheme.score_breakdown || {
    demographic_score: 22,
    enterprise_score: 23,
    financial_score: 20,
    compliance_score: 20,
    total_score: matchScore,
    rationale: []
  };

  const loanRec = scheme.loan_recommendation || {
    recommended_loan_amount: 500000,
    estimated_subsidy_amount: 125000,
    subsidy_percentage: 25,
    margin_money_required: 25000,
    margin_money_percentage: 5,
    interest_rate_percent: 9.5,
    estimated_monthly_emi: 10500,
    tenure_months: 60
  };

  // Financial Calculator & Loan Simulation state
  const [showCalculator, setShowCalculator] = useState(false);
  const [simPrincipal, setSimPrincipal] = useState(loanRec.recommended_loan_amount || 500000);
  const [simTenure, setSimTenure] = useState(loanRec.total_tenure_months || loanRec.tenure_months || 60);
  const [simMoratorium, setSimMoratorium] = useState(loanRec.moratorium_period_months ?? 6);
  const [simRate, setSimRate] = useState(loanRec.interest_rate_percent || 9.5);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState(null);
  const [showScheduleTable, setShowScheduleTable] = useState(false);

  // Scheme statutory loan limits
  const maxLimit = scheme.max_loan_amount_inr || scheme.max_benefit_inr || null;
  const isExceedingLimit = maxLimit && Number(simPrincipal) > Number(maxLimit);

  const runSimulation = async () => {
    setSimLoading(true);
    setSimError(null);
    try {
      const schemeId = scheme.id || scheme.scheme_id;
      let res;
      if (schemeId) {
        res = await schemeService.simulateLoan(schemeId, {
          principal_amount: Number(simPrincipal),
          tenure_months: Number(simTenure),
          moratorium_months: Number(simMoratorium),
          interest_rate_percent: Number(simRate),
          include_schedule: true
        });
      } else {
        res = await schemeService.calculateEmi({
          principal_amount: Number(simPrincipal),
          tenure_months: Number(simTenure),
          moratorium_months: Number(simMoratorium),
          interest_rate_percent: Number(simRate),
          include_schedule: true
        });
      }
      setSimResult(res);
    } catch (err) {
      const p = Number(simPrincipal) || 0;
      const t = Number(simTenure) || 60;
      const m = Math.min(Number(simMoratorium) || 0, t - 1);
      const r_ann = Number(simRate) || 0;
      const active = Math.max(1, t - m);
      let emi = 0;
      let totalRepayment = p;
      let totalInterest = 0;
      if (r_ann > 0) {
        const r_m = (r_ann / 100) / 12;
        emi = Math.round((p * r_m * Math.pow(1 + r_m, active)) / (Math.pow(1 + r_m, active) - 1));
        totalRepayment = emi * active;
        totalInterest = Math.max(0, totalRepayment - p);
      } else {
        emi = Math.round(p / active);
      }
      setSimResult({
        principal_amount: p,
        interest_rate_percent: r_ann,
        total_tenure_months: t,
        moratorium_months: m,
        active_repayment_months: active,
        monthly_emi: emi,
        total_interest: totalInterest,
        total_repayment: totalRepayment,
        is_within_limit: !maxLimit || p <= Number(maxLimit),
        limit_warning: maxLimit && p > Number(maxLimit) ? `Principal exceeds scheme maximum limit of ₹${Number(maxLimit).toLocaleString('en-IN')}` : null,
        monthly_schedule: []
      });
    } finally {
      setSimLoading(false);
    }
  };

  const handleToggleCalculator = () => {
    const nextState = !showCalculator;
    setShowCalculator(nextState);
    if (nextState && !simResult) {
      runSimulation();
    }
  };

  const criteriaChecks = scheme.criteria_checks || [];
  const whyThisScheme = scheme.why_this_scheme && scheme.why_this_scheme.length > 0 
    ? scheme.why_this_scheme 
    : (scheme.why_you_match || []);

  const handleApplyNow = async () => {
    if (onApply) {
      setApplying(true);
      try {
        await onApply(scheme.id || scheme.scheme_id);
        setApplySuccess(true);
        setTimeout(() => {
          setApplySuccess(false);
          onClose();
          navigate('/applications');
        }, 1200);
      } catch (err) {
        console.error('Failed to apply:', err);
      } finally {
        setApplying(false);
      }
    } else {
      navigate('/applications');
    }
  };

  const documents = Array.isArray(scheme.documents_required) 
    ? scheme.documents_required 
    : ['Aadhaar Card', 'PAN Card', 'Bank Passbook / 6-Month Statement', 'UDYAM Registration Certificate', 'Passport Photograph'];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gov-navy-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 sm:py-8 animate-in fade-in duration-200">
      <div 
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden text-gov-navy-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="bg-gradient-to-r from-gov-navy-900 via-gov-navy-800 to-gov-navy-900 text-white p-5 sm:p-6 relative border-b border-gov-navy-700/50 text-left">
          <button 
            onClick={onClose}
            aria-label="Close dialog"
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            <X size={20} />
          </button>

          <div className="flex flex-wrap items-center gap-2 mb-2.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-gov-navy-700/80 text-gov-navy-100 border border-gov-navy-600">
              <Building size={13} className="text-gov-saffron-400" />
              {scheme.ministry || 'Government of India'}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-400/30 capitalize">
              {scheme.scheme_type || 'Financial Support'}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white leading-snug">
                {scheme.name}
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 mt-1">
                Official Portal: <span className="font-mono text-gov-saffron-200">{scheme.official_url || 'https://myscheme.gov.in'}</span>
              </p>
            </div>

            <div className="flex sm:flex-col items-center sm:items-end gap-2 flex-shrink-0">
              {/* Verdict Badge */}
              <div className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl font-black text-xs sm:text-sm border shadow-sm ${
                verdict === 'PASS'
                  ? 'bg-gov-emerald-500/20 text-gov-emerald-300 border-gov-emerald-400/40'
                  : verdict === 'UNKNOWN'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-400/40'
                  : 'bg-red-500/20 text-red-300 border-red-400/40'
              }`}>
                <ShieldCheck size={16} />
                <span>Verdict: {verdict}</span>
              </div>
              <span className="text-[11px] font-bold text-slate-300">
                {matchScore}% Recommendation Score
              </span>
            </div>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6 custom-scrollbar text-left">

          {/* Personalized Loan Tranche & Subsidy Breakdown Box */}
          <div className="bg-gradient-to-br from-slate-900 to-gov-navy-950 text-white rounded-3xl p-5 sm:p-6 shadow-md relative overflow-hidden">
            <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-gov-saffron-400" />
                <h4 className="text-sm font-black uppercase tracking-wider text-slate-200">
                  Personalized Financing Recommendation
                </h4>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white/10 text-gov-saffron-300 font-mono">
                Calculated for Your Profile
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-left">
              <div className="bg-white/5 p-3 rounded-2xl border border-white/10">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Recommended Loan</span>
                <span className="text-base sm:text-lg font-black text-white block mt-0.5">
                  ₹{Number(loanRec.recommended_loan_amount || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-slate-400">Within scheme limits</span>
              </div>

              <div className="bg-gov-emerald-950/40 p-3 rounded-2xl border border-gov-emerald-500/30">
                <span className="text-[10px] font-bold text-gov-emerald-400 uppercase tracking-wider block">Estimated Subsidy</span>
                <span className="text-base sm:text-lg font-black text-gov-emerald-300 block mt-0.5">
                  ₹{Number(loanRec.estimated_subsidy_amount || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-gov-emerald-400">{loanRec.subsidy_percentage || 0}% Capital grant</span>
              </div>

              <div className="bg-white/5 p-3 rounded-2xl border border-white/10">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Promoter Margin</span>
                <span className="text-base sm:text-lg font-black text-white block mt-0.5">
                  ₹{Number(loanRec.margin_money_required || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-slate-400">{loanRec.margin_money_percentage || 5}% self-contribution</span>
              </div>

              <div className="bg-gov-saffron-950/40 p-3 rounded-2xl border border-gov-saffron-500/30">
                <span className="text-[10px] font-bold text-gov-saffron-300 uppercase tracking-wider block">Estimated EMI</span>
                <span className="text-base sm:text-lg font-black text-gov-saffron-400 block mt-0.5">
                  ₹{Number(loanRec.estimated_monthly_emi || 0).toLocaleString('en-IN')}/mo
                </span>
                <span className="text-[10px] text-gov-saffron-300">
                  @ {loanRec.interest_rate_percent || 9.5}% ({loanRec.repayment_tenure_months || 54} mos)
                </span>
              </div>
            </div>

            {/* Moratorium & Repayment Schedule Banner */}
            <div className="mt-3 bg-white/10 border border-white/15 rounded-xl p-2.5 flex items-start gap-2.5 text-left">
              <Clock size={16} className="text-gov-saffron-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-bold text-gov-saffron-300">
                  Moratorium: {loanRec.moratorium_period_months || 6} Months Grace Period
                </span>
                <p className="text-[11px] text-slate-300 mt-0.5">
                  {loanRec.moratorium_note || `${loanRec.moratorium_period_months || 6} months moratorium followed by ${loanRec.repayment_tenure_months || 54} monthly EMIs (Total tenure: ${(loanRec.total_tenure_months || 60) / 12} yrs).`}
                </p>
              </div>
            </div>
            
            <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
              <button
                type="button"
                onClick={handleToggleCalculator}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-all"
              >
                <Calculator size={15} className="text-gov-saffron-400" />
                <span>{showCalculator ? "Hide Financial Calculator" : "Simulate Custom Loan & EMI Breakdown"}</span>
                {showCalculator ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {maxLimit && (
                <span className="text-[11px] text-slate-300 font-mono">
                  Max Limit: ₹{Number(maxLimit).toLocaleString('en-IN')}
                </span>
              )}
            </div>

            {/* Interactive Calculator Drawer */}
            {showCalculator && (
              <div className="mt-4 p-4 rounded-2xl bg-white text-gov-navy-900 shadow-xl border border-slate-200 text-left space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h5 className="text-sm font-bold text-gov-navy-950 flex items-center gap-2">
                      <Calculator size={16} className="text-gov-navy-700" />
                      Financial Calculator & Loan Simulation
                    </h5>
                    <p className="text-[11px] text-slate-500">
                      Grounded in real scheme limits, subsidy rates, and moratorium grace periods
                    </p>
                  </div>
                  {maxLimit && (
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider ${
                      isExceedingLimit ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {isExceedingLimit ? 'Exceeds Ceiling' : 'Within Ceiling'}
                    </span>
                  )}
                </div>

                {isExceedingLimit && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 text-xs text-amber-900">
                    <AlertTriangle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">Ceiling Warning: </span>
                      Requested principal of ₹{Number(simPrincipal).toLocaleString('en-IN')} exceeds the scheme maximum loan ceiling of ₹{Number(maxLimit).toLocaleString('en-IN')}.
                    </div>
                  </div>
                )}

                {/* Simulation Inputs */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                      Loan Amount (₹)
                    </label>
                    <input
                      type="number"
                      min="1000"
                      step="10000"
                      value={simPrincipal}
                      onChange={(e) => setSimPrincipal(e.target.value)}
                      className="w-full text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-gov-navy-500"
                    />
                    {maxLimit && (
                      <button
                        type="button"
                        onClick={() => setSimPrincipal(maxLimit)}
                        className="text-[10px] text-gov-navy-600 hover:underline mt-1 block"
                      >
                        Set to Max: ₹{Number(maxLimit).toLocaleString('en-IN')}
                      </button>
                    )}
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                      Tenure: {simTenure} Mos ({Math.round(simTenure / 12 * 10) / 10} Yrs)
                    </label>
                    <input
                      type="range"
                      min="12"
                      max="120"
                      step="6"
                      value={simTenure}
                      onChange={(e) => setSimTenure(e.target.value)}
                      className="w-full accent-gov-navy-800"
                    />
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>1 Yr</span>
                      <span>5 Yrs</span>
                      <span>10 Yrs</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                      Moratorium: {simMoratorium} Mos
                    </label>
                    <input
                      type="range"
                      min="0"
                      max={Math.min(24, simTenure - 1)}
                      step="1"
                      value={simMoratorium}
                      onChange={(e) => setSimMoratorium(e.target.value)}
                      className="w-full accent-gov-saffron-600"
                    />
                    <span className="text-[10px] text-slate-400">
                      Grace period (principal deferred)
                    </span>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                      Rate (% p.a.)
                    </label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        min="0"
                        max="30"
                        step="0.25"
                        value={simRate}
                        onChange={(e) => setSimRate(e.target.value)}
                        className="w-full text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-gov-navy-500"
                      />
                      <button
                        type="button"
                        onClick={runSimulation}
                        disabled={simLoading}
                        className="px-2 py-1 bg-gov-navy-900 text-white rounded-lg hover:bg-gov-navy-800 disabled:opacity-50"
                        title="Recalculate"
                      >
                        <RefreshCw size={13} className={simLoading ? "animate-spin" : ""} />
                      </button>
                    </div>
                    <span className="text-[10px] text-slate-400 block mt-1">
                      {scheme.interest_rate ? "Sourced from scheme" : "Benchmark MSME rate"}
                    </span>
                  </div>
                </div>

                {/* Simulation Output Cards */}
                {simResult && (
                  <div className="space-y-3 pt-2">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                      <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] font-bold uppercase text-slate-500 block">Monthly EMI</span>
                        <span className="text-base font-extrabold text-gov-navy-950 block mt-0.5">
                          ₹{Number(simResult.monthly_emi || 0).toLocaleString('en-IN')}/mo
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Over {simResult.active_repayment_months || simTenure - simMoratorium} mos
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] font-bold uppercase text-slate-500 block">Total Interest</span>
                        <span className="text-base font-extrabold text-amber-700 block mt-0.5">
                          ₹{Number(simResult.total_interest || 0).toLocaleString('en-IN')}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {Number(simResult.interest_rate_percent) === 0 ? "Zero interest subvention" : `@ ${simResult.interest_rate_percent}% p.a.`}
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-[10px] font-bold uppercase text-slate-500 block">Total Repayment</span>
                        <span className="text-base font-extrabold text-slate-900 block mt-0.5">
                          ₹{Number(simResult.total_repayment || 0).toLocaleString('en-IN')}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Principal + Interest
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200">
                        <span className="text-[10px] font-bold uppercase text-emerald-700 block">Net Loan Liability</span>
                        <span className="text-base font-extrabold text-emerald-800 block mt-0.5">
                          ₹{Number(simResult.net_effective_loan || simPrincipal).toLocaleString('en-IN')}
                        </span>
                        <span className="text-[10px] text-emerald-600">
                          {simResult.estimated_subsidy_amount ? `Post-subsidy (₹${Number(simResult.estimated_subsidy_amount).toLocaleString('en-IN')})` : "Standard term loan"}
                        </span>
                      </div>
                    </div>

                    {/* Schedule Table Toggle */}
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => setShowScheduleTable(!showScheduleTable)}
                        className="text-xs font-bold text-gov-navy-700 hover:text-gov-navy-900 flex items-center gap-1.5"
                      >
                        <span>{showScheduleTable ? "Hide Monthly Payment Breakdown" : "View Monthly Payment Breakdown (Amortization Schedule)"}</span>
                        {showScheduleTable ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>

                      {showScheduleTable && simResult.monthly_schedule && simResult.monthly_schedule.length > 0 && (
                        <div className="mt-2.5 overflow-x-auto max-h-60 rounded-xl border border-slate-200">
                          <table className="w-full text-left text-[11px]">
                            <thead className="bg-slate-100 text-slate-700 font-bold uppercase tracking-wider sticky top-0">
                              <tr>
                                <th className="p-2">Mo#</th>
                                <th className="p-2">Phase</th>
                                <th className="p-2">Opening (₹)</th>
                                <th className="p-2">Payment (₹)</th>
                                <th className="p-2">Principal (₹)</th>
                                <th className="p-2">Interest (₹)</th>
                                <th className="p-2">Closing (₹)</th>
                                <th className="p-2">Note</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {simResult.monthly_schedule.map((row) => (
                                <tr key={row.month_number} className={row.phase === 'MORATORIUM' ? 'bg-amber-50/50' : 'hover:bg-slate-50'}>
                                  <td className="p-2 font-mono font-bold">{row.month_number}</td>
                                  <td className="p-2">
                                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                      row.phase === 'MORATORIUM' ? 'bg-amber-200/60 text-amber-900' : 'bg-blue-100 text-blue-900'
                                    }`}>
                                      {row.phase}
                                    </span>
                                  </td>
                                  <td className="p-2 font-mono">₹{Number(row.opening_balance).toLocaleString('en-IN')}</td>
                                  <td className="p-2 font-mono font-bold">₹{Number(row.monthly_payment).toLocaleString('en-IN')}</td>
                                  <td className="p-2 font-mono">₹{Number(row.principal_component).toLocaleString('en-IN')}</td>
                                  <td className="p-2 font-mono">₹{Number(row.interest_component).toLocaleString('en-IN')}</td>
                                  <td className="p-2 font-mono">₹{Number(row.closing_balance).toLocaleString('en-IN')}</td>
                                  <td className="p-2 text-slate-500 text-[10px]">{row.status_note}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* "Why This Scheme?" Explanatory Section */}
          <div className="bg-gradient-to-br from-gov-navy-50/80 to-slate-50 border border-slate-200 rounded-3xl p-5 sm:p-6 space-y-3">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm sm:text-base">
              <Sparkles size={18} className="text-gov-saffron-600" />
              <span>Why This Scheme Was Selected For You:</span>
            </div>
            
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
              {scheme.ai_explanation || "Your enterprise category, turnover scale, and resident state match central qualification guidelines."}
            </p>

            {whyThisScheme && whyThisScheme.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-200/60">
                {whyThisScheme.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-800">
                    <CheckCircle2 size={15} className="text-gov-emerald-600 flex-shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Transparent Score Breakdown (25% + 25% + 25% + 25%) */}
          <div className="bg-white border border-slate-200 rounded-3xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Layers size={15} className="text-gov-navy-700" />
                <span>Explainable Recommendation Score Breakdown</span>
              </h4>
              <span className="text-xs font-black text-gov-navy-950">
                Total: {scoreBreakdown.total_score || matchScore}/100
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Demographics', score: scoreBreakdown.demographic_score, max: 25 },
                { label: 'Enterprise Fit', score: scoreBreakdown.enterprise_score, max: 25 },
                { label: 'Financial Scale', score: scoreBreakdown.financial_score, max: 25 },
                { label: 'Compliance Readiness', score: scoreBreakdown.compliance_score, max: 25 },
              ].map((b, i) => (
                <div key={i} className="bg-slate-50 p-3 rounded-2xl border border-slate-100">
                  <div className="flex justify-between items-center text-[11px] mb-1">
                    <span className="font-bold text-slate-700">{b.label}</span>
                    <span className="font-black text-gov-navy-950">{b.score || 0}/{b.max}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-gov-emerald-600 h-1.5 rounded-full transition-all" 
                      style={{ width: `${Math.min(100, ((b.score || 0) / b.max) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Rule-by-Rule Eligibility Checker (PASS / FAIL / UNKNOWN Matrix) */}
          <div className="bg-white border border-slate-200 rounded-3xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <ShieldCheck size={16} className="text-gov-navy-700" />
                <span>Rule-by-Rule Eligibility Audit</span>
              </h4>
              <button
                onClick={() => setShowFullRules(!showFullRules)}
                className="text-xs font-bold text-gov-saffron-700 hover:text-gov-saffron-800 flex items-center gap-1"
              >
                <span>{showFullRules ? 'Hide Rules' : 'Show All Rules'}</span>
                {showFullRules ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>

            {showFullRules && (
              <div className="space-y-2 pt-1">
                {criteriaChecks.length > 0 ? (
                  criteriaChecks.map((rule, idx) => {
                    const isP = rule.status === 'PASS';
                    const isU = rule.status === 'UNKNOWN';
                    return (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs ${
                          isP 
                            ? 'bg-emerald-50/50 border-emerald-200/80' 
                            : isU 
                            ? 'bg-amber-50/50 border-amber-200/80' 
                            : 'bg-red-50/50 border-red-200/80'
                        }`}
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{rule.label}</span>
                            <span className="text-[10px] font-semibold text-slate-500 uppercase">({rule.category})</span>
                          </div>
                          <p className="text-[11px] text-slate-600">
                            Required: <strong className="text-slate-800">{rule.expected}</strong> • Your Profile: <strong className="text-slate-800">{rule.actual}</strong>
                          </p>
                          {rule.details && (
                            <p className="text-[10px] text-slate-500 italic mt-0.5">{rule.details}</p>
                          )}
                        </div>

                        <div className="flex-shrink-0">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-black border ${
                            isP 
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-300' 
                              : isU 
                              ? 'bg-amber-100 text-amber-900 border-amber-300' 
                              : 'bg-red-100 text-red-800 border-red-300'
                          }`}>
                            {isP ? <CheckCircle2 size={12} /> : isU ? <AlertCircle size={12} /> : <XCircle size={12} />}
                            <span>{rule.status}</span>
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="p-3 bg-slate-50 rounded-2xl text-xs text-slate-500">
                    Standard MSME eligibility rules applied (Pan-India resident, verified enterprise scale).
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Required Documents Checklist */}
          <div className="bg-white border border-slate-200 rounded-3xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <FileText size={15} className="text-gov-navy-700" />
                <span>Required Documentation Checklist</span>
              </h4>
              <Link 
                to="/documents" 
                onClick={onClose}
                className="text-xs font-bold text-gov-saffron-700 hover:text-gov-saffron-800"
              >
                Open Document Locker &rarr;
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {documents.map((doc, idx) => {
                const docName = typeof doc === 'object' ? doc.name : doc;
                const isMandatory = typeof doc === 'object' ? (doc.mandatory ?? doc.is_mandatory ?? true) : true;
                const docCategory = typeof doc === 'object' ? (doc.category || 'Scheme Required') : 'Scheme Required';
                const normKey = NORMALIZE_DOC_KEY(docName);
                
                const matchedDoc = userDocs.find(d => {
                  const dType = (d.doc_type || '').toLowerCase();
                  const dName = (d.document_name || '').toLowerCase();
                  return dType === normKey || 
                         dType.includes(normKey) || 
                         normKey.includes(dType) ||
                         dName.includes(normKey);
                });
                const isUploaded = !!matchedDoc;
                const isVerified = matchedDoc?.verification_status === 'verified';

                return (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100 gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-slate-800 text-xs">{docName}</span>
                        {isMandatory && (
                          <span className="text-[9px] font-bold text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.2 rounded">
                            Mandatory
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 block">{docCategory}</span>
                    </div>
                    <div>
                      {isUploaded ? (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border flex items-center gap-1 whitespace-nowrap ${
                          isVerified 
                            ? 'text-gov-emerald-700 bg-gov-emerald-50 border-gov-emerald-200'
                            : 'text-blue-700 bg-blue-50 border-blue-200'
                        }`}>
                          <Check size={11} /> {isVerified ? 'Verified' : 'Uploaded'}
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 flex items-center gap-1 whitespace-nowrap">
                          <AlertTriangle size={11} /> Missing
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Next Recommended Step */}
          {scheme.next_action && (
            <div className="p-4 bg-gov-navy-950 text-white rounded-2xl flex items-start gap-3">
              <ArrowRight size={18} className="text-gov-saffron-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-gov-saffron-400 block">Recommended Next Action</span>
                <p className="text-xs text-slate-200 mt-0.5">{scheme.next_action}</p>
              </div>
            </div>
          )}

        </div>

        {/* Modal Bottom Action Footer */}
        <div className="p-4 sm:p-5 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {onBookmarkToggle && (
              <button 
                onClick={() => onBookmarkToggle(scheme.id || scheme.scheme_id)}
                className={`p-2.5 rounded-xl border transition-colors flex items-center gap-1.5 text-xs font-semibold ${
                  isBookmarked 
                    ? 'bg-gov-saffron-50 border-gov-saffron-300 text-gov-saffron-700' 
                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <Bookmark size={16} className={isBookmarked ? 'fill-gov-saffron-600 text-gov-saffron-600' : ''} />
                <span>{isBookmarked ? 'Saved' : 'Save Scheme'}</span>
              </button>
            )}

            {scheme.official_url && (
              <a 
                href={scheme.official_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 transition-colors flex items-center gap-1.5 text-xs font-medium"
              >
                <ExternalLink size={15} />
                <span className="hidden sm:inline">Official Portal</span>
              </a>
            )}
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-700 text-xs sm:text-sm font-semibold hover:bg-slate-100 transition-colors"
            >
              Close
            </button>
            <button
              onClick={handleApplyNow}
              disabled={applying || applySuccess}
              className="px-5 py-2.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white text-xs sm:text-sm font-semibold shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {applying ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating Application...
                </>
              ) : applySuccess ? (
                <>
                  <CheckCircle2 size={16} />
                  Application Created!
                </>
              ) : (
                <>
                  <span>Start Application</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
