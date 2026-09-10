import React from 'react';
import { X } from 'lucide-react';

/**
 * FilterChips: Accessible horizontal chips for instant category, stage, and tag filtering.
 */
export const FilterChips = ({
  options = [], // [{ id, label, count, icon: Icon }]
  selected, // single id or array of ids
  onChange,
  isMulti = false,
  onClear,
  className = '',
}) => {
  const isSelected = (id) => {
    if (isMulti) {
      return Array.isArray(selected) && selected.includes(id);
    }
    return selected === id;
  };

  const handleToggle = (id) => {
    if (isMulti) {
      const arr = Array.isArray(selected) ? [...selected] : [];
      const idx = arr.indexOf(id);
      if (idx > -1) {
        arr.splice(idx, 1);
      } else {
        arr.push(id);
      }
      onChange(arr);
    } else {
      onChange(selected === id ? null : id);
    }
  };

  const hasSelection = isMulti
    ? Array.isArray(selected) && selected.length > 0
    : selected !== null && selected !== undefined && selected !== '';

  return (
    <div className={`flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin ${className}`}>
      {options.map((opt) => {
        const active = isSelected(opt.id);
        const Icon = opt.icon;

        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => handleToggle(opt.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold shrink-0 transition-all ${
              active
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
            }`}
          >
            {Icon && <Icon className={`w-3.5 h-3.5 ${active ? 'text-orange-400' : 'text-slate-400'}`} />}
            <span>{opt.label}</span>
            {opt.count !== undefined && (
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                  active ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {opt.count}
              </span>
            )}
          </button>
        );
      })}

      {hasSelection && onClear && (
        <button
          type="button"
          onClick={onClear}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-semibold text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors shrink-0"
          title="Clear all filters"
        >
          <X className="w-3.5 h-3.5" />
          <span>Clear</span>
        </button>
      )}
    </div>
  );
};

export default FilterChips;
