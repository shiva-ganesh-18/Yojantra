import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { 
  FolderUp, FileText, CheckCircle2, AlertTriangle, Clock, 
  XCircle, ShieldCheck, Download, Plus, ArrowRight, Check
} from 'lucide-react';
import DocumentUploader from '../components/DocumentUploader';
import SkeletonLoader from '../components/SkeletonLoader';

const CORE_DOCUMENTS = [
  { id: 'aadhaar', name: 'Aadhaar Card', desc: 'UIDAI biometric identity', required: true },
  { id: 'pan', name: 'PAN Card', desc: 'Permanent Account Number', required: true },
  { id: 'bank_passbook', name: 'Bank Passbook / Statement', desc: 'Direct Benefit Transfer (DBT)', required: true },
  { id: 'udyam', name: 'UDYAM Registration', desc: 'Ministry of MSME registration', required: false },
  { id: 'income_certificate', name: 'Income Certificate', desc: 'Tahsildar/SDM issued certificate', required: true },
  { id: 'caste_certificate', name: 'Caste Certificate', desc: 'SC/ST/OBC verification', required: false },
];

export default function Documents() {
  const { api } = useAuthStore();
  const queryClient = useQueryClient();
  const [showUploader, setShowUploader] = useState(false);
  const [selectedTypeForUpload, setSelectedTypeForUpload] = useState('');

  const { data: uploadedDocs = [], isLoading } = useQuery('my_documents', () =>
    api().get('/documents/my-documents').then(r => r.data || [])
  );

  const getDocStatus = (docId) => {
    const found = uploadedDocs.find(d => d.doc_type === docId);
    if (!found) return { label: 'Not Uploaded', color: 'bg-slate-100 text-slate-500 border-slate-200', state: 'missing' };
    if (found.verification_status === 'verified') return { label: 'Verified', color: 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200', state: 'verified' };
    if (found.verification_status === 'pending') return { label: 'Needs Review', color: 'bg-amber-50 text-amber-800 border-amber-200', state: 'review' };
    if (found.verification_status === 'rejected') return { label: 'Rejected', color: 'bg-red-50 text-red-700 border-red-200', state: 'rejected' };
    return { label: 'Uploaded', color: 'bg-blue-50 text-blue-700 border-blue-200', state: 'uploaded' };
  };

  const openUploadFor = (type) => {
    setSelectedTypeForUpload(type);
    setShowUploader(true);
    window.scrollTo({ top: 400, behavior: 'smooth' });
  };

  return (
    <div className="space-y-6 text-left">
      
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-2 rounded-xl bg-gov-saffron-100 text-gov-saffron-700">
                <FolderUp size={20} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                Your Documents
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              Keep your documents ready for instant auto-filling and 1-click scheme applications.
            </p>
          </div>

          <button
            onClick={() => { setSelectedTypeForUpload(''); setShowUploader(!showUploader); }}
            className="self-start sm:self-auto px-5 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs sm:text-sm font-bold transition-all flex items-center gap-2 shadow-sm"
          >
            <Plus size={16} />
            <span>{showUploader ? 'Close Uploader' : 'Upload New Document'}</span>
          </button>
        </div>

        {/* Readiness Checklist Grid (MANDATORY REQUIREMENT) */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
            Application Readiness Status
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {CORE_DOCUMENTS.map((doc) => {
              const status = getDocStatus(doc.id);
              return (
                <div 
                  key={doc.id}
                  className="bg-slate-50/70 border border-slate-200 rounded-2xl p-3.5 flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 text-slate-500 font-bold">
                      <FileText size={17} />
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="text-xs font-bold text-gov-navy-950 truncate">{doc.name}</h4>
                      <p className="text-[10px] text-slate-400 truncate">{doc.desc}</p>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${status.color}`}>
                      {status.state === 'verified' && '✓ '}
                      {status.state === 'missing' && doc.required && '⚠ '}
                      {status.label}
                    </span>
                    {status.state === 'missing' && (
                      <button
                        onClick={() => openUploadFor(doc.id)}
                        className="text-[10px] font-bold text-gov-saffron-700 hover:underline"
                      >
                        Upload &rarr;
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Document Uploader Area */}
      {showUploader && (
        <DocumentUploader
          defaultDocType={selectedTypeForUpload}
          onUploadComplete={() => {
            queryClient.invalidateQueries('my_documents');
          }}
        />
      )}

      {/* Uploaded Documents Archive */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="font-bold text-base text-gov-navy-950">
              Verified Documents Archive
            </h3>
            <p className="text-xs text-slate-500">
              Encrypted digital vault linked to your SchemeMatch AI citizen profile.
            </p>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {uploadedDocs.length} Documents
          </span>
        </div>

        {isLoading ? (
          <SkeletonLoader.Table rows={3} cols={3} />
        ) : uploadedDocs.length === 0 ? (
          <div className="py-10 text-center space-y-2">
            <FileText size={40} className="mx-auto text-slate-300" />
            <p className="text-sm font-bold text-gov-navy-950">No documents uploaded yet</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload your documents to speed up scheme eligibility checks and auto-fill loan forms.
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
                    <h4 className="text-sm font-bold text-gov-navy-950 capitalize">
                      {doc.doc_type?.replace('_', ' ')}
                    </h4>
                    <p className="text-xs text-slate-400">
                      Uploaded on {new Date(doc.created_at).toLocaleDateString()} • Format: {doc.file_format?.toUpperCase()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                    doc.verification_status === 'verified'
                      ? 'bg-gov-emerald-50 text-gov-emerald-700 border-gov-emerald-200'
                      : doc.verification_status === 'pending'
                      ? 'bg-amber-50 text-amber-800 border-amber-200'
                      : 'bg-slate-100 text-slate-600 border-slate-200'
                  }`}>
                    {doc.verification_status === 'verified' && '✓ Verified'}
                    {doc.verification_status === 'pending' && '⏳ Processing OCR'}
                    {doc.verification_status === 'rejected' && '✕ Action Needed'}
                  </span>

                  {doc.ocr_preview && (
                    <span className="text-[11px] text-slate-500 bg-slate-100 px-2 py-1 rounded-lg font-mono hidden md:inline">
                      OCR Extracted
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
