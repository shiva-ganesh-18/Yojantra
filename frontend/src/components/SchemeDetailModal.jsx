import React, { useState } from 'react';
import { 
  X, CheckCircle2, AlertTriangle, Calendar, Building, IndianRupee, 
  FileText, ExternalLink, Bookmark, ShieldCheck, ArrowRight, Clock, HelpCircle
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export default function SchemeDetailModal({ 
  scheme, 
  isOpen, 
  onClose, 
  onApply, 
  isBookmarked, 
  onBookmarkToggle 
}) {
  const navigate = useNavigate();
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  if (!isOpen || !scheme) return null;

  const matchScore = scheme.match_score || 85;
  const isHighMatch = matchScore >= 80;

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

  // Parse required documents if array or string
  const documents = Array.isArray(scheme.documents_required) 
    ? scheme.documents_required 
    : ['Aadhaar Card', 'PAN Card', 'Bank Passbook / Statement', 'Business Registration or UDYAM', 'Passport Sized Photograph'];

  // Parse eligibility criteria
  const eligibility = Array.isArray(scheme.eligibility_criteria)
    ? scheme.eligibility_criteria
    : [
        'Open to micro, small, and medium enterprise owners',
        'Valid Indian citizenship and resident proof in eligible district',
        'Age must be 18 years or above with active bank account'
      ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gov-navy-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 sm:py-8 animate-in fade-in duration-200">
      <div 
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden text-gov-navy-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="bg-gradient-to-r from-gov-navy-900 via-gov-navy-800 to-gov-navy-900 text-white p-5 sm:p-6 relative border-b border-gov-navy-700/50">
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

          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white leading-snug">
                {scheme.name}
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 mt-1">
                Official Scheme Code: <span className="font-mono text-gov-saffron-200">{scheme.code || 'GOV-SCH-AI'}</span>
              </p>
            </div>

            <div className="flex-shrink-0 text-right">
              <div className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl font-bold text-sm sm:text-base border shadow-sm ${
                isHighMatch 
                  ? 'bg-gov-emerald-500/20 text-gov-emerald-300 border-gov-emerald-400/30' 
                  : 'bg-gov-saffron-500/20 text-gov-saffron-300 border-gov-saffron-400/30'
              }`}>
                <ShieldCheck size={18} />
                <span>{matchScore}% Match</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1 font-medium">
                {isHighMatch ? 'High Eligibility Match' : 'Conditional Match'}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6 custom-scrollbar">

          {/* AI Explanation Callout Box */}
          <div className="bg-gradient-to-br from-gov-navy-50/70 to-gov-emerald-50/40 border border-gov-emerald-200/80 rounded-xl p-4 sm:p-5">
            <div className="flex items-center gap-2 text-gov-navy-900 font-semibold mb-2 text-sm sm:text-base">
              <span className="flex h-6 w-6 rounded-full bg-gov-emerald-600 text-white items-center justify-center text-xs font-bold shadow-sm">
                AI
              </span>
              <span>Why SchemeMatch AI Matched You</span>
            </div>
            <p className="text-xs sm:text-sm text-slate-700 leading-relaxed mb-3">
              {scheme.ai_explanation || 
               "You appear eligible because your business category, operational stage, turnover profile, and location align with the central ministry eligibility parameters."}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2 text-gov-emerald-800 bg-gov-emerald-100/60 px-2.5 py-1.5 rounded-lg border border-gov-emerald-200">
                <CheckCircle2 size={14} className="text-gov-emerald-600 flex-shrink-0" />
                <span>Your enterprise category is prioritized</span>
              </div>
              <div className="flex items-center gap-2 text-gov-emerald-800 bg-gov-emerald-100/60 px-2.5 py-1.5 rounded-lg border border-gov-emerald-200">
                <CheckCircle2 size={14} className="text-gov-emerald-600 flex-shrink-0" />
                <span>Location & state boundaries eligible</span>
              </div>
              <div className="flex items-center gap-2 text-gov-emerald-800 bg-gov-emerald-100/60 px-2.5 py-1.5 rounded-lg border border-gov-emerald-200">
                <CheckCircle2 size={14} className="text-gov-emerald-600 flex-shrink-0" />
                <span>Funding requirement matches ceiling limits</span>
              </div>
              <div className="flex items-center gap-2 text-gov-saffron-800 bg-gov-saffron-100/60 px-2.5 py-1.5 rounded-lg border border-gov-saffron-200">
                <AlertTriangle size={14} className="text-gov-saffron-600 flex-shrink-0" />
                <span>Bank passbook verification required before final submit</span>
              </div>
            </div>
          </div>

          {/* Key Financial Benefit Banner */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gov-emerald-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
              <IndianRupee size={20} />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Primary Financial Benefit</h4>
              <p className="text-base sm:text-lg font-bold text-gov-navy-900 mt-0.5">
                {scheme.benefit_description || 'Direct Capital Subsidy up to 35% with collateral-free credit facilitation'}
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Disbursed through scheduled commercial banks and digital Direct Benefit Transfer (DBT).
              </p>
            </div>
          </div>

          {/* Scheme Overview */}
          <div>
            <h3 className="text-sm font-bold text-gov-navy-900 uppercase tracking-wider text-slate-500 mb-2">
              Scheme Overview
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed">
              {scheme.description || 
               'This program is launched to provide sustainable livelihood and self-employment generation opportunities for traditional artisans, small enterprise founders, and marginalized community entrepreneurs.'}
            </p>
          </div>

          {/* Eligibility Criteria & Documents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Eligibility Section */}
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-gov-navy-900 mb-3 flex items-center gap-2">
                <ShieldCheck size={16} className="text-gov-navy-700" />
                Eligibility Criteria
              </h4>
              <ul className="space-y-2.5">
                {eligibility.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-700 leading-normal">
                    <span className="w-1.5 h-1.5 rounded-full bg-gov-navy-700 mt-1.5 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Documents Section */}
            <div className="bg-white border border-slate-200 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-gov-navy-900 mb-3 flex items-center gap-2">
                <FileText size={16} className="text-gov-navy-700" />
                Required Documents
              </h4>
              <ul className="space-y-2">
                {documents.map((doc, idx) => (
                  <li key={idx} className="flex items-center justify-between text-xs bg-slate-50 px-2.5 py-2 rounded-lg border border-slate-200/60">
                    <span className="font-medium text-slate-800">{doc}</span>
                    <span className="text-[10px] font-semibold text-gov-emerald-700 bg-gov-emerald-100/70 px-2 py-0.5 rounded">
                      Accepted via OCR
                    </span>
                  </li>
                ))}
              </ul>
              <Link 
                to="/documents" 
                onClick={onClose}
                className="mt-3 text-xs font-semibold text-gov-saffron-700 hover:text-gov-saffron-800 flex items-center gap-1 block text-right"
              >
                Upload missing documents in Document Center &rarr;
              </Link>
            </div>
          </div>

          {/* 4-Step Application Roadmap */}
          <div>
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">
              Application Roadmap
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                { step: '1', title: 'Prepare Documents', desc: 'Scan Aadhaar, PAN, & Bank proof' },
                { step: '2', title: 'Verify Details', desc: 'Auto-fill form via SchemeMatch AI' },
                { step: '3', title: 'Submit Application', desc: 'Direct portal API transmission' },
                { step: '4', title: 'Track Status', desc: 'Live DBT & verification alerts' },
              ].map((s) => (
                <div key={s.step} className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
                  <span className="w-6 h-6 rounded-full bg-gov-navy-900 text-white inline-flex items-center justify-center text-xs font-bold mb-1.5 shadow-sm">
                    {s.step}
                  </span>
                  <p className="text-xs font-bold text-gov-navy-900">{s.title}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Important Dates */}
          {scheme.application_deadline && (
            <div className="flex items-center gap-2 p-3 bg-red-50/70 border border-red-200 rounded-xl text-xs text-red-800">
              <Calendar size={15} className="text-red-600 flex-shrink-0" />
              <span>Application Deadline: <strong>{new Date(scheme.application_deadline).toLocaleDateString(undefined, { dateStyle: 'long' })}</strong>. Early submission is strongly advised.</span>
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
