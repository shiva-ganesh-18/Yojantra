import React, { useState, useEffect, useRef } from 'react';
import { institutionsService } from '../services';
import { Search, Building2, Award, Check, X, PlusCircle, ExternalLink, MapPin, RefreshCw, Clock } from 'lucide-react';

export default function InstitutionAutocomplete({
  state,
  district,
  selectedInstitution,
  onSelectInstitution,
  onRequestAddCollege,
  label = "College / University",
  required = false,
  className = "",
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentInstitutions, setRecentInstitutions] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Load recent selections
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_recent_institutions') || '[]');
      if (Array.isArray(saved)) setRecentInstitutions(saved.slice(0, 3));
    } catch {}
  }, []);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Search institutions
  const fetchInstitutions = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await institutionsService.getInstitutions({
        q: query,
        state: state || undefined,
        district: district || undefined,
        page_size: 20
      });
      setResults(data || []);
    } catch (err) {
      setError('Unable to search institutions. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(fetchInstitutions, 250);
    return () => clearTimeout(timer);
  }, [query, state, district, isOpen]);

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
      setActiveIndex(prev => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < results.length) {
        handleSelect(results[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (inst) => {
    onSelectInstitution(inst);
    setIsOpen(false);
    setQuery('');
    setActiveIndex(-1);

    try {
      const updated = [inst, ...recentInstitutions.filter(item => item.id !== inst.id)].slice(0, 3);
      setRecentInstitutions(updated);
      localStorage.setItem('yojantra_recent_institutions', JSON.stringify(updated));
    } catch {}
  };

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedInstitution && (
            <button
              type="button"
              onClick={() => onSelectInstitution(null)}
              className="text-[11px] font-semibold text-slate-400 hover:text-rose-600 transition-colors"
            >
              Change
            </button>
          )}
        </div>
      )}

      {/* Main Selected Display */}
      {selectedInstitution ? (
        <div className="flex items-center justify-between p-3 bg-white border border-slate-300 rounded-xl shadow-xs">
          <div className="flex items-start gap-2.5 truncate">
            <div className="w-8 h-8 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center shrink-0 mt-0.5">
              <Building2 size={16} />
            </div>
            <div className="truncate text-left">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-900 truncate">
                  {selectedInstitution.name}
                </span>
                {selectedInstitution.nirf_rank && (
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-900 flex items-center gap-0.5 shrink-0">
                    <Award size={10} /> #{selectedInstitution.nirf_rank}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 flex items-center gap-1.5 truncate">
                <MapPin size={12} className="shrink-0" />
                <span>{selectedInstitution.city || selectedInstitution.district}, {selectedInstitution.state}</span>
                {selectedInstitution.code && (
                  <span className="font-mono text-[11px] bg-slate-100 px-1 rounded">
                    AISHE: {selectedInstitution.code}
                  </span>
                )}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onSelectInstitution(null)}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 shrink-0 ml-2"
            title="Clear and change college"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <div className="relative">
          <div className="flex items-center px-3.5 py-2.5 bg-white border border-slate-300 focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-500/10 rounded-xl shadow-xs transition-all">
            <Search size={16} className="text-slate-400 mr-2 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (!isOpen) setIsOpen(true);
                setActiveIndex(0);
              }}
              onFocus={() => setIsOpen(true)}
              onKeyDown={handleKeyDown}
              placeholder="Search by college name, abbreviation (IIT, NIT, etc.), or AISHE code..."
              className="w-full bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Results Dropdown */}
          {isOpen && (
            <div className="absolute z-50 mt-1.5 w-full bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
              {/* Recent selections */}
              {!query && recentInstitutions.length > 0 && (
                <div className="p-2.5 bg-slate-50/80 border-b border-slate-100 text-[11px]">
                  <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                    <Clock size={11} /> Recently Selected Colleges:
                  </div>
                  <div className="space-y-1">
                    {recentInstitutions.map(inst => (
                      <button
                        key={inst.id}
                        type="button"
                        onClick={() => handleSelect(inst)}
                        className="w-full text-left px-2 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-orange-400 hover:bg-orange-50/50 flex items-center justify-between text-xs"
                      >
                        <span className="font-semibold text-slate-800 truncate">{inst.name}</span>
                        <span className="text-[10px] text-slate-400 shrink-0 ml-2">{inst.city || inst.district}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="max-h-72 overflow-y-auto p-1.5 divide-y divide-slate-100">
                {loading ? (
                  <div className="py-8 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
                    <span className="w-5 h-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
                    <span>Searching All-India college repository...</span>
                  </div>
                ) : error ? (
                  <div className="py-6 px-4 text-center text-xs text-rose-600 flex flex-col items-center gap-2">
                    <span>{error}</span>
                    <button
                      type="button"
                      onClick={fetchInstitutions}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-orange-600 underline"
                    >
                      <RefreshCw size={12} /> Retry Search
                    </button>
                  </div>
                ) : results.length === 0 ? (
                  <div className="py-6 px-4 text-center">
                    <p className="text-xs text-slate-500 mb-2">
                      No verified institution matching "{query}".
                    </p>
                    {onRequestAddCollege && (
                      <button
                        type="button"
                        onClick={() => {
                          setIsOpen(false);
                          onRequestAddCollege(query);
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition-colors"
                      >
                        <PlusCircle size={13} />
                        <span>Request Institution Addition</span>
                      </button>
                    )}
                  </div>
                ) : (
                  results.map((inst, idx) => {
                    const isKeyboardActive = activeIndex === idx;
                    return (
                      <button
                        key={inst.id}
                        type="button"
                        onClick={() => handleSelect(inst)}
                        className={`w-full text-left p-2.5 rounded-xl transition-colors flex items-start justify-between gap-3 group ${
                          isKeyboardActive ? 'bg-orange-50/80' : 'hover:bg-slate-50'
                        }`}
                      >
                        <div className="truncate">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-900 group-hover:text-orange-600 truncate">
                              {inst.name}
                            </span>
                            {inst.short_name && (
                              <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 text-[10px] font-bold rounded">
                                {inst.short_name}
                              </span>
                            )}
                            {inst.nirf_rank && (
                              <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                NIRF #{inst.nirf_rank}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-1">
                            <span>{inst.city || inst.district}, {inst.state}</span>
                            {inst.institution_type && (
                              <>
                                <span>•</span>
                                <span className="truncate">{inst.institution_type}</span>
                              </>
                            )}
                          </div>
                        </div>
                        {inst.code && (
                          <div className="text-right shrink-0">
                            <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                              {inst.code}
                            </span>
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
