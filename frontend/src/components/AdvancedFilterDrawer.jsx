import React from 'react';
import { X, Filter, RotateCcw, Check } from 'lucide-react';

/**
 * AdvancedFilterDrawer: Slide-over drawer with multi-criteria filters and reset/apply triggers.
 */
export const AdvancedFilterDrawer = ({
  isOpen,
  onClose,
  title = "Advanced Filters",
  children,
  onApply,
  onReset,
  activeCount = 0,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity animate-in fade-in"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600">
                <Filter className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">{title}</h3>
                {activeCount > 0 && (
                  <span className="text-xs text-orange-600 font-semibold">
                    {activeCount} active filter{activeCount > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Filter Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {children}
          </div>

          {/* Actions Footer */}
          <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-3">
            {onReset && (
              <button
                type="button"
                onClick={onReset}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-white text-xs font-bold transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
            {onApply && (
              <button
                type="button"
                onClick={() => {
                  onApply();
                  onClose();
                }}
                className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white text-xs sm:text-sm font-bold shadow-sm transition-all"
              >
                <Check className="w-4 h-4" />
                <span>Apply Filters</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedFilterDrawer;
