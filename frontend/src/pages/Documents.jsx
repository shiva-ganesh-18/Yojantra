import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  FolderUp, FileText, CheckCircle2, AlertTriangle, Clock, 
  XCircle, ShieldCheck, Download, Plus, X, ArrowRight, Check,
  Sparkles, Layers, Target, Info, CheckCircle, RefreshCw, Trash2
} from 'lucide-react';
import DocumentUploader from '../components/DocumentUploader';
import SkeletonLoader from '../components/SkeletonLoader';
import documentService from '../services/documentService';
import schemeService from '../services/schemeService';

export default function Documents() {
  const { user } = useAuthStore();
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [showUploader, setShowUploader] = useState(false);
  const [selectedTypeForUpload, setSelectedTypeForUpload] = useState('');
  const [selectedSchemeId, setSelectedSchemeId] = useState('');
  const [autoFillSuccess, setAutoFillSuccess] = useState(null);
  const [autoFillError, setAutoFillError] = useState(null);
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  // Fetch schemes list for dynamic scheme checklist selector
  const { data: schemesData } = useQuery('schemes_dropdown', async () => {
    try {
      const res = await schemeService.searchSchemes({ page: 1, page_size: 50 });
      return Array.isArray(res) ? res : (res?.items || []);
    } catch {
      return [];
    }
  });

  // Fetch user uploaded documents
  const { data: uploadedDocs = [], isLoading: isDocsLoading } = useQuery(
    'my_documents', 
    () => documentService.listMyDocuments()
  );

  // Fetch dynamic readiness score and checklist
  const { data: readinessData, isLoading: isReadinessLoading } = useQuery(
    ['document_readiness', selectedSchemeId],
    () => documentService.getReadiness(selectedSchemeId || null),
    { keepPreviousData: true }
  );

  const openUploadFor = (type) => {
    setSelectedTypeForUpload(type);
    setShowUploader(true);
    window.scrollTo({ top: 400, behavior: 'smooth' });
  };

  const refreshVaultDependents = () => {
    // SINGLE shared vault: refresh every view derived from it.
    queryClient.invalidateQueries('my_documents');
    queryClient.invalidateQueries('document_readiness');
    queryClient.invalidateQueries('applications_list');
    queryClient.invalidateQueries('matches');
    queryClient.invalidateQueries('schemes');
  };

  const handle1ClickAutoFill = async () => {
    setAutoFillLoading(true);
    setAutoFillError(null);
    try {
      const res = await documentService.autoFillProfile();
      setAutoFillSuccess(res.message);
      refreshVaultDependents();
      setTimeout(() => setAutoFillSuccess(null), 5000);
    } catch (e) {
      console.error(e);
      setAutoFillError(e?.message || 'Auto-fill failed. Please try again.');
      setTimeout(() => setAutoFillError(null), 5000);
    } finally {
      setAutoFillLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (window.confirm("Are you sure you want to delete this document?")) {
      setDeletingId(docId);
      try {
        await documentService.deleteDocument(docId);
        refreshVaultDependents();
      } catch (e) {
        console.error(e);
        alert(e?.message || 'Failed to delete document. Please try again.');
      } finally {
        setDeletingId(null);
      }
    }
  };

  const handleDownload = async (docId, defaultName) => {
    setDownloadingId(docId);
    try {
      await documentService.downloadDocument(docId, defaultName);
    } catch (e) {
      console.error(e);
      alert(e?.message || 'Failed to download document. Please try again.');
    } finally {
      setDownloadingId(null);
    }
  };

  const readinessScore = readinessData?.readiness_score ?? 0;
  const isReady = readinessData?.is_ready_to_apply ?? false;
  const checklist = readinessData?.checklist || [];

  return (
    <div className="space-y-6 text-left">
      
      {/* Header Banner & Readiness Score Meter */}
      <div className="bg-white p-6 sm:p-7 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-gov-saffron-100 text-gov-saffron-700">
                <FolderUp size={22} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                {t('docs_title', 'Document Vault & Readiness Checker')}
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              {t('docs_subtitle', 'Upload once, apply anywhere. Optical Character Recognition (OCR) extracts your verified identity & enterprise credentials while keeping Aadhaar/PAN secure.')}
            </p>
            
            {/* Scheme Selector Dropdown */}
            <div className="pt-2 flex items-center gap-2">
              <label htmlFor="scheme-checklist-select" className="text-xs font-bold text-gov-navy-950 whitespace-nowrap">{t('docs_checklist_for_scheme', 'Checklist For Scheme')}:</label>
              <select
                id="scheme-checklist-select"
                value={selectedSchemeId}
                onChange={(e) => setSelectedSchemeId(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded-xl px-3 py-1.5 text-xs font-semibold text-gov-navy-950 focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10 focus:border-gov-navy-950"
              >
                <option value="">-- {t('docs_tab_all', 'General Enterprise Readiness (All Core Docs)')} --</option>
                {(schemesData || []).map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.ministry})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Readiness Score Progress Card */}
          <div className="bg-gradient-to-br from-gov-navy-950 to-gov-navy-900 text-white p-5 rounded-2xl flex items-center gap-5 sm:min-w-[320px] shadow-md">
            <div className="relative w-18 h-18 flex items-center justify-center flex-shrink-0">
              <svg className="w-18 h-18 -rotate-90" viewBox="0 0 36 36" role="img" aria-label={`${t('docs_readiness_score', 'Document Readiness')}: ${readinessScore}%`}>
                <path
                  className="text-white/10"
                  strokeWidth="3.8"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={readinessScore >= 70 ? 'text-gov-emerald-400' : 'text-gov-saffron-400'}
                  strokeDasharray={`${readinessScore}, 100`}
                  strokeWidth="3.8"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-base font-extrabold">{readinessScore}%</span>
            </div>

            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className={`text-[10px] uppercase font-extrabold px-2 py-0.5 rounded-full ${
                  isReady ? 'bg-gov-emerald-500/20 text-gov-emerald-300 border border-gov-emerald-400/30' : 'bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-400/30'
                }`}>
                  {isReady ? `✓ ${t('docs_readiness_score', 'Ready to Apply')}` : `⚠ ${t('docs_action_needed', 'Action Needed')}`}
                </span>
              </div>
              <h4 className="text-sm font-bold">{t('docs_readiness_score', 'Document Readiness')}</h4>
              <p className="text-[11px] text-slate-300 mt-0.5">
                {readinessData?.total_uploaded || 0} of {readinessData?.total_required || 0} {t('nav_documents', 'documents uploaded')}
                {readinessData?.missing_mandatory_count > 0 && (
                  <span className="text-amber-300 font-bold block sm:inline sm:ml-1">
                    ({readinessData.missing_mandatory_count} mandatory missing)
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Dynamic Scheme Checklist Grid */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              {readinessData?.scheme_name ? `${t('docs_checklist_title', 'Checklist')}: ${readinessData.scheme_name}` : t('docs_checklist_general', 'Document Checklist')}
            </p>
            <span className="text-[11px] text-slate-500 font-medium">
              {readinessData?.readiness_summary}
            </span>
          </div>

          {isReadinessLoading ? (
            <SkeletonLoader.Table rows={2} cols={3} />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {checklist.map((item) => (
                <div 
                  key={item.doc_type}
                  className={`border rounded-2xl p-3.5 flex items-center justify-between gap-3 transition-all ${
                    item.is_uploaded 
                      ? 'bg-gov-emerald-50/40 border-gov-emerald-200' 
                      : item.is_mandatory 
                      ? 'bg-amber-50/40 border-amber-200' 
                      : 'bg-slate-50/70 border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className={`w-9 h-9 rounded-xl border flex items-center justify-center flex-shrink-0 font-bold mt-0.5 ${
                      item.is_uploaded 
                        ? 'bg-gov-emerald-100 text-gov-emerald-800 border-gov-emerald-300' 
                        : 'bg-white text-slate-500 border-slate-200'
                    }`}>
                      <FileText size={17} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <h4 className="text-xs font-bold text-gov-navy-950 leading-tight">{item.name}</h4>
                        <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded border flex-shrink-0 ${
                          item.is_scheme_specific
                            ? 'bg-purple-50 text-purple-700 border-purple-200'
                            : 'bg-blue-50 text-blue-700 border-blue-200'
                        }`}>
                          {item.category || (item.is_scheme_specific ? 'Scheme-Specific' : 'General Enterprise')}
                        </span>
                        {item.is_mandatory && (
                          <span className="text-[9px] font-bold text-red-600 bg-red-50 border border-red-200/60 px-1 py-0.2 rounded flex-shrink-0">
                            Mandatory
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 line-clamp-1 mt-0.5">{item.description}</p>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      item.is_verified
                        ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200'
                        : item.is_uploaded
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : item.is_mandatory 
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-slate-100 text-slate-500 border-slate-200'
                    }`}>
                      {item.is_verified
                        ? '✓ Verified in Document Vault'
                        : item.is_uploaded
                        ? `✓ ${t('docs_status_uploaded', 'Uploaded')}`
                        : t('docs_missing', 'Missing')}
                    </span>
                    {!item.is_uploaded && (
                      <button
                        onClick={() => openUploadFor(item.doc_type)}
                        className="text-[10px] font-bold text-gov-saffron-700 hover:underline"
                      >
                        Upload to Document Vault &rarr;
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Row */}
          <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <ShieldCheck size={16} className="text-gov-emerald-600 flex-shrink-0" />
              <span>DPDP Act 2023 Compliant: Sensitive numbers masked. Connect with DigiLocker or accredited channel partners for official e-KYC.</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handle1ClickAutoFill}
                disabled={uploadedDocs.length === 0 || autoFillLoading}
                className="px-4 py-2 rounded-xl bg-gov-saffron-50 hover:bg-gov-saffron-100 text-gov-saffron-800 text-xs font-bold transition-all flex items-center gap-1.5 border border-gov-saffron-200 disabled:opacity-50"
              >
                {autoFillLoading ? (
                  <span className="w-3.5 h-3.5 border-2 border-gov-saffron-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Sparkles size={14} className="text-gov-saffron-600" />
                )}
                <span>{autoFillLoading ? 'Processing...' : t('docs_auto_fill', 'Auto-Fill Profile from OCR')}</span>
              </button>

              <button
                onClick={() => { setSelectedTypeForUpload(''); setShowUploader(!showUploader); }}
                className="px-4 py-2 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
              >
                {showUploader ? <X size={15} /> : <Plus size={15} />}
                <span>{showUploader ? t('btn_close', 'Close') : t('btn_upload', 'Upload Document')}</span>
              </button>
            </div>
          </div>

          {autoFillSuccess && (
            <div role="status" className="mt-3 p-3 bg-gov-emerald-50 border border-gov-emerald-200 rounded-xl text-xs font-bold text-gov-emerald-800 flex items-center gap-2">
              <CheckCircle size={16} />
              <span>{autoFillSuccess}</span>
            </div>
          )}
          {autoFillError && (
            <div role="alert" className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-xs font-bold text-red-700 flex items-center gap-2">
              <AlertTriangle size={16} />
              <span>{autoFillError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Document Uploader Area */}
      {showUploader && (
        <DocumentUploader
          key={selectedTypeForUpload}
          defaultDocType={selectedTypeForUpload}
          onUploadComplete={() => {
            refreshVaultDependents();
          }}
        />
      )}

      {/* Uploaded Documents Vault Archive */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="font-bold text-base text-gov-navy-950">
              {t('docs_vault_title', 'Encrypted Document Vault')}
            </h3>
            <p className="text-xs text-slate-500">
              {t('docs_vault_sub', 'Tamper-tested digital repository linked to your Yojantra entrepreneur profile.')}
            </p>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {uploadedDocs.length} Documents
          </span>
        </div>

        {isDocsLoading ? (
          <SkeletonLoader.Table rows={3} cols={3} />
        ) : uploadedDocs.length === 0 ? (
          <div className="py-10 text-center space-y-2">
            <FileText size={40} className="mx-auto text-slate-400" />
            <p className="text-sm font-bold text-gov-navy-950">{t('docs_empty_title', 'No documents uploaded yet')}</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload your Aadhaar, PAN, Bank Passbook, or UDYAM certificate to automatically unlock 1-click scheme matching and profile auto-fill.
            </p>
            <button
              onClick={() => setShowUploader(true)}
              className="mt-3 px-5 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold transition-all shadow-sm"
            >
              Upload First Document
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {uploadedDocs.map((doc) => (
              <div 
                key={doc.id}
                className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 p-2 rounded-xl transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gov-navy-100 text-gov-navy-900 flex items-center justify-center font-bold flex-shrink-0">
                    <FileText size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-gov-navy-950 capitalize">
                        {doc.doc_type?.replace('_', ' ')}
                      </h4>
                      {doc.masked_number && (
                        <span className="text-[11px] font-mono font-bold text-gov-navy-900 bg-slate-100 px-2 py-0.5 rounded">
                          {doc.masked_number}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Uploaded on {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'Recently'} • Format: {doc.file_format?.toUpperCase()}
                    </p>
                    {doc.duplicate_warning && (
                      <p className="text-[11px] text-amber-700 font-semibold flex items-center gap-1 mt-1">
                        <AlertTriangle size={12} />
                        <span>{doc.duplicate_warning}</span>
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <span className="text-[10px] font-bold text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full">
                    {doc.verification_tier || 'Heuristic OCR'}
                  </span>

                  <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                    doc.verification_status === 'verified'
                      ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}>
                    {doc.verification_status === 'verified' ? '✓ OCR Parsed' : '⏳ Pending'}
                  </span>

                  <button
                    onClick={() => handleDownload(doc.id, `${doc.doc_type || 'document'}.${doc.file_format || 'pdf'}`)}
                    disabled={downloadingId === doc.id}
                    aria-label="Download document"
                    title="Download document"
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center p-1.5 rounded-lg text-slate-500 hover:text-gov-navy-950 hover:bg-slate-100 transition-colors disabled:opacity-50"
                  >
                    {downloadingId === doc.id ? (
                      <span className="w-4 h-4 border-2 border-slate-600 border-t-transparent rounded-full animate-spin inline-block" />
                    ) : (
                      <Download size={16} />
                    )}
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    aria-label="Delete document"
                    className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center p-1.5 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                  >
                    {deletingId === doc.id ? (
                      <span className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin inline-block" />
                    ) : (
                      <Trash2 size={16} />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

