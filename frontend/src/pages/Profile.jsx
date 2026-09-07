import React, { useState } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useQuery, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import { 
  User, Building2, FileText, LogOut, ChevronRight, 
  MapPin, ShieldCheck, CheckCircle2, Edit3, Sparkles, 
  IndianRupee, X, Save, Check
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

export default function Profile() {
  const { api, user, setUser, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('personal');
  const [isEditing, setIsEditing] = useState(false);

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
    gender: user?.gender || 'male',
    social_category: user?.social_category || 'obc',
    date_of_birth: user?.date_of_birth || '',
    literacy_level: user?.literacy_level || 'secondary',
    state: user?.state || 'Bihar',
    district: user?.district || 'Patna',
    is_rural: user?.is_rural ?? true,
    preferred_language: user?.preferred_language || 'hi',
    // Business
    business_name: business?.business_name || '',
    business_type: business?.business_type || 'individual',
    business_stage: business?.business_stage || 'operating',
    sector: business?.sector || 'manufacturing',
    annual_turnover_inr: business?.annual_turnover_inr || 500000,
    funding_needed_inr: business?.funding_needed_inr || 1000000,
    has_collateral: business?.has_collateral || false,
  });

  const handleOpenEdit = () => {
    setEditForm({
      full_name: user?.full_name || '',
      gender: user?.gender || 'male',
      social_category: user?.social_category || 'obc',
      date_of_birth: user?.date_of_birth || '',
      literacy_level: user?.literacy_level || 'secondary',
      state: user?.state || 'Bihar',
      district: user?.district || 'Patna',
      is_rural: user?.is_rural ?? true,
      preferred_language: user?.preferred_language || 'hi',
      business_name: business?.business_name || '',
      business_type: business?.business_type || 'individual',
      business_stage: business?.business_stage || 'operating',
      sector: business?.sector || 'manufacturing',
      annual_turnover_inr: business?.annual_turnover_inr || 500000,
      funding_needed_inr: business?.funding_needed_inr || 1000000,
      has_collateral: business?.has_collateral || false,
    });
    setIsEditing(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      const res = await api().put('/users/me', {
        full_name: editForm.full_name,
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

      await api().post('/users/me/business', {
        business_name: editForm.business_name || 'My Business Enterprise',
        business_type: editForm.business_type,
        business_stage: editForm.business_stage,
        sector: editForm.sector || null,
        annual_turnover_inr: parseFloat(editForm.annual_turnover_inr) || 0,
        funding_needed_inr: parseFloat(editForm.funding_needed_inr) || 0,
        has_collateral: editForm.has_collateral,
      });

      queryClient.invalidateQueries('user_business');
      setIsEditing(false);
    } catch (err) {
      console.error(err);
    }
  };

  // Calculate profile completion percentage
  let completionScore = 50;
  if (user?.full_name) completionScore += 10;
  if (user?.social_category) completionScore += 10;
  if (business?.business_name) completionScore += 15;
  if (documents.length > 0) completionScore += 15;

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
            <div className="w-16 h-16 rounded-2xl bg-gov-saffron-600 text-white font-extrabold flex items-center justify-center text-2xl shadow-inner uppercase">
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white">
                  {user?.full_name || 'Citizen User'}
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-500/20 text-gov-emerald-300 border border-gov-emerald-400/30 uppercase">
                  {user?.role || 'Citizen'}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 mt-0.5">
                {user?.phone} • {user?.district}, {user?.state} ({user?.is_rural ? 'Rural' : 'Urban'})
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
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950 pb-3 border-b border-slate-100">
            Personal & Demographic Details
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ProfileItem label="Legal Full Name" value={user?.full_name} />
            <ProfileItem label="Mobile Number" value={user?.phone} />
            <ProfileItem label="Gender" value={user?.gender?.toUpperCase()} />
            <ProfileItem label="Social Category" value={`${user?.social_category?.toUpperCase()} (Affirmative Quota Eligible)`} />
            <ProfileItem label="Date of Birth" value={user?.date_of_birth || 'Not specified'} />
            <ProfileItem label="Education / Literacy" value={user?.literacy_level || 'Secondary (10th)'} />
            <ProfileItem label="State" value={user?.state} />
            <ProfileItem label="District" value={user?.district} />
            <ProfileItem label="Area Type" value={user?.is_rural ? 'Rural Village (Higher Subsidies)' : 'Urban Town/City'} />
            <ProfileItem label="Preferred Language" value={user?.preferred_language?.toUpperCase()} />
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
              <ProfileItem label="Legal Structure" value={business.business_type?.replace('_', ' ')?.toUpperCase()} />
              <ProfileItem label="Operational Stage" value={business.business_stage?.toUpperCase()} />
              <ProfileItem label="Industry Sector" value={business.sector?.toUpperCase() || 'General'} />
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
          <span>Sign Out of SchemeMatch AI</span>
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
                  <label className="block font-bold text-slate-700 uppercase mb-1">Enterprise Name</label>
                  <input
                    type="text"
                    value={editForm.business_name}
                    onChange={(e) => setEditForm({ ...editForm, business_name: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">State</label>
                  <input
                    type="text"
                    value={editForm.state}
                    onChange={(e) => setEditForm({ ...editForm, state: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase mb-1">District</label>
                  <input
                    type="text"
                    value={editForm.district}
                    onChange={(e) => setEditForm({ ...editForm, district: e.target.value })}
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm"
                  />
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

                <div>
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
