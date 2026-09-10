import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { 
  ChevronRight, ChevronLeft, User, Building2, IndianRupee, 
  Sparkles, CheckCircle2, ShieldCheck, HelpCircle, Briefcase, 
  MapPin, Check, FileCheck
} from 'lucide-react';
import offlineStorage from '../utils/offlineStorage';
import StateSelector from '../components/StateSelector';
import DistrictSelector from '../components/DistrictSelector';
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

const STEPS = [
  { id: 'identity', stepNumber: 1, label: 'About You', title: 'Personal Demographics', icon: User },
  { id: 'business', stepNumber: 2, label: 'Your Business', title: 'Enterprise Classification', icon: Building2 },
  { id: 'financial', stepNumber: 3, label: 'Financial Profile', title: 'Turnover & Funding Needs', icon: IndianRupee },
  { id: 'goals', stepNumber: 4, label: 'Your Goals', title: 'Support & Priorities', icon: Sparkles },
  { id: 'review', stepNumber: 5, label: 'Review & Match', title: 'Confirm Profile', icon: FileCheck },
];

export default function Onboarding() {
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    // Step 1: Personal
    full_name: user?.full_name || '',
    gender: user?.gender || 'male',
    social_category: user?.social_category || 'obc',
    date_of_birth: user?.date_of_birth || '1995-05-15',
    literacy_level: user?.literacy_level || 'secondary',
    state: user?.state || '',
    district: user?.district || '',
    is_rural: user?.is_rural ?? true,
    preferred_language: user?.preferred_language || 'hi',

    // Step 2: Business
    business_name: '',
    registration_type: 'individual', // individual, startup, msme, self_employed, partnership, pvt_ltd
    business_type: 'manufacturing', // manufacturing, service, trading, agriculture, food_processing, technology, handicraft, retail, other
    business_stage: 'revenue', // idea, pre_revenue, revenue, growth, mature
    sector: 'manufacturing',

    // Step 3: Financial
    annual_turnover_inr: '500000',
    num_employees: '3',
    funding_needed_inr: '1000000',
    has_collateral: false,

    // Step 4: Goals & Interests
    support_interests: ['loans', 'subsidies'], // loans, subsidies, grants, training
  });

  const { api, setUser } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const draft = offlineStorage.getOnboardingDraft();
    if (draft) {
      // Normalize any legacy draft values to canonical backend constraints
      const canonicalDraft = {
        ...draft,
        business_type: normalizeBusinessType(draft.business_type || draft.sector),
        business_stage: normalizeBusinessStage(draft.business_stage),
        registration_type: normalizeRegistrationType(draft.registration_type || (['individual', 'startup', 'msme', 'self_employed'].includes(draft.business_type) ? draft.business_type : 'individual')),
        sector: normalizeBusinessType(draft.sector || draft.business_type),
      };
      setForm((prev) => ({ ...prev, ...canonicalDraft }));
    }
  }, []);

  const update = (field, value) => {
    setForm((prev) => {
      const updated = { ...prev, [field]: value };
      offlineStorage.saveOnboardingDraft(updated);
      return updated;
    });
  };

  const handleNext = () => {
    setError('');
    // Validation per step
    if (currentStep === 0 && !form.full_name.trim()) {
      setError('Please enter your full legal name');
      return;
    }
    if (currentStep === 1 && !form.business_name.trim()) {
      setError('Please enter your business or project name');
      return;
    }
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleBack = () => {
    setError('');
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleFinalSubmit = async () => {
    try {
      setLoading(true);
      setError('');

      // 1. Save user profile demographics
      const userRes = await api().put('/users/me', {
        full_name: form.full_name,
        gender: form.gender,
        social_category: form.social_category,
        date_of_birth: form.date_of_birth || null,
        literacy_level: form.literacy_level || null,
        state: form.state,
        district: form.district,
        is_rural: form.is_rural,
        preferred_language: form.preferred_language,
        onboarding_completed: true,
      });

      if (userRes.data) {
        setUser(userRes.data);
      }

      // Canonicalize enum values before sending to backend
      const canonicalBusinessType = normalizeBusinessType(form.business_type);
      const canonicalBusinessStage = normalizeBusinessStage(form.business_stage);
      const canonicalRegistrationType = normalizeRegistrationType(form.registration_type);

      // 2. Save enterprise profile
      await api().post('/users/me/business', {
        business_name: form.business_name,
        business_type: canonicalBusinessType,
        business_stage: canonicalBusinessStage,
        registration_type: canonicalRegistrationType,
        sector: canonicalBusinessType,
        annual_turnover_inr: parseFloat(form.annual_turnover_inr) || 0,
        num_employees: parseInt(form.num_employees) || 0,
        funding_needed_inr: parseFloat(form.funding_needed_inr) || 0,
        has_collateral: form.has_collateral,
      });

      // 3. Clear draft and route to matches
      offlineStorage.clearOnboardingDraft();
      navigate('/matches');
    } catch (err) {
      const serverDetail = err.response?.data?.detail;
      let errorMsg = 'Failed to save profile. Please check your details.';
      if (Array.isArray(serverDetail)) {
        errorMsg = serverDetail.map(d => `${d.loc ? d.loc.join('.') : 'Field'}: ${d.msg}`).join(', ');
      } else if (typeof serverDetail === 'string') {
        errorMsg = serverDetail;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const stepMeta = STEPS[currentStep];

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 text-left">
      {/* Wizard Header Bar */}
      <div className="mb-6 bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <span className="text-xs font-bold text-gov-saffron-700 tracking-wider uppercase">
              Step {stepMeta.stepNumber} of {STEPS.length}
            </span>
            <h1 className="text-xl sm:text-2xl font-extrabold text-gov-navy-950">
              {stepMeta.label}: {stepMeta.title}
            </h1>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-bold text-gov-emerald-700 bg-gov-emerald-50 px-3 py-1.5 rounded-full border border-gov-emerald-200/60 self-start sm:self-auto">
            <ShieldCheck size={16} />
            <span>DPDP Act Verified</span>
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden flex">
          <div 
            className="bg-gradient-to-r from-gov-navy-900 to-gov-saffron-500 h-full transition-all duration-300 rounded-full"
            style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        {/* Step indicator pills */}
        <div className="flex items-center justify-between mt-3 text-[11px] font-semibold text-slate-400">
          {STEPS.map((s, idx) => (
            <span 
              key={s.id}
              className={`${idx <= currentStep ? 'text-gov-navy-950 font-bold' : ''} hidden sm:inline`}
            >
              {s.label}
            </span>
          ))}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm font-medium">
          {error}
        </div>
      )}

      {/* Wizard Card Body */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-gov space-y-6">

        {/* =========================================================================
            STEP 1: ABOUT YOU (PERSONAL DEMOGRAPHICS)
           ========================================================================= */}
        {currentStep === 0 && (
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Full Legal Name (as per Aadhaar) *
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => update('full_name', e.target.value)}
                placeholder="e.g. Ramesh Kumar Verma"
                className="w-full border border-slate-300 rounded-xl px-4 py-3 text-base text-slate-900 focus:border-gov-navy-900 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none"
              />
            </div>

            {/* Gender Selection Chips */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Gender
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'female', label: 'Female', note: 'Special grants for women' },
                  { value: 'male', label: 'Male', note: 'Standard criteria' },
                  { value: 'other', label: 'Other', note: 'Affirmative inclusion' },
                ].map((g) => (
                  <button
                    key={g.value}
                    type="button"
                    onClick={() => update('gender', g.value)}
                    className={`p-3.5 rounded-2xl border text-left transition-all ${
                      form.gender === g.value
                        ? 'border-gov-navy-950 bg-gov-navy-950 text-white shadow-md'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 text-slate-800'
                    }`}
                  >
                    <p className="font-bold text-sm">{g.label}</p>
                    <p className={`text-[11px] mt-0.5 ${form.gender === g.value ? 'text-slate-300' : 'text-slate-500'}`}>
                      {g.note}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Social Category Large Chips */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Social Category *
                </label>
                <span className="text-[11px] text-gov-saffron-700 font-medium">
                  Higher subsidy quotas apply
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {[
                  { value: 'sc', label: 'SC', full: 'Scheduled Caste' },
                  { value: 'st', label: 'ST', full: 'Scheduled Tribe' },
                  { value: 'obc', label: 'OBC', full: 'Other Backward Class' },
                  { value: 'general', label: 'General', full: 'Open Merit' },
                ].map((cat) => (
                  <button
                    key={cat.value}
                    type="button"
                    onClick={() => update('social_category', cat.value)}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      form.social_category === cat.value
                        ? 'border-gov-saffron-600 bg-gov-saffron-50 text-gov-saffron-900 ring-2 ring-gov-saffron-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white text-slate-800'
                    }`}
                  >
                    <p className="font-bold text-sm">{cat.label}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{cat.full}</p>
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5 flex items-center gap-1">
                <HelpCircle size={12} />
                Government schemes like PMEGP and Stand-Up India provide up to 35% subsidies for SC/ST/OBC/Women.
              </p>
            </div>

            {/* Location & Area */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StateSelector
                selectedState={form.state}
                onSelectState={(val) => {
                  update('state', val);
                  update('district', '');
                }}
                label="State / UT"
                required={true}
              />

              <DistrictSelector
                state={form.state}
                selectedDistrict={form.district}
                onSelectDistrict={(val) => update('district', val)}
                label="District"
                required={true}
              />

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Area Classification
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => update('is_rural', true)}
                    className={`py-2.5 rounded-xl border text-xs font-bold transition-all ${
                      form.is_rural ? 'border-gov-navy-900 bg-gov-navy-900 text-white' : 'border-slate-200 bg-white text-slate-700'
                    }`}
                  >
                    Rural (Village)
                  </button>
                  <button
                    type="button"
                    onClick={() => update('is_rural', false)}
                    className={`py-2.5 rounded-xl border text-xs font-bold transition-all ${
                      !form.is_rural ? 'border-gov-navy-900 bg-gov-navy-900 text-white' : 'border-slate-200 bg-white text-slate-700'
                    }`}
                  >
                    Urban (Town/City)
                  </button>
                </div>
              </div>
            </div>

            {/* Date of Birth & Literacy Level */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={form.date_of_birth}
                  onChange={(e) => update('date_of_birth', e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-medium focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Highest Education
                </label>
                <select
                  value={form.literacy_level}
                  onChange={(e) => update('literacy_level', e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-medium bg-white focus:outline-none"
                >
                  <option value="primary">8th Standard / Primary</option>
                  <option value="secondary">10th Standard / Matriculation</option>
                  <option value="higher_secondary">12th Standard / Intermediate</option>
                  <option value="graduate">Graduate / Degree</option>
                  <option value="post_graduate">Post-Graduate / Professional</option>
                  <option value="informal">Informal / Self-Taught</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            STEP 2: YOUR BUSINESS (ENTERPRISE CLASSIFICATION)
           ========================================================================= */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Business / Enterprise Name *
              </label>
              <input
                type="text"
                value={form.business_name}
                onChange={(e) => update('business_name', e.target.value)}
                placeholder="e.g. Verma Agro Processing / Patna Handlooms"
                className="w-full border border-slate-300 rounded-xl px-4 py-3 text-base text-slate-900 focus:border-gov-navy-900 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none"
              />
            </div>

            {/* Business Type / Sector - Canonical Backend Values */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Primary Business / Activity Type *
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {BUSINESS_TYPES.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => {
                      update('business_type', type.value);
                      update('sector', type.value);
                    }}
                    className={`p-3.5 rounded-2xl border text-left transition-all ${
                      form.business_type === type.value
                        ? 'border-gov-navy-950 bg-gov-navy-950 text-white shadow-md'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 text-slate-800'
                    }`}
                  >
                    <p className="font-bold text-sm">{type.label}</p>
                    <p className={`text-[11px] mt-1 leading-snug ${form.business_type === type.value ? 'text-slate-300' : 'text-slate-500'}`}>
                      {type.desc}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Business Stage - Canonical Backend Values */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Current Operational Stage *
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
                {BUSINESS_STAGES.map((stage) => (
                  <button
                    key={stage.value}
                    type="button"
                    onClick={() => update('business_stage', stage.value)}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      form.business_stage === stage.value
                        ? 'border-gov-saffron-600 bg-gov-saffron-50 text-gov-saffron-900 ring-2 ring-gov-saffron-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white text-slate-800'
                    }`}
                  >
                    <p className="font-bold text-sm">{stage.label}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{stage.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Legal Registration Structure */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Legal Registration Structure
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {REGISTRATION_TYPES.map((reg) => (
                  <button
                    key={reg.value}
                    type="button"
                    onClick={() => update('registration_type', reg.value)}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      form.registration_type === reg.value
                        ? 'border-gov-emerald-700 bg-gov-emerald-50 text-gov-emerald-950 font-bold ring-1 ring-gov-emerald-600'
                        : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <p className="font-bold">{reg.label}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{reg.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            STEP 3: FINANCIAL PROFILE
           ========================================================================= */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Annual Turnover (INR ₹)
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                  <input
                    type="number"
                    value={form.annual_turnover_inr}
                    onChange={(e) => update('annual_turnover_inr', e.target.value)}
                    placeholder="500000"
                    className="w-full border border-slate-300 rounded-xl pl-8 pr-4 py-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Enter approximate sales in the last financial year.
                </p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Required Funding / Loan Needed (INR ₹)
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
                  <input
                    type="number"
                    value={form.funding_needed_inr}
                    onChange={(e) => update('funding_needed_inr', e.target.value)}
                    placeholder="1000000"
                    className="w-full border border-slate-300 rounded-xl pl-8 pr-4 py-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Mudra loans cover up to ₹10L; PMEGP covers up to ₹50L.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Number of Employees
                </label>
                <input
                  type="number"
                  value={form.num_employees}
                  onChange={(e) => update('num_employees', e.target.value)}
                  placeholder="3"
                  className="w-full border border-slate-300 rounded-xl px-4 py-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-gov-navy-900/10"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Do You Have Property / Collateral?
                </label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() => update('has_collateral', false)}
                    className={`py-3 rounded-xl border text-xs font-bold transition-all ${
                      !form.has_collateral
                        ? 'border-gov-emerald-600 bg-gov-emerald-50 text-gov-emerald-900 ring-2 ring-gov-emerald-500/20'
                        : 'border-slate-200 bg-white text-slate-700'
                    }`}
                  >
                    No Collateral (Recommended)
                  </button>
                  <button
                    type="button"
                    onClick={() => update('has_collateral', true)}
                    className={`py-3 rounded-xl border text-xs font-bold transition-all ${
                      form.has_collateral
                        ? 'border-gov-navy-900 bg-gov-navy-900 text-white'
                        : 'border-slate-200 bg-white text-slate-700'
                    }`}
                  >
                    Yes, I have Collateral
                  </button>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-start gap-3 text-xs text-slate-600">
              <HelpCircle size={18} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
              <p>
                <strong>What is Collateral?</strong> Assets such as land, buildings, or gold pledged to a bank. Under CGTMSE and Mudra schemes, government credit guarantee agencies act as your guarantor, eliminating personal collateral requirements.
              </p>
            </div>
          </div>
        )}

        {/* =========================================================================
            STEP 4: YOUR GOALS & PREFERENCES
           ========================================================================= */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Preferred Interface Language (12 Indian Languages)
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {[
                  { code: 'hi', label: 'हिन्दी (Hindi)' },
                  { code: 'en', label: 'English' },
                  { code: 'mr', label: 'मराठी (Marathi)' },
                  { code: 'ta', label: 'தமிழ் (Tamil)' },
                  { code: 'te', label: 'తెలుగు (Telugu)' },
                  { code: 'bn', label: 'বাংলা (Bengali)' },
                  { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
                  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
                  { code: 'ml', label: 'മലയാളം (Malayalam)' },
                  { code: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
                  { code: 'or', label: 'ଓଡ଼ିଆ (Odia)' },
                  { code: 'as', label: 'অসমীয়া (Assamese)' },
                ].map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    onClick={() => update('preferred_language', lang.code)}
                    className={`p-3 rounded-xl border text-xs font-bold transition-all text-center ${
                      form.preferred_language === lang.code
                        ? 'border-gov-navy-950 bg-gov-navy-950 text-white'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                What Type of Government Support Are You Looking For?
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { id: 'loans', label: 'Subsidized Bank Loans', desc: 'Low interest working capital and term loans' },
                  { id: 'subsidies', label: 'Direct Capital Subsidies', desc: 'Up to 35% non-repayable government funding' },
                  { id: 'grants', label: 'Equipment & Machining Grants', desc: 'Technology upgradation assistance' },
                  { id: 'training', label: 'Skill & Entrepreneurship Training', desc: 'Free certified vocational programs' },
                ].map((item) => {
                  const selected = form.support_interests.includes(item.id);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        const next = selected 
                          ? form.support_interests.filter(x => x !== item.id)
                          : [...form.support_interests, item.id];
                        update('support_interests', next);
                      }}
                      className={`p-4 rounded-2xl border text-left transition-all flex items-start gap-3 ${
                        selected 
                          ? 'border-gov-emerald-600 bg-gov-emerald-50/70 text-gov-emerald-950 ring-1 ring-gov-emerald-500' 
                          : 'border-slate-200 bg-white text-slate-800 hover:border-slate-300'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-md flex items-center justify-center mt-0.5 flex-shrink-0 ${
                        selected ? 'bg-gov-emerald-600 text-white' : 'border border-slate-300 bg-white'
                      }`}>
                        {selected && <Check size={14} />}
                      </div>
                      <div>
                        <p className="font-bold text-sm">{item.label}</p>
                        <p className="text-xs text-slate-500 mt-0.5 leading-snug">{item.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            STEP 5: REVIEW & CONFIRM PROFILE
           ========================================================================= */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="bg-gradient-to-br from-gov-navy-50 to-slate-50 border border-slate-200 rounded-2xl p-5">
              <h3 className="text-sm font-bold text-gov-navy-950 uppercase tracking-wider mb-4 flex items-center gap-2">
                <CheckCircle2 size={18} className="text-gov-emerald-600" />
                Profile Summary for AI Matching
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="bg-white p-3 rounded-xl border border-slate-200/80">
                  <span className="text-slate-400 block uppercase font-medium">Entrepreneur</span>
                  <span className="text-sm font-bold text-gov-navy-950">{form.full_name}</span>
                  <span className="text-slate-500 block mt-0.5">{form.gender.toUpperCase()} • {form.social_category.toUpperCase()} • {form.district}, {form.state}</span>
                </div>

                <div className="bg-white p-3 rounded-xl border border-slate-200/80">
                  <span className="text-slate-400 block uppercase font-medium">Enterprise</span>
                  <span className="text-sm font-bold text-gov-navy-950">{form.business_name}</span>
                  <span className="text-slate-500 block mt-0.5">
                    {getBusinessTypeLabel(form.business_type)} • {getBusinessStageLabel(form.business_stage)}
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Structure: {getRegistrationTypeLabel(form.registration_type)}
                  </span>
                </div>

                <div className="bg-white p-3 rounded-xl border border-slate-200/80">
                  <span className="text-slate-400 block uppercase font-medium">Financial Metrics</span>
                  <span className="text-sm font-bold text-gov-navy-950">Turnover: ₹{parseInt(form.annual_turnover_inr).toLocaleString()}</span>
                  <span className="text-slate-500 block mt-0.5">Need: ₹{parseInt(form.funding_needed_inr).toLocaleString()} ({form.has_collateral ? 'With Collateral' : 'Collateral-Free'})</span>
                </div>

                <div className="bg-white p-3 rounded-xl border border-slate-200/80">
                  <span className="text-slate-400 block uppercase font-medium">Target Opportunities</span>
                  <span className="text-sm font-bold text-gov-navy-950 capitalize">{form.support_interests.join(', ')}</span>
                  <span className="text-slate-500 block mt-0.5">Location: {form.is_rural ? 'Rural Area' : 'Urban Area'}</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-gov-emerald-50/70 border border-gov-emerald-200 rounded-2xl flex items-start gap-3 text-xs text-gov-emerald-900">
              <Sparkles size={18} className="text-gov-emerald-600 flex-shrink-0 mt-0.5" />
              <p>
                Clicking <strong>"Complete & Generate Matches"</strong> runs our deterministic AI engine across central databases (PMEGP, Mudra, Stand-Up India, PMFME) to calculate your personalized eligibility percentage.
              </p>
            </div>
          </div>
        )}

        {/* Wizard Bottom Navigation Buttons */}
        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 0 || loading}
            className="px-5 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs sm:text-sm hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 transition-colors"
          >
            <ChevronLeft size={16} />
            <span>Previous</span>
          </button>

          {currentStep < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={handleNext}
              className="px-6 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white font-bold text-xs sm:text-sm shadow-md flex items-center gap-1.5 transition-all"
            >
              <span>Next Step</span>
              <ChevronRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinalSubmit}
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-xs sm:text-sm shadow-md flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Calculating Matches...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Complete & Generate Matches</span>
                </>
              )}
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
