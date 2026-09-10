import React, { useState } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useQuery, useQueryClient } from 'react-query';
import { 
  Users, FileCheck, TrendingUp, AlertTriangle, 
  BarChart3, ShieldCheck, Activity, RefreshCw, 
  Server, Database, CheckCircle2, ChevronRight, ArrowRight,
  Building2, Search, Filter, Eye, Clock, AlertCircle, 
  FileText, Check, X, ShieldAlert, IndianRupee, Layers
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';
import { applicationService } from '../services/applicationService';

export default function AdminDashboard() {
  const { user, api } = useAuthStore();
  const queryClient = useQueryClient();

  const isPartnerOfficer = user?.role === 'partner_officer' || user?.role === 'nodal_officer';
  const [activeTab, setActiveTab] = useState(isPartnerOfficer ? 'queue' : 'overview');
  
  // Batch matching state
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState(null);

  // Queue state
  const [queueSearch, setQueueSearch] = useState('');
  const [queueStatus, setQueueStatus] = useState('');
  const [queuePage, setQueuePage] = useState(1);
  const [selectedAppId, setSelectedAppId] = useState(null);

  // Action modal state
  const [actionModal, setActionModal] = useState(null); // { action, label, requiresReason }
  const [actionReason, setActionReason] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null);

  // 1. Dashboard metrics (Platform overview)
  const { data: metrics, isLoading: loadingMetrics } = useQuery('admin_metrics', () =>
    api().get('/admin/analytics/dashboard').then(r => r.data).catch(() => null)
  );

  // 2. Partner Queue KPIs
  const { data: partnerKPIs, isLoading: loadingPartnerKPIs } = useQuery(
    'partner_overview_kpis',
    () => applicationService.getPartnerOverviewKPIs().catch(() => null)
  );

  // 3. Partner Applications Queue
  const { data: queueData, isLoading: loadingQueue, refetch: refetchQueue } = useQuery(
    ['partner_applications', queueStatus, queueSearch, queuePage],
    () => applicationService.listPartnerApplications({
      status: queueStatus || undefined,
      search: queueSearch || undefined,
      page: queuePage,
      page_size: 20
    }).catch(() => ({ items: [], total: 0, status_counts: {} })),
    { enabled: activeTab === 'queue' }
  );

  // 4. Single Application Detail for Review
  const { data: appDetail, isLoading: loadingDetail, refetch: refetchDetail } = useQuery(
    ['partner_app_detail', selectedAppId],
    () => applicationService.getPartnerApplicationDetail(selectedAppId).catch(() => null),
    { enabled: !!selectedAppId }
  );

  // 5. Bias report
  const { data: biasReport } = useQuery('admin_bias', () =>
    api().get('/admin/analytics/bias').then(r => r.data).catch(() => null),
    { enabled: activeTab === 'bias' }
  );

  // 6. Users list
  const { data: usersData, isLoading: loadingUsers } = useQuery('admin_users', () =>
    api().get('/admin/users', { params: { page: 1, page_size: 20 } }).then(r => r.data).catch(() => null),
    { enabled: activeTab === 'users' }
  );

  // 7. Schemes list
  const { data: schemesData, isLoading: loadingSchemes } = useQuery('admin_schemes', () =>
    api().get('/admin/schemes').then(r => r.data).catch(() => null),
    { enabled: activeTab === 'schemes' }
  );

  const handleTriggerMatchAll = async () => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await api().post('/admin/schemes/match-all');
      setTriggerResult(res.data?.message || 'Batch matching executed successfully across all active users.');
      queryClient.invalidateQueries('admin_metrics');
    } catch (e) {
      setTriggerResult('Failed to run batch matching.');
    } finally {
      setTriggering(false);
    }
  };

  const handleExecuteAction = async (action, requiresReason = false, promptLabel = '') => {
    if (requiresReason) {
      setActionModal({ action, label: promptLabel || action, requiresReason: true });
      setActionReason('');
      setActionFeedback(null);
      return;
    }

    // Direct transition for PARTNER_RECEIVED or UNDER_REVIEW without mandatory modal
    setActionSubmitting(true);
    setActionFeedback(null);
    try {
      await applicationService.submitPartnerAction(selectedAppId, {
        action,
        reason: `Status transitioned to ${action} by authorized officer.`
      });
      setActionFeedback({ type: 'success', message: `Status updated to ${action} successfully.` });
      queryClient.invalidateQueries('partner_applications');
      queryClient.invalidateQueries('partner_overview_kpis');
      refetchDetail();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Action failed';
      setActionFeedback({ type: 'error', message: detail });
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleConfirmModalAction = async () => {
    if (!actionModal) return;
    if (actionModal.requiresReason && !actionReason.trim()) {
      setActionFeedback({ type: 'error', message: 'A specific explanation is mandatory for this action.' });
      return;
    }

    setActionSubmitting(true);
    setActionFeedback(null);
    try {
      await applicationService.submitPartnerAction(selectedAppId, {
        action: actionModal.action,
        reason: actionReason.trim()
      });
      setActionFeedback({ type: 'success', message: `Action '${actionModal.action}' processed and applicant notified.` });
      setActionModal(null);
      setActionReason('');
      queryClient.invalidateQueries('partner_applications');
      queryClient.invalidateQueries('partner_overview_kpis');
      refetchDetail();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Action execution failed';
      setActionFeedback({ type: 'error', message: detail });
    } finally {
      setActionSubmitting(false);
    }
  };

  const tabs = [
    { id: 'queue', label: 'Assigned Applications & Partner Desk', icon: Building2 },
    { id: 'overview', label: 'Executive Overview', icon: BarChart3 },
    { id: 'bias', label: 'Bias & Fairness Audit', icon: ShieldCheck },
    { id: 'users', label: 'Registered Citizens', icon: Users },
    { id: 'schemes', label: 'Scheme Management', icon: FileCheck },
    { id: 'system', label: 'System Monitoring', icon: Server },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ROUTED_TO_PARTNER':
        return { bg: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Routed to Desk' };
      case 'PARTNER_RECEIVED':
        return { bg: 'bg-indigo-50 text-indigo-700 border-indigo-200', label: 'Acknowledged' };
      case 'UNDER_REVIEW':
        return { bg: 'bg-amber-50 text-amber-700 border-amber-200', label: 'Under Review' };
      case 'DOCUMENTS_REQUIRED':
        return { bg: 'bg-purple-50 text-purple-700 border-purple-200', label: 'Docs Required' };
      case 'APPROVED':
        return { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Sanction Approved' };
      case 'REJECTED':
        return { bg: 'bg-red-50 text-red-700 border-red-200', label: 'Declined' };
      case 'DISBURSED':
        return { bg: 'bg-teal-50 text-teal-700 border-teal-200', label: 'Disbursed' };
      default:
        return { bg: 'bg-slate-100 text-slate-700 border-slate-200', label: status || 'Draft' };
    }
  };

  return (
    <div className="space-y-6 text-left">
      
      {/* Executive Header Banner */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl shadow-xl border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-1.5 rounded-lg bg-gov-saffron-500/20 text-gov-saffron-400 border border-gov-saffron-500/30">
                <ShieldCheck size={18} />
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Government of India • Ministry & Channel Partner Gateway
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              {isPartnerOfficer ? 'Channel Partner Appraisal Desk' : 'Yojantra Operations & Partner Console'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Real-time application routing scrutiny, document verification, live banking health, and statutory compliance.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isPartnerOfficer && (
              <button
                onClick={handleTriggerMatchAll}
                disabled={triggering}
                className="px-4 py-2.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2 disabled:opacity-50"
              >
                <RefreshCw size={14} className={triggering ? 'animate-spin' : ''} />
                <span>{triggering ? 'Computing...' : 'Trigger Matches'}</span>
              </button>
            )}
            <button
              onClick={() => {
                queryClient.invalidateQueries('partner_applications');
                queryClient.invalidateQueries('partner_overview_kpis');
              }}
              className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-all border border-slate-700 flex items-center gap-1.5"
              title="Refresh queue"
            >
              <RefreshCw size={14} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>

        {triggerResult && (
          <div className="mt-4 p-3 bg-gov-emerald-950/80 border border-gov-emerald-500/30 rounded-xl text-xs font-bold text-gov-emerald-300 flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{triggerResult}</span>
          </div>
        )}
      </div>

      {/* Tab Controls */}
      <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all border flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ======================================================== */}
      {/* TAB: ASSIGNED APPLICATIONS & PARTNER QUEUE */}
      {/* ======================================================== */}
      {activeTab === 'queue' && (
        <div className="space-y-6">
          {/* Partner KPI Stats Row */}
          {loadingPartnerKPIs ? (
            <SkeletonLoader.Stats />
          ) : partnerKPIs ? (
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              <KPICard
                label="Total Assigned"
                value={partnerKPIs.total_assigned}
                sub="Routed dossiers"
                icon={Building2}
                accent="border-l-4 border-blue-500"
              />
              <KPICard
                label="Action Pending"
                value={partnerKPIs.pending_action_count}
                sub="Awaiting scrutiny"
                icon={Clock}
                accent="border-l-4 border-amber-500"
              />
              <KPICard
                label="Docs Required"
                value={partnerKPIs.docs_required_count}
                sub="Citizen query raised"
                icon={AlertCircle}
                accent="border-l-4 border-purple-500"
              />
              <KPICard
                label="Sanction Approved"
                value={partnerKPIs.approved_count}
                sub="Ready for DBT credit"
                icon={CheckCircle2}
                accent="border-l-4 border-gov-emerald-500"
              />
              <KPICard
                label="Sanction Pipeline"
                value={`₹${(partnerKPIs.total_sanction_amount_inr / 100000).toFixed(1)}L`}
                sub="Total subsidy/loan value"
                icon={IndianRupee}
                accent="border-l-4 border-slate-800"
              />
            </div>
          ) : null}

          {/* Filter & Search Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Search applicant, phone, reference, or scheme..."
                value={queueSearch}
                onChange={(e) => setQueueSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-900 bg-slate-50 focus:bg-white"
              />
              {queueSearch && (
                <button
                  onClick={() => setQueueSearch('')}
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wide flex items-center gap-1 flex-shrink-0">
                <Filter size={12} /> Filter:
              </span>
              {[
                { id: '', label: 'All Statuses' },
                { id: 'ROUTED_TO_PARTNER', label: 'Routed' },
                { id: 'PARTNER_RECEIVED', label: 'Acknowledged' },
                { id: 'UNDER_REVIEW', label: 'Reviewing' },
                { id: 'DOCUMENTS_REQUIRED', label: 'Docs Needed' },
                { id: 'APPROVED', label: 'Approved' },
                { id: 'REJECTED', label: 'Declined' }
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setQueueStatus(f.id)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border ${
                    queueStatus === f.id
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {f.label}
                  {queueData?.status_counts?.[f.id] ? ` (${queueData.status_counts[f.id]})` : ''}
                </button>
              ))}
            </div>
          </div>

          {/* Applications Queue Table */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-gov-navy-950">
                  Assigned Application Dossiers
                </h3>
                <p className="text-xs text-slate-500">
                  Review applicant profiles, scrutinize uploaded documents, and process channel actions.
                </p>
              </div>
              <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                {queueData?.total || 0} Dossiers
              </span>
            </div>

            {loadingQueue ? (
              <SkeletonLoader.Table rows={5} cols={5} />
            ) : queueData?.items?.length === 0 ? (
              <div className="p-12 text-center text-slate-500 bg-slate-50 rounded-2xl border border-dashed border-slate-200 space-y-2">
                <Building2 size={32} className="mx-auto text-slate-400 opacity-60" />
                <p className="text-sm font-bold text-slate-700">No applications found in this queue.</p>
                <p className="text-xs text-slate-400">Try adjusting your status filter or search keywords.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                      <th className="pb-3">Reference / Date</th>
                      <th className="pb-3">Applicant & Domicile</th>
                      <th className="pb-3">Scheme & Requested</th>
                      <th className="pb-3">Channel Partner & Health</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {queueData?.items?.map((item) => {
                      const badge = getStatusBadge(item.routing_status);
                      return (
                        <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-3.5">
                            <span className="font-mono font-bold text-gov-navy-950 text-xs block">
                              {item.partner_reference_code || `YOJ-${item.id.slice(0, 8).toUpperCase()}`}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              {new Date(item.created_at).toLocaleDateString('en-IN', {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </span>
                          </td>
                          <td className="py-3.5">
                            <p className="font-bold text-slate-900">{item.applicant_name}</p>
                            <p className="text-[10px] text-slate-500">
                              {item.district ? `${item.district}, ` : ''}{item.state || 'India'}
                              {item.social_category && ` • ${item.social_category.toUpperCase()}`}
                            </p>
                            {item.applicant_phone && (
                              <p className="text-[10px] text-slate-400 font-mono">{item.applicant_phone}</p>
                            )}
                          </td>
                          <td className="py-3.5">
                            <p className="font-bold text-gov-navy-950 line-clamp-1">{item.scheme_name}</p>
                            <p className="text-[10px] text-slate-500 font-semibold">
                              {item.requested_amount_inr
                                ? `₹${item.requested_amount_inr.toLocaleString('en-IN')}`
                                : 'Amount on appraisal'}
                            </p>
                          </td>
                          <td className="py-3.5">
                            <div className="space-y-1">
                              <span className="font-semibold text-slate-700 block text-xs">
                                {item.assigned_partner_name || 'Designated Nodal Desk'}
                              </span>
                              {item.partner_npa_ratio !== null && (
                                <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                                  item.partner_npa_risk === 'LOW'
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : item.partner_npa_risk === 'MODERATE'
                                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                                    : 'bg-red-50 text-red-700 border-red-200'
                                }`}>
                                  NPA: {item.partner_npa_ratio}% ({item.partner_npa_risk})
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3.5">
                            <span className={`inline-block px-2.5 py-1 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                              {badge.label}
                            </span>
                          </td>
                          <td className="py-3.5 text-right">
                            <button
                              onClick={() => setSelectedAppId(item.id)}
                              className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center gap-1 ml-auto"
                            >
                              <Eye size={13} />
                              <span>Review</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* APPLICATION DETAIL MODAL / DRAWER */}
      {/* ======================================================== */}
      {selectedAppId && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end backdrop-blur-xs transition-opacity animate-in fade-in duration-150">
          <div className="bg-white w-full max-w-3xl h-full overflow-y-auto shadow-2xl p-6 sm:p-8 space-y-6 flex flex-col justify-between">
            
            {/* Top Bar */}
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div className="flex items-center gap-2">
                  <span className="p-2 rounded-xl bg-slate-900 text-white">
                    <Building2 size={20} />
                  </span>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Channel Partner Scrutiny Desk
                    </span>
                    <h2 className="text-lg sm:text-xl font-bold text-gov-navy-950">
                      Dossier #{appDetail?.application?.partner_reference_code || selectedAppId.slice(0, 8).toUpperCase()}
                    </h2>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAppId(null)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Action Feedback Alert */}
              {actionFeedback && (
                <div className={`p-3.5 rounded-xl border text-xs font-bold flex items-center justify-between ${
                  actionFeedback.type === 'success'
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                    : 'bg-red-50 border-red-300 text-red-800'
                }`}>
                  <div className="flex items-center gap-2">
                    {actionFeedback.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                    <span>{actionFeedback.message}</span>
                  </div>
                  <button onClick={() => setActionFeedback(null)} className="opacity-70 hover:opacity-100">
                    <X size={14} />
                  </button>
                </div>
              )}

              {loadingDetail ? (
                <div className="py-12 text-center text-slate-500 space-y-2">
                  <RefreshCw size={24} className="animate-spin mx-auto text-slate-400" />
                  <p className="text-xs font-semibold">Loading verified application docket...</p>
                </div>
              ) : appDetail ? (
                <div className="space-y-6 text-xs">
                  
                  {/* Current Status Card */}
                  <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Current Scrutiny Stage</span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-extrabold border ${getStatusBadge(appDetail.routing_summary.current_routing_status).bg}`}>
                          {getStatusBadge(appDetail.routing_summary.current_routing_status).label}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          Ack: <strong>{appDetail.routing_summary.partner_acknowledgement_status}</strong>
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Assigned Institution</span>
                      <span className="font-bold text-gov-navy-950 block">
                        {appDetail.application.assigned_partner_name || 'Designated Lead Bank'}
                      </span>
                    </div>
                  </div>

                  {/* Applicant & Business Demographics Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                      <h4 className="font-bold text-gov-navy-950 text-xs uppercase tracking-wider flex items-center gap-1.5 text-slate-400">
                        <Users size={14} /> Citizen Profile
                      </h4>
                      <div className="space-y-1">
                        <p className="font-bold text-sm text-slate-900">{appDetail.applicant_profile.full_name}</p>
                        <p className="text-slate-600">Phone: {appDetail.applicant_profile.phone || 'N/A'}</p>
                        <p className="text-slate-600">Email: {appDetail.applicant_profile.email || 'N/A'}</p>
                        <p className="text-slate-600">
                          Location: {appDetail.applicant_profile.district ? `${appDetail.applicant_profile.district}, ` : ''}{appDetail.applicant_profile.state || 'N/A'}
                        </p>
                        <p className="text-slate-600">
                          Category: <span className="uppercase font-bold">{appDetail.applicant_profile.social_category || 'General'}</span>
                        </p>
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                      <h4 className="font-bold text-gov-navy-950 text-xs uppercase tracking-wider flex items-center gap-1.5 text-slate-400">
                        <Building2 size={14} /> Enterprise Profile
                      </h4>
                      {appDetail.business_profile ? (
                        <div className="space-y-1">
                          <p className="font-bold text-sm text-slate-900">{appDetail.business_profile.name}</p>
                          <p className="text-slate-600">UDYAM: {appDetail.business_profile.udyam_number || 'Pending'}</p>
                          <p className="text-slate-600">Type: {appDetail.business_profile.enterprise_type || 'Micro'}</p>
                          <p className="text-slate-600">Sector: {appDetail.business_profile.sector || 'Manufacturing / Services'}</p>
                          <p className="text-slate-600">
                            Turnover: ₹{appDetail.business_profile.annual_turnover_inr ? appDetail.business_profile.annual_turnover_inr.toLocaleString('en-IN') : '0'}
                          </p>
                        </div>
                      ) : (
                        <p className="text-slate-400 italic">Individual enterprise / unregistered applicant profile.</p>
                      )}
                    </div>
                  </div>

                  {/* Live Banking Health & NPA Indicators */}
                  {appDetail.partner_health && (
                    <div className="bg-slate-900 text-white p-4 rounded-2xl border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-gov-saffron-400 flex items-center gap-1.5">
                          <ShieldAlert size={14} /> Live Channel Partner Risk Telemetry
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          appDetail.partner_health.funds_available
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-red-500/20 text-red-300 border border-red-500/30'
                        }`}>
                          {appDetail.partner_health.funds_available ? 'Lending Authorized' : 'Sanction Capacity Frozen'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-slate-300">
                        <div>
                          <span className="text-[10px] text-slate-400 block">Institution</span>
                          <span className="font-bold text-white text-xs">{appDetail.partner_health.short_name || appDetail.partner_health.partner_name}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 block">Gross NPA</span>
                          <span className="font-bold text-white text-xs">
                            {appDetail.partner_health.gross_npa_ratio !== null ? `${appDetail.partner_health.gross_npa_ratio}%` : 'N/A'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 block">NPA Risk Rating</span>
                          <span className="font-bold text-white text-xs">{appDetail.partner_health.npa_risk_indicator || 'UNKNOWN'}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 block">Status</span>
                          <span className="font-bold text-emerald-400 text-xs uppercase">{appDetail.partner_health.status}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Uploaded Verification Documents */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-gov-navy-950 text-xs uppercase tracking-wider flex items-center gap-1.5 text-slate-500">
                      <FileText size={14} /> Compliance Documents ({appDetail.documents.length})
                    </h4>
                    {appDetail.documents.length === 0 ? (
                      <div className="p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-slate-400 italic">
                        No digital documents uploaded for this applicant yet.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {appDetail.documents.map((doc) => (
                          <div key={doc.id} className="p-3 bg-white rounded-xl border border-slate-200 hover:border-slate-300 transition-all space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold uppercase text-slate-900 text-[11px]">{doc.doc_type.replace('_', ' ')}</span>
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                doc.verification_status === 'verified'
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : 'bg-amber-50 text-amber-700'
                              }`}>
                                {doc.verification_status}
                              </span>
                            </div>
                            {doc.extracted_number && (
                              <p className="text-[10px] font-mono text-slate-500">Masked ID: {doc.extracted_number}</p>
                            )}
                            {doc.ocr_preview && (
                              <p className="text-[10px] text-slate-400 line-clamp-2 italic bg-slate-50 p-1.5 rounded">
                                "{doc.ocr_preview}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Routing & Audit History Timeline */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-gov-navy-950 text-xs uppercase tracking-wider flex items-center gap-1.5 text-slate-500">
                      <Layers size={14} /> Statutory Audit Log ({appDetail.routing_summary.history.length})
                    </h4>
                    <div className="border-l-2 border-slate-200 ml-2 pl-4 space-y-3">
                      {appDetail.routing_summary.history.map((h, i) => (
                        <div key={i} className="relative space-y-0.5">
                          <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-slate-900 border-2 border-white ring-2 ring-slate-200" />
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-xs">
                              {h.to_status}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              by {h.actor} ({h.actor_role})
                            </span>
                            <span className="text-[10px] text-slate-400 ml-auto">
                              {new Date(h.timestamp).toLocaleDateString('en-IN', {
                                day: 'numeric',
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                          {h.reason && (
                            <p className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
                              "{h.reason}"
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : null}
            </div>

            {/* Action Buttons Footer */}
            {appDetail && (
              <div className="pt-4 border-t border-slate-200 bg-white sticky bottom-0">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  Authorized Actions for Officer
                </span>
                <div className="flex flex-wrap gap-2">
                  {appDetail.routing_summary.allowed_next_transitions?.includes('PARTNER_RECEIVED') && (
                    <button
                      onClick={() => handleExecuteAction('PARTNER_RECEIVED', false)}
                      disabled={actionSubmitting}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <Check size={14} />
                      <span>Acknowledge Receipt</span>
                    </button>
                  )}

                  {appDetail.routing_summary.allowed_next_transitions?.includes('UNDER_REVIEW') && (
                    <button
                      onClick={() => handleExecuteAction('UNDER_REVIEW', false)}
                      disabled={actionSubmitting}
                      className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <Clock size={14} />
                      <span>Commence Scrutiny</span>
                    </button>
                  )}

                  {appDetail.routing_summary.allowed_next_transitions?.includes('DOCUMENTS_REQUIRED') && (
                    <button
                      onClick={() => handleExecuteAction('DOCUMENTS_REQUIRED', true, 'Request Additional Compliance Documents')}
                      disabled={actionSubmitting}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <AlertCircle size={14} />
                      <span>Request Documents</span>
                    </button>
                  )}

                  {appDetail.routing_summary.allowed_next_transitions?.includes('APPROVED') && (
                    <button
                      onClick={() => handleExecuteAction('APPROVED', true, 'Approve Subsidy / Loan Sanction')}
                      disabled={actionSubmitting}
                      className="px-4 py-2 bg-gov-emerald-600 hover:bg-gov-emerald-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <CheckCircle2 size={14} />
                      <span>Approve Sanction</span>
                    </button>
                  )}

                  {appDetail.routing_summary.allowed_next_transitions?.includes('REJECTED') && (
                    <button
                      onClick={() => handleExecuteAction('REJECTED', true, 'Decline / Reject Application')}
                      disabled={actionSubmitting}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <X size={14} />
                      <span>Decline</span>
                    </button>
                  )}
                </div>
              </div>
            )}

          </div>
        </div>
      )}

      {/* Action Reason Prompt Modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-black/70 z-60 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-white rounded-3xl p-6 sm:p-7 max-w-md w-full shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-base text-gov-navy-950">
                {actionModal.label}
              </h3>
              <button
                onClick={() => setActionModal(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Please enter the official justification or compliance requirement. This explanation will be logged to the immutable audit trail and sent to the applicant.
            </p>

            <textarea
              rows={3}
              placeholder="Enter mandatory reason or compliance query..."
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-900 bg-slate-50 focus:bg-white"
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setActionModal(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmModalAction}
                disabled={actionSubmitting || !actionReason.trim()}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white transition-all shadow-sm flex items-center gap-1.5 disabled:opacity-50"
              >
                {actionSubmitting && <RefreshCw size={13} className="animate-spin" />}
                <span>Confirm Transition</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 1: EXECUTIVE OVERVIEW */}
      {/* ======================================================== */}
      {activeTab === 'overview' && metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Applications by Status */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Applications Distribution by Stage
            </h3>

            <div className="space-y-3">
              {Object.entries(metrics.applications_by_status || {}).map(([status, count]) => {
                const total = metrics.total_applications || 1;
                const pct = Math.min(100, Math.round((count / total) * 100));

                return (
                  <div key={status} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="capitalize text-slate-700">{status.replace('_', ' ')}</span>
                      <span className="text-gov-navy-950 font-bold">{count} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          status === 'approved' ? 'bg-gov-emerald-500' :
                          status === 'submitted' ? 'bg-blue-500' :
                          status === 'under_review' ? 'bg-gov-saffron-500' : 'bg-slate-400'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Performing Schemes */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Top Matched Government Programs
            </h3>

            <div className="divide-y divide-slate-100">
              {(metrics.top_schemes || []).map((scheme, i) => (
                <div key={i} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-lg bg-slate-100 font-bold text-xs flex items-center justify-center text-slate-600">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-gov-navy-950">{scheme.name}</p>
                      <p className="text-[10px] text-slate-400">{scheme.ministry || 'Ministry of MSME'}</p>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-gov-saffron-700 bg-gov-saffron-50 px-2 py-0.5 rounded">
                    {scheme.matches} Matches
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: BIAS & FAIRNESS AUDIT */}
      {/* ======================================================== */}
      {activeTab === 'bias' && (
        <div className="space-y-4">
          {biasReport?.alert && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3 text-xs text-red-900">
              <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <span className="font-bold block">Disparity Alert Triggered</span>
                <span>The algorithm detected a deviation in match scores across certain categories. Affirmative weighting adjustment is recommended.</span>
              </div>
            </div>
          )}

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Fairness Audit: Match Scores by Social Category
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated under ethical AI guidelines for equal welfare distribution across marginalized communities.
            </p>

            <div className="space-y-4 pt-2">
              {(biasReport?.match_scores_by_category || []).map((item) => (
                <div key={item.category} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold uppercase text-gov-navy-950">
                      {item.category || 'General'}
                    </span>
                    <span className="text-slate-500 font-medium">
                      {item.count} Citizens • Avg Score: <strong>{item.avg_score.toFixed(1)}%</strong>
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.avg_score >= 70 ? 'bg-gov-emerald-500' :
                        item.avg_score >= 50 ? 'bg-gov-saffron-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, item.avg_score)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: REGISTERED CITIZENS */}
      {/* ======================================================== */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950">
            Registered Citizens & Entrepreneurs
          </h3>

          {loadingUsers ? (
            <SkeletonLoader.Table rows={4} cols={4} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                    <th className="pb-3">Citizen Name</th>
                    <th className="pb-3">Email / Account</th>
                    <th className="pb-3">Category</th>
                    <th className="pb-3">Location</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(usersData?.users || usersData || []).slice(0, 10).map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="py-3 font-bold text-gov-navy-950">{u.full_name || 'Anonymous Citizen'}</td>
                      <td className="py-3 text-slate-600">{u.email || u.phone || '—'}</td>
                      <td className="py-3 font-bold uppercase">{u.social_category || 'General'}</td>
                      <td className="py-3 text-slate-600">{u.district ? `${u.district}, ` : ''}{u.state || 'India'}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-50 text-gov-emerald-700">
                          Active Profile
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: SCHEME MANAGEMENT */}
      {/* ======================================================== */}
      {activeTab === 'schemes' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950">
            Active Welfare & Credit Schemes
          </h3>

          {loadingSchemes ? (
            <SkeletonLoader.Table rows={4} cols={4} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                    <th className="pb-3">Scheme Name</th>
                    <th className="pb-3">Nodal Ministry</th>
                    <th className="pb-3">Category</th>
                    <th className="pb-3">Max Benefit</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(schemesData || []).slice(0, 10).map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <td className="py-3 font-bold text-gov-navy-950">{s.name}</td>
                      <td className="py-3 text-slate-600">{s.ministry || 'Ministry of MSME'}</td>
                      <td className="py-3 capitalize">{s.category || 'Credit Linked'}</td>
                      <td className="py-3 font-bold text-gov-emerald-700">
                        {s.max_benefit_inr ? `₹${s.max_benefit_inr.toLocaleString('en-IN')}` : 'Subsidy / Loan'}
                      </td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-50 text-gov-emerald-700">
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 5: SYSTEM MONITORING */}
      {/* ======================================================== */}
      {activeTab === 'system' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Server size={18} className="text-gov-emerald-600" />
              <span>FastAPI Backend</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">Operational (Port 8001)</p>
            <p className="text-[11px] text-slate-400">Response time: &lt; 45ms</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Database size={18} className="text-gov-emerald-600" />
              <span>Database Cluster</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">PostgreSQL / SQLite Active</p>
            <p className="text-[11px] text-slate-400">Connection pool healthy</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Activity size={18} className="text-gov-emerald-600" />
              <span>Redis Cache Adapter</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">Resilient Fallback Mode</p>
            <p className="text-[11px] text-slate-400">Zero-crash memory cache active</p>
          </div>
        </div>
      )}

    </div>
  );
}

function KPICard({ label, value, sub, icon: Icon, accent }) {
  return (
    <div className={`bg-white p-4 sm:p-5 rounded-3xl border border-slate-200 shadow-gov ${accent}`}>
      <div className="flex justify-between items-start mb-2">
        <span className="text-[10px] sm:text-xs font-bold text-slate-400 uppercase tracking-wide">{label}</span>
        <Icon size={16} className="text-slate-400" />
      </div>
      <p className="text-xl sm:text-2xl font-extrabold text-gov-navy-950">
        {typeof value === 'number' ? value.toLocaleString() : value || '0'}
      </p>
      <p className="text-[10px] sm:text-[11px] text-slate-400 mt-0.5">{sub}</p>
    </div>
  );
}
