import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  Search, Filter, Building2, Calendar, ExternalLink, 
  IndianRupee, ChevronRight, Sparkles, ArrowRight, ShieldCheck,
  CheckCircle2, AlertCircle, X
} from 'lucide-react';
import SchemeDetailModal from '../components/SchemeDetailModal';
import SkeletonLoader from '../components/SkeletonLoader';

export default function Schemes() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { api } = useAuthStore();
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('q') || '');
  const [filter, setFilter] = useState('');
  const [selectedScheme, setSelectedScheme] = useState(null);

  // Honor deep-links from global search (SearchCommand navigates to /schemes?q=...).
  useEffect(() => {
    const q = searchParams.get('q') || '';
    if (q !== search) setSearch(q);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Keep ?q= in sync when the user types (replace to avoid history spam).
  useEffect(() => {
    const current = searchParams.get('q') || '';
    if (search !== current) {
      const next = new URLSearchParams(searchParams);
      if (search) next.set('q', search);
      else next.delete('q');
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // Application submission state
  const [applyingSchemeId, setApplyingSchemeId] = useState(null);
  const [feedbackToast, setFeedbackToast] = useState(null); // { type: 'success' | 'error', message: string }

  const { data: schemes = [], isLoading } = useQuery(['schemes_browse', search, filter], () =>
    api().get('/schemes', { params: { q: search, scheme_type: filter } }).then(r => r.data || [])
  );

  const handleApplyScheme = async (schemeId) => {
    if (applyingSchemeId) return; // Prevent duplicate clicks
    setApplyingSchemeId(schemeId);
    setFeedbackToast(null);

    try {
      await api().post('/applications', { scheme_id: schemeId });
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
      setTimeout(() => {
        setFeedbackToast((prev) => (prev?.type === 'error' ? null : prev));
      }, 5000);
    } finally {
      setApplyingSchemeId(null);
    }
  };

  const filters = [
    { value: '', label: t('schemes_filter_all', 'All Schemes') },
    { value: 'loan', label: t('schemes_filter_loan', 'Bank Loans') },
    { value: 'subsidy', label: t('schemes_filter_subsidy', 'Capital Subsidies') },
    { value: 'grant', label: t('schemes_filter_grant', 'Grants & Assistance') },
    { value: 'guarantee', label: t('schemes_filter_guarantee', 'Credit Guarantees') },
  ];

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
              <span className="p-2 rounded-xl bg-gov-navy-100 text-gov-navy-900">
                <Building2 size={20} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                {t('schemes_title', 'National Scheme Directory')}
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              {t('schemes_subtitle', 'Browse official central and state government schemes, guidelines, subsidy rates, and nodal ministries.')}
            </p>
          </div>
          <span className="self-start sm:self-auto text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
            {schemes.length} {t('schemes_indexed', 'Active Schemes Indexed')}
          </span>
        </div>

        {/* Search Bar */}
        <div className="mt-5 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={19} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('schemes_search_placeholder', 'Search by scheme name, ministry, subsidy, or sector (e.g., PMEGP, Mudra, Women)...')}
            className="w-full pl-11 pr-4 py-3.5 border border-slate-300 rounded-2xl text-sm sm:text-base text-slate-900 bg-slate-50/50 focus:bg-white focus:border-gov-navy-950 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none transition-all"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex gap-2 overflow-x-auto mt-4 pb-1 custom-scrollbar">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all border ${
                filter === f.value
                  ? 'bg-gov-navy-950 text-white border-gov-navy-950 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Schemes Grid / List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
        </div>
      ) : schemes.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-gov text-center">
          <Building2 size={48} className="mx-auto text-slate-300 mb-3" />
          <h3 className="text-base font-bold text-gov-navy-950">{t('schemes_no_schemes', 'No schemes found')}</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {t('schemes_no_schemes_sub', 'We couldn\'t find any schemes matching your search. Try searching for broader terms like "Loan", "MSME", or "Subsidy".')}
          </p>
          <button
            onClick={() => { setSearch(''); setFilter(''); }}
            className="mt-4 px-5 py-2.5 rounded-xl bg-gov-navy-950 text-white text-xs font-bold"
          >
            {t('btn_clear', 'Clear Search & Filters')}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {schemes.map((scheme) => (
            <div
              key={scheme.id}
              className="bg-white rounded-3xl p-5 sm:p-6 border border-slate-200 hover:border-gov-navy-900/40 hover:shadow-gov-hover transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                      {scheme.ministry || 'Government of India'}
                    </span>
                    <h3 className="font-bold text-base sm:text-lg text-gov-navy-950 mt-0.5 leading-snug">
                      {scheme.name}
                    </h3>
                  </div>

                  <span className="px-2.5 py-1 rounded-xl text-[11px] font-bold bg-gov-navy-50 text-gov-navy-900 border border-gov-navy-200 capitalize flex-shrink-0">
                    {scheme.scheme_type || 'Scheme'}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                  {scheme.description}
                </p>

                {scheme.benefit_description && (
                  <div className="flex items-start gap-2 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <IndianRupee size={15} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
                    <p className="text-slate-800 text-[11px] font-medium leading-snug">
                      <strong>{t('schemes_subsidy_rate', 'Benefit')}:</strong> {scheme.benefit_description}
                    </p>
                  </div>
                )}

                {scheme.application_deadline && (
                  <div className="flex items-center gap-1.5 text-[11px] text-red-600 font-medium">
                    <Calendar size={13} />
                    <span>{t('schemes_deadline', 'Deadline')}: {new Date(scheme.application_deadline).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => setSelectedScheme(scheme)}
                  className="px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-gov-navy-950 text-xs font-bold transition-colors"
                >
                  {t('btn_view_details', 'View Scheme Details')}
                </button>

                <div className="flex items-center gap-1.5">
                  {scheme.official_url && (
                    <a
                      href={scheme.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-gov-navy-950 transition-colors"
                      title="Open Official Ministry Portal"
                    >
                      <ExternalLink size={16} />
                    </a>
                  )}

                  <button
                    onClick={() => setSelectedScheme(scheme)}
                    className="px-4 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1"
                  >
                    <span>{t('btn_apply_scheme', 'Check Eligibility')}</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scheme Detail Deep-Dive Modal */}
      {selectedScheme && (
        <SchemeDetailModal
          scheme={selectedScheme}
          isOpen={!!selectedScheme}
          onClose={() => setSelectedScheme(null)}
          onApply={handleApplyScheme}
        />
      )}

    </div>
  );
}
