import React, { useState } from 'react';
import StateSelector from './StateSelector';
import DistrictSelector from './DistrictSelector';
import CitySelector from './CitySelector';
import InstitutionAutocomplete from './InstitutionAutocomplete';
import LocationBreadcrumb from './LocationBreadcrumb';
import { 
  Building2, MapPin, CheckCircle2, 
  RotateCcw, ArrowRight, X, Sparkles 
} from 'lucide-react';

export default function IndiaLocationCommand({
  initialState = '',
  initialDistrict = '',
  initialCity = '',
  initialInstitution = null,
  onComplete,
  onClose
}) {
  const [state, setState] = useState(initialState);
  const [district, setDistrict] = useState(initialDistrict);
  const [city, setCity] = useState(initialCity);
  const [institution, setInstitution] = useState(initialInstitution);

  const handleReset = () => {
    setState('');
    setDistrict('');
    setCity('');
    setInstitution(null);
  };

  const handleBreadcrumbHop = (level) => {
    if (level === 'india') {
      handleReset();
    } else if (level === 'state') {
      setDistrict('');
      setCity('');
      setInstitution(null);
    } else if (level === 'district') {
      setCity('');
      setInstitution(null);
    } else if (level === 'city') {
      setInstitution(null);
    }
  };

  const handleFinish = () => {
    if (onComplete) {
      onComplete({
        state,
        district,
        city,
        institution
      });
    }
    if (onClose) onClose();
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 shadow-2xl overflow-hidden p-6 sm:p-8 text-left max-w-3xl mx-auto animate-in fade-in zoom-in-95 duration-200">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-100 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🇮🇳</span>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">India Location & Channel Partner Navigator</h2>
          </div>
          <p className="text-xs text-slate-500 max-w-xl">
            Select your State, District, and City to discover local government schemes, subsidies, and authorized channel partner centers.
          </p>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Interactive Breadcrumb */}
      <div className="mb-6">
        <LocationBreadcrumb
          state={state}
          district={district}
          city={city}
          institution={institution}
          onSelectLevel={handleBreadcrumbHop}
          onResetAll={handleReset}
        />
      </div>

      {/* Hierarchy Controls Grid */}
      <div className="space-y-4">
        {/* Tier 1: State & District */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <StateSelector
            selectedState={state}
            onSelectState={(val) => {
              setState(val);
              setDistrict('');
              setCity('');
              setInstitution(null);
            }}
            required
          />
          <DistrictSelector
            state={state}
            selectedDistrict={district}
            onSelectDistrict={(val) => {
              setDistrict(val);
              setCity('');
              setInstitution(null);
            }}
            required
          />
        </div>

        {/* Tier 2: City / Town */}
        <div className="grid grid-cols-1 gap-4">
          <CitySelector
            state={state}
            district={district}
            selectedCity={city}
            onSelectCity={(val) => {
              setCity(val);
            }}
          />
        </div>

        {/* Tier 3: Channel Partner / Facilitation Center Autocomplete */}
        <div className="pt-1">
          <InstitutionAutocomplete
            state={state}
            district={district}
            selectedInstitution={institution}
            onSelectInstitution={(inst) => {
              setInstitution(inst);
              if (inst && inst.city && !city) {
                setCity(inst.city);
              }
            }}
            label="Authorized Channel Partner / Facilitation Center (Optional)"
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
        <button
          type="button"
          onClick={handleReset}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <RotateCcw size={13} />
          <span>Reset Selection</span>
        </button>

        <div className="flex items-center gap-3">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            onClick={handleFinish}
            disabled={!state}
            className="px-6 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white text-xs sm:text-sm font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span>Apply Location</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
