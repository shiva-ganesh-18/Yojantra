import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { institutionsService, schemeService } from '../services';
import { 
  StateSelector, DistrictSelector, CitySelector, LocationBreadcrumb, 
  InstitutionDrawer, RetryState, PartnerMap 
} from '../components';
import { 
  Building2, Search, MapPin, ShieldCheck, 
  PlusCircle, ArrowRight, X, Check, Landmark, Network,
  Sparkles, Navigation, Award, Info, Filter, Phone, Map as MapIcon,
  Compass, ExternalLink, AlertCircle
} from 'lucide-react';

const PARTNER_TYPES = [
  { value: '', label: 'All Partner Categories' },
  { value: 'SCA', label: 'State Channelizing Agency (SCA)' },
  { value: 'PSB', label: 'Public Sector Bank (PSB)' },
  { value: 'RRB', label: 'Regional Rural Bank (RRB)' },
  { value: 'NBFC-MFI', label: 'NBFC-MFI (Micro-Finance)' },
  { value: 'Facilitation Center', label: 'CSC / Facilitation Center' },
];

export default function Institutions() {
  const { user } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // URL state synchronization with fallback to user saved profile location
  const urlState = searchParams.get('state') || user?.state || '';
  const urlDistrict = searchParams.get('district') || user?.district || '';
  const urlCity = searchParams.get('city') || '';
  const urlSchemeId = searchParams.get('scheme_id') || '';

  const [state, setState] = useState(urlState);
  const [district, setDistrict] = useState(urlDistrict);
  const [city, setCity] = useState(urlCity);
  const [selectedSchemeId, setSelectedSchemeId] = useState(urlSchemeId);
  const [selectedPartnerType, setSelectedPartnerType] = useState('');
  const [search, setSearch] = useState(searchParams.get('q') || '');

  // Honor deep-links from global search (SearchCommand navigates to /institutions?q=...).
  useEffect(() => {
    const q = searchParams.get('q') || '';
    setSearch((prev) => (prev !== q ? q : prev));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Geolocation state
  const [userLocation, setUserLocation] = useState(null);
  const [gpsActive, setGpsActive] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsError, setGpsError] = useState(null);
  const [showMap, setShowMap] = useState(true);

  // Data & Modal states
  const [recommendationSummary, setRecommendationSummary] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedInst, setSelectedInst] = useState(null);
  const [showRequestModal, setShowRequestModal] = useState(false);

  // Request partner/center form
  const [requestForm, setRequestForm] = useState({
    name: '',
    state: '',
    district: '',
    city: '',
    requested_by_email: '',
  });
  const [requestSuccess, setRequestSuccess] = useState(false);
  const [requestSubmitting, setRequestSubmitting] = useState(false);
  const [requestError, setRequestError] = useState(null);

  // Fetch schemes list for Scheme Compatibility Filter
  useEffect(() => {
    schemeService.searchSchemes({ page: 1, page_size: 100 })
      .then(res => setSchemes(res.items || []))
      .catch(() => setSchemes([]));
  }, []);

  // Sync state with URL params (keep ?q= in sync with keyword search)
  useEffect(() => {
    const params = {};
    if (state) params.state = state;
    if (district) params.district = district;
    if (city) params.city = city;
    if (selectedSchemeId) params.scheme_id = selectedSchemeId;
    if (search) params.q = search;
    const current = searchParams.toString();
    const next = new URLSearchParams(params).toString();
    if (current !== next) setSearchParams(params, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state, district, city, selectedSchemeId, search]);

  const handleUseGPS = () => {
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser. You can still search by State, District, or City.");
      return;
    }
    setGpsLoading(true);
    setGpsError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setGpsActive(true);
        setGpsLoading(false);
        setGpsError(null);
      },
      (err) => {
        setGpsLoading(false);
        setGpsActive(false);
        if (err.code === 1) {
          setGpsError("GPS location access was denied. Showing directory ranked by district administrative headquarters.");
        } else {
          setGpsError("Unable to retrieve precise GPS coordinates. Showing directory ranked by district administrative headquarters.");
        }
      },
      { timeout: 8000, enableHighAccuracy: false }
    );
  };

  const fetchPartnerRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        state: state || undefined,
        district: district || undefined,
        city: city || undefined,
        scheme_id: selectedSchemeId || undefined,
        institution_type: selectedPartnerType || undefined,
      };

      if (userLocation) {
        params.lat = userLocation.lat;
        params.lng = userLocation.lng;
      }

      const data = await institutionsService.getRecommendations(params);
      setRecommendationSummary(data);
      
      let list = data.partners || [];
      if (search) {
        const q = search.toLowerCase();
        list = list.filter(i => 
          i.name.toLowerCase().includes(q) || 
          (i.short_name && i.short_name.toLowerCase().includes(q)) ||
          (i.city && i.city.toLowerCase().includes(q)) ||
          (i.code && i.code.toLowerCase().includes(q))
        );
      }
      setInstitutions(list);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchPartnerRecommendations, 250);
    return () => clearTimeout(timer);
  }, [search, state, district, city, selectedSchemeId, selectedPartnerType, userLocation]);

  const handleResetFilters = () => {
    setState('');
    setDistrict('');
    setCity('');
    setSelectedSchemeId('');
    setSelectedPartnerType('');
    setSearch('');
  };

  const handleBreadcrumbHop = (level) => {
    if (level === 'india') {
      handleResetFilters();
    } else if (level === 'state') {
      setDistrict('');
      setCity('');
    } else if (level === 'district') {
      setCity('');
    }
  };

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    try {
      setRequestError(null);
      setRequestSubmitting(true);
      await institutionsService.requestInstitution({
        ...requestForm,
        state: requestForm.state || state || 'India',
        district: requestForm.district || district || 'General',
      });
      setRequestSuccess(true);
      setTimeout(() => {
        setShowRequestModal(false);
        setRequestSuccess(false);
        setRequestForm({ name: '', state: '', district: '', city: '', requested_by_email: '' });
      }, 2000);
    } catch (err) {
      const detail = err?.response?.data?.detail ?? err?.details?.detail;
      const msg = typeof detail === 'string'
        ? detail
        : (detail?.message || (typeof err?.message === 'string' ? err.message : null) || 'Unable to submit partner request. Please verify inputs.');
      setRequestError(msg);
    } finally {
      setRequestSubmitting(false);
    }
  };

  const bestPartner = recommendationSummary?.best_partner;

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="w-7 h-7 text-gov-saffron-600" />
            <h1 className="text-2xl sm:text-3xl font-black text-gov-navy-950 tracking-tight">
              Channel Partner & Lending Institution Locator
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Distance-ranked directory of State Channelizing Agencies (SCAs), Public Sector Banks (PSBs), Regional Rural Banks (RRBs), and NBFC-MFIs matched for your scheme application.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            onClick={() => setShowMap(prev => !prev)}
            className={`inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border text-xs font-bold transition-all ${
              showMap 
                ? 'bg-slate-900 text-white border-slate-900' 
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <MapIcon size={14} className={showMap ? 'text-gov-saffron-400' : 'text-slate-500'} />
            <span>{showMap ? 'Hide Map View' : 'Show Map View'}</span>
          </button>

          <button
            onClick={handleUseGPS}
            disabled={gpsLoading}
            className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-bold transition-all ${
              gpsActive 
                ? 'bg-gov-emerald-50 text-gov-emerald-800 border-gov-emerald-300' 
                : 'border-slate-200 hover:bg-slate-50 text-slate-700'
            }`}
          >
            <Navigation size={14} className={gpsActive ? 'text-gov-emerald-600' : 'text-slate-500'} />
            <span>{gpsLoading ? 'Detecting Location...' : gpsActive ? 'GPS Distance Active' : 'Sort by My GPS Distance'}</span>
          </button>

          <button
            onClick={() => {
              setRequestForm(prev => ({ ...prev, state, district, city }));
              setRequestError(null);
              setShowRequestModal(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-bold transition-all shadow-sm"
          >
            <PlusCircle className="w-4 h-4 text-gov-saffron-400" />
            <span>Request Partner Addition</span>
          </button>
        </div>
      </div>

      {/* GPS Status Alert / Fallback Notice */}
      {gpsError && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-2xl text-xs font-medium flex items-start justify-between gap-3 animate-in fade-in">
          <div className="flex items-start gap-2">
            <AlertCircle size={16} className="text-amber-600 shrink-0 mt-0.5" />
            <span>{gpsError}</span>
          </div>
          <button 
            onClick={() => setGpsError(null)}
            className="text-amber-700 hover:text-amber-900 font-bold text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Best Recommended Partner Highlight Banner */}
      {bestPartner && !loading && (
        <div className="bg-gradient-to-r from-gov-navy-950 via-gov-navy-900 to-gov-navy-950 text-white rounded-3xl p-6 sm:p-7 shadow-lg border border-gov-navy-800 relative overflow-hidden">
          <div className="absolute right-0 top-0 translate-x-10 -translate-y-10 w-48 h-48 bg-gov-saffron-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 relative z-10">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-400/40 text-[11px] font-extrabold uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={13} className="text-gov-saffron-400" />
                  <span>Best Partner Recommendation</span>
                </span>
                <span className="px-2.5 py-1 rounded-full bg-white/10 text-slate-300 text-[11px] font-bold">
                  {bestPartner.institution_type}
                </span>
                {bestPartner.distance_km !== null && (
                  <span className="px-2.5 py-1 rounded-full bg-gov-emerald-500/20 text-gov-emerald-300 border border-gov-emerald-400/30 text-[11px] font-bold flex items-center gap-1">
                    <Navigation size={11} />
                    <span>{bestPartner.distance_km} km away</span>
                  </span>
                )}
              </div>

              <h2 className="text-xl sm:text-2xl font-black text-white leading-tight">
                {bestPartner.name}
              </h2>

              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                {bestPartner.recommendation_reason}
              </p>

              <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
                <span>📍 {bestPartner.city || bestPartner.district}, {bestPartner.state}</span>
                <span>•</span>
                <span className="text-gov-emerald-400 font-semibold">✓ {bestPartner.fund_availability_status}</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedInst(bestPartner)}
              className="self-start md:self-auto px-6 py-3 rounded-2xl bg-gov-saffron-500 hover:bg-gov-saffron-600 text-gov-navy-950 font-black text-xs sm:text-sm shadow-md transition-all flex items-center gap-2"
            >
              <span>View Recommended Route</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Interactive Breadcrumb Hierarchy */}
      <LocationBreadcrumb
        state={state}
        district={district}
        city={city}
        onSelectLevel={handleBreadcrumbHop}
        onResetAll={handleResetFilters}
      />

      {/* Interactive Map View */}
      {showMap && (
        <PartnerMap
          partners={institutions}
          userLocation={userLocation}
          selectedPartner={selectedInst}
          onSelectPartner={(inst) => setSelectedInst(inst)}
          centerState={state}
          centerDistrict={district}
        />
      )}

      {/* Scheme & Partner Category Filters Bar */}
      <div className="bg-white rounded-3xl border border-slate-200/90 p-5 shadow-xs space-y-4">
        
        {/* Row 1: Scheme Selector & Partner Category Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pb-3 border-b border-slate-100">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Award size={14} className="text-gov-saffron-600" />
              <span>Target Scheme Compatibility</span>
            </label>
            <select
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs sm:text-sm font-semibold text-gov-navy-950 focus:outline-none focus:bg-white focus:ring-2 focus:ring-gov-navy-900/10 focus:border-gov-navy-950"
            >
              <option value="">-- All National & State Schemes (General Matching) --</option>
              {schemes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.ministry})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Landmark size={14} className="text-gov-navy-900" />
              <span>Partner Institution Category</span>
            </label>
            <select
              value={selectedPartnerType}
              onChange={(e) => setSelectedPartnerType(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs sm:text-sm font-semibold text-gov-navy-950 focus:outline-none focus:bg-white focus:ring-2 focus:ring-gov-navy-900/10 focus:border-gov-navy-950"
            >
              {PARTNER_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Row 2: Cascading State, District, City Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <StateSelector
            selectedState={state}
            onSelectState={(val) => {
              setState(val);
              setDistrict('');
              setCity('');
            }}
            label="State / Union Territory"
          />
          <DistrictSelector
            state={state}
            selectedDistrict={district}
            onSelectDistrict={(val) => {
              setDistrict(val);
              setCity('');
            }}
            label="District"
          />
          <CitySelector
            state={state}
            district={district}
            selectedCity={city}
            onSelectCity={setCity}
            label="City / Town"
          />
        </div>

        {/* Row 3: Keyword Search Bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2 border-t border-slate-100">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by partner name, branch code, or city..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 focus:outline-none focus:bg-white focus:border-gov-navy-950"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Partners Grid with RetryState */}
      <RetryState
        isLoading={loading}
        error={error}
        isEmpty={!loading && institutions.length === 0}
        onRetry={fetchPartnerRecommendations}
        emptyTitle="No Channel Partners Match Your Search"
        emptyDescription="Try selecting a different district, changing partner type filter, or request addition of your local facilitation center or branch."
        emptyActionText="Request Partner Addition"
        onEmptyAction={() => setShowRequestModal(true)}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Accredited Channel Partners ({institutions.length})
            </h2>
            <span className="text-xs text-slate-400">
              {gpsActive ? 'Ranked by GPS distance' : 'Ranked by scheme priority & administrative jurisdiction'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {institutions.map((inst, idx) => {
              const isFirst = inst.is_best_partner || idx === 0;

              return (
                <div
                  key={inst.id}
                  onClick={() => setSelectedInst(inst)}
                  className={`bg-white rounded-3xl border transition-all p-6 flex flex-col justify-between cursor-pointer group hover:shadow-md ${
                    isFirst 
                      ? 'border-gov-saffron-300 ring-2 ring-gov-saffron-500/10 hover:border-gov-saffron-500' 
                      : 'border-slate-200/90 hover:border-gov-navy-900/40'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                          #{inst.recommendation_rank || idx + 1}
                        </span>
                        {inst.distance_km !== null && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 flex items-center gap-1">
                            <Navigation size={10} className="text-gov-saffron-600" />
                            <span>{inst.distance_km} km</span>
                          </span>
                        )}
                      </div>

                      {inst.institution_type && (
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black border flex items-center gap-1 ${
                          inst.institution_type === 'SCA' 
                            ? 'bg-purple-50 text-purple-900 border-purple-200'
                            : inst.institution_type === 'PSB'
                            ? 'bg-blue-50 text-blue-900 border-blue-200'
                            : inst.institution_type === 'RRB'
                            ? 'bg-amber-50 text-amber-900 border-amber-200'
                            : 'bg-emerald-50 text-emerald-900 border-emerald-200'
                        }`}>
                          <Landmark className="w-3 h-3" />
                          <span>{inst.institution_type}</span>
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-gov-saffron-700 transition-colors line-clamp-2 leading-snug mb-1">
                      {inst.name}
                    </h3>

                    {inst.short_name && (
                      <span className="inline-block mb-2 text-[10px] font-bold px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded">
                        {inst.short_name}
                      </span>
                    )}

                    <p className="text-xs text-slate-500 flex items-center gap-1.5 mb-3">
                      <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{inst.city || inst.district}, {inst.state}</span>
                    </p>

                    {/* Recommendation Reason Snippet */}
                    <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 mb-3 text-[11px] text-slate-600 leading-relaxed">
                      <p className="line-clamp-2">{inst.recommendation_reason}</p>
                    </div>

                    {/* Status, NPA & Geographic Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 mb-2.5">
                      {/* Eligibility Badge */}
                      <span className={`px-2 py-0.5 rounded-md border text-[10px] font-bold flex items-center gap-1 ${
                        inst.eligibility_verdict === 'ELIGIBLE' || inst.fund_availability_status === 'ELIGIBLE'
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                          : inst.eligibility_verdict === 'INELIGIBLE' || inst.fund_availability_status === 'INELIGIBLE'
                          ? 'bg-red-50 border-red-300 text-red-800'
                          : 'bg-amber-50 border-amber-300 text-amber-800'
                      }`}>
                        <ShieldCheck className="w-3 h-3" />
                        <span>{inst.eligibility_verdict || inst.fund_availability_status || 'ELIGIBLE'}</span>
                      </span>

                      {/* Geographic Tier */}
                      {inst.geographic_tier && (
                        <span className="px-2 py-0.5 rounded-md border border-slate-200 bg-slate-100/70 text-[10px] font-bold text-slate-700 capitalize">
                          {inst.geographic_tier === 'district' ? '📍 District Level' : inst.geographic_tier === 'state' ? '🏛️ State Level' : '🌐 National'}
                        </span>
                      )}

                      {/* NPA / Risk Status */}
                      {inst.gross_npa_ratio !== null && inst.gross_npa_ratio !== undefined && (
                        <span className="px-2 py-0.5 rounded-md border border-slate-200 bg-slate-50 text-[10px] font-mono text-slate-700">
                          NPA: {inst.gross_npa_ratio}%
                        </span>
                      )}

                      {/* Verification Status */}
                      <span className={`px-2 py-0.5 rounded-md border text-[10px] font-bold ${
                        inst.sync_status === 'LIVE'
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                          : inst.sync_status === 'FALLBACK'
                          ? 'bg-amber-50 border-amber-200 text-amber-800'
                          : 'bg-blue-50 border-blue-200 text-blue-800'
                      }`}>
                        {inst.sync_status === 'LIVE' ? 'LIVE CBS' : 'CONFIG-READY'}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3.5 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
                    {inst.navigation_url ? (
                      <a
                        href={inst.navigation_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-gov-saffron-700 hover:text-gov-saffron-800 hover:underline"
                      >
                        <Navigation size={12} />
                        <span>Directions</span>
                      </a>
                    ) : (
                      <span className="text-[10px] text-slate-400">Accredited Partner</span>
                    )}

                    <span className="font-bold text-gov-navy-950 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform shrink-0">
                      <span>View Details</span>
                      <ArrowRight className="w-3.5 h-3.5 text-gov-saffron-600" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </RetryState>

      {/* Partner Drawer */}
      <InstitutionDrawer
        institution={selectedInst}
        isOpen={!!selectedInst}
        onClose={() => setSelectedInst(null)}
        onSelectPartner={(inst) => {
          setSelectedInst(inst);
          setShowMap(true);
        }}
      />

      {/* Request Unlisted Partner Modal */}
      {showRequestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-slate-200 text-left relative">
            <button
              onClick={() => setShowRequestModal(false)}
              className="absolute right-6 top-6 p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-black text-slate-900 mb-1">
              Request Partner / Center Addition
            </h3>
            <p className="text-xs text-slate-500 mb-5">
              Submit an unlisted State Channelizing Agency, Bank branch, or CSC facilitation center. Our desk will verify credentials.
            </p>

            {requestSuccess ? (
              <div className="p-6 rounded-2xl bg-emerald-50 text-center text-emerald-800">
                <Check className="w-8 h-8 mx-auto text-emerald-600 mb-2" />
                <h4 className="text-sm font-bold">Request Submitted!</h4>
                <p className="text-xs text-emerald-700 mt-1">Our partner verification team will review and update the directory.</p>
              </div>
            ) : (
              <>
              {requestError && (
                <div className="p-3 mb-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {requestError}
                </div>
              )}
              <form onSubmit={handleSubmitRequest} className="space-y-4 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Partner / Center Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={requestForm.name}
                    onChange={(e) => setRequestForm({ ...requestForm, name: e.target.value })}
                    placeholder="e.g., State SC/ST Financial Development Corp / Bank Branch..."
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">State *</label>
                    <StateSelector
                      selectedState={requestForm.state || state}
                      onSelectState={(val) => setRequestForm({ ...requestForm, state: val, district: '', city: '' })}
                      label="State / Union Territory"
                      required={true}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">District *</label>
                    <DistrictSelector
                      state={requestForm.state || state}
                      selectedDistrict={requestForm.district || district}
                      onSelectDistrict={(val) => setRequestForm({ ...requestForm, district: val, city: '' })}
                      label="District"
                      required={true}
                      className="w-full"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    City / Town
                  </label>
                  <CitySelector
                    state={requestForm.state || state}
                    district={requestForm.district || district}
                    selectedCity={requestForm.city || city}
                    onSelectCity={(val) => setRequestForm({ ...requestForm, city: val })}
                    label="City / Town"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Your Official Email ID
                  </label>
                  <input
                    type="email"
                    value={requestForm.requested_by_email}
                    onChange={(e) => setRequestForm({ ...requestForm, requested_by_email: e.target.value })}
                    placeholder="officer@agency.gov.in"
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>

                <div className="pt-3 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowRequestModal(false)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={requestSubmitting}
                    className="px-5 py-2 rounded-xl bg-orange-600 text-white font-bold hover:bg-orange-700 shadow-sm"
                  >
                    {requestSubmitting ? 'Submitting...' : 'Submit Request'}
                  </button>
                </div>
              </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

