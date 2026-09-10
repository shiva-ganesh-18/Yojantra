import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, GraduationCap, Check, ChevronDown, X, Clock, Sparkles } from 'lucide-react';

const PROMINENT_UNIVERSITIES = [
  'IIT - Institute of National Importance',
  'NIT - Institute of National Importance',
  'Anna University, Chennai',
  'Visvesvaraya Technological University (VTU), Belagavi',
  'Savitribai Phule Pune University (SPPU)',
  'University of Mumbai',
  'Dr. A.P.J. Abdul Kalam Technical University (AKTU), Lucknow',
  'Jawaharlal Nehru Technological University (JNTUH), Hyderabad',
  'Delhi Technological University (DTU)',
  'Indraprastha Institute of Information Technology (IIIT Delhi)',
  'Guru Gobind Singh Indraprastha University (GGSIPU)',
  'Rajiv Gandhi Proudyogiki Vishwavidyalaya (RGPV), Bhopal',
  'Biju Patnaik University of Technology (BPUT)',
  'Maulana Abul Kalam Azad University of Technology (MAKAUT), WB',
  'Gujarat Technological University (GTU)',
  'Deemed-to-be University / Autonomous'
];

export default function UniversitySelector({
  selectedUniversity,
  onSelectUniversity,
  label = "University / Affiliating Body",
  required = false,
  className = "",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentUniversities, setRecentUniversities] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_recent_univs') || '[]');
      if (Array.isArray(saved)) setRecentUniversities(saved.slice(0, 3));
    } catch {}
  }, []);

  const filteredUniversities = useMemo(() => {
    if (!search.trim()) return PROMINENT_UNIVERSITIES;
    const q = search.toLowerCase().trim();
    return PROMINENT_UNIVERSITIES.filter(u => u.toLowerCase().includes(q));
  }, [search]);

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
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < filteredUniversities.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredUniversities.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredUniversities.length) {
        handleSelect(filteredUniversities[activeIndex]);
      } else if (search.trim()) {
        handleSelect(search.trim());
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (univ) => {
    onSelectUniversity(univ);
    setIsOpen(false);
    setSearch('');
    setActiveIndex(-1);

    try {
      const updated = [univ, ...recentUniversities.filter(u => u !== univ)].slice(0, 3);
      setRecentUniversities(updated);
      localStorage.setItem('yojantra_recent_univs', JSON.stringify(updated));
    } catch {}
  };

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedUniversity && (
            <button
              type="button"
              onClick={() => onSelectUniversity('')}
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
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all shadow-xs border ${
          isOpen
            ? "bg-white border-purple-500 ring-2 ring-purple-500/10 text-slate-800"
            : "bg-white border-slate-300 hover:border-slate-400 text-slate-800"
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <GraduationCap size={16} className="text-purple-600 shrink-0" />
          <span className={selectedUniversity ? "text-slate-900 font-semibold" : "text-slate-400"}>
            {selectedUniversity || "Select Affiliating University / Board"}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-slate-400">
          {selectedUniversity && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onSelectUniversity('');
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

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1.5 w-full bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
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
              placeholder="Search or enter University name..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={14} />
              </button>
            )}
          </div>

          {!search && recentUniversities.length > 0 && (
            <div className="px-3 py-2 bg-slate-50/70 border-b border-slate-100 text-[11px]">
              <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                <Clock size={11} /> Recent:
              </div>
              <div className="flex flex-wrap gap-1">
                {recentUniversities.map(u => (
                  <button
                    key={u}
                    type="button"
                    onClick={() => handleSelect(u)}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-purple-400 hover:text-purple-700 transition-colors"
                  >
                    {u}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="max-h-60 overflow-y-auto p-1.5 divide-y divide-slate-50">
            {filteredUniversities.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                <p>No matching preset university found.</p>
                {search.trim() && (
                  <button
                    type="button"
                    onClick={() => handleSelect(search.trim())}
                    className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-50 border border-purple-200 text-purple-700 font-semibold text-xs hover:bg-purple-100"
                  >
                    Use "{search.trim()}"
                  </button>
                )}
              </div>
            ) : (
              filteredUniversities.map((u, idx) => {
                const isSelected = selectedUniversity === u;
                const isKeyboardActive = activeIndex === idx;
                return (
                  <button
                    key={u}
                    type="button"
                    onClick={() => handleSelect(u)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-xl transition-colors text-left ${
                      isSelected
                        ? "bg-slate-900 text-white font-bold"
                        : isKeyboardActive
                        ? "bg-purple-50 text-purple-900 font-semibold"
                        : "text-slate-700 hover:bg-slate-100 font-medium"
                    }`}
                  >
                    <span>{u}</span>
                    {isSelected && <Check size={14} className="text-purple-400 shrink-0" />}
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
