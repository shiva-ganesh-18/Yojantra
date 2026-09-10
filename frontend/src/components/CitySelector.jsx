import React, { useState, useEffect, useMemo, useRef } from 'react';
import { locationsService } from '../services';
import { Search, Building, Check, ChevronDown, X, RefreshCw, Clock, Plus } from 'lucide-react';

export default function CitySelector({
  state,
  district,
  selectedCity,
  onSelectCity,
  label = "City / Town",
  required = false,
  allowCustom = true,
  className = "",
}) {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentCities, setRecentCities] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Load recent selections
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_recent_cities') || '[]');
      if (Array.isArray(saved)) setRecentCities(saved.slice(0, 4));
    } catch {}
  }, []);

  const fetchCities = async () => {
    if (!state && !district) {
      setCities([]);
      return;
    }
    try {
      setLoading(true);
      setError('');
      const data = await locationsService.getCities({ state, district, q: search });
      setCities(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to load cities. Check connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCities();
  }, [state, district]);

  const filteredCities = useMemo(() => {
    if (!search.trim()) return cities;
    const q = search.toLowerCase().trim();
    return cities.filter(c => c.name.toLowerCase().includes(q));
  }, [cities, search]);

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
      if ((e.key === 'ArrowDown' || e.key === 'Enter') && (state || district)) {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < filteredCities.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredCities.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredCities.length) {
        handleSelect(filteredCities[activeIndex].name);
      } else if (allowCustom && search.trim()) {
        handleSelect(search.trim());
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (cityName) => {
    onSelectCity(cityName);
    setIsOpen(false);
    setSearch('');
    setActiveIndex(-1);

    try {
      const updated = [cityName, ...recentCities.filter(c => c !== cityName)].slice(0, 4);
      setRecentCities(updated);
      localStorage.setItem('yojantra_recent_cities', JSON.stringify(updated));
    } catch {}
  };

  const isDisabled = !state && !district;

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedCity && (
            <button
              type="button"
              onClick={() => onSelectCity('')}
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
            ? "bg-white border-sky-500 ring-2 ring-sky-500/10 text-slate-800"
            : "bg-white border-slate-300 hover:border-slate-400 text-slate-800"
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <Building size={16} className={`shrink-0 ${isDisabled ? 'text-slate-400' : 'text-sky-600'}`} />
          <span className={selectedCity ? "text-slate-900 font-semibold" : "text-slate-400"}>
            {isDisabled
              ? "Select District / State First"
              : selectedCity || `Select City/Town ${district ? `in ${district}` : ''}`}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-slate-400">
          {selectedCity && !isDisabled && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onSelectCity('');
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
              placeholder={`Search city or town in ${district || state}...`}
              className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Quick Suggestions / Recent */}
          {!search && recentCities.length > 0 && (
            <div className="px-3 py-2 bg-slate-50/70 border-b border-slate-100 text-[11px]">
              <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                <Clock size={11} /> Recent:
              </div>
              <div className="flex flex-wrap gap-1">
                {recentCities.map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => handleSelect(c)}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-sky-500 hover:text-sky-700 transition-colors"
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* List Area */}
          <div className="max-h-60 overflow-y-auto p-1.5 divide-y divide-slate-50">
            {loading ? (
              <div className="py-8 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
                <span className="w-5 h-5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                <span>Loading cities...</span>
              </div>
            ) : error ? (
              <div className="py-6 px-4 text-center text-xs text-rose-600 flex flex-col items-center gap-2">
                <span>{error}</span>
                <button
                  type="button"
                  onClick={fetchCities}
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-sky-600 underline"
                >
                  <RefreshCw size={12} /> Retry
                </button>
              </div>
            ) : filteredCities.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                <p>No matching registered city found in this area.</p>
                {allowCustom && search.trim() && (
                  <button
                    type="button"
                    onClick={() => handleSelect(search.trim())}
                    className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-50 border border-sky-200 text-sky-700 font-semibold text-xs hover:bg-sky-100"
                  >
                    <Plus size={13} />
                    Use "{search.trim()}" as city
                  </button>
                )}
              </div>
            ) : (
              <>
                {filteredCities.map((c, idx) => {
                  const isSelected = selectedCity === c.name;
                  const isKeyboardActive = activeIndex === idx;
                  return (
                    <button
                      key={`${c.name}-${idx}`}
                      type="button"
                      onClick={() => handleSelect(c.name)}
                      className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-xl transition-colors text-left ${
                        isSelected
                          ? "bg-slate-900 text-white font-bold"
                          : isKeyboardActive
                          ? "bg-sky-50 text-sky-900 font-semibold"
                          : "text-slate-700 hover:bg-slate-100 font-medium"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span>{c.name}</span>
                        {c.district && (
                          <span className={`text-[10px] ${isSelected ? 'text-slate-300' : 'text-slate-400'}`}>
                            ({c.district})
                          </span>
                        )}
                      </div>
                      {isSelected && <Check size={14} className="text-sky-400 shrink-0" />}
                    </button>
                  );
                })}

                {allowCustom && search.trim() && !filteredCities.some(c => c.name.toLowerCase() === search.toLowerCase().trim()) && (
                  <button
                    type="button"
                    onClick={() => handleSelect(search.trim())}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs rounded-xl text-sky-700 hover:bg-sky-50 font-semibold border-t border-slate-100"
                  >
                    <Plus size={14} />
                    <span>Use "{search.trim()}"</span>
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
