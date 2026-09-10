import React from 'react';
import { 
  X, Building2, Award, Globe, MapPin, Phone, Mail, 
  CheckCircle2, ShieldCheck, ExternalLink, ArrowRight, Navigation 
} from 'lucide-react';

/**
 * InstitutionDrawer: Channel partner & facilitation center details drawer.
 */
export const InstitutionDrawer = ({
  institution,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !institution) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity animate-in fade-in"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-lg bg-white shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-2xl bg-orange-100 text-orange-700 flex items-center justify-center shrink-0 shadow-inner">
                <Building2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900 leading-tight">
                    {institution.name}
                  </h3>
                </div>
                {institution.short_name && (
                  <span className="inline-block mt-1 px-2 py-0.5 rounded text-[11px] font-bold bg-slate-200/80 text-slate-700">
                    {institution.short_name}
                  </span>
                )}
                <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>{institution.city || institution.district}, {institution.state}</span>
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Key Accreditations / Badges */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-left">
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block mb-1">
                  Partner Code
                </span>
                <span className="font-mono text-sm font-bold text-slate-800">
                  {institution.code || 'Registered Partner'}
                </span>
              </div>

              <div className="p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-100 text-left">
                <span className="text-[11px] font-medium text-emerald-700 uppercase tracking-wider block mb-1 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Verification Status
                </span>
                <span className="text-sm font-bold text-emerald-900">
                  Authorized Center
                </span>
              </div>
            </div>

            {/* Partner Details */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Partner Details & Accreditation
              </h4>
              <div className="divide-y divide-slate-100 text-xs border border-slate-100 rounded-2xl overflow-hidden bg-white">
                <div className="px-4 py-3 flex justify-between">
                  <span className="text-slate-500">Institution Category</span>
                  <span className="font-semibold text-slate-800">{institution.institution_type || 'State Channelizing Agency / Facilitation'}</span>
                </div>
                {institution.distance_km !== null && institution.distance_km !== undefined && (
                  <div className="px-4 py-3 flex justify-between">
                    <span className="text-slate-500">Distance from You</span>
                    <span className="font-bold text-gov-emerald-700">{institution.distance_km} km</span>
                  </div>
                )}
                <div className="px-4 py-3 flex justify-between items-center">
                  <span className="text-slate-500">Channel Partner Classification</span>
                  <span className="font-semibold text-blue-700">{institution.fund_availability_status || 'Eligible Channel Type'}</span>
                </div>
                <div className="px-4 py-3 flex justify-between">
                  <span className="text-slate-500">Location</span>
                  <span className="font-semibold text-slate-800">{institution.district}, {institution.state}</span>
                </div>
                {institution.address && (
                  <div className="px-4 py-3 flex justify-between">
                    <span className="text-slate-500">Address</span>
                    <span className="font-semibold text-slate-800 max-w-[240px] text-right">{institution.address}</span>
                  </div>
                )}
                {institution.website && (
                  <div className="px-4 py-3 flex justify-between items-center">
                    <span className="text-slate-500">Official Portal</span>
                    <a
                      href={institution.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-orange-600 hover:text-orange-700 flex items-center gap-1"
                    >
                      <span>Visit Portal</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Live Banking / CBS Data Sync Status */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center justify-between">
                <span>Core Banking & Quota Status</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                  institution.sync_status === 'LIVE'
                    ? 'bg-emerald-100 text-emerald-900'
                    : institution.sync_status === 'FALLBACK'
                    ? 'bg-amber-100 text-amber-900'
                    : 'bg-blue-100 text-blue-900'
                }`}>
                  {institution.sync_status === 'LIVE' ? 'VERIFIED LIVE' : institution.sync_status === 'FALLBACK' ? 'FALLBACK METADATA' : 'CONFIGURATION-READY'}
                </span>
              </h4>

              <div className="divide-y divide-slate-100 text-xs border border-slate-100 rounded-2xl overflow-hidden bg-slate-50/60 p-3 space-y-2">
                <div className="flex justify-between items-center text-slate-600">
                  <span>Data Provider</span>
                  <span className="font-semibold text-slate-800">{institution.provider_name || 'National Banking & SCA Gateway'}</span>
                </div>
                <div className="flex justify-between items-center text-slate-600 pt-2">
                  <span>Lending Capacity Tier</span>
                  <span className="font-semibold text-slate-800">{institution.capacity_tier || 'UNVERIFIED'}</span>
                </div>
                <div className="flex justify-between items-center text-slate-600 pt-2">
                  <span>NPA Risk Safeguard</span>
                  <span className="font-semibold text-slate-800">{institution.npa_risk_indicator || 'UNKNOWN'}</span>
                </div>
                <div className="flex justify-between items-center text-slate-600 pt-2">
                  <span>Last Sync Status</span>
                  <span className="font-semibold text-slate-700">
                    {institution.last_synced_at ? new Date(institution.last_synced_at).toLocaleString() : 'Standby (Metadata Default)'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 leading-relaxed italic">
                  * {institution.fund_disclosure || 'Live banking telemetry activates when accredited banking gateway credentials are provided.'}
                </p>
              </div>
            </div>

            {/* Recommendation & Routing Notice */}
            {institution.recommendation_reason && (
              <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-xs text-amber-950 space-y-1">
                <p className="font-bold flex items-center gap-1.5 text-amber-900">
                  <Award className="w-4 h-4 text-amber-600" />
                  Routing & Recommendation Note
                </p>
                <p className="text-[11px] text-amber-900/90 leading-relaxed">
                  {institution.recommendation_reason}
                </p>
              </div>
            )}

            {/* Entrepreneur Facilitation Notice */}
            <div className="p-4 rounded-2xl bg-orange-50/70 border border-orange-100 text-xs text-orange-950 space-y-1">
              <p className="font-bold flex items-center gap-1.5 text-orange-800">
                <ShieldCheck className="w-4 h-4 text-orange-600" />
                Scheme Routing & Assistance
              </p>
              <p className="text-[11px] text-orange-900/80 leading-relaxed">
                Entrepreneurs can visit or contact this channel partner for scheme application facilitation, physical document verification, and credit subsidy processing.
              </p>
            </div>
            {/* Directions & Contact Actions */}
            <div className="pt-2 flex flex-col sm:flex-row gap-2">
              {institution.latitude !== null && institution.latitude !== undefined && institution.longitude !== null && institution.longitude !== undefined ? (
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${institution.latitude},${institution.longitude}`)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-3 px-4 rounded-xl bg-gov-saffron-500 hover:bg-gov-saffron-600 text-gov-navy-950 font-black text-xs transition-all shadow-sm flex items-center justify-center gap-2"
                >
                  <Navigation size={14} />
                  <span>Get Directions</span>
                </a>
              ) : (
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${institution.name} ${institution.district} ${institution.state}`)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-3 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-all flex items-center justify-center gap-2"
                >
                  <MapPin size={14} />
                  <span>Search on Map</span>
                </a>
              )}

              {institution.contact_phone && (
                <a
                  href={`tel:${institution.contact_phone}`}
                  className="py-3 px-4 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs transition-all flex items-center justify-center gap-2"
                >
                  <Phone size={14} className="text-gov-emerald-600" />
                  <span>Call Branch</span>
                </a>
              )}
            </div>

            {/* Mandatory Real-Time Banking & Dispersal Disclosure */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[10px] text-slate-500 leading-relaxed">
              <p className="font-semibold text-slate-700 mb-0.5">Informational Routing Notice:</p>
              <p>Fund availability and current quota are not verified in real time. Contact the partner to confirm current availability. Yojantra's ranking is informational and does not constitute government endorsement or loan sanction guarantee.</p>
            </div>
          </div>

          {/* Footer */}
          <div className="p-5 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-3">
            <span className="text-[11px] text-slate-400">Standard RBI / Ministry Dispersal Facility</span>
            <button
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InstitutionDrawer;

