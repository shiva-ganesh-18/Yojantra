import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { 
  MapPin, Phone, Navigation, Clock, Search, 
  Building2, ShieldCheck, CheckCircle2, ArrowRight, ExternalLink 
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

export default function CSCLocator() {
  const { api, user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState(user?.district || 'Patna');
  const [centers, setCenters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [locationUsed, setLocationUsed] = useState(false);

  const fetchCentersByDistrict = async (query = searchQuery) => {
    setLoading(true);
    setError('');
    try {
      const res = await api().get('/csc/by-district', {
        params: { state: user?.state || 'Bihar', district: query }
      });
      const data = res.data?.centers || res.data || [];
      setCenters(Array.isArray(data) ? data : []);
    } catch (e) {
      // If error, search nearby fallback with coordinates
      try {
        const nearbyRes = await api().get('/csc/nearby', {
          params: { lat: 25.5941, lng: 85.1376, radius_km: 15 }
        });
        setCenters(nearbyRes.data?.centers || []);
      } catch (err2) {
        setError('Unable to load CSC centers. Please check your district name or internet connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCentersByDistrict(user?.district || 'Patna');
  }, []);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setLoading(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          setLocationUsed(true);
          const res = await api().get('/csc/nearby', {
            params: { lat: latitude, lng: longitude, radius_km: 15 }
          });
          setCenters(res.data?.centers || []);
        } catch (e) {
          setError('Failed to fetch centers near your GPS coordinates.');
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setError('Location permission denied. Please enter your town, village, or district above.');
        setLoading(false);
      }
    );
  };

  const openGoogleMaps = (lat, lng, name) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6 text-left">
      
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-2 rounded-xl bg-gov-emerald-100 text-gov-emerald-800">
                <MapPin size={20} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                Find a CSC Center
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 max-w-xl">
              Common Service Centers (CSCs) provide Village Level Entrepreneur (VLE) support for Aadhaar authentication, document scanning, UDYAM registration, and scheme filings.
            </p>
          </div>

          <button
            onClick={handleUseMyLocation}
            disabled={loading}
            className="self-start sm:self-auto px-4 py-2.5 rounded-xl bg-gov-emerald-600 hover:bg-gov-emerald-700 text-white text-xs sm:text-sm font-bold transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
          >
            <Navigation size={15} />
            <span>Use My GPS Location</span>
          </button>
        </div>

        {/* Search Input Bar */}
        <div className="mt-5 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchCentersByDistrict()}
              placeholder="Enter village, town, district, or PIN code..."
              className="w-full pl-11 pr-4 py-3.5 border border-slate-300 rounded-2xl text-sm font-medium bg-slate-50 focus:bg-white focus:border-gov-navy-950 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none"
            />
          </div>
          <button
            onClick={() => fetchCentersByDistrict()}
            disabled={loading}
            className="px-6 py-3.5 rounded-2xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs sm:text-sm font-bold shadow-md transition-all"
          >
            Search
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-2xl text-xs sm:text-sm font-medium">
          {error}
        </div>
      )}

      {/* Centers Listing & Clean Map Card */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider">
            Nearby Service Centers ({centers.length})
          </h2>
          <span className="text-xs text-slate-400">
            {locationUsed ? 'Sorted by GPS proximity' : `Showing centers in ${searchQuery}`}
          </span>
        </div>

        {loading ? (
          <div className="space-y-3">
            <SkeletonLoader.Card lines={3} />
            <SkeletonLoader.Card lines={3} />
          </div>
        ) : centers.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-gov text-center space-y-2">
            <MapPin size={48} className="mx-auto text-slate-300" />
            <h3 className="text-base font-bold text-gov-navy-950">No CSC centers found in this area</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Try searching for a neighboring district or use the GPS button to detect centers within 15 km.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {centers.map((c) => {
              const services = c.services_offered || ['Aadhaar KYC', 'PAN Card', 'UDYAM MSME', 'Scheme Application', 'DBT Account Linking'];
              const distance = c.distance_km ? `${c.distance_km} km away` : 'Near District Center';

              return (
                <div
                  key={c.id}
                  className="bg-white rounded-3xl p-5 sm:p-6 border border-slate-200 hover:border-gov-navy-900/30 hover:shadow-gov-hover transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-bold text-gov-emerald-700 uppercase tracking-wider bg-gov-emerald-50 px-2 py-0.5 rounded border border-gov-emerald-200">
                          Authorized CSC VLE
                        </span>
                        <h3 className="font-bold text-base sm:text-lg text-gov-navy-950 mt-1">
                          {c.name}
                        </h3>
                      </div>
                      <span className="text-xs font-bold text-gov-navy-900 bg-slate-100 px-2.5 py-1 rounded-xl flex-shrink-0 flex items-center gap-1">
                        <Navigation size={12} className="text-gov-emerald-600" />
                        {distance}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {c.address || `${c.district}, ${c.state}`}
                    </p>

                    <div className="flex items-center gap-2 text-xs text-gov-emerald-800 font-semibold">
                      <Clock size={13} />
                      <span>Open Now • 9:30 AM to 6:30 PM (Mon-Sat)</span>
                    </div>

                    {/* Services Offered Tags */}
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                        Available Services:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {services.map((s, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-medium bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                    {c.phone ? (
                      <a
                        href={`tel:${c.phone}`}
                        className="px-3.5 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-xs font-bold text-gov-navy-950 flex items-center gap-1.5 transition-colors"
                      >
                        <Phone size={14} className="text-gov-emerald-600" />
                        <span>Call Center</span>
                      </a>
                    ) : (
                      <span className="text-xs text-slate-400 font-medium">Helpline: 1800-3000-3468</span>
                    )}

                    <button
                      onClick={() => openGoogleMaps(c.latitude || 25.5941, c.longitude || 85.1376, c.name)}
                      className="px-4 py-2 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <span>Get Directions</span>
                      <ExternalLink size={13} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
