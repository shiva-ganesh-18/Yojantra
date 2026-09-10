import React, { useState, useEffect, useMemo, useRef } from 'react';
import { locationsService } from '../services';
import { Search, MapPin, Check, ChevronDown, X, RefreshCw, Clock, Sparkles } from 'lucide-react';

export default function DistrictSelector({
  state,
  selectedDistrict,
  onSelectDistrict,
  label = "District",
  required = false,
  showSuggestions = true,
  className = "",
}) {
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentDistricts, setRecentDistricts] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Load recent districts
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(`yojantra_recent_districts_${state || 'all'}`) || '[]');
      if (Array.isArray(saved)) setRecentDistricts(saved.slice(0, 4));
    } catch {}
  }, [state]);

  const fetchDistricts = async () => {
    if (!state) {
      setDistricts([]);
      return;
    }
    try {
      setLoading(true);
      setError('');
      const data = await locationsService.getDistricts(state);
      setDistricts(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to load districts for selected state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDistricts();
  }, [state]);

  // Ensure selectedDistrict actually belongs to the loaded state's districts
  useEffect(() => {
    if (!loading && districts.length > 0 && selectedDistrict) {
      const match = districts.some(d => d.name.toLowerCase() === selectedDistrict.toLowerCase());
      if (!match) {
        onSelectDistrict?.('');
      }
    }
  }, [districts, selectedDistrict, loading, onSelectDistrict]);

  const filteredDistricts = useMemo(() => {
    if (!search.trim()) return districts;
    const q = search.toLowerCase().trim();
    return districts.filter(d => d.name.toLowerCase().includes(q));
  }, [districts, search]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (!isOpen) {
      if ((e.key === 'ArrowDown' || e.key === 'Enter') && state) {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < filteredDistricts.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredDistricts.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredDistricts.length) {
        handleSelect(filteredDistricts[activeIndex].name);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (districtName) => {
    onSelectDistrict(districtName);
    setIsOpen(false);
    setSearch('');
    setActiveIndex(-1);

    try {
      const key = `yojantra_recent_districts_${state || 'all'}`;
      const updated = [districtName, ...recentDistricts.filter(d => d !== districtName)].slice(0, 4);
      setRecentDistricts(updated);
      localStorage.setItem(key, JSON.stringify(updated));
    } catch {}
  };

  const isDisabled = !state;

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedDistrict && (
            <button
              type="button"
              onClick={() => onSelectDistrict('')}
              className="text-[11px] font-semibold text-slate-400 hover:text-rose-600 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => {
          if (!isDisabled) {
            setIsOpen(!isOpen);
            setTimeout(() => inputRef.current?.focus(), 50);
          }
        }}
        disabled={isDisabled}
        onKeyDown={handleKeyDown}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all shadow-xs border ${
          isDisabled
            ? "bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed"
            : isOpen
            ? "bg-white border-emerald-500 ring-2 ring-emerald-500/10 text-slate-800"
            : "bg-white border-slate-300 hover:border-slate-400 text-slate-800"
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <MapPin size={16} className={`shrink-0 ${isDisabled ? 'text-slate-400' : 'text-emerald-600'}`} />
          <span className={selectedDistrict ? "text-slate-900 font-semibold" : "text-slate-400"}>
            {isDisabled
              ? "Select State / UT First"
              : selectedDistrict || `Select District in ${state}`}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-slate-400">
          {selectedDistrict && !isDisabled && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onSelectDistrict('');
              }}
              className="p-0.5 hover:text-slate-600 rounded-full cursor-pointer"
              title="Clear selection"
            >
              <X size={14} />
            </span>
          )}
          <ChevronDown size={16} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && !isDisabled && (
        <div className="absolute z-50 mt-1.5 w-full bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Search Box */}
          <div className="p-2.5 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
            <Search size={16} className="text-slate-400 shrink-0 ml-1" />
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={handleKeyDown}
              placeholder={`Search districts in ${state}...`}
              className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Quick Suggestions / Recent */}
          {!search && showSuggestions && recentDistricts.length > 0 && (
            <div className="px-3 py-2 bg-slate-50/70 border-b border-slate-100 text-[11px]">
              <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                <Clock size={11} /> Recent in {state}:
              </div>
              <div className="flex flex-wrap gap-1">
                {recentDistricts.map(dst => (
                  <button
                    key={dst}
                    type="button"
                    onClick={() => handleSelect(dst)}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-emerald-500 hover:text-emerald-700 transition-colors"
                  >
                    {dst}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* List Area */}
          <div className="max-h-60 overflow-y-auto p-1.5 divide-y divide-slate-50">
            {loading ? (
              <div className="py-8 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
                <span className="w-5 h-5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                <span>Loading districts...</span>
              </div>
            ) : error ? (
              <div className="py-6 px-4 text-center text-xs text-rose-600 flex flex-col items-center gap-2">
                <span>{error}</span>
                <button
                  type="button"
                  onClick={fetchDistricts}
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 underline"
                >
                  <RefreshCw size={12} /> Retry
                </button>
              </div>
            ) : filteredDistricts.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No matching district found in {state}
              </div>
            ) : (
              filteredDistricts.map((d, idx) => {
                const isSelected = selectedDistrict === d.name;
                const isKeyboardActive = activeIndex === idx;
                return (
                  <button
                    key={d.name}
                    type="button"
                    onClick={() => handleSelect(d.name)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-xl transition-colors text-left ${
                      isSelected
                        ? "bg-slate-900 text-white font-bold"
                        : isKeyboardActive
                        ? "bg-emerald-50 text-emerald-900 font-semibold"
                        : "text-slate-700 hover:bg-slate-100 font-medium"
                    }`}
                  >
                    <span>{d.name}</span>
                    {isSelected && <Check size={14} className="text-emerald-400 shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
