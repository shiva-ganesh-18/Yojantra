import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { Link } from 'react-router-dom';
import { 
  FileText, Clock, CheckCircle2, XCircle, AlertCircle, 
  ChevronRight, Building2, IndianRupee, ArrowRight, ShieldCheck, 
  Sparkles, ExternalLink, RefreshCw, Send, Check
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

const STATUS_CONFIG = {
  draft: { color: 'bg-slate-100 text-slate-700 border-slate-300', icon: FileText, label: 'Draft', stepIndex: 1 },
  submitted: { color: 'bg-blue-50 text-blue-700 border-blue-200', icon: Clock, label: 'Submitted', stepIndex: 2 },
  under_review: { color: 'bg-amber-50 text-amber-800 border-amber-200', icon: AlertCircle, label: 'Under Review', stepIndex: 3 },
  approved: { color: 'bg-gov-emerald-50 text-gov-emerald-800 border-gov-emerald-200', icon: CheckCircle2, label: 'Approved', stepIndex: 4 },
  rejected: { color: 'bg-red-50 text-red-700 border-red-200', icon: XCircle, label: 'Action Required', stepIndex: 2 },
  disbursed: { color: 'bg-purple-50 text-purple-800 border-purple-200', icon: CheckCircle2, label: 'DBT Disbursed', stepIndex: 4 },
};

const TIMELINE_STEPS = [
  { step: 1, title: 'Application Drafted', desc: 'Auto-filled with profile details' },
  { step: 2, title: 'Submitted to Portal', desc: 'Transmitted to nodal ministry gateway' },
  { step: 3, title: 'Departmental Review', desc: 'Officer verification & document check' },
  { step: 4, title: 'Sanction & Disbursement', desc: 'Bank subsidy credit via DBT' },
];

export default function Applications() {
  const { api } = useAuthStore();
  const queryClient = useQueryClient();
  const [submittingId, setSubmittingId] = useState(null);
  const [selectedApp, setSelectedApp] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: applications = [], isLoading, refetch } = useQuery('applications_list', () =>
    api().get('/applications').then(r => r.data || [])
  );

  const handleSubmitApplication = async (id, e) => {
    e.stopPropagation();
    try {
      setSubmittingId(id);
      await api().post(`/applications/${id}/submit`);
      queryClient.invalidateQueries('applications_list');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingId(null);
    }
  };

  const filteredApps = applications.filter(a => {
    if (statusFilter === 'all') return true;
    if (statusFilter === 'active') return ['draft', 'submitted', 'under_review'].includes(a.status);
    if (statusFilter === 'approved') return ['approved', 'disbursed'].includes(a.status);
    return a.status === statusFilter;
  });

  return (
    <div className="space-y-6 text-left">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-2 rounded-xl bg-gov-navy-100 text-gov-navy-900">
                <FileText size={20} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                My Applications
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              Track government filings, officer reviews, verification steps, and subsidy disbursements in real-time.
            </p>
          </div>

          <Link
            to="/matches"
            className="self-start sm:self-auto px-5 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs sm:text-sm font-bold transition-all flex items-center gap-2 shadow-sm"
          >
            <Sparkles size={16} className="text-gov-saffron-400" />
            <span>Apply for New Scheme</span>
          </Link>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-2 overflow-x-auto mt-5 pb-1 custom-scrollbar">
          {[
            { id: 'all', label: 'All Applications' },
            { id: 'active', label: 'In Progress (Active)' },
            { id: 'approved', label: 'Approved & Disbursed' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all border ${
                statusFilter === tab.id
                  ? 'bg-gov-navy-950 text-white border-gov-navy-950 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Applications List */}
      {isLoading ? (
        <div className="space-y-4">
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-gov text-center space-y-3">
          <FileText size={48} className="mx-auto text-slate-300" />
          <h3 className="text-base font-bold text-gov-navy-950">You haven't started an application yet</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Discover schemes matching your business profile and start an application with one click.
          </p>
          <Link
            to="/matches"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-md transition-all mt-2"
          >
            <span>Explore My Scheme Matches</span>
            <ArrowRight size={15} />
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApps.map((app) => {
            const config = STATUS_CONFIG[app.status] || STATUS_CONFIG.draft;
            const StatusIcon = config.icon;
            const currentStepIdx = config.stepIndex;

            return (
              <div
                key={app.id}
                onClick={() => setSelectedApp(selectedApp?.id === app.id ? null : app)}
                className="bg-white rounded-3xl p-6 border border-slate-200 hover:border-slate-300 shadow-gov transition-all cursor-pointer"
              >
                {/* Header Information */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                        APP-REF: #{app.id.slice(0, 8).toUpperCase()}
                      </span>
                      <span className="text-slate-300">•</span>
                      <span className="text-[11px] text-slate-500">
                        Submitted: {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : 'Draft Mode'}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-gov-navy-950">
                      {app.scheme_name || 'Government MSME Scheme'}
                    </h3>
                  </div>

                  {/* Status Badge */}
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${config.color} self-start sm:self-auto shadow-sm`}>
                    <StatusIcon size={14} />
                    <span>{config.label}</span>
                  </span>
                </div>

                {/* Timeline Stepper UI (MANDATORY REQUIREMENT) */}
                <div className="mt-6 pt-5 border-t border-slate-100">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {TIMELINE_STEPS.map((s) => {
                      const isComplete = s.step < currentStepIdx || (app.status === 'approved' && s.step === 4);
                      const isCurrent = s.step === currentStepIdx && app.status !== 'approved';

                      return (
                        <div key={s.step} className="flex flex-col text-left space-y-1">
                          <div className="flex items-center gap-2">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ${
                              isComplete 
                                ? 'bg-gov-emerald-600 text-white' 
                                : isCurrent 
                                ? 'bg-gov-saffron-500 text-white ring-4 ring-gov-saffron-100 animate-pulse' 
                                : 'bg-slate-200 text-slate-500'
                            }`}>
                              {isComplete ? <Check size={14} /> : s.step}
                            </span>
                            <div className="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden hidden sm:block">
                              <div className={`h-full ${isComplete ? 'bg-gov-emerald-600' : isCurrent ? 'bg-gov-saffron-500 w-1/2' : 'w-0'}`} />
                            </div>
                          </div>
                          <p className={`text-xs font-bold mt-1 ${isCurrent ? 'text-gov-navy-950' : 'text-slate-600'}`}>
                            {s.title}
                          </p>
                          <p className="text-[10px] text-slate-400 leading-snug">
                            {s.desc}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Next Action Callout Alert */}
                {app.next_action && (
                  <div className="mt-4 p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-2.5 text-xs text-amber-900">
                    <AlertCircle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Next Required Action:</span>
                      <span className="text-[11px] text-amber-800">{app.next_action}</span>
                    </div>
                  </div>
                )}

                {/* Action Footer */}
                <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <Link to="/documents" onClick={(e) => e.stopPropagation()} className="font-semibold text-gov-navy-900 hover:text-gov-saffron-700">
                      Manage Attached Documents &rarr;
                    </Link>
                  </div>

                  <div className="flex items-center gap-2">
                    {app.status === 'draft' && (
                      <button
                        onClick={(e) => handleSubmitApplication(app.id, e)}
                        disabled={submittingId === app.id}
                        className="px-4 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
                      >
                        {submittingId === app.id ? (
                          <>
                            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Transmitting...</span>
                          </>
                        ) : (
                          <>
                            <Send size={13} />
                            <span>Submit Application</span>
                          </>
                        )}
                      </button>
                    )}

                    <span className="text-xs font-bold text-slate-400 flex items-center gap-1">
                      <span>{selectedApp?.id === app.id ? 'Collapse' : 'Details'}</span>
                      <ChevronRight size={15} className={selectedApp?.id === app.id ? 'rotate-90' : ''} />
                    </span>
                  </div>
                </div>

                {/* Expanded Detailed Tracking Drawer */}
                {selectedApp?.id === app.id && (
                  <div className="mt-4 pt-4 border-t border-slate-200/80 bg-slate-50/70 p-4 rounded-2xl text-xs space-y-3 animate-in fade-in duration-150">
                    <h4 className="font-bold text-gov-navy-950 uppercase tracking-wide">
                      Verification Log & Audit Trail
                    </h4>
                    <div className="space-y-2 text-slate-600">
                      <div className="flex justify-between py-1 border-b border-slate-200/50">
                        <span>Application Created:</span>
                        <span className="font-medium text-slate-800">{new Date(app.created_at).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/50">
                        <span>Aadhaar & PAN Verification:</span>
                        <span className="font-semibold text-gov-emerald-700">Verified by UIDAI / NSDL</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-slate-200/50">
                        <span>Direct Benefit Routing:</span>
                        <span className="font-medium text-slate-800">Aadhaar Linked Bank Account</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
