import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  Compass, ZoomIn, ZoomOut, RotateCcw, 
  MapPin, Navigation, ExternalLink, Info, AlertTriangle, ShieldCheck
} from 'lucide-react';

/**
 * Validates latitude and longitude values safely.
 */
export const isValidCoord = (lat, lng) => {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180 &&
    !(lat === 0 && lng === 0)
  );
};

const CATEGORY_COLORS = {
  SCA: { bg: '#9333ea', text: '#ffffff', label: 'SCA', border: '#7e22ce' },
  PSB: { bg: '#2563eb', text: '#ffffff', label: 'PSB', border: '#1d4ed8' },
  RRB: { bg: '#d97706', text: '#ffffff', label: 'RRB', border: '#b45309' },
  'NBFC-MFI': { bg: '#059669', text: '#ffffff', label: 'NBFC', border: '#047857' },
  'Facilitation Center': { bg: '#4f46e5', text: '#ffffff', label: 'CSC', border: '#4338ca' },
};

const getCategoryColor = (type) => {
  return CATEGORY_COLORS[type] || { bg: '#0284c7', text: '#ffffff', label: type || 'BANK', border: '#0369a1' };
};

// Safe external directions URL constructor
export const getDirectionsUrl = (lat, lng, name, district, state) => {
  if (isValidCoord(lat, lng)) {
    const query = encodeURIComponent(`${lat},${lng}`);
    return `https://www.google.com/maps/dir/?api=1&destination=${query}`;
  }
  const query = encodeURIComponent([name, district, state, 'India'].filter(Boolean).join(' '));
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
};

/**
 * PartnerMap: Proper geographic interactive Leaflet map for Channel Partners & Lending Institutions.
 * Never creates fake coordinates; honestly segregates unmapped partners into an administrative fallback list.
 */
