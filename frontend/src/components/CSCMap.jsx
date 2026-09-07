import React, { useState } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { MapPin, Phone, Navigation, Clock, X, ExternalLink } from 'lucide-react';

export default function CSCMap({ onClose }) {
  const { api } = useAuthStore();
  const [location, setLocation] = useState(null);
  const [centers, setCenters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const getLocation = () => {
    setLoading(true);
    setError('');

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your device');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setLocation({ lat: latitude, lng: longitude });

        try {
          const res = await api().get('/csc/nearby', {
            params: { lat: latitude, lng: longitude, radius_km: 15 }
          });
          setCenters(res.data?.centers || []);
        } catch (e) {
          setError('Failed to fetch CSC centers in your area.');
        }
        setLoading(false);
      },
      (err) => {
        setError('Please enable location access in browser settings to find nearby centers.');
        setLoading(false);
      }
    );
  };

  const openDirections = (lat, lng) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    window.open(url, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-gov-navy-950/70 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-150">
      <div className="bg-white w-full max-w-lg max-h-[90vh] rounded-t-3xl sm:rounded-3xl overflow-hidden flex flex-col shadow-2xl border border-slate-200 text-left">
        {/* Header */}
        <div className="bg-gov-navy-950 text-white p-4 sm:p-5 flex justify-between items-center border-b border-gov-navy-800">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-gov-emerald-500/20 text-gov-emerald-400">
              <MapPin size={18} />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base">Find Nearest CSC Center</h3>
              <p className="text-[11px] text-slate-400">Authorized Common Service Center network</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
          {!location ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-2xl bg-gov-emerald-50 text-gov-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-sm border border-gov-emerald-100">
                <MapPin size={32} />
              </div>
              <h4 className="text-base font-bold text-gov-navy-950">Locate Nearby CSCs</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto mb-6">
                VLE centers assist with Aadhaar biometric update, PAN card, UDYAM registration, and scheme submission.
              </p>
              <button
                onClick={getLocation}
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 text-white text-xs sm:text-sm font-bold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Detecting GPS Coordinates...</span>
                  </>
                ) : (
                  <>
                    <Navigation size={15} />
                    <span>Use My GPS Location</span>
                  </>
                )}
              </button>
              {error && <p className="text-red-600 text-xs mt-3 bg-red-50 p-2.5 rounded-xl">{error}</p>}
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Found {centers.length} Centers Within 15 KM
              </p>
              {centers.map(center => (
                <div key={center.id} className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 space-y-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <h5 className="font-bold text-sm text-gov-navy-950">{center.name}</h5>
                    <span className="text-[11px] font-bold text-gov-navy-900 bg-white px-2 py-0.5 rounded-md border border-slate-200 flex-shrink-0">
                      {center.distance_km} km
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{center.address}</p>
                  
                  <div className="flex flex-wrap gap-1">
                    {center.services_offered?.map(s => (
                      <span key={s} className="bg-white border border-slate-200 text-slate-700 px-2 py-0.5 rounded text-[10px] font-medium">
                        {s}
                      </span>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between">
                    {center.phone ? (
                      <a href={`tel:${center.phone}`} className="text-xs font-bold text-gov-emerald-700 hover:underline flex items-center gap-1">
                        <Phone size={13} />
                        <span>{center.phone}</span>
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-400">Gov Helpline: 1800-3000-3468</span>
                    )}

                    <button
                      onClick={() => openDirections(center.latitude, center.longitude)}
                      className="px-3 py-1.5 rounded-lg bg-gov-navy-950 text-white text-xs font-bold hover:bg-gov-navy-900 transition-all flex items-center gap-1"
                    >
                      <span>Directions</span>
                      <ExternalLink size={12} />
                    </button>
                  </div>
                </div>
              ))}
              {centers.length === 0 && (
                <p className="text-center text-slate-500 py-8 text-xs">No CSC centers found nearby</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
