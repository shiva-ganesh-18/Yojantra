import React, { useState, useEffect, useMemo, useRef } from 'react';
import { locationsService } from '../services';
import { Search, MapPin, Check, ChevronDown, X, RefreshCw, Clock, Sparkles } from 'lucide-react';

const POPULAR_SUGGESTIONS = [
  'Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu', 'Uttar Pradesh', 'Gujarat', 'Telangana'
];

export default function StateSelector({
  selectedState,
  onSelectState,
  label = "State / Union Territory",
  required = false,
  showSuggestions = true,
  className = "",
}) {
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentStates, setRecentStates] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Load recent selections
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_recent_states') || '[]');
      if (Array.isArray(saved)) setRecentStates(saved.slice(0, 4));
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Fetch states from API
  const fetchStates = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await locationsService.getStates();
      setStates(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to load Indian states. Check network connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStates();
  }, []);

  // Filtered states based on search
  const filteredStates = useMemo(() => {
    if (!search.trim()) return states;
    const q = search.toLowerCase().trim();
    return states.filter(s => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q));
  }, [states, search]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < filteredStates.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredStates.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredStates.length) {
        handleSelect(filteredStates[activeIndex].name);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (stateName) => {
    onSelectState(stateName);
    setIsOpen(false);
    setSearch('');
    setActiveIndex(-1);

    // Save recent selection
    try {
      const updated = [stateName, ...recentStates.filter(s => s !== stateName)].slice(0, 4);
      setRecentStates(updated);
      localStorage.setItem('yojantra_recent_states', JSON.stringify(updated));
    } catch {}
  };

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedState && (
            <button
              type="button"
              onClick={() => onSelectState('')}
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
          setIsOpen(!isOpen);
          setTimeout(() => inputRef.current?.focus(), 50);
        }}
        onKeyDown={handleKeyDown}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 bg-white border rounded-xl text-sm font-medium transition-all shadow-xs ${
          isOpen ? 'border-orange-500 ring-2 ring-orange-500/10' : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <MapPin size={16} className="text-orange-500 shrink-0" />
          <span className={selectedState ? "text-slate-900 font-semibold" : "text-slate-400"}>
            {selectedState || "Select Indian State / UT"}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-slate-400">
          {selectedState && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onSelectState('');
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
      {isOpen && (
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
              placeholder="Search 28 States & 8 UTs (e.g., Delhi, MH, KA)..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Quick Suggestions / Recent */}
          {!search && showSuggestions && (
            <div className="px-3 py-2 bg-slate-50/70 border-b border-slate-100 text-[11px]">
              {recentStates.length > 0 && (
                <div className="mb-2">
                  <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                    <Clock size={11} /> Recent:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {recentStates.map(st => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => handleSelect(st)}
                        className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-orange-400 hover:text-orange-600 transition-colors"
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                  <Sparkles size={11} className="text-amber-500" /> Popular:
                </div>
                <div className="flex flex-wrap gap-1">
                  {POPULAR_SUGGESTIONS.map(st => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => handleSelect(st)}
                      className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-orange-400 hover:text-orange-600 transition-colors"
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* List Area */}
          <div ref={listRef} className="max-h-60 overflow-y-auto p-1.5 divide-y divide-slate-50">
            {loading ? (
              <div className="py-8 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
                <span className="w-5 h-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
                <span>Loading Indian states & UTs...</span>
              </div>
            ) : error ? (
              <div className="py-6 px-4 text-center text-xs text-rose-600 flex flex-col items-center gap-2">
                <span>{error}</span>
                <button
                  type="button"
                  onClick={fetchStates}
                  className="inline-flex items-center gap-1 text-[11px] font-bold text-orange-600 underline"
                >
                  <RefreshCw size={12} /> Retry
                </button>
              </div>
            ) : filteredStates.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No matching state or union territory found
              </div>
            ) : (
              filteredStates.map((s, idx) => {
                const isSelected = selectedState === s.name;
                const isKeyboardActive = activeIndex === idx;
                return (
                  <button
                    key={s.code}
                    type="button"
                    onClick={() => handleSelect(s.name)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-xl transition-colors text-left ${
                      isSelected
                        ? "bg-slate-900 text-white font-bold"
                        : isKeyboardActive
                        ? "bg-orange-50 text-orange-900 font-semibold"
                        : "text-slate-700 hover:bg-slate-100 font-medium"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isSelected ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600"
                      }`}>
                        {s.code}
                      </span>
                      <span>{s.name}</span>
                      <span className={`text-[10px] ${isSelected ? "text-slate-300" : "text-slate-400"}`}>
                        ({s.type === "Union Territory" ? "UT" : `${s.districts_count || 0} Districts`})
                      </span>
                    </div>
                    {isSelected && <Check size={14} className="text-orange-400 shrink-0" />}
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