export default function PartnerMap({
  partners = [],
  userLocation = null,
  selectedPartner = null,
  onSelectPartner = () => {},
  centerState = '',
  centerDistrict = ''
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const userMarkerRef = useRef(null);
  const partnerMarkersMapRef = useRef(new Map());

  const [mapReady, setMapReady] = useState(false);

  // Split partners into verified geo-coordinates vs unmapped jurisdiction partners
  const validPartners = partners.filter(p => isValidCoord(p.latitude, p.longitude));
  const unmappedPartners = partners.filter(p => !isValidCoord(p.latitude, p.longitude));

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default India center
    const defaultCenter = [20.5937, 78.9629];
    const defaultZoom = 5;

    const map = L.map(mapContainerRef.current, {
      center: defaultCenter,
      zoom: defaultZoom,
      zoomControl: false, // We render modern accessible custom zoom buttons
      attributionControl: true,
      maxZoom: 18,
      minZoom: 4,
    });

    // Clean OpenStreetMap standard tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    const markersGroup = L.featureGroup().addTo(map);
    markersLayerRef.current = markersGroup;
    mapInstanceRef.current = map;
    setMapReady(true);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
      markersLayerRef.current = null;
      userMarkerRef.current = null;
      partnerMarkersMapRef.current.clear();
      setMapReady(false);
    };
  }, []);

  // Update markers when partners list or selectedPartner changes
  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current || !markersLayerRef.current) return;

    const map = mapInstanceRef.current;
    const markersGroup = markersLayerRef.current;
    markersGroup.clearLayers();
    partnerMarkersMapRef.current.clear();

    const boundsPoints = [];

    // 1. Plot user GPS location if valid
    if (userLocation && isValidCoord(userLocation.lat, userLocation.lng)) {
      const userHtml = `
        <div class="relative flex items-center justify-center -translate-x-1/2 -translate-y-1/2 cursor-pointer">
          <span class="absolute w-8 h-8 rounded-full bg-amber-500/30 animate-ping"></span>
          <span class="w-6 h-6 rounded-full bg-amber-500 border-2 border-white shadow-lg flex items-center justify-center text-slate-900 font-extrabold text-[10px]">
            📍
          </span>
        </div>
      `;
      const userIcon = L.divIcon({
        html: userHtml,
        className: 'user-gps-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const uMarker = L.marker([userLocation.lat, userLocation.lng], {
        icon: userIcon,
        zIndexOffset: 1000,
      }).bindPopup(`
        <div class="p-2 text-slate-900 text-left font-sans">
          <div class="flex items-center gap-1.5 text-xs font-black text-amber-600 mb-1">
            <span>📍 Your Current GPS Location</span>
          </div>
          <p class="text-[11px] text-slate-600">Active distance origin for nearby channel partner discovery.</p>
        </div>
      `);

      uMarker.addTo(markersGroup);
      userMarkerRef.current = uMarker;
      boundsPoints.push([userLocation.lat, userLocation.lng]);
    }

    // 2. Plot each partner with authentic coordinates
    validPartners.forEach((partner) => {
      const isSelected = selectedPartner?.id === partner.id;
      const theme = getCategoryColor(partner.institution_type);

      const markerHtml = `
        <div class="relative flex items-center justify-center -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-transform group">
          <div style="background-color: ${isSelected ? '#ea580c' : theme.bg}; border-color: ${isSelected ? '#ffffff' : theme.border};"
               class="px-2 py-0.5 rounded-full shadow-md border-2 flex items-center gap-1 text-white font-black text-[10px] ${isSelected ? 'ring-4 ring-orange-400/50 scale-125' : 'hover:scale-110'}">
            <span>${theme.label}</span>
          </div>
          <div class="w-2 h-2 rotate-45 -mt-1" style="background-color: ${isSelected ? '#ea580c' : theme.bg};"></div>
        </div>
      `;

      const markerIcon = L.divIcon({
        html: markerHtml,
        className: `partner-pin-icon-${partner.id}`,
        iconSize: [40, 26],
        iconAnchor: [20, 26],
      });

      const marker = L.marker([partner.latitude, partner.longitude], {
        icon: markerIcon,
        zIndexOffset: isSelected ? 800 : 100,
      });

      // Direction link
      const directionsUrl = getDirectionsUrl(
        partner.latitude, 
        partner.longitude, 
        partner.name, 
        partner.district, 
        partner.state
      );

// Popup Content
      const popupHtml = `
        <div class="p-2.5 text-slate-900 text-left max-w-[280px] font-sans">
          <div class="flex items-center justify-between gap-2 mb-1.5">
            <span style="background-color: ${theme.bg};" class="text-[9px] font-black px-2 py-0.5 rounded-full text-white">
              ${partner.institution_type || 'PSB'}
            </span>
            ${partner.distance_km !== null && partner.distance_km !== undefined ? `
              <span class="text-[10px] font-extrabold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                ${partner.distance_km} km away
              </span>
            ` : ''}
          </div>
          <h4 class="font-bold text-xs leading-snug text-slate-950 mb-1">
            ${partner.name}
          </h4>
          <p class="text-[11px] text-slate-500 mb-2">
            📍 ${partner.address || `${partner.city || partner.district || ''}, ${partner.state || ''}`}
          </p>
          <div class="flex items-center gap-2 pt-2 border-t border-slate-100">
            <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" 
               class="px-3 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-700 text-white font-bold text-[11px] inline-flex items-center gap-1 shadow-sm text-decoration-none">
              <span>Directions</span>
              <span>↗</span>
            </a>
            <button id="select-partner-${partner.id}" 
                    class="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-[11px]">
              Details
            </button>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);

      marker.on('popupopen', () => {
        const btn = document.getElementById(`select-partner-${partner.id}`);
        if (btn) {
          btn.onclick = () => onSelectPartner(partner);
        }
      });

      marker.on('click', () => {
        onSelectPartner(partner);
      });

      marker.addTo(markersGroup);
      partnerMarkersMapRef.current.set(partner.id, marker);
      boundsPoints.push([partner.latitude, partner.longitude]);
    });

    // Auto-fit bounds if we have points and not manually focusing a single item
    if (boundsPoints.length > 1) {
      map.fitBounds(boundsPoints, { padding: [40, 40], maxZoom: 14 });
    } else if (boundsPoints.length === 1) {
      map.setView(boundsPoints[0], 13);
    }
  }, [validPartners.length, userLocation, mapReady]);

  // Open popup and pan to selected partner when selected externally
  useEffect(() => {
    if (!mapReady || !selectedPartner || !mapInstanceRef.current) return;

    if (isValidCoord(selectedPartner.latitude, selectedPartner.longitude)) {
      const marker = partnerMarkersMapRef.current.get(selectedPartner.id);
      if (marker) {
        mapInstanceRef.current.setView([selectedPartner.latitude, selectedPartner.longitude], 14, { animate: true });
        marker.openPopup();
      }
    }
  }, [selectedPartner, mapReady]);

  // Map controls
  const handleZoomIn = () => {
    if (mapInstanceRef.current) mapInstanceRef.current.zoomIn();
  };

  const handleZoomOut = () => {
    if (mapInstanceRef.current) mapInstanceRef.current.zoomOut();
  };

  const handleResetZoom = () => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;
    const layers = markersLayerRef.current.getLayers();
    if (layers.length > 0) {
      const bounds = markersLayerRef.current.getBounds();
      mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    } else {
      mapInstanceRef.current.setView([20.5937, 78.9629], 5);
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col text-left">
      {/* Map Control Bar */}
      <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="p-1.5 rounded-lg bg-gov-navy-950 text-white font-black text-[10px] flex items-center gap-1">
            <Compass size={12} className="text-gov-saffron-400" />
            <span>Geographic Partner Locator</span>
          </span>
          <span className="text-slate-600 font-semibold hidden sm:inline">
            {validPartners.length} Mapped Locations
            {centerDistrict && ` in ${centerDistrict}`}
            {centerState && `, ${centerState}`}
          </span>
        </div>

        {/* Legend - simplified on mobile */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[11px] font-bold">
          <span className="flex items-center gap-1 text-purple-700">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600" /> SCA
          </span>
          <span className="flex items-center gap-1 text-blue-700">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> PSB
          </span>
          <span className="flex items-center gap-1 text-amber-700">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-600" /> RRB
          </span>
          <span className="flex items-center gap-1 text-emerald-700">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" /> NBFC-MFI
          </span>
          {userLocation && (
            <span className="flex items-center gap-1 text-amber-700">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 ring-2 ring-amber-300 animate-pulse" /> My GPS
            </span>
          )}
        </div>

        {/* Zoom & Reset Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomIn}
            title="Zoom In"
            aria-label="Zoom In"
            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 shadow-xs transition-colors min-h-[44px] min-w-[44px]"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out"
            aria-label="Zoom Out"
            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 shadow-xs transition-colors min-h-[44px] min-w-[44px]"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={handleResetZoom}
            title="Fit to All Partners"
            aria-label="Fit to All Partners"
            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 shadow-xs transition-colors flex items-center gap-1 text-[11px] font-bold min-h-[44px]"
          >
            <RotateCcw size={14} />
            <span className="hidden sm:inline">Fit View</span>
          </button>
        </div>
      </div>

      {/* Main Map Viewport */}
      <div className="relative w-full h-80 sm:h-96 bg-slate-100 overflow-hidden">
        <div 
          ref={mapContainerRef} 
          className="w-full h-full z-10"
          style={{ minHeight: '320px' }}
        />

        {/* Notice when no valid partners have coordinates */}
        {validPartners.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/70 backdrop-blur-xs p-6 text-center text-white z-20 pointer-events-none">
            <div className="max-w-md space-y-2">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
              <h4 className="text-sm font-bold">No Direct GPS Pin Available</h4>
              <p className="text-xs text-slate-200">
                Partners in this jurisdiction are indexed by administrative headquarters. Select any partner from the directory below to view branch details and contact information.
              </p>
            </div>
          </div>
        )}

        {/* Real-time Banking & Dispersal Disclosure Pill */}
        <div className="absolute bottom-3 left-3 right-3 sm:left-auto sm:right-3 sm:max-w-xs bg-slate-950/85 backdrop-blur-md text-slate-300 text-[10px] p-2.5 rounded-xl border border-slate-800 shadow-lg flex items-start gap-2 z-20 pointer-events-none">
          <Info size={14} className="text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-tight">
            Fund availability and current quota are not verified in real time. Contact the partner to confirm current availability.
          </p>
        </div>
      </div>

      {/* Honest Administrative Jurisdiction Fallback Section for Unmapped Partners */}
      {unmappedPartners.length > 0 && (
        <div className="p-4 bg-amber-50/80 border-t border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-start gap-2.5">
            <Info size={16} className="text-amber-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-extrabold text-amber-950">
                {unmappedPartners.length} Partner{unmappedPartners.length > 1 ? 's' : ''} with Administrative Headquarters (Unmapped GPS):
              </span>
              <p className="text-[11px] text-amber-900/90 mt-0.5">
                These partners are accredited for this area, but do not have verified physical map coordinates. They are not displayed with fake coordinates.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 shrink-0">
            {unmappedPartners.map(p => (
              <button
                key={p.id}
                onClick={() => onSelectPartner(p)}
                className="px-2.5 py-1 rounded-lg bg-white border border-amber-300 hover:bg-amber-100/60 text-amber-950 text-[11px] font-bold transition-colors"
              >
                {p.short_name || p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Partner Action Footer */}
      {selectedPartner && (
        <div className="p-4 bg-gov-navy-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-800 animate-in slide-in-from-bottom duration-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gov-saffron-500 text-gov-navy-950 flex items-center justify-center font-black text-xs shrink-0">
              {selectedPartner.institution_type || 'PSB'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-xs sm:text-sm text-white">
                  {selectedPartner.name}
                </h4>
                {selectedPartner.distance_km !== null && selectedPartner.distance_km !== undefined && (
                  <span className="text-[10px] font-extrabold text-gov-saffron-400 bg-white/10 px-2 py-0.5 rounded-full">
                    {selectedPartner.distance_km} km away
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400">
                📍 {selectedPartner.address || `${selectedPartner.city || selectedPartner.district || ''}, ${selectedPartner.state || ''}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <a
              href={getDirectionsUrl(
                selectedPartner.latitude, 
                selectedPartner.longitude, 
                selectedPartner.name, 
                selectedPartner.district, 
                selectedPartner.state
              )}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-xl bg-gov-saffron-500 hover:bg-gov-saffron-600 text-gov-navy-950 font-black text-xs transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span>{isValidCoord(selectedPartner.latitude, selectedPartner.longitude) ? 'Open in Maps / Directions' : 'Search Location on Map'}</span>
              <ExternalLink size={12} />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
