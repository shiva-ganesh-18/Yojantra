import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { Link } from 'react-router-dom';
import { 
  FileText, Clock, CheckCircle2, XCircle, AlertCircle, 
  ChevronRight, Building2, IndianRupee, ArrowRight, ShieldCheck, 
  Sparkles, ExternalLink, RefreshCw, Send, Check, Copy, Info, 
  ListChecks, AlertTriangle, HelpCircle, ArrowUpRight,
  UploadCloud, Phone, Mail, MapPin, CreditCard, Award, ArrowDownCircle
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';
import { integrationService } from '../services/integrationService';

const STATUS_CONFIG = {
  draft: { color: 'bg-slate-100 text-slate-700 border-slate-300', icon: FileText, label: 'Draft', stepIndex: 1 },
  submitted: { color: 'bg-blue-50 text-blue-700 border-blue-200', icon: Clock, label: 'Submitted & Routed', stepIndex: 2 },
  under_review: { color: 'bg-amber-50 text-amber-800 border-amber-200', icon: AlertCircle, label: 'Under Review', stepIndex: 3 },
  approved: { color: 'bg-gov-emerald-50 text-gov-emerald-800 border-gov-emerald-200', icon: CheckCircle2, label: 'Sanction Approved', stepIndex: 4 },
  rejected: { color: 'bg-red-50 text-red-700 border-red-200', icon: XCircle, label: 'Application Rejected', stepIndex: 2 },
  disbursed: { color: 'bg-purple-50 text-purple-800 border-purple-200', icon: CheckCircle2, label: 'DBT Disbursed', stepIndex: 4 },
};

const ROUTING_STATUS_CONFIG = {
  NOT_ROUTED: { color: 'bg-slate-100 text-slate-700 border-slate-300', label: 'Not Routed' },
  PARTNER_ASSIGNED: { color: 'bg-indigo-50 text-indigo-700 border-indigo-200', label: 'Partner Assigned' },
  ROUTED_TO_PARTNER: { color: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Routed to Partner' },
  PARTNER_RECEIVED: { color: 'bg-cyan-50 text-cyan-800 border-cyan-200', label: 'Partner Received' },
  UNDER_REVIEW: { color: 'bg-amber-50 text-amber-800 border-amber-200', label: 'Under Review' },
  DOCUMENTS_REQUIRED: { color: 'bg-orange-50 text-orange-800 border-orange-300', label: 'Documents Required' },
  APPROVED: { color: 'bg-emerald-50 text-emerald-800 border-emerald-200', label: 'Approved' },
  REJECTED: { color: 'bg-red-50 text-red-700 border-red-200', label: 'Rejected' },
  DISBURSEMENT_PROCESSING: { color: 'bg-violet-50 text-violet-800 border-violet-200', label: 'Disbursement Processing' },
  DISBURSED: { color: 'bg-purple-50 text-purple-800 border-purple-200', label: 'Disbursed' },
};

const ACKNOWLEDGEMENT_CONFIG = {
  NOT_ROUTED: { label: 'Not Routed', color: 'text-slate-600 bg-slate-100 border-slate-200' },
  PENDING: { label: 'Pending Partner Acknowledgement', color: 'text-amber-800 bg-amber-50 border-amber-300' },
  ACKNOWLEDGED: { label: 'Receipt Confirmed by Partner', color: 'text-emerald-800 bg-emerald-50 border-emerald-300' },
  REJECTED: { label: 'Routing Terminated', color: 'text-red-800 bg-red-50 border-red-300' },
};

export default function Applications() {
  const { api } = useAuthStore();
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [submittingId, setSubmittingId] = useState(null);
  const [selectedApp, setSelectedApp] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [validationModalApp, setValidationModalApp] = useState(null);
  const [validationData, setValidationData] = useState(null);
  const [checklistData, setChecklistData] = useState(null);
  const [partnerRoutingData, setPartnerRoutingData] = useState(null);
  const [loadingValidation, setLoadingValidation] = useState(false);
  const [copiedRef, setCopiedRef] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  // Document Resolution Modal State
  const [resolveModalApp, setResolveModalApp] = useState(null);
  const [resolveComments, setResolveComments] = useState('');
  const [resolvingDoc, setResolvingDoc] = useState(false);
  const [resolveError, setResolveError] = useState(null);
  const [resolveSuccess, setResolveSuccess] = useState(null);

  // Gateway Sync State
  const [syncingAppId, setSyncingAppId] = useState(null);
  const [syncNotice, setSyncNotice] = useState(null);

  const getErrorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail ?? err?.details?.detail;
    if (typeof detail === 'string' && detail) return detail;
    if (detail && typeof detail === 'object' && detail.message) {
      const extra = Array.isArray(detail.errors) && detail.errors.length ? ` (${detail.errors.join(', ')})` : '';
      return `${detail.message}${extra}`;
    }
    if (typeof err?.message === 'string' && err.message) return err.message;
    return fallback;
  };

  const handleSyncStatus = async (appId, e) => {
    if (e) e.stopPropagation();
    setSyncingAppId(appId);
    setSyncNotice(null);
    try {
      const res = await integrationService.syncApplicationStatus(appId);
      queryClient.invalidateQueries('applications_list');
      setSyncNotice({ appId, message: res.message || 'Status synchronized with nodal gateway.' });
      setTimeout(() => setSyncNotice(null), 4000);
    } catch (err) {
      setSyncNotice({ appId, error: getErrorMessage(err, 'Status sync temporarily unavailable') });
      setTimeout(() => setSyncNotice(null), 4000);
    } finally {
      setSyncingAppId(null);
    }
  };

  const { data: applications = [], isLoading } = useQuery('applications_list', () =>
    api().get('/applications').then(r => r.data || [])
  );

  const handleCopyRef = (refCode, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(refCode);
    setCopiedRef(refCode);
    setTimeout(() => setCopiedRef(null), 2000);
  };

  const handleOpenValidation = async (app, e) => {
    e.stopPropagation();
    setValidationModalApp(app);
    setLoadingValidation(true);
    setSubmitError(null);
    setPartnerRoutingData(null);
    try {
      const [valRes, chkRes, partRes] = await Promise.all([
        api().get(`/applications/${app.id}/validate`),
        api().get(`/applications/${app.id}/checklist`),
        api().get(`/applications/${app.id}/partners`).catch(() => ({ data: null }))
      ]);
      setValidationData(valRes.data);
      setChecklistData(chkRes.data);
      setPartnerRoutingData(partRes?.data || null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingValidation(false);
    }
  };

  const handleSubmitApplication = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      setSubmittingId(id);
      setSubmitError(null);
      await api().post(`/applications/${id}/submit`);
      queryClient.invalidateQueries('applications_list');
      setValidationModalApp(null);
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Submission failed. Please check document and profile requirements.'));
    } finally {
      setSubmittingId(null);
    }
  };

  const handleOpenResolveModal = (app, e) => {
    if (e) e.stopPropagation();
    setResolveModalApp(app);
    setResolveComments('');
    setResolveError(null);
    setResolveSuccess(null);
  };

  const handleResolveDocumentRequest = async () => {
    if (!resolveModalApp) return;
    if (!resolveComments.trim()) {
      setResolveError('Please provide compliance notes or a summary of updated documents.');
      return;
    }
    setResolvingDoc(true);
    setResolveError(null);
    try {
      await api().post(`/applications/${resolveModalApp.id}/resolve-document-request`, {
        comments: resolveComments,
        uploaded_doc_ids: []
      });
      setResolveSuccess('Compliance response submitted! Application returned to channel partner for review.');
      queryClient.invalidateQueries('applications_list');
      setTimeout(() => {
        setResolveModalApp(null);
        setResolveSuccess(null);
      }, 1600);
    } catch (err) {
      setResolveError(getErrorMessage(err, 'Failed to submit response. Please try again.'));
    } finally {
      setResolvingDoc(false);
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
                {t('apps_title', 'My Applications & Tracking')}
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              {t('apps_subtitle', 'End-to-end transparent application tracking: assigned partner status, scrutiny queries, sanction decisions, and DBT disbursement progress.')}
            </p>
          </div>

          <Link
            to="/matches"
            className="self-start sm:self-auto px-5 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs sm:text-sm font-bold transition-all flex items-center gap-2 shadow-sm"
          >
            <Sparkles size={16} className="text-gov-saffron-400" />
            <span>{t('btn_apply_scheme', 'Apply for New Scheme')}</span>
          </Link>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-2 overflow-x-auto mt-5 pb-1 custom-scrollbar">
          {[
            { id: 'all', label: t('apps_tab_all', 'All Applications') },
            { id: 'active', label: t('apps_tab_active', 'In Progress (Active)') },
            { id: 'approved', label: t('apps_tab_approved', 'Approved & Disbursed') },
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
            Discover schemes matching your business profile, complete pre-submission checks, and route your verified dossier.
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
        <div className="space-y-5">
          {filteredApps.map((app) => {
            const config = STATUS_CONFIG[app.status] || STATUS_CONFIG.draft;
            const StatusIcon = config.icon;
            const timelineEvents = app.timeline || [];
            const rawPartner = app.assigned_partner_details;
            // Backend sends {partner_name, partner_type, location, ...}; accept legacy keys too.
            const partnerDetails = rawPartner ? {
              name: rawPartner.partner_name || rawPartner.name,
              institution_type: rawPartner.partner_type || rawPartner.institution_type,
              address: rawPartner.location || rawPartner.address,
              district: rawPartner.district,
              state: rawPartner.state,
              distance_km: rawPartner.distance_km,
              is_active: rawPartner.is_active,
              contact_person: rawPartner.contact_person,
              contact_phone: rawPartner.contact_phone,
              contact_email: rawPartner.contact_email,
            } : null;
            const rawAlert = app.documents_required_alert ||
              (app.routing_status === 'DOCUMENTS_REQUIRED' ? {
                is_active: true,
                reason: 'Channel partner review officer has requested clarifications.',
                requested_by: app.assigned_partner_name || 'Nodal Officer'
              } : null);
            // Backend sends {reason, requested_at, requested_by}; accept legacy keys too.
            const docAlert = rawAlert ? {
              is_active: rawAlert.is_active,
              notes: rawAlert.reason || rawAlert.notes,
              requested_by_name: rawAlert.requested_by || rawAlert.requested_by_name,
              requested_at: rawAlert.requested_at,
              requested_documents: rawAlert.requested_documents || [],
            } : null;
            const rawApproval = app.approval_details;
            const approval = rawApproval ? {
              approval_date: rawApproval.approved_at || rawApproval.approval_date,
              sanction_reference_number: rawApproval.sanction_reference || rawApproval.sanction_reference_number,
              approved_amount_inr: rawApproval.subsidy_amount_inr ?? rawApproval.approved_amount_inr,
              approver_name: rawApproval.approved_by || rawApproval.approver_name,
              sanction_notes: rawApproval.reason_or_remarks || rawApproval.sanction_notes,
            } : null;
            const rawRejection = app.rejection_details;
            const rejection = rawRejection ? {
              rejected_at: rawRejection.rejected_at,
              rejection_reason: rawRejection.reason || rawRejection.rejection_reason,
              rejected_by: rawRejection.rejected_by,
              alternative_schemes_recommended: rawRejection.can_reapply ?? rawRejection.alternative_schemes_recommended,
            } : null;
            const rawDisb = app.disbursement_progress;
            const disbursement = rawDisb ? {
              status: rawDisb.status,
              amount_inr: rawDisb.amount_inr,
              account_routing: rawDisb.channel || rawDisb.account_routing,
              transaction_reference: rawDisb.reference_number || rawDisb.transaction_reference,
              remarks: rawDisb.remarks,
            } : null;
            const rawNext = app.clear_next_action || (app.next_action ? {
              action_type: 'GENERAL',
              action_title: 'Next Step',
              action_description: app.next_action,
              is_applicant_action_required: false
            } : null);
            // Backend sends {action_title, action_description, action_type, action_url, ...};
            // accept legacy {title, instruction, is_blocking, expected_timeline} too.
            const nextAction = rawNext ? {
              action_type: rawNext.action_type,
              title: rawNext.action_title || rawNext.title,
              instruction: rawNext.action_description || rawNext.instruction,
              expected_timeline: rawNext.expected_timeline,
              is_blocking: rawNext.is_applicant_action_required ?? rawNext.is_blocking ?? false,
              action_url: rawNext.action_url,
            } : null;

            return (
              <div
                key={app.id}
                onClick={() => setSelectedApp(selectedApp?.id === app.id ? null : app)}
                className="bg-white rounded-3xl p-6 border border-slate-200 hover:border-slate-300 shadow-gov transition-all cursor-pointer space-y-4"
              >
                {/* Header Information */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {app.partner_reference_code && (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-lg text-[11px] font-mono font-bold text-slate-700">
                          <span>REF: {app.partner_reference_code}</span>
                          <button
                            onClick={(e) => handleCopyRef(app.partner_reference_code, e)}
                            className="text-slate-400 hover:text-slate-700 transition-colors"
                            title="Copy reference number"
                          >
                            {copiedRef === app.partner_reference_code ? <Check size={12} className="text-gov-emerald-600" /> : <Copy size={12} />}
                          </button>
                        </div>
                      )}

                      <span className="text-slate-300 hidden sm:inline">•</span>
                      <span className="text-[11px] text-slate-500">
                        Initiated: {new Date(app.created_at).toLocaleDateString()}
                      </span>

                      {app.ministry && (
                        <span className="text-[11px] font-semibold text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                          {app.ministry}
                        </span>
                      )}
                    </div>

                    <h3 className="text-lg font-bold text-gov-navy-950 pt-1">
                      {app.scheme_name || 'Government MSME Scheme'}
                    </h3>
                  </div>

                  {/* Status & Readiness Badges */}
                  <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
                    {app.status === 'draft' && (
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                        app.is_ready_to_submit ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        Readiness: {app.readiness_score || 0}%
                      </span>
                    )}

                    {/* Partner Routing Status Badge */}
                    {app.routing_status && (
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${
                        ROUTING_STATUS_CONFIG[app.routing_status]?.color || 'bg-slate-100 text-slate-700 border-slate-300'
                      }`}>
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        <span>{ROUTING_STATUS_CONFIG[app.routing_status]?.label || app.routing_status}</span>
                      </span>
                    )}

                    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${config.color} shadow-sm`}>
                      <StatusIcon size={14} />
                      <span>{config.label}</span>
                    </span>
                  </div>
                </div>

                {/* Documents Required Alert Banner */}
                {docAlert?.is_active && (
                  <div 
                    onClick={(e) => e.stopPropagation()}
                    className="p-4 bg-orange-50/95 border-2 border-orange-300 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
                  >
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2 font-bold text-orange-950">
                        <AlertTriangle size={18} className="text-orange-600 flex-shrink-0 animate-bounce" />
                        <span className="text-sm">Action Needed: Additional Documents / Information Requested</span>
                      </div>
                      {docAlert.requested_by_name && (
                        <p className="text-orange-800 text-[11px]">
                          Requested by: <strong>{docAlert.requested_by_name}</strong>
                          {docAlert.requested_at && ` on ${new Date(docAlert.requested_at).toLocaleDateString()}`}
                        </p>
                      )}
                      {docAlert.notes && (
                        <p className="text-orange-900 bg-white/70 p-2 rounded-xl border border-orange-200/80 font-medium">
                          "{docAlert.notes}"
                        </p>
                      )}
                      {docAlert.requested_documents?.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="font-semibold text-orange-900">Required Items:</span>
                          {docAlert.requested_documents.map((doc, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-orange-100 text-orange-800 font-bold border border-orange-200">
                              {doc}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={(e) => handleOpenResolveModal(app, e)}
                      className="px-4 py-2 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1.5 self-start sm:self-center flex-shrink-0"
                    >
                      <UploadCloud size={14} />
                      <span>Respond & Submit</span>
                    </button>
                  </div>
                )}

                {/* Clear Next Action Banner */}
                {nextAction && !docAlert?.is_active && (
                  <div className={`p-3.5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                    nextAction.is_blocking 
                      ? 'bg-amber-50/90 border-amber-200 text-amber-950' 
                      : 'bg-slate-50 border-slate-200 text-slate-800'
                  }`}>
                    <div className="flex items-start gap-2.5">
                      <AlertCircle size={16} className={`flex-shrink-0 mt-0.5 ${nextAction.is_blocking ? 'text-amber-600' : 'text-gov-navy-600'}`} />
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-gov-navy-950">{nextAction.title || 'Next Step'}:</span>
                          {nextAction.expected_timeline && (
                            <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-white border border-slate-200 text-slate-600">
                              {nextAction.expected_timeline}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-600">{nextAction.instruction}</p>
                      </div>
                    </div>

                    {(nextAction.action_type === 'EXPLORE_ALTERNATIVES' || nextAction.action_type === 'REVIEW_REJECTION') && (
                      <Link
                        to={nextAction.action_url || '/matches'}
                        onClick={(e) => e.stopPropagation()}
                        className="self-start sm:self-center px-3 py-1.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white font-bold text-xs flex items-center gap-1.5 flex-shrink-0 shadow-sm"
                      >
                        <span>View Matching Schemes</span>
                        <ArrowRight size={13} />
                      </Link>
                    )}
                    {nextAction.action_type === 'UPLOAD_DOCS' && (
                      <Link
                        to={nextAction.action_url || '/documents'}
                        onClick={(e) => e.stopPropagation()}
                        className="self-start sm:self-center px-3 py-1.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-bold text-xs flex items-center gap-1.5 flex-shrink-0 shadow-sm"
                      >
                        <span>Upload Documents</span>
                        <ArrowRight size={13} />
                      </Link>
                    )}
                    {nextAction.action_type === 'SUBMIT_APPLICATION' && (
                      <button
                        onClick={(e) => handleOpenValidation(app, e)}
                        className="self-start sm:self-center px-3 py-1.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-xs flex items-center gap-1.5 flex-shrink-0 shadow-sm"
                      >
                        <span>Validate & Submit</span>
                        <Send size={12} />
                      </button>
                    )}
                  </div>
                )}

                {/* Milestone Timeline Stepper */}
                <div className="pt-2">
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    {timelineEvents.map((evt) => {
                      const isComplete = evt.status === 'completed';
                      const isCurrent = evt.status === 'current';
                      const isFailed = evt.status === 'failed';

                      return (
                        <div key={evt.step} className="flex flex-col text-left space-y-1 bg-slate-50/70 p-3 rounded-2xl border border-slate-100">
                          <div className="flex items-center justify-between gap-2">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-sm ${
                              isComplete 
                                ? 'bg-gov-emerald-600 text-white' 
                                : isCurrent 
                                ? 'bg-gov-saffron-500 text-white ring-4 ring-gov-saffron-100 animate-pulse' 
                                : isFailed
                                ? 'bg-red-500 text-white'
                                : 'bg-slate-200 text-slate-500'
                            }`}>
                              {isComplete ? <Check size={14} /> : isFailed ? <XCircle size={14} /> : evt.step}
                            </span>

                            <span className="text-[10px] font-mono text-slate-400">
                              {evt.timestamp ? new Date(evt.timestamp).toLocaleDateString() : 'Pending'}
                            </span>
                          </div>

                          <p className={`text-xs font-bold mt-1 line-clamp-1 ${isCurrent ? 'text-gov-navy-950 font-extrabold' : 'text-slate-700'}`}>
                            {evt.title}
                          </p>
                          <p className="text-[10px] text-slate-500 leading-snug line-clamp-2">
                            {evt.note}
                          </p>
                          {evt.channel_or_portal && (
                            <span className="text-[9px] font-medium text-slate-400 pt-0.5">
                              Via: {evt.channel_or_portal}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Approval Details Card */}
                {approval && (
                  <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-2xl text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-950 flex items-center gap-1.5 text-sm">
                        <Award size={18} className="text-gov-emerald-600" />
                        <span>Official Sanction Approval Notice</span>
                      </span>
                      {approval.approval_date && (
                        <span className="text-[11px] font-mono text-emerald-700">
                          Date: {new Date(approval.approval_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                      {approval.sanction_reference_number && (
                        <div className="bg-white p-2.5 rounded-xl border border-emerald-200">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">Sanction Reference</span>
                          <span className="font-mono font-bold text-emerald-900">{approval.sanction_reference_number}</span>
                        </div>
                      )}
                      {approval.approved_amount_inr != null && (
                        <div className="bg-white p-2.5 rounded-xl border border-emerald-200">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">Approved Grant / Loan</span>
                          <span className="font-extrabold text-emerald-900 text-sm">
                            ₹{Number(approval.approved_amount_inr).toLocaleString('en-IN')}
                          </span>
                        </div>
                      )}
                      {approval.approver_name && (
                        <div className="bg-white p-2.5 rounded-xl border border-emerald-200">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">Sanctioning Authority</span>
                          <span className="font-semibold text-slate-800">{approval.approver_name}</span>
                        </div>
                      )}
                    </div>

                    {approval.sanction_notes && (
                      <p className="text-[11px] text-emerald-800 italic pt-1">
                        "{approval.sanction_notes}"
                      </p>
                    )}
                  </div>
                )}

                {/* Rejection Details Card */}
                {rejection && (
                  <div className="p-4 bg-red-50/90 border border-red-200 rounded-2xl text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-red-950 flex items-center gap-1.5 text-sm">
                        <XCircle size={18} className="text-red-600" />
                        <span>Application Scrutiny Decision: Not Approved</span>
                      </span>
                      {rejection.rejected_at && (
                        <span className="text-[11px] font-mono text-red-700">
                          Date: {new Date(rejection.rejected_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    <div className="bg-white p-3 rounded-xl border border-red-200 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-red-500 block">Reason for Decision</span>
                      <p className="font-medium text-red-900 text-xs">{rejection.rejection_reason}</p>
                      {rejection.rejected_by && (
                        <p className="text-[10px] text-slate-500 pt-1">
                          Evaluated by: {rejection.rejected_by}
                        </p>
                      )}
                    </div>

                    {rejection.alternative_schemes_recommended && (
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
                        <p className="text-[11px] text-red-800">
                          You may be eligible for other government initiatives with modified criteria.
                        </p>
                        <Link
                          to="/matches"
                          onClick={(e) => e.stopPropagation()}
                          className="px-3 py-1.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white font-bold text-[11px] flex items-center gap-1 self-start sm:self-auto shadow-sm"
                        >
                          <span>Explore Alternatives</span>
                          <ArrowRight size={12} />
                        </Link>
                      </div>
                    )}
                  </div>
                )}

                {/* Disbursement Progress Card */}
                {disbursement && (
                  <div className="p-4 bg-purple-50/80 border border-purple-200 rounded-2xl text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-950 flex items-center gap-1.5 text-sm">
                        <CreditCard size={18} className="text-purple-600" />
                        <span>Direct Benefit Transfer (DBT) & Payment Progress</span>
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full font-bold text-[11px] bg-purple-100 text-purple-800 border border-purple-300">
                        {disbursement.status || 'PROCESSING'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                      <div className="bg-white p-2.5 rounded-xl border border-purple-200">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Disbursed Amount</span>
                        <span className="font-extrabold text-purple-900 text-sm">
                          ₹{Number(disbursement.amount_inr || 0).toLocaleString('en-IN')}
                        </span>
                      </div>
                      <div className="bg-white p-2.5 rounded-xl border border-purple-200">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">PFMS / DBT Routing</span>
                        <span className="font-semibold text-slate-800 text-[11px]">{disbursement.account_routing || 'Aadhaar Payment Bridge'}</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-xl border border-purple-200">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Transaction Reference / UTR</span>
                        <span className="font-mono font-bold text-purple-950 text-[11px]">
                          {disbursement.transaction_reference || 'In PFMS Clearing'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Footer & Official Links */}
                <div className="pt-2 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-3 text-xs">
                    <button
                      onClick={(e) => handleOpenValidation(app, e)}
                      className="font-bold text-gov-navy-900 hover:text-gov-saffron-700 flex items-center gap-1.5 underline decoration-slate-300 underline-offset-4"
                    >
                      <ListChecks size={14} className="text-gov-navy-700" />
                      <span>Readiness & Scheme Checklist</span>
                    </button>

                    {app.status !== 'draft' && (
                      <button
                        onClick={(e) => handleSyncStatus(app.id, e)}
                        disabled={syncingAppId === app.id}
                        className="font-bold text-slate-700 hover:text-gov-navy-900 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
                        title="Synchronize live status with accredited channel partner / PFMS gateway"
                      >
                        <RefreshCw size={12} className={syncingAppId === app.id ? 'animate-spin text-gov-saffron-600' : 'text-slate-500'} />
                        <span>{syncingAppId === app.id ? 'Syncing...' : 'Sync Gateway Status'}</span>
                      </button>
                    )}

                    {app.official_portal_url && (
                      <a
                        href={app.official_portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-slate-600 hover:text-gov-navy-900 font-medium"
                      >
                        <ExternalLink size={12} />
                        <span>Official Ministry Portal</span>
                      </a>
                    )}
                  </div>

                  {syncNotice && syncNotice.appId === app.id && (
                    <div className={`w-full mt-2 p-2 rounded-lg text-xs font-semibold ${
                      syncNotice.error ? 'bg-amber-50 text-amber-900 border border-amber-200' : 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                    }`}>
                      {syncNotice.message || syncNotice.error}
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    {app.status === 'draft' && (
                      <button
                        onClick={(e) => handleOpenValidation(app, e)}
                        className="px-4 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                      >
                        <Send size={13} />
                        <span>Validate & Submit</span>
                      </button>
                    )}

                    <span className="text-xs font-bold text-slate-400 flex items-center gap-1">
                      <span>{selectedApp?.id === app.id ? 'Collapse' : 'Tracking Details'}</span>
                      <ChevronRight size={15} className={selectedApp?.id === app.id ? 'rotate-90' : ''} />
                    </span>
                  </div>
                </div>

                {/* Expanded Detailed Audit Log Drawer */}
                {selectedApp?.id === app.id && (
                  <div className="mt-4 pt-4 border-t border-slate-200/80 bg-slate-50/70 p-4 rounded-2xl text-xs space-y-4 animate-in fade-in duration-150">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-gov-navy-950 uppercase tracking-wide">
                        Assigned Partner & Audit Trail
                      </h4>
                      <span className="text-[11px] text-slate-400 font-mono">
                        Tracking ID: {app.id}
                      </span>
                    </div>

                    {/* Assigned Partner Profile Card */}
                    <div className="p-4 bg-white border border-slate-200 rounded-2xl space-y-3 shadow-xs">
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                        <span className="font-bold text-gov-navy-950 flex items-center gap-1.5 text-xs">
                          <Building2 size={16} className="text-gov-navy-700" />
                          <span>Assigned Channel Partner / Nodal Agency</span>
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${
                            ROUTING_STATUS_CONFIG[app.routing_status]?.color || 'bg-slate-100 text-slate-700 border-slate-300'
                          }`}>
                            {ROUTING_STATUS_CONFIG[app.routing_status]?.label || app.routing_status || 'NOT_ROUTED'}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            ACKNOWLEDGEMENT_CONFIG[app.partner_acknowledgement_status]?.color || 'text-slate-600 bg-slate-100 border-slate-200'
                          }`}>
                            {ACKNOWLEDGEMENT_CONFIG[app.partner_acknowledgement_status]?.label || 'Pending'}
                          </span>
                        </div>
                      </div>

                      {partnerDetails || app.assigned_partner_name ? (
                        <div className="space-y-2 text-slate-700">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-extrabold text-sm text-gov-navy-950">
                              {partnerDetails?.name || app.assigned_partner_name}
                            </span>
                            <div className="flex flex-wrap items-center gap-1.5">
                              {(partnerDetails?.institution_type || app.assigned_partner_type) && (
                                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200 text-[10px]">
                                  {partnerDetails?.institution_type || app.assigned_partner_type}
                                </span>
                              )}
                              {partnerDetails?.is_active && (
                                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200 text-[10px] flex items-center gap-1">
                                  <ShieldCheck size={11} />
                                  <span>Accredited Live Partner</span>
                                </span>
                              )}
                              {partnerDetails?.distance_km != null && (
                                <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                                  {partnerDetails.distance_km} km away
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px]">
                            {(partnerDetails?.address || partnerDetails?.district) && (
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <MapPin size={13} className="text-slate-400 flex-shrink-0" />
                                <span>{[partnerDetails.address, partnerDetails.district, partnerDetails.state].filter(Boolean).join(', ')}</span>
                              </div>
                            )}
                            {partnerDetails?.contact_person && (
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <span className="text-slate-400 font-medium">Contact:</span>
                                <span className="font-semibold text-slate-800">{partnerDetails.contact_person}</span>
                              </div>
                            )}
                            {partnerDetails?.contact_phone && (
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <Phone size={12} className="text-slate-400 flex-shrink-0" />
                                <span>{partnerDetails.contact_phone}</span>
                              </div>
                            )}
                            {partnerDetails?.contact_email && (
                              <div className="flex items-center gap-1.5 text-slate-600">
                                <Mail size={12} className="text-slate-400 flex-shrink-0" />
                                <span>{partnerDetails.contact_email}</span>
                              </div>
                            )}
                          </div>

                          {app.partner_acknowledgement_status === 'PENDING' && (
                            <p className="text-[11px] text-amber-800 bg-amber-50/80 p-2.5 rounded-xl border border-amber-200 leading-relaxed mt-2">
                              <strong>Pending Partner Acknowledgement:</strong> Your dossier has been transmitted to the accredited channel partner. Official receipt acknowledgement is pending (receipt is not assumed or faked).
                            </p>
                          )}
                        </div>
                      ) : (
                        <p className="text-slate-500 italic text-[11px]">
                          No local partner assigned yet. Application will be processed directly through central nodal ministry portal.
                        </p>
                      )}
                    </div>

                    {/* Routing Audit Trail History */}
                    {((app.routing_history && app.routing_history.length > 0) || (app.form_data?.routing_history && app.form_data.routing_history.length > 0)) && (
                      <div className="p-4 bg-white border border-slate-200 rounded-2xl space-y-2 shadow-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-gov-navy-950 text-[11px] uppercase tracking-wider">
                            Routing & Scrutiny Audit Trail ({((app.routing_history || app.form_data?.routing_history) || []).length} events)
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">Immutable Log</span>
                        </div>

                        <div className="space-y-2 max-h-56 overflow-y-auto pr-1 custom-scrollbar">
                          {((app.routing_history || app.form_data?.routing_history) || []).map((audit, idx) => (
                            <div key={idx} className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-[11px] space-y-1">
                              <div className="flex items-center justify-between font-mono text-[10px] text-slate-400">
                                <span>{audit.timestamp ? new Date(audit.timestamp).toLocaleString() : 'N/A'}</span>
                                <span className="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 uppercase text-[9px] font-bold">
                                  {audit.source || 'portal'}
                                </span>
                              </div>
                              <div className="flex flex-wrap items-center gap-1.5 font-bold text-slate-800">
                                {audit.from_status && (
                                  <>
                                    <span className="text-slate-500 font-normal">{audit.from_status}</span>
                                    <span className="text-slate-400">→</span>
                                  </>
                                )}
                                <span className="text-gov-navy-900">{audit.to_status}</span>
                                {audit.partner_name && (
                                  <span className="text-[10px] font-normal text-slate-500">
                                    via {audit.partner_name}
                                  </span>
                                )}
                              </div>
                              {audit.reason && (
                                <p className="text-[11px] text-slate-600 italic">
                                  "{audit.reason}"
                                </p>
                              )}
                              <div className="text-[10px] text-slate-400 pt-0.5">
                                Actor: <span className="font-medium text-slate-600">{audit.actor}</span> ({audit.actor_role})
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Honest Disclosure Notice */}
                    <div className="p-3 bg-blue-50/80 border border-blue-200/80 rounded-xl text-[11px] text-blue-900 flex items-start gap-2">
                      <Info size={15} className="text-blue-600 flex-shrink-0 mt-0.5" />
                      <p>
                        <strong>Transparency Notice:</strong> {app.submission_disclaimer || 'Yojantra compiles, validates, and routes your verified application dossier to accredited channel partners and official nodal ministries.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Resolve Document Request Modal */}
      {resolveModalApp && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4 animate-in zoom-in-95 duration-200 text-left">
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-orange-600 bg-orange-50 px-2 py-0.5 rounded">
                  Document Query Resolution
                </span>
                <h3 className="text-lg font-extrabold text-gov-navy-950 mt-1">
                  Respond to Officer Query
                </h3>
                <p className="text-xs text-slate-500">
                  {resolveModalApp.scheme_name}
                </p>
              </div>

              <button
                onClick={() => setResolveModalApp(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all"
              >
                ✕
              </button>
            </div>

            {/* Officer Query Callout */}
            <div className="p-3 bg-orange-50/70 border border-orange-200 rounded-2xl text-xs space-y-1">
              <span className="font-bold text-orange-950 block">Requested Documents / Query:</span>
              <p className="text-orange-900">
                {resolveModalApp.documents_required_alert?.reason || resolveModalApp.documents_required_alert?.notes || 'Additional documents or clarifications requested by reviewing officer.'}
              </p>
              {(resolveModalApp.documents_required_alert?.requested_documents?.length > 0) && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {resolveModalApp.documents_required_alert.requested_documents.map((doc, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-orange-100 text-orange-900 text-[10px] font-bold">
                      {doc}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-1 text-xs text-slate-600">
              <label className="font-bold text-slate-800 block">
                Applicant Compliance Notes / Upload Confirmation:
              </label>
              <textarea
                value={resolveComments}
                onChange={(e) => setResolveComments(e.target.value)}
                placeholder="Explain the changes made, or note which documents have been uploaded to your Document Vault..."
                rows={4}
                className="w-full p-3 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-orange-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Tip: You can upload required PDFs or certificates in your <Link to="/documents" className="text-gov-navy-900 font-bold underline">Documents Vault</Link> before submitting.
              </p>
            </div>

            {resolveError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                {resolveError}
              </div>
            )}

            {resolveSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-bold flex items-center gap-1.5">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span>{resolveSuccess}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                onClick={() => setResolveModalApp(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleResolveDocumentRequest}
                disabled={resolvingDoc || !resolveComments.trim()}
                className="px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white text-xs font-bold shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {resolvingDoc ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <Send size={13} />
                    <span>Submit Compliance Response</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pre-Submission Validation & Checklist Modal */}
      {validationModalApp && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto space-y-5 animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-gov-saffron-600 bg-gov-saffron-50 px-2 py-0.5 rounded">
                  Pre-Submission Readiness Check
                </span>
                <h3 className="text-xl font-extrabold text-gov-navy-950 mt-1">
                  {validationModalApp.scheme_name}
                </h3>
                {validationData?.partner_reference_code && (
                  <p className="text-xs font-mono text-slate-500 mt-0.5">
                    Reference Code: {validationData.partner_reference_code}
                  </p>
                )}
              </div>

              <button
                onClick={() => setValidationModalApp(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all"
              >
                ✕
              </button>
            </div>

            {loadingValidation ? (
              <div className="py-12 text-center space-y-3">
                <RefreshCw size={28} className="mx-auto text-gov-saffron-600 animate-spin" />
                <p className="text-xs font-bold text-slate-600">
                  Running automated pre-submission compliance audit...
                </p>
              </div>
            ) : (
              <>
                {/* Readiness Score Card */}
                {validationData && (
                  <div className={`p-4 rounded-2xl border flex items-center justify-between gap-4 ${
                    validationData.is_ready_to_submit
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                      : 'bg-amber-50/70 border-amber-200 text-amber-950'
                  }`}>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {validationData.is_ready_to_submit ? (
                          <ShieldCheck size={20} className="text-gov-emerald-600" />
                        ) : (
                          <AlertTriangle size={20} className="text-amber-600" />
                        )}
                        <span className="font-extrabold text-sm">
                          {validationData.is_ready_to_submit 
                            ? 'Dossier Ready for Submission' 
                            : 'Mandatory Requirements Incomplete'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600">
                        {validationData.is_ready_to_submit
                          ? 'All required profile attributes and mandatory scheme document requirements are fulfilled.'
                          : 'Please address the highlighted errors below before transmitting your application dossier.'}
                      </p>
                    </div>

                    <div className="text-right flex-shrink-0">
                      <span className="text-2xl font-black">{validationData.readiness_score}%</span>
                      <span className="block text-[10px] uppercase font-bold text-slate-500">Readiness</span>
                    </div>
                  </div>
                )}

                {/* Channel Partner Digital Routing Preview */}
                {partnerRoutingData && (
                  <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-gov-navy-950 flex items-center gap-1.5">
                        <Building2 size={13} className="text-gov-navy-700" />
                        Channel Partner Digital Routing
                      </span>
                      <span className="text-[11px] font-medium text-slate-500">
                        {partnerRoutingData.scheme_category}
                      </span>
                    </div>

                    {partnerRoutingData.assigned_partner ? (
                      <div className="bg-white p-3 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-xs text-gov-navy-950">
                              {partnerRoutingData.assigned_partner.partner_name}
                            </span>
                            <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200">
                              {partnerRoutingData.assigned_partner.partner_type}
                            </span>
                            {partnerRoutingData.assigned_partner.geographic_tier && (
                              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200 capitalize">
                                {partnerRoutingData.assigned_partner.geographic_tier} tier
                              </span>
                            )}
                            {partnerRoutingData.assigned_partner.distance_km != null && (
                              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                {partnerRoutingData.assigned_partner.distance_km} km
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            {partnerRoutingData.assigned_partner.location || partnerRoutingData.assigned_partner.address || 'Accredited Nodal Center'}
                          </p>
                          <p className="text-[10px] text-slate-400 mt-0.5">
                            {partnerRoutingData.assigned_partner.recommendation_reason}
                          </p>
                          {partnerRoutingData.assigned_partner.eligibility_reason && (
                            <p className="text-[10px] text-slate-500 mt-0.5">
                              <span className="font-semibold text-slate-600">Verification Note:</span> {partnerRoutingData.assigned_partner.eligibility_reason}
                            </p>
                          )}
                        </div>
                        <div className="flex flex-col items-start sm:items-end gap-1 self-start sm:self-center">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            partnerRoutingData.assigned_partner.eligibility_verdict === 'ELIGIBLE'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : partnerRoutingData.assigned_partner.eligibility_verdict === 'NEEDS_VERIFICATION'
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-blue-50 text-blue-700 border-blue-200'
                          }`}>
                            {partnerRoutingData.assigned_partner.eligibility_verdict === 'ELIGIBLE'
                              ? 'Verified Live Partner'
                              : partnerRoutingData.assigned_partner.eligibility_verdict === 'NEEDS_VERIFICATION'
                              ? 'Needs Nodal Verification'
                              : partnerRoutingData.assigned_partner.routing_status || 'Eligible Partner'}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-white p-2.5 rounded-xl border border-slate-200 text-slate-500 text-xs flex items-center gap-2">
                        <Info size={14} className="text-slate-400 flex-shrink-0" />
                        <span>No regional channel partner registered; application will be routed directly via central nodal portal.</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Validation Errors & Warnings */}
                {validationData?.errors?.length > 0 && (
                  <div className="p-4 bg-red-50/90 border border-red-200 rounded-2xl space-y-2 shadow-xs">
                    <span className="text-xs font-bold text-red-900 flex items-center gap-1.5">
                      <AlertCircle size={15} className="text-red-600 flex-shrink-0" />
                      Critical Missing Items Before Submission:
                    </span>
                    <ul className="text-xs text-red-800 list-disc list-inside space-y-1 pl-1">
                      {validationData.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {submitError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-700">
                    {submitError}
                  </div>
                )}

                {/* Scheme-Specific Checklist Items */}
                {checklistData && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Scheme-Specific Compliance Checklist ({checklistData.completed_items}/{checklistData.total_items})
                      </h4>
                      <span className="text-xs font-bold text-slate-600">
                        {checklistData.completion_percentage}%
                      </span>
                    </div>

                    <div className="space-y-2">
                      {checklistData.items.map((item) => (
                        <div
                          key={item.id}
                          className={`p-3 rounded-2xl border flex items-start justify-between gap-3 text-xs ${
                            item.is_completed
                              ? 'bg-slate-50/70 border-slate-200 text-slate-800'
                              : 'bg-amber-50/40 border-amber-200/80 text-amber-900'
                          }`}
                        >
                          <div className="flex items-start gap-2.5">
                            <span className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                              item.is_completed ? 'bg-gov-emerald-600 text-white' : 'bg-slate-200 text-slate-500'
                            }`}>
                              {item.is_completed ? <Check size={12} /> : '•'}
                            </span>
                            <div>
                              <p className="font-bold text-gov-navy-950">{item.title}</p>
                              <p className="text-[11px] text-slate-500 mt-0.5">{item.description}</p>
                            </div>
                          </div>

                          {item.action_url && !item.is_completed && (
                            item.action_url.startsWith('http') ? (
                              <a
                                href={item.action_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-3 py-1 rounded-lg bg-white border border-slate-200 hover:border-slate-300 font-bold text-gov-navy-950 flex items-center gap-1 flex-shrink-0"
                              >
                                <span>Visit</span>
                                <ArrowUpRight size={12} />
                              </a>
                            ) : (
                              <Link
                                to={item.action_url}
                                className="px-3 py-1 rounded-lg bg-white border border-slate-200 hover:border-slate-300 font-bold text-gov-navy-950 flex items-center gap-1 flex-shrink-0"
                              >
                                <span>Complete</span>
                                <ArrowRight size={12} />
                              </Link>
                            )
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Honest Government Portal Hand-off Disclaimer */}
                <div className="p-3.5 bg-slate-100 border border-slate-200 rounded-2xl text-[11px] text-slate-600 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-slate-800">
                    <Info size={14} className="text-slate-600" />
                    <span>Submission Protocol & Official Portal Hand-off</span>
                  </div>
                  <p>
                    {validationData?.disclaimer || 'Yojantra compiles, validates, and routes your verified application dossier to accredited channel partners and official nodal ministries.'}
                  </p>
                  {validationData?.official_portal_url && (
                    <div className="pt-1.5">
                      <a
                        href={validationData.official_portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-gov-navy-900 font-bold hover:underline"
                      >
                        <ExternalLink size={12} />
                        <span>Open Official Government Scheme Portal ({validationData.official_portal_url})</span>
                      </a>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => setValidationModalApp(null)}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-all"
                  >
                    Close
                  </button>

                  {validationModalApp.status === 'draft' && (
                    <button
                      onClick={() => handleSubmitApplication(validationModalApp.id)}
                      disabled={submittingId === validationModalApp.id || (validationData && !validationData.is_ready_to_submit)}
                      className="px-5 py-2.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                    >
                      {submittingId === validationModalApp.id ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          <span>Transmitting Dossier...</span>
                        </>
                      ) : (
                        <>
                          <Send size={14} />
                          <span>Confirm & Submit Application</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
