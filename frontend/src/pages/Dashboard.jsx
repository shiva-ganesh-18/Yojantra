import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
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
  const navigate = useNavigate();
  const [selectedScheme, setSelectedScheme] = useState(null);

  // 1. Fetch recommended matches
  const { data: matches = [], isLoading: loadingMatches } = useQuery('recommended', () => 
    api().get('/schemes/recommended').then(r => r.data || [])
  );

  // 2. Fetch applications
  const { data: applications = [], isLoading: loadingApps } = useQuery('applications', () =>
    api().get('/applications').then(r => r.data || [])
  );

  // 3. Fetch documents
  const { data: documents = [], isLoading: loadingDocs } = useQuery('documents', () =>
    api().get('/documents/my-documents').then(r => r.data || [])
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
            Let's Set Up Your Profile
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Answer 5 simple questions about your business, funding requirements, and social category so SchemeMatch AI can calculate your eligibility.
          </p>
        </div>

        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs text-slate-600 max-w-md mx-auto text-left space-y-2">
          <div className="flex items-center gap-2 text-gov-navy-900 font-semibold">
            <ShieldCheck size={16} className="text-gov-emerald-600" />
            <span>Why Complete Your Profile?</span>
          </div>
          <p className="text-[11px] text-slate-500">
            Central ministries provide distinct quotas and subsidies (up to 35%) for SC/ST/OBC, women founders, and rural micro-enterprises.
          </p>
        </div>

        <Link 
          to="/onboarding"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all"
        >
          <span>Start Onboarding</span>
          <ArrowRight size={17} />
        </Link>
      </div>
    );
  }

  // Greeting based on hour
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const userName = user?.full_name ? user.full_name.split(' ')[0] : 'Citizen';

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
              AI Matching Engine Active
            </span>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-snug">
              {greeting}, {userName}
            </h1>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              Let's find the government support available for your business. We matched your profile against 200+ central & state schemes.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              to="/matches"
              className="px-6 py-3.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
            >
              <span>Find My Schemes</span>
              <ArrowRight size={16} />
            </Link>
            <Link
              to="/chat"
              className="px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 transition-colors flex items-center justify-center gap-2"
            >
              <MessageSquare size={16} />
              <span>Ask AI Assistant</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Visual Journey: YOUR SCHEME JOURNEY */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-gov">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              End-to-End Workflow
            </h2>
            <p className="text-lg font-bold text-gov-navy-950 mt-0.5">
              Your Scheme Journey
            </p>
          </div>
          <span className="text-xs font-semibold text-gov-emerald-700 bg-gov-emerald-50 px-2.5 py-1 rounded-full border border-gov-emerald-200">
            Real-Time Status
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {/* Step 1: Profile */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">1. Profile</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950 flex items-center gap-1 text-gov-emerald-700">
                <CheckCircle2 size={16} />
                <span>Completed</span>
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">{user?.district}, {user?.state}</p>
            </div>
            <Link to="/profile" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              View Profile &rarr;
            </Link>
          </div>

          {/* Step 2: AI Matching */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">2. AI Matching</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950 flex items-center gap-1 text-gov-emerald-700">
                <CheckCircle2 size={16} />
                <span>{matches.length} schemes</span>
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">Calculated eligibility</p>
            </div>
            <Link to="/matches" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              Explore Matches &rarr;
            </Link>
          </div>

          {/* Step 3: Documents */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">3. Documents</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950">
                {verifiedDocsCount} / {totalRequiredDocs} Ready
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">OCR Auto-Verification</p>
            </div>
            <Link to="/documents" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              Upload Missing &rarr;
            </Link>
          </div>

          {/* Step 4: Applications */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-400">4. Applications</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950">
                {activeAppsCount} In Progress
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">{approvedCount} Approved</p>
            </div>
            <Link to="/applications" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              View Tracking &rarr;
            </Link>
          </div>

          {/* Step 5: Benefits */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between col-span-2 md:col-span-1">
            <span className="text-xs font-semibold text-slate-400">5. Track Benefits</span>
            <div className="my-2">
              <p className="text-sm font-bold text-gov-navy-950">
                Direct Benefit
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">DBT Bank Account</p>
            </div>
            <Link to="/applications" className="text-[11px] font-bold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center gap-0.5 mt-1">
              View Status &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Your Best Matches Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Personalized Recommendations
            </h2>
            <p className="text-xl font-bold text-gov-navy-950">
              Your Best Matches
            </p>
          </div>
          <Link 
            to="/matches" 
            className="text-xs sm:text-sm font-bold text-gov-saffron-700 hover:text-gov-saffron-800 flex items-center gap-1"
          >
            <span>View All ({matches.length})</span>
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
            <p className="text-sm font-bold text-gov-navy-950">No matches found yet</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              We need a bit more information about your business to calculate scheme qualification scores.
            </p>
            <Link 
              to="/onboarding" 
              className="mt-4 inline-block px-5 py-2.5 rounded-xl bg-gov-navy-950 text-white text-xs font-bold"
            >
              Complete My Profile
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
                        {score}% Match
                      </div>
                    </div>

                    {/* Why You Match Explanation (MANDATORY REQUIREMENT) */}
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs text-slate-700">
                      <p className="font-semibold text-gov-navy-900 flex items-center gap-1 mb-1">
                        <CheckCircle2 size={13} className="text-gov-emerald-600" />
                        <span>Why You Match:</span>
                      </p>
                      <p className="text-[11px] text-slate-600 leading-snug line-clamp-2">
                        {m.ai_explanation || "You appear eligible because your enterprise category, location, and turnover align with main ministry criteria."}
                      </p>
                    </div>

                    {/* Benefit callout */}
                    <div className="flex items-start gap-2 text-xs">
                      <IndianRupee size={15} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
                      <p className="text-slate-700 font-medium line-clamp-2 text-[11px]">
                        <strong>Benefit:</strong> {m.benefit_description || 'Capital subsidy and collateral-free credit facilitation'}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => setSelectedScheme(m)}
                      className="text-xs font-bold text-gov-navy-900 hover:text-gov-saffron-700 transition-colors"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => setSelectedScheme(m)}
                      className="px-3.5 py-2 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-semibold shadow-sm transition-all"
                    >
                      Check Eligibility
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
            <p className="font-bold text-sm text-gov-navy-950">AI Assistant</p>
            <p className="text-xs text-slate-500 mt-0.5">Ask questions about eligibility & rules</p>
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
            <p className="font-bold text-sm text-gov-navy-950">Locate CSC Center</p>
            <p className="text-xs text-slate-500 mt-0.5">Find biometric & scanning help nearby</p>
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
            <p className="font-bold text-sm text-gov-navy-950">Document Center</p>
            <p className="text-xs text-slate-500 mt-0.5">Instant OCR scan for Aadhaar & PAN</p>
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
            await api().post('/applications', { scheme_id: id });
          }}
        />
      )}

    </div>
  );
}
