import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Sparkles, CheckCircle2, ArrowRight, ShieldCheck, 
  Building2, IndianRupee, FileText, MapPin, 
  Clock, AlertTriangle, ChevronRight, FolderUp, MessageSquare
} from 'lucide-react';
import SchemeDetailModal from '../components/SchemeDetailModal';
import SkeletonLoader from '../components/SkeletonLoader';

export default function Dashboard() {
  const { api, user } = useAuthStore();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedScheme, setSelectedScheme] = useState(null);

  // 1. Fetch recommended matches — key matches Matches.jsx for cross-page invalidation
  const { data: matches = [], isLoading: loadingMatches, error: errorMatches } = useQuery('all_matches', () => 
    api().get('/schemes/recommended').then(r => r.data || [])
  );

  // 2. Fetch applications — key matches Applications.jsx for cross-page invalidation
  const { data: applications = [], isLoading: loadingApps, error: errorApps } = useQuery('applications_list', () =>
    api().get('/applications').then(r => r.data || [])
  );

  // 3. Fetch documents — key matches Documents.jsx for cross-page invalidation
  const { data: documents = [], isLoading: loadingDocs, error: errorDocs } = useQuery('my_documents', () =>
    api().get('/documents/my-documents').then(r => r.data || [])
  );

  // 4. Fetch document readiness — key matches Documents.jsx for cross-page invalidation
  const { data: docReadiness } = useQuery('document_readiness', () =>
    api().get('/documents/readiness').then(r => r.data).catch(() => null)
  );

  // If user hasn't finished onboarding, show focused guidance
  if (!user?.onboarding_completed) {
    return (
      <div className="bg-white rounded-3xl p-8 sm:p-12 border border-slate-200 shadow-gov text-center max-w-2xl mx-auto my-8 space-y-6">
        <div className="w-16 h-16 bg-gov-saffron-100 text-gov-saffron-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
          <Sparkles size={32} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gov-navy-950">
            {t('onboard_title', 'Let\'s Set Up Your Profile')}
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            {t('onboard_subtitle', 'Answer a few simple questions about your business, funding requirements, and social category so Yojantra can calculate your eligibility.')}
          </p>
        </div>

        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs text-slate-600 max-w-md mx-auto text-left space-y-2">
          <div className="flex items-center gap-2 text-gov-navy-900 font-semibold">
            <ShieldCheck size={16} className="text-gov-emerald-600" />
            <span>{t('onboard_step1_title', 'Basic Details & Social Category')}</span>
          </div>
          <p className="text-[11px] text-slate-500">
            Central ministries provide distinct quotas and subsidies (up to 35%) for SC/ST/OBC, women founders, and rural micro-enterprises.
          </p>
        </div>

        <Link 
          to="/onboarding"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all"
        >
          <span>{t('onboard_title', 'Start Onboarding')}</span>
          <ArrowRight size={17} />
        </Link>
      </div>
    );
  }

  // Greeting based on hour
  const hour = new Date().getHours();
  const greeting = hour < 12 
    ? t('dash_greeting_morning', 'Good morning') 
    : hour < 17 
      ? t('dash_greeting_afternoon', 'Good afternoon') 
      : t('dash_greeting_evening', 'Good evening');
  const userName = user?.full_name ? user.full_name.split(' ')[0] : t('guest_citizen', 'Citizen');

  // Counts for Journey Tracker
  const verifiedDocsCount = documents.filter(d => d.verification_status === 'verified').length;
  const totalRequiredDocs = Math.max(5, documents.length);
  const activeAppsCount = applications.filter(a => ['submitted', 'under_review', 'draft'].includes(a.status)).length;
  const approvedCount = applications.filter(a => a.status === 'approved').length;

  return (
    <div className="space-y-8 text-left">
      
      {/* Top Hero Section: 5-Second Clarity */}
      <div className="bg-gradient-to-r from-gov-navy-950 via-gov-navy-900 to-gov-navy-950 text-white rounded-3xl p-6 sm:p-8 shadow-xl border border-gov-navy-800 relative overflow-hidden">
        {/* Subtle decorative motif */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-gov-saffron-500/10 to-transparent pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-500/30 uppercase tracking-wider">
              <Sparkles size={13} />
              {t('dash_hero_tag', 'AI Matching Engine Active')}
            </span>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-snug">
              {greeting}, {userName}
            </h1>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              {t('dash_hero_subtitle', 'Let\'s find the government support available for your business. We matched your profile against 200+ central & state schemes.')}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              to="/matches"
              className="px-6 py-3.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
            >
              <span>{t('dash_btn_view_matches', 'View AI Recommendations')}</span>
              <ArrowRight size={16} />
            </Link>
            <Link
              to="/chat"
              className="px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 transition-colors flex items-center justify-center gap-2"
            >
              <MessageSquare size={16} />
              <span>{t('nav_ai_chat', 'Ask AI Assistant')}</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Visual Journey: YOUR SCHEME JOURNEY */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-gov">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              {t('dash_journey_title', 'Your Scheme Access Journey')}
            </h2>
            <p className="text-lg font-bold text-gov-navy-950 mt-0.5">
              {t('dash_journey_title', 'End-to-End Workflow')}
            </p>
          </div>
          <span className="text-xs font-semibold text-gov-emerald-700 bg-gov-emerald-50 px-2.5 py-1 rounded-full border border-gov-emerald-200">
            {t('inst_tab_active', 'Active')}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {/* Step 1: Profile */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">{t('dash_step_profile', '1. Profile')}</span>
            <div className="my-2">
              {(() => {
                const completionPct = user?.profile_completion_percentage ?? (user?.phone ? 85 : 65);
                const hasPhone = !!user?.phone;
                const isComplete = completionPct >= 100 && hasPhone;
                return (
                  <>
                    <p className={`text-sm font-bold flex items-center gap-1 ${isComplete ? 'text-gov-emerald-700' : 'text-amber-600'}`}>
                      {isComplete ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                      <span>
                        {isComplete 
                          ? t('docs_verified', 'Completed') 
                          : (!hasPhone ? `${completionPct}% (Phone Missing)` : `${completionPct}% Complete`)}
                      </span>
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {[user?.district, user?.state].filter(Boolean).join(', ') || 'Location Pending'}
                    </p>
                  </>
                );
              })()}
            </div>
            <Link to="/profile" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              {user?.phone ? t('btn_view_details', 'View Profile') : 'Complete Profile'} &rarr;
            </Link>
          </div>

          {/* Step 2: AI Matching */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">{t('dash_step_matching', '2. AI Matching')}</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950 flex items-center gap-1 text-gov-emerald-700">
                <CheckCircle2 size={16} />
                <span>{matches.length} {t('nav_govt_schemes', 'Schemes')}</span>
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">{t('matches_eligible_tag', 'Eligible')}</p>
            </div>
            <Link to="/matches" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              {t('matches_filter_all', 'Explore Matches')} &rarr;
            </Link>
          </div>

          {/* Step 3: Documents */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">{t('dash_step_docs', '3. Documents')}</span>
            <div className="my-2">
              {loadingDocs ? (
                <p className="text-sm font-bold text-slate-400 flex items-center gap-1">
                  <span className="w-3.5 h-3.5 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
                  Loading...
                </p>
              ) : errorDocs ? (
                <p className="text-sm font-bold text-red-600">Error loading</p>
              ) : (
                (() => {
                  const totalReq = docReadiness?.total_required ?? Math.max(3, documents.length);
                  const totalUp = docReadiness?.total_uploaded ?? documents.length;
                  const missingMandatory = docReadiness?.missing_mandatory_count ?? (totalUp >= 3 ? 0 : 3 - totalUp);
                  const isReady = docReadiness ? docReadiness.is_ready_to_apply : (missingMandatory === 0 && totalUp > 0);
                  return (
                    <>
                      <p className={`text-sm font-bold flex items-center gap-1 ${isReady ? 'text-gov-emerald-700' : 'text-amber-600'}`}>
                        {isReady ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                        <span>{totalUp} / {totalReq} {t('docs_tab_all', 'Ready')}</span>
                      </p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {missingMandatory > 0 
                          ? `${missingMandatory} mandatory missing`
                          : t('docs_ocr_verified', 'OCR Format & Data Extraction')}
                      </p>
                    </>
                  );
                })()
              )}
            </div>
            <Link to="/documents" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              {(docReadiness?.missing_mandatory_count ?? 0) > 0 ? t('btn_upload', 'Upload Missing') : 'Manage Docs'} &rarr;
            </Link>
          </div>

          {/* Step 4: Applications */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">{t('dash_step_apps', '4. Applications')}</span>
            <div className="my-2">
              {loadingApps ? (
                <p className="text-sm font-bold text-slate-400 flex items-center gap-1">
                  <span className="w-3.5 h-3.5 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
                  Loading...
                </p>
              ) : errorApps ? (
                <p className="text-sm font-bold text-red-600">Error loading</p>
              ) : (
                <>
                  <p className="text-sm font-bold text-gov-navy-950">
                    {activeAppsCount} {t('apps_status_submitted', 'In Progress')}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">{approvedCount} {t('apps_status_approved', 'Approved')}</p>
                </>
              )}
            </div>
            <Link to="/applications" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              {t('nav_applications', 'View Tracking')} &rarr;
            </Link>
          </div>

          {/* Step 5: Benefits */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between col-span-2 md:col-span-1">
            <span className="text-xs font-semibold text-slate-400">{t('dash_step_benefits', '5. Track Benefits')}</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950">
                {t('schemes_filter_subsidy', 'Direct Benefit')}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">{t('apps_step_sanction', 'DBT Bank Account')}</p>
            </div>
            <Link to="/applications" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              {t('btn_view_details', 'View Status')} &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Your Best Matches Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              {t('matches_title', 'Personalized Recommendations')}
            </h2>
            <p className="text-xl font-bold text-gov-navy-950">
              {t('dash_stat_matches', 'Your Best Matches')}
            </p>
          </div>
          <Link 
            to="/matches" 
            className="text-xs sm:text-sm font-bold text-gov-saffron-700 hover:text-gov-saffron-800 flex items-center gap-1"
          >
            <span>{t('matches_filter_all', 'View All')} ({matches.length})</span>
            <ChevronRight size={16} />
          </Link>
        </div>

        {loadingMatches ? (
          <div className="space-y-3">
            <SkeletonLoader.Card lines={2} />
            <SkeletonLoader.Card lines={2} />
          </div>
        ) : matches.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-gov">
            <Sparkles size={40} className="mx-auto text-slate-300 mb-2" />
            <p className="text-sm font-bold text-gov-navy-950">{t('matches_no_results', 'No matches found yet')}</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {t('matches_no_results_sub', 'We need a bit more information about your business to calculate scheme qualification scores.')}
            </p>
            <Link 
              to="/onboarding" 
              className="mt-4 inline-block px-5 py-2.5 rounded-xl bg-gov-navy-950 text-white text-xs font-bold"
            >
              {t('onboard_title', 'Complete My Profile')}
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {matches.slice(0, 3).map((m) => {
              const score = m.match_score || 85;
              const isHigh = score >= 80;

              return (
                <div 
                  key={m.scheme_id || m.id}
                  className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-gov-navy-900/40 hover:shadow-gov-hover transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Header with Match % and Ministry */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          {m.ministry || 'Government of India'}
                        </span>
                        <h3 className="font-bold text-base text-gov-navy-950 mt-0.5 line-clamp-1">
                          {m.name}
                        </h3>
                      </div>
                      <div className={`px-2.5 py-1 rounded-xl font-extrabold text-xs flex-shrink-0 ${
                        isHigh ? 'bg-gov-emerald-50 text-gov-emerald-700 border border-gov-emerald-200' : 'bg-gov-saffron-50 text-gov-saffron-700 border border-gov-saffron-200'
                      }`}>
                        {score}% {t('matches_badge_match', 'Match')}
                      </div>
                    </div>

                    {/* Why You Match Explanation (MANDATORY REQUIREMENT) */}
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs text-slate-700">
                      <p className="font-semibold text-gov-navy-900 flex items-center gap-1 mb-1">
                        <CheckCircle2 size={13} className="text-gov-emerald-600" />
                        <span>{t('matches_why_match', 'Why You Match')}:</span>
                      </p>
                      <p className="text-[11px] text-slate-600 leading-snug line-clamp-2">
                        {m.ai_explanation || "You appear eligible because your enterprise category, location, and turnover align with main ministry criteria."}
                      </p>
                    </div>

                    {/* Benefit callout */}
                    <div className="flex items-start gap-2 text-xs">
                      <IndianRupee size={15} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
                      <p className="text-slate-700 font-medium line-clamp-2 text-[11px]">
                        <strong>{t('schemes_subsidy_rate', 'Benefit')}:</strong> {m.benefit_description || 'Capital subsidy and collateral-free credit facilitation'}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => setSelectedScheme(m)}
                      className="text-xs font-bold text-gov-navy-900 hover:text-gov-saffron-700 transition-colors"
                    >
                      {t('btn_view_details', 'View Details')}
                    </button>
                    <button
                      onClick={() => setSelectedScheme(m)}
                      className="px-3.5 py-2 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-semibold shadow-sm transition-all"
                    >
                      {t('btn_apply_scheme', 'Check Eligibility')}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Quick Action Cards: Ask AI, Find CSC, Upload Document */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link 
          to="/chat"
          className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-slate-300 shadow-gov flex items-center gap-4 transition-all group"
        >
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
            <MessageSquare size={24} />
          </div>
          <div>
            <p className="font-bold text-sm text-gov-navy-950">{t('nav_ai_chat', 'AI Assistant')}</p>
            <p className="text-xs text-slate-500 mt-0.5">{t('dash_action_chat_desc', 'Ask questions about eligibility & rules')}</p>
          </div>
        </Link>

        <Link 
          to="/csc"
          className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-slate-300 shadow-gov flex items-center gap-4 transition-all group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gov-emerald-50 text-gov-emerald-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
            <MapPin size={24} />
          </div>
          <div>
            <p className="font-bold text-sm text-gov-navy-950">{t('nav_csc_locator', 'Locate CSC Center')}</p>
            <p className="text-xs text-slate-500 mt-0.5">{t('dash_action_partners_desc', 'Find SCAs, Lead Banks, RRBs & CSCs')}</p>
          </div>
        </Link>

        <Link 
          to="/documents"
          className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-slate-300 shadow-gov flex items-center gap-4 transition-all group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gov-saffron-50 text-gov-saffron-600 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
            <FolderUp size={24} />
          </div>
          <div>
            <p className="font-bold text-sm text-gov-navy-950">{t('nav_documents', 'Document Center')}</p>
            <p className="text-xs text-slate-500 mt-0.5">{t('dash_action_docs_desc', 'Instant OCR scan for Aadhaar & PAN')}</p>
          </div>
        </Link>
      </div>

      {/* Scheme Detail Deep-Dive Modal */}
      {selectedScheme && (
        <SchemeDetailModal
          scheme={selectedScheme}
          isOpen={!!selectedScheme}
          onClose={() => setSelectedScheme(null)}
          onApply={async (id) => {
            const res = await api().post('/applications', { scheme_id: id });
            queryClient.invalidateQueries('applications_list');
            return res.data;
          }}
        />
      )}

    </div>
  );
}
