import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, BookOpen, Check, ChevronDown, X, Clock, Sparkles } from 'lucide-react';

const COMMON_DEPARTMENTS = [
  'Computer Science & Engineering (CSE)',
  'Artificial Intelligence & Machine Learning (AI/ML)',
  'Data Science & Analytics',
  'Information Technology (IT)',
  'Electronics & Communication Engineering (ECE)',
  'Electrical & Electronics Engineering (EEE)',
  'Mechanical Engineering',
  'Civil Engineering',
  'Robotics & Automation',
  'Biotechnology / Biomedical',
  'Aerospace & Aeronautical',
  'Chemical Engineering',
  'Master of Computer Applications (MCA)',
  'Management Studies / MBA / BBA',
  'Agricultural Engineering & Food Tech',
  'Design & Human-Computer Interaction'
];

export default function DepartmentSelector({
  selectedDepartment,
  onSelectDepartment,
  label = "College / Department",
  required = false,
  className = "",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const [recentDepts, setRecentDepts] = useState([]);

  const containerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_recent_depts') || '[]');
      if (Array.isArray(saved)) setRecentDepts(saved.slice(0, 3));
    } catch {}
  }, []);

  const filteredDepartments = useMemo(() => {
    if (!search.trim()) return COMMON_DEPARTMENTS;
    const q = search.toLowerCase().trim();
    return COMMON_DEPARTMENTS.filter(d => d.toLowerCase().includes(q));
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
      setActiveIndex(prev => (prev < filteredDepartments.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : filteredDepartments.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < filteredDepartments.length) {
        handleSelect(filteredDepartments[activeIndex]);
      } else if (search.trim()) {
        handleSelect(search.trim());
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (dept) => {
    onSelectDepartment(dept);
    setIsOpen(false);
    setSearch('');
    setActiveIndex(-1);

    try {
      const updated = [dept, ...recentDepts.filter(d => d !== dept)].slice(0, 3);
      setRecentDepts(updated);
      localStorage.setItem('yojantra_recent_depts', JSON.stringify(updated));
    } catch {}
  };

  return (
    <div ref={containerRef} className={`relative text-left w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {label} {required && <span className="text-red-500">*</span>}
          </label>
          {selectedDepartment && (
            <button
              type="button"
              onClick={() => onSelectDepartment('')}
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
            ? "bg-white border-indigo-500 ring-2 ring-indigo-500/10 text-slate-800"
            : "bg-white border-slate-300 hover:border-slate-400 text-slate-800"
        }`}
      >
        <div className="flex items-center gap-2 truncate">
          <BookOpen size={16} className="text-indigo-600 shrink-0" />
          <span className={selectedDepartment ? "text-slate-900 font-semibold" : "text-slate-400"}>
            {selectedDepartment || "Select Academic Department"}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-slate-400">
          {selectedDepartment && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                onSelectDepartment('');
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
              placeholder="Search or enter department / branch..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 p-1">
                <X size={14} />
              </button>
            )}
          </div>

          {!search && recentDepts.length > 0 && (
            <div className="px-3 py-2 bg-slate-50/70 border-b border-slate-100 text-[11px]">
              <div className="flex items-center gap-1 text-slate-400 font-semibold mb-1">
                <Clock size={11} /> Recent:
              </div>
              <div className="flex flex-wrap gap-1">
                {recentDepts.map(d => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => handleSelect(d)}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 hover:border-indigo-400 hover:text-indigo-700 transition-colors"
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="max-h-60 overflow-y-auto p-1.5 divide-y divide-slate-50">
            {filteredDepartments.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                <p>No matching preset department found.</p>
                {search.trim() && (
                  <button
                    type="button"
                    onClick={() => handleSelect(search.trim())}
                    className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 font-semibold text-xs hover:bg-indigo-100"
                  >
                    Use "{search.trim()}"
                  </button>
                )}
              </div>
            ) : (
              filteredDepartments.map((d, idx) => {
                const isSelected = selectedDepartment === d;
                const isKeyboardActive = activeIndex === idx;
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => handleSelect(d)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-xl transition-colors text-left ${
                      isSelected
                        ? "bg-slate-900 text-white font-bold"
                        : isKeyboardActive
                        ? "bg-indigo-50 text-indigo-900 font-semibold"
                        : "text-slate-700 hover:bg-slate-100 font-medium"
                    }`}
                  >
                    <span>{d}</span>
                    {isSelected && <Check size={14} className="text-indigo-400 shrink-0" />}
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
