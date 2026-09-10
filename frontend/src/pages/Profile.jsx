import React, { useState } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useQuery, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import { 
  User, Building2, FileText, LogOut, ChevronRight, 
  MapPin, ShieldCheck, CheckCircle2, Edit3, Sparkles, 
  IndianRupee, X, Save, Check, Link2, AlertCircle, Phone
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';
import StateSelector from '../components/StateSelector';
import DistrictSelector from '../components/DistrictSelector';
import { signInWithGooglePopup, isFirebaseConfigured } from '../config/firebase';
import { linkGoogleAccount } from '../services/authService';
import { 
  BUSINESS_TYPES, 
  BUSINESS_STAGES, 
  REGISTRATION_TYPES, 
  normalizeBusinessType, 
  normalizeBusinessStage, 
  normalizeRegistrationType,
  getBusinessTypeLabel,
  getBusinessStageLabel,
  getRegistrationTypeLabel
} from '../utils/businessMappings';

export default function Profile() {
  const { api, user, setUser, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('personal');
  const [isEditing, setIsEditing] = useState(false);
  const [linkingGoogle, setLinkingGoogle] = useState(false);
  const [linkMessage, setLinkMessage] = useState(null);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch business info
  const { data: business, isLoading: loadingBusiness } = useQuery('user_business', () =>
    api().get('/users/me/business').then(r => r.data).catch(() => null), { enabled: !!user }
  );

  // Fetch documents count
  const { data: documents = [] } = useQuery('user_documents', () =>
    api().get('/documents/my-documents').then(r => r.data || []), { enabled: !!user }
  );

  // Edit form state
  const [editForm, setEditForm] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    gender: user?.gender || 'male',
    social_category: user?.social_category || 'obc',
    date_of_birth: user?.date_of_birth || '',
    literacy_level: user?.literacy_level || 'secondary',
    state: user?.state || '',
    district: user?.district || '',
    is_rural: user?.is_rural ?? true,
    preferred_language: user?.preferred_language || 'hi',
    // Business
    business_name: business?.business_name || '',
    registration_type: normalizeRegistrationType(business?.registration_type),
    business_type: normalizeBusinessType(business?.business_type || business?.sector),
    business_stage: normalizeBusinessStage(business?.business_stage),
    sector: normalizeBusinessType(business?.sector || business?.business_type),
    annual_turnover_inr: business?.annual_turnover_inr || 500000,
    funding_needed_inr: business?.funding_needed_inr || 1000000,
    has_collateral: business?.has_collateral || false,
  });

  const handleOpenEdit = () => {
    setSaveError('');
    setEditForm({
      full_name: user?.full_name || '',
      phone: user?.phone || '',
      gender: user?.gender || 'male',
      social_category: user?.social_category || 'obc',
      date_of_birth: user?.date_of_birth || '',
      literacy_level: user?.literacy_level || 'secondary',
      state: user?.state || '',
      district: user?.district || '',
      is_rural: user?.is_rural ?? true,
      preferred_language: user?.preferred_language || 'hi',
      business_name: business?.business_name || '',
      registration_type: normalizeRegistrationType(business?.registration_type),
      business_type: normalizeBusinessType(business?.business_type || business?.sector),
      business_stage: normalizeBusinessStage(business?.business_stage),
      sector: normalizeBusinessType(business?.sector || business?.business_type),
      annual_turnover_inr: business?.annual_turnover_inr || 500000,
      funding_needed_inr: business?.funding_needed_inr || 1000000,
      has_collateral: business?.has_collateral || false,
    });
    setIsEditing(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaveError('');
    setSaveSuccess(false);

    // Client-side validation
    if (!editForm.state) {
      setSaveError('State is required.');
      return;
    }
    if (!editForm.district) {
      setSaveError('District is required.');
      return;
    }
    if (editForm.phone) {
      const digits = editForm.phone.replace(/\D/g, '').slice(-10);
      if (!/^[6-9]\d{9}$/.test(digits)) {
        setSaveError('Enter a valid 10-digit Indian mobile number.');
        return;
      }
    }

    try {
      const res = await api().put('/users/me', {
        full_name: editForm.full_name,
        phone: editForm.phone || null,
        gender: editForm.gender,
        social_category: editForm.social_category,
        date_of_birth: editForm.date_of_birth || null,
        literacy_level: editForm.literacy_level || null,
        state: editForm.state,
        district: editForm.district,
        is_rural: editForm.is_rural,
        preferred_language: editForm.preferred_language,
        onboarding_completed: true,
      });

      if (res.data) setUser(res.data);

      const canonicalBType = normalizeBusinessType(editForm.business_type);
      const canonicalBStage = normalizeBusinessStage(editForm.business_stage);
      const canonicalRegType = normalizeRegistrationType(editForm.registration_type);

      await api().post('/users/me/business', {
        business_name: editForm.business_name || 'My Business Enterprise',
        business_type: canonicalBType,
        business_stage: canonicalBStage,
        registration_type: canonicalRegType,
        sector: canonicalBType,
        annual_turnover_inr: parseFloat(editForm.annual_turnover_inr) || 0,
        funding_needed_inr: parseFloat(editForm.funding_needed_inr) || 0,
        has_collateral: editForm.has_collateral,
      });

      queryClient.invalidateQueries('user_business');
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      const serverDetail = err.response?.data?.detail;
      let errorMsg = 'Failed to update profile. Please verify your details.';
      if (Array.isArray(serverDetail)) {
        errorMsg = serverDetail.map(d => `${d.loc ? d.loc.join('.') : 'Field'}: ${d.msg}`).join(', ');
      } else if (typeof serverDetail === 'string') {
        errorMsg = serverDetail;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setSaveError(errorMsg);
    }
  };

  const handleLinkGoogle = async () => {
    if (!isFirebaseConfigured()) {
      setLinkMessage({
        type: 'error',
        text: 'Google authentication is currently not configured on this environment.'
      });
      return;
    }
    setLinkingGoogle(true);
    setLinkMessage(null);
    try {
      const { idToken } = await signInWithGooglePopup();
      const updatedUser = await linkGoogleAccount(idToken);
      if (updatedUser) {
        setUser(updatedUser);
      }
      setLinkMessage({
        type: 'success',
        text: 'Google account linked successfully!'
      });
    } catch (err) {
      console.error('Google linking error:', err);
      let errMsg = 'Failed to link Google account.';
      if (err.code === 'auth/popup-closed-by-user') {
        errMsg = 'Google sign-in was cancelled.';
      } else if (err.response?.data?.detail) {
        errMsg = err.response.data.detail;
      }
      setLinkMessage({
        type: 'error',
        text: errMsg
      });
    } finally {
      setLinkingGoogle(false);
    }
  };

  // Calculate truthful profile completion percentage aligned with backend
  let completionScore = 0;
  if (user?.profile_completion_percentage != null && user?.profile_completion_percentage > 0) {
    completionScore = user.profile_completion_percentage;
  } else {
    // Aligned client calculation
    if (user?.full_name?.trim()) completionScore += 15;
    if (user?.phone?.trim() && user.phone.length >= 10) completionScore += 15;
    if (user?.state) {
      completionScore += 7;
      if (user?.district) completionScore += 8;
    }
    if (user?.social_category) completionScore += 10;
    if (user?.date_of_birth) completionScore += 10;
    if (user?.gender) completionScore += 5;
    if (business?.business_name) completionScore += 15;
    if (business?.annual_turnover_inr != null || business?.funding_needed_inr != null) completionScore += 15;

    // Strict Gating: Active mobile number is mandatory. Without phone or location, score CANNOT exceed 70%
    if (!user?.phone || user.phone.trim().length < 10) {
      completionScore = Math.min(70, completionScore);
    }
    if (!user?.state || !user?.district) {
      completionScore = Math.min(70, completionScore);
    }
  }

  const tabs = [
    { id: 'personal', label: 'Personal Information', icon: User },
    { id: 'business', label: 'Business Profile', icon: Building2 },
    { id: 'eligibility', label: 'Eligibility & Quotas', icon: ShieldCheck },
    { id: 'documents', label: 'Documents & Vault', icon: FileText },
  ];

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto">
      
      {/* Top Profile Card */}
      <div className="bg-gradient-to-r from-gov-navy-950 via-gov-navy-900 to-gov-navy-950 text-white p-6 sm:p-8 rounded-3xl shadow-xl border border-gov-navy-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gov-saffron-600 text-white font-extrabold flex items-center justify-center text-2xl shadow-inner uppercase overflow-hidden">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt={user.full_name || 'User'} className="w-full h-full object-cover" />
              ) : (
                user?.full_name ? user.full_name.charAt(0) : 'U'
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white">
                  {user?.full_name || 'Citizen User'}
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-500/20 text-gov-emerald-300 border border-gov-emerald-400/30 uppercase">
                  {user?.role || 'Citizen'}
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-400/30 uppercase">
                  {user?.auth_provider === 'google+phone' ? 'Google + Phone' : user?.auth_provider === 'google' ? 'Google' : 'Phone'}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
                {user?.phone ? user.phone : (user?.email || 'No contact specified')} • {user?.district ? `${user.district}, ` : ''}{user?.state || 'State not set'} ({user?.is_rural ? 'Rural' : 'Urban'})
              </p>
            </div>
          </div>

          <button
            onClick={handleOpenEdit}
            className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs sm:text-sm font-semibold border border-white/20 transition-all flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Edit3 size={15} />
            <span>Edit Profile</span>
          </button>
        </div>

        {/* Profile Completion Bar (MANDATORY REQUIREMENT) */}
        <div className="mt-6 pt-5 border-t border-gov-navy-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gov-saffron-300">
                {completionScore}% Profile Completed
              </span>
              <span className="text-[11px] text-slate-400">
                — Complete your profile to improve scheme matching accuracy
              </span>
            </div>
            <div className="w-full sm:w-96 bg-gov-navy-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-gov-saffron-500 to-gov-emerald-400 h-full rounded-full transition-all duration-300"
                style={{ width: `${completionScore}%` }}
              />
            </div>
          </div>

          {completionScore < 100 && (
            <button
              onClick={handleOpenEdit}
              className="text-xs font-bold text-gov-saffron-300 hover:text-gov-saffron-200 flex items-center gap-1 self-start sm:self-auto"
            >
              <span>Complete Missing Fields</span>
              <ChevronRight size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all border flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-gov-navy-950 text-white border-gov-navy-950 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Personal Information */}
      {activeTab === 'personal' && (
        <div className="space-y-4">
          {!user?.phone && (
            <div className="p-4 bg-amber-50 border border-amber-300 rounded-2xl flex items-center justify-between gap-3 text-amber-950">
              <div className="flex items-center gap-2.5">
                <AlertCircle size={20} className="text-amber-600 flex-shrink-0" />
                <div>
                  <p className="text-xs font-bold">Active Mobile Number Missing</p>
                  <p className="text-[11px] text-amber-800">
                    A valid mobile number is required for nodal SMS alerts, Direct Benefit Transfer (DBT), and scheme submission. Profile completion is capped at 70% until updated.
                  </p>
                </div>
              </div>
              <button
                onClick={handleOpenEdit}
                className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold flex-shrink-0 shadow-xs"
              >
                Add Mobile
              </button>
            </div>
          )}

          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950 pb-3 border-b border-slate-100">
              Personal & Demographic Details
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ProfileItem label="Legal Full Name" value={user?.full_name} />
              <ProfileItem label="Mobile Number" value={user?.phone || 'Not provided (Action Required)'} />
              <ProfileItem label="Email Address" value={user?.email || 'Not connected'} />
              <ProfileItem 
                label="Sign-In Method" 
                value={user?.auth_provider === 'google+phone' ? 'Google & Phone (Linked)' : user?.auth_provider === 'google' ? 'Google Account' : 'Phone / OTP'} 
              />
              <ProfileItem label="Gender" value={user?.gender?.toUpperCase()} />
              <ProfileItem label="Social Category" value={`${user?.social_category?.toUpperCase()} (Affirmative Quota Eligible)`} />
              <ProfileItem label="Date of Birth" value={user?.date_of_birth || 'Not specified'} />
              <ProfileItem label="Education / Literacy" value={user?.literacy_level || 'Secondary (10th)'} />
              <ProfileItem label="State" value={user?.state || 'Not specified'} />
              <ProfileItem label="District" value={user?.district || (user?.state ? `Action Required: Select district in ${user.state}` : 'Not specified')} />
              <ProfileItem label="Area Type" value={user?.is_rural ? 'Rural Village (Higher Subsidies)' : 'Urban Town/City'} />
              <ProfileItem label="Preferred Language" value={user?.preferred_language?.toUpperCase()} />
            </div>
          </div>

          {/* Connected Accounts & Security */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-base text-gov-navy-950">
                Connected Sign-In Methods
              </h3>
              <span className="text-xs text-slate-500 font-medium">Safe Account Linking</span>
            </div>

            {linkMessage && (
              <div className={`p-3.5 rounded-2xl text-xs font-semibold flex items-center gap-2.5 ${
                linkMessage.type === 'success' 
                  ? 'bg-gov-emerald-50 text-gov-emerald-800 border border-gov-emerald-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                {linkMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                <span>{linkMessage.text}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Phone Account */}
              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50/80 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center font-bold">
                    <Phone size={18} />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Phone Authentication</p>
                    <p className="text-[11px] text-slate-500">{user?.phone || 'No phone attached'}</p>
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-100 text-gov-emerald-800 border border-gov-emerald-200">
                  {user?.phone ? 'Active' : 'Optional'}
                </span>
              </div>

              {/* Google Account */}
              <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50/80 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center shadow-xs">
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Google Account</p>
                    <p className="text-[11px] text-slate-500 truncate max-w-[140px]">
                      {user?.email || (user?.firebase_uid ? 'Linked' : 'Not linked')}
                    </p>
                  </div>
                </div>
                {user?.firebase_uid ? (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-100 text-gov-emerald-800 border border-gov-emerald-200 flex items-center gap-1">
                    <CheckCircle2 size={12} />
                    <span>Linked</span>
                  </span>
                ) : (
                  <button
                    onClick={handleLinkGoogle}
                    disabled={linkingGoogle}
                    className="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <Link2 size={13} />
                    <span>{linkingGoogle ? 'Linking...' : 'Link Google'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Business Profile */}
      {activeTab === 'business' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950 pb-3 border-b border-slate-100">
            Enterprise Classification & Metrics
          </h3>
          {business ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ProfileItem label="Enterprise Name" value={business.business_name} />
              <ProfileItem label="Activity / Business Type" value={getBusinessTypeLabel(business.business_type)} />
              <ProfileItem label="Operational Stage" value={getBusinessStageLabel(business.business_stage)} />
              <ProfileItem label="Legal Structure" value={getRegistrationTypeLabel(business.registration_type)} />
              <ProfileItem label="Annual Turnover" value={`₹${(business.annual_turnover_inr || 0).toLocaleString()}`} />
              <ProfileItem label="Target Funding Needed" value={`₹${(business.funding_needed_inr || 0).toLocaleString()}`} />
              <ProfileItem label="Employees Count" value={business.num_employees || '1 - 5'} />
              <ProfileItem label="Collateral Security" value={business.has_collateral ? 'Available' : 'None (Collateral-Free Eligible)'} />
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-xs">
              No business registered yet. Click Edit Profile to add business details.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Eligibility & Quotas */}
      {activeTab === 'eligibility' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950 pb-3 border-b border-slate-100">
            Government Scheme Quotas & Benefits
          </h3>
          <div className="space-y-3 text-xs">
            <div className="p-4 rounded-2xl bg-gov-emerald-50/70 border border-gov-emerald-200 flex items-start gap-3">
              <CheckCircle2 size={18} className="text-gov-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-gov-emerald-950 block">PMEGP Special Category Subsidy</span>
                <span className="text-slate-600">
                  Because you reside in a <strong>{user?.is_rural ? 'Rural' : 'Urban'}</strong> area and belong to <strong>{user?.social_category?.toUpperCase()}</strong>, you are entitled to up to <strong>35% capital subsidy</strong> on eligible project costs.
                </span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 flex items-start gap-3">
              <CheckCircle2 size={18} className="text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-blue-950 block">CGTMSE Collateral-Free Guarantee</span>
                <span className="text-slate-600">
                  Eligible for 85% credit guarantee coverage by Ministry of MSME, removing the requirement to pledge personal land or property.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Documents & Vault */}
      {activeTab === 'documents' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-base text-gov-navy-950">
              Attached Digital Documents ({documents.length})
            </h3>
            <Link to="/documents" className="text-xs font-bold text-gov-saffron-700 hover:underline">
              Go to Document Center &rarr;
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {documents.map((d) => (
              <div key={d.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
                <span className="font-bold text-slate-800 capitalize">{d.doc_type?.replace('_', ' ')}</span>
                <span className="text-[10px] font-bold text-gov-emerald-700 bg-gov-emerald-100 px-2 py-0.5 rounded">
                  {d.verification_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Danger Zone: Log Out */}
      <div className="pt-4 border-t border-slate-200">
        <button
          onClick={logout}
          className="w-full py-3.5 px-4 rounded-2xl bg-red-50 hover:bg-red-100 text-red-700 font-bold text-xs sm:text-sm transition-colors flex items-center justify-center gap-2 border border-red-200"
        >
          <LogOut size={16} />
          <span>Sign Out of Yojantra</span>
        </button>
      </div>

      {/* Edit Profile Modal */}
      {isEditing && (
        <div className="fixed inset-0 z-50 bg-gov-navy-950/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden text-left">
            <div className="bg-gov-navy-950 text-white p-5 flex items-center justify-between border-b border-gov-navy-800">
              <h3 className="font-bold text-base">Edit Citizen & Enterprise Profile</h3>
              <button onClick={() => setIsEditing(false)} className="p-1 rounded-full text-slate-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="p-6 overflow-y-auto space-y-4 custom-scrollbar">
              {saveError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-medium">
                  {saveError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Full Name</label>
                  <input
                    type="text"
                    value={editForm.full_name}
                    onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">
                    Active Mobile Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    placeholder="+91 98765 43210"
                    value={editForm.phone}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Enterprise Name</label>
                  <input
                    type="text"
                    value={editForm.business_name}
                    onChange={(e) => setEditForm({ ...editForm, business_name: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <StateSelector
                  selectedState={editForm.state}
                  onSelectState={(val) => setEditForm({ ...editForm, state: val, district: '' })}
                  label="State / UT"
                  required={true}
                />

                <DistrictSelector
                  state={editForm.state}
                  selectedDistrict={editForm.district}
                  onSelectDistrict={(val) => setEditForm({ ...editForm, district: val })}
                  label="District"
                  required={true}
                />

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Gender</label>
                  <select
                    value={editForm.gender}
                    onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Social Category</label>
                  <select
                    value={editForm.social_category}
                    onChange={(e) => setEditForm({ ...editForm, social_category: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    <option value="sc">SC (Scheduled Caste)</option>
                    <option value="st">ST (Scheduled Tribe)</option>
                    <option value="obc">OBC (Other Backward Class)</option>
                    <option value="general">General</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Date of Birth</label>
                  <input
                    type="date"
                    value={editForm.date_of_birth}
                    onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Area Type</label>
                  <select
                    value={editForm.is_rural ? 'rural' : 'urban'}
                    onChange={(e) => setEditForm({ ...editForm, is_rural: e.target.value === 'rural' })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    <option value="rural">Rural Village (Higher Subsidies)</option>
                    <option value="urban">Urban Town/City</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Business / Sector Type</label>
                  <select
                    value={editForm.business_type}
                    onChange={(e) => setEditForm({ ...editForm, business_type: e.target.value, sector: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    {BUSINESS_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Operational Stage</label>
                  <select
                    value={editForm.business_stage}
                    onChange={(e) => setEditForm({ ...editForm, business_stage: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    {BUSINESS_STAGES.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Legal Structure</label>
                  <select
                    value={editForm.registration_type}
                    onChange={(e) => setEditForm({ ...editForm, registration_type: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white font-medium"
                  >
                    {REGISTRATION_TYPES.map(r => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">Turnover (INR ₹)</label>
                  <input
                    type="number"
                    value={editForm.annual_turnover_inr}
                    onChange={(e) => setEditForm({ ...editForm, annual_turnover_inr: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block font-bold text-slate-700 uppercase mb-1">Funding Needed (INR ₹)</label>
                  <input
                    type="number"
                    value={editForm.funding_needed_inr}
                    onChange={(e) => setEditForm({ ...editForm, funding_needed_inr: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-sm"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}

function ProfileItem({ label, value }) {
  return (
    <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-2xl">
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
        {label}
      </span>
      <span className="text-sm font-bold text-gov-navy-950 mt-0.5 block">
        {value || '—'}
      </span>
    </div>
  );
}
