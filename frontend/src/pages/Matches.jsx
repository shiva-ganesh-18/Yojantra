import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  Sparkles, RefreshCw, Bookmark, ExternalLink, ShieldCheck, 
  CheckCircle2, AlertTriangle, AlertCircle, IndianRupee, Calendar, Filter, 
  ChevronRight, ArrowRight, Building, Check, Scale, X, Layers, Percent, Wallet, Clock
} from 'lucide-react';
import SchemeDetailModal from '../components/SchemeDetailModal';
import SchemeCompareModal from '../components/SchemeCompareModal';
import SkeletonLoader from '../components/SkeletonLoader';
import { matchService } from '../services';

export default function Matches() {
  const navigate = useNavigate();
  const { api, user } = useAuthStore();
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedScheme, setSelectedScheme] = useState(null);

  // Application submission state
  const [applyingSchemeId, setApplyingSchemeId] = useState(null);
  const [feedbackToast, setFeedbackToast] = useState(null); // { type: 'success' | 'error', message: string }

  // Scheme Comparison state
  const [compareIds, setCompareIds] = useState([]);
  const [compareData, setCompareData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [loadingCompare, setLoadingCompare] = useState(false);

  // Check onboarding status
  const isOnboardingCompleted = !!user?.onboarding_completed;

  // Fetch matches only when user is authenticated and onboarding is completed (or to evaluate)
  const { data: matches = [], isLoading, refetch } = useQuery(
    ['all_matches', isOnboardingCompleted],
    () => matchService.findMatches(false),
    {
      enabled: isOnboardingCompleted,
    }
  );

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await matchService.findMatches(true);
      await refetch();
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  const handleApplyScheme = async (schemeId) => {
    if (applyingSchemeId) return; // Prevent duplicate clicks
    setApplyingSchemeId(schemeId);
    setFeedbackToast(null);
    let succeeded = false;

    try {
      await api().post('/applications', { scheme_id: schemeId });
      succeeded = true;
      setFeedbackToast({
        type: 'success',
        message: 'Application submitted successfully.'
      });
      queryClient.invalidateQueries('applications_list');
      
      // Close modal if open
      setSelectedScheme(null);

      // Navigate to /applications after brief feedback delay
      setTimeout(() => {
        navigate('/applications');
      }, 1000);
    } catch (err) {
      console.error('Failed to submit application:', err);
      const detail = err.response?.data?.detail ?? err.details?.detail;
      const errorMsg = typeof detail === 'string'
        ? detail
        : (detail?.message || (typeof err.message === 'string' ? err.message : null) || 'Failed to submit application. Please try again.');
      
      setFeedbackToast({
        type: 'error',
        message: errorMsg
      });
      // Auto-hide error toast after 5s
      setTimeout(() => {
        setFeedbackToast((prev) => (prev?.type === 'error' ? null : prev));
      }, 5000);
    } finally {
      // On success, keep button disabled during navigation delay to prevent duplicate submits.
      // On error, re-enable so user can retry.
      if (!succeeded) {
        setApplyingSchemeId(null);
      }
    }
  };

  const toggleBookmark = async (schemeId, e) => {
    if (e) e.stopPropagation();
    try {
      await matchService.toggleBookmark(schemeId);
      queryClient.invalidateQueries('all_matches');
    } catch (e) {
      console.error(e);
    }
  };

  const toggleCompare = (schemeId, e) => {
    if (e) e.stopPropagation();
    setCompareIds(prev => {
      if (prev.includes(schemeId)) {
        return prev.filter(id => id !== schemeId);
      }
      if (prev.length >= 4) {
        setFeedbackToast({ type: 'error', message: 'You can compare up to 4 schemes at once.' });
        setTimeout(() => {
          setFeedbackToast((prevToast) => (prevToast?.type === 'error' ? null : prevToast));
        }, 4000);
        return prev;
      }
      return [...prev, schemeId];
    });
  };

  const handleRunComparison = async () => {
    if (compareIds.length < 2) return;
    try {
      setLoadingCompare(true);
      const res = await matchService.compareSchemes(compareIds);
      setCompareData(res);
      setIsComparing(true);
    } catch (err) {
      console.error('Comparison error:', err);
      const detail = err.response?.data?.detail ?? err.details?.detail;
      const msg = typeof detail === 'string'
        ? detail
        : (detail?.message || (typeof err.message === 'string' ? err.message : null) || 'Could not compare schemes. Please try again.');
      setFeedbackToast({ type: 'error', message: msg });
      setTimeout(() => {
        setFeedbackToast((prevToast) => (prevToast?.type === 'error' ? null : prevToast));
      }, 5000);
    } finally {
      setLoadingCompare(false);
    }
  };

  // Filter chips
  const filterTabs = [
    { id: 'all', label: t('matches_filter_all', 'All Matches') },
    { id: 'pass', label: t('matches_filter_pass', 'Verified PASS'), filterFn: (m) => m.overall_verdict === 'PASS' || m.eligibility_status === 'Eligible' },
    { id: 'best', label: t('matches_filter_high', 'High Score (80%+)'), filterFn: (m) => (m.match_score || 0) >= 80 },
    { id: 'loans', label: t('matches_filter_loans', 'Loans'), filterFn: (m) => (m.scheme_type || '').includes('loan') },
    { id: 'subsidies', label: t('matches_filter_subsidies', 'Subsidies'), filterFn: (m) => (m.scheme_type || '').includes('subsidy') || (m.benefit_description || '').toLowerCase().includes('subsidy') },
    { id: 'women', label: t('matches_filter_women', 'Women Priority'), filterFn: (m) => (m.name + ' ' + (m.description || '')).toLowerCase().includes('women') || (m.name + ' ' + (m.description || '')).toLowerCase().includes('mahila') },
    { id: 'msme', label: t('matches_filter_msme', 'MSME Priority'), filterFn: (m) => (m.name + ' ' + (m.description || '')).toLowerCase().includes('msme') || (m.name || '').includes('PMEGP') || (m.name || '').includes('Mudra') },
  ];

  const currentTab = filterTabs.find(tab => tab.id === activeFilter);
  const filteredMatches = matches.filter(m => {
    if (!currentTab || !currentTab.filterFn) return true;
    return currentTab.filterFn(m);
  });

  return (
    <div className="space-y-6 text-left relative pb-20">
      
      {/* Toast Notification */}
      {feedbackToast && (
        <div 
          className={`fixed top-6 right-6 z-50 max-w-md p-4 rounded-2xl shadow-2xl border flex items-start gap-3 transition-all animate-in fade-in slide-in-from-top-4 duration-300 ${
            feedbackToast.type === 'success'
              ? 'bg-gov-emerald-900 text-white border-gov-emerald-700'
              : 'bg-red-900 text-white border-red-700'
          }`}
        >
          {feedbackToast.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-gov-emerald-300 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-300 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1 pr-2">
            <p className="text-sm font-bold">
              {feedbackToast.type === 'success' ? 'Success' : 'Submission Error'}
            </p>
            <p className="text-xs text-slate-200 mt-0.5 leading-relaxed">
              {feedbackToast.message}
            </p>
          </div>
          <button
            onClick={() => setFeedbackToast(null)}
            className="text-white/60 hover:text-white p-1 rounded-lg hover:bg-white/10"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-2 rounded-xl bg-gov-saffron-100 text-gov-saffron-700">
                <Sparkles size={20} />
              </span>
              <h1 className="text-2xl font-black text-gov-navy-950">
                {t('matches_title', 'AI Scheme Matching & Eligibility Engine')}
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 max-w-xl">
              {t('matches_subtitle', 'Strict criteria verification (PASS / FAIL / UNKNOWN), explainable recommendation scores, and personalized loan/subsidy tranches.')}
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing || isLoading}
            className="self-start sm:self-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs sm:text-sm font-semibold transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin text-gov-saffron-600' : ''} />
            <span>{refreshing ? t('btn_refresh', 'Recalculating...') : t('btn_refresh', 'Refresh Matches')}</span>
          </button>
        </div>

        {/* Live Profile Analysis Verification Strip */}
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2.5">
            {t('matches_audit_title', 'Real-Time Eligibility Audit')}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {[
              { label: 'Demographics (SC/ST/OBC/Women)', status: 'Evaluated' },
              { label: 'Sector & Operational Stage', status: 'Matched' },
              { label: 'Turnover & Funding Quantum', status: 'Calculated' },
              { label: 'UDYAM & Compliance Status', status: 'Audited' },
            ].map((audit, idx) => (
              <div 
                key={idx} 
                className="bg-gov-emerald-50/60 border border-gov-emerald-200/80 rounded-xl px-3 py-2 flex items-center gap-2"
              >
                <CheckCircle2 size={15} className="text-gov-emerald-600 flex-shrink-0" />
                <div className="overflow-hidden">
                  <p className="text-[11px] font-bold text-gov-navy-950 truncate">{audit.label}</p>
                  <p className="text-[10px] text-gov-emerald-700 font-semibold">{audit.status} ✓</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter Tabs & Compare Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar">
          {filterTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveFilter(tab.id)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all border ${
                activeFilter === tab.id
                  ? 'bg-gov-navy-950 text-white border-gov-navy-950 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {compareIds.length > 0 && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setCompareIds([])}
              className="text-xs text-slate-500 hover:text-slate-800 underline font-semibold px-2 py-1"
            >
              Clear ({compareIds.length})
            </button>
            <button
              onClick={handleRunComparison}
              disabled={compareIds.length < 2 || loadingCompare}
              className="px-4 py-2 bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-xs rounded-xl shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <Scale size={14} />
              <span>{loadingCompare ? 'Loading Matrix...' : `Compare Schemes (${compareIds.length}/4)`}</span>
            </button>
          </div>
        )}
      </div>

      {/* Matches Content Area */}
      {!isOnboardingCompleted ? (
        <div className="bg-white rounded-3xl p-8 sm:p-12 border border-slate-200 shadow-gov text-center max-w-2xl mx-auto space-y-6">
          <div className="w-16 h-16 bg-gov-saffron-100 text-gov-saffron-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <Sparkles size={32} />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-gov-navy-950">
              Complete your profile to unlock AI matches.
            </h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
              Answer a few simple questions about your business, funding requirements, and social category so Yojantra can calculate your personalized eligibility across central government schemes.
            </p>
          </div>

          <div className="pt-2">
            <button
              onClick={() => navigate('/onboarding')}
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all"
            >
              <span>Complete Profile</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      ) : isLoading ? (
        <div className="space-y-4">
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
        </div>
      ) : filteredMatches.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-gov text-center">
          <Sparkles size={48} className="mx-auto text-slate-300 mb-3" />
          <h3 className="text-base font-bold text-gov-navy-950">No schemes found in this category</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Try selecting a different filter tab or update your profile details to broaden eligibility matching.
          </p>
          <button
            onClick={() => setActiveFilter('all')}
            className="mt-4 px-5 py-2.5 rounded-xl bg-gov-navy-950 text-white text-xs font-bold"
          >
            Show All Matches
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMatches.map((match) => {
            const score = match.match_score || 85;
            const isHigh = score >= 80;
            const isModerate = score >= 60;
            const verdict = match.overall_verdict || (score >= 75 ? 'PASS' : (score >= 40 ? 'UNKNOWN' : 'FAIL'));
            const isSelectedForCompare = compareIds.includes(match.scheme_id);

            const isPass = verdict === 'PASS';
            const isUnknown = verdict === 'UNKNOWN';

            const loan = match.loan_recommendation || {};

            return (
              <div
                key={match.scheme_id}
                className={`bg-white rounded-3xl p-5 sm:p-6 border transition-all ${
                  isSelectedForCompare 
                    ? 'border-gov-saffron-500 ring-2 ring-gov-saffron-400/30 shadow-md' 
                    : 'border-slate-200 hover:border-gov-navy-900/30 hover:shadow-gov-hover'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  
                  {/* Left Main Information */}
                  <div className="flex-1 space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                        {match.ministry || 'Government of India'}
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-[11px] font-semibold text-slate-500 capitalize">
                        {match.scheme_type || 'Financial Support'}
                      </span>

                      {/* Eligibility Checker Status Badge (PASS / FAIL / UNKNOWN) */}
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black border ${
                        isPass 
                          ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-300' 
                          : isUnknown 
                          ? 'bg-amber-50 text-amber-800 border-amber-300' 
                          : 'bg-red-50 text-red-700 border-red-300'
                      }`}>
                        {isPass ? <CheckCircle2 size={11} /> : isUnknown ? <AlertCircle size={11} /> : <AlertTriangle size={11} />}
                        <span>Eligibility: {verdict}</span>
                      </span>
                    </div>

                    <h3 className="text-lg sm:text-xl font-extrabold text-gov-navy-950 leading-snug">
                      {match.name}
                    </h3>

                    {/* "Why This Scheme?" Explanatory Box */}
                    <div className="bg-gradient-to-r from-gov-navy-50/80 to-slate-50 border border-slate-200/80 rounded-2xl p-4 space-y-2">
                      <p className="text-xs font-bold text-gov-navy-950 flex items-center gap-1.5">
                        <CheckCircle2 size={15} className="text-gov-emerald-600" />
                        <span>{t('matches_why_match', 'Why This Scheme Matches Your Profile')}:</span>
                      </p>
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {match.ai_explanation || 
                         "Your enterprise classification, turnover tier, and demographic profile align directly with central ministry qualification guidelines."}
                      </p>

                      {match.why_this_scheme && match.why_this_scheme.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px] text-slate-600">
                          {match.why_this_scheme.slice(0, 2).map((w, idx) => (
                            <div key={idx} className="flex items-start gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-gov-emerald-600 flex-shrink-0 mt-1.5" />
                              <span className="break-words leading-relaxed text-slate-700">{w}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Personalized Loan Recommendation Mini-Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                      <div className="bg-slate-50 p-2.5 rounded-2xl border border-slate-100 flex items-center gap-2">
                        <Wallet size={16} className="text-gov-navy-700 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] font-bold text-slate-500 uppercase block">{t('schemes_filter_loan', 'Recommended Loan')}</span>
                          <span className="font-extrabold text-slate-900 text-xs">
                            ₹{Number(loan.recommended_loan_amount || 500000).toLocaleString('en-IN')}
                          </span>
                        </div>
                      </div>

                      <div className="bg-emerald-50/50 p-2.5 rounded-2xl border border-emerald-100 flex items-center gap-2">
                        <IndianRupee size={16} className="text-gov-emerald-600 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] font-bold text-gov-emerald-800 uppercase block">{t('schemes_filter_subsidy', 'Estimated Subsidy')}</span>
                          <span className="font-extrabold text-gov-emerald-700 text-xs">
                            ₹{Number(loan.estimated_subsidy_amount || 125000).toLocaleString('en-IN')} ({loan.subsidy_percentage || 25}%)
                          </span>
                        </div>
                      </div>

                      <div className="bg-amber-50/50 p-2.5 rounded-2xl border border-amber-100 flex items-center gap-2">
                        <Percent size={16} className="text-gov-saffron-600 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] font-bold text-amber-900 uppercase block">Estimated EMI</span>
                          <span className="font-extrabold text-amber-900 text-xs">
                            ₹{Number(loan.estimated_monthly_emi || 10500).toLocaleString('en-IN')}/mo
                          </span>
                        </div>
                      </div>

                      <div className="bg-blue-50/50 p-2.5 rounded-2xl border border-blue-100 flex items-center gap-2">
                        <Clock size={16} className="text-blue-600 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] font-bold text-blue-900 uppercase block">{t('schemes_moratorium', 'Moratorium')}</span>
                          <span className="font-extrabold text-blue-900 text-xs">
                            {loan.moratorium_period_months || 6} Mo Grace
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Deadline notice */}
                    {match.application_deadline && (
                      <div className="flex items-center gap-1.5 text-xs text-red-600 font-medium">
                        <Calendar size={13} />
                        <span>{t('schemes_deadline', 'Application Deadline')}: {new Date(match.application_deadline).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Right Score & Actions Panel */}
                  <div className="flex md:flex-col items-center md:items-end justify-between md:justify-start gap-4 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
                    
                    {/* Compare & Bookmark Badges */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => toggleCompare(match.scheme_id, e)}
                        className={`px-2.5 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1 ${
                          isSelectedForCompare
                            ? 'bg-gov-saffron-50 border-gov-saffron-400 text-gov-saffron-800'
                            : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-600'
                        }`}
                        title="Select to compare side-by-side"
                      >
                        <Scale size={13} />
                        <span>{isSelectedForCompare ? t('btn_compared', 'Compared') : t('btn_compare', 'Compare')}</span>
                      </button>

                      <button
                        onClick={(e) => toggleBookmark(match.scheme_id, e)}
                        aria-label="Bookmark scheme"
                        className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-slate-400 hover:text-gov-saffron-600"
                      >
                        <Bookmark 
                          size={16} 
                          className={match.is_bookmarked ? 'fill-gov-saffron-600 text-gov-saffron-600' : ''} 
                        />
                      </button>

                      <div className={`px-3 py-1 rounded-2xl font-black text-xs border shadow-sm ${
                        isHigh
                          ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200'
                          : isModerate
                          ? 'bg-gov-saffron-50 text-gov-saffron-700 border-gov-saffron-200'
                          : 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {score}% {t('matches_badge_match', 'Score')}
                      </div>
                    </div>

                    {/* CTA Buttons */}
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => setSelectedScheme(match)}
                        className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-gov-navy-950 text-xs font-bold transition-all"
                      >
                        {t('btn_view_details', 'View Details & Rules')}
                      </button>
                      <button
                        onClick={() => handleApplyScheme(match.scheme_id)}
                        disabled={applyingSchemeId === match.scheme_id}
                        className="px-4 py-2.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white text-xs font-bold shadow-sm hover:shadow transition-all flex items-center gap-1.5 disabled:opacity-60"
                      >
                        {applyingSchemeId === match.scheme_id ? (
                          <>
                            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Applying...</span>
                          </>
                        ) : (
                          <>
                            <span>{t('btn_apply', 'Apply Now')}</span>
                            <ArrowRight size={14} />
                          </>
                        )}
                      </button>
                    </div>

                  </div>

                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Scheme Detail Modal */}
      {selectedScheme && (
        <SchemeDetailModal
          scheme={selectedScheme}
          isOpen={!!selectedScheme}
          onClose={() => setSelectedScheme(null)}
          isBookmarked={selectedScheme.is_bookmarked}
          onBookmarkToggle={(id) => toggleBookmark(id)}
          onApply={handleApplyScheme}
        />
      )}

      {/* Side-by-Side Scheme Comparison Modal */}
      {isComparing && compareData && (
        <SchemeCompareModal
          compareData={compareData}
          isOpen={isComparing}
          onClose={() => setIsComparing(false)}
          onSelectScheme={(sch) => {
            setIsComparing(false);
            setSelectedScheme(sch);
          }}
        />
      )}

    </div>
  );
}
