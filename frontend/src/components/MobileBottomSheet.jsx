import React, { useEffect } from 'react';
import { X } from 'lucide-react';

/**
 * MobileBottomSheet: Mobile-responsive bottom sheet / drawer with touch handle and spring feel.
 */
export const MobileBottomSheet = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxHeight = 'max-h-[88vh]',
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sheet Content */}
      <div
        className={`relative w-full sm:max-w-xl bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden z-10 flex flex-col ${maxHeight} animate-in slide-in-from-bottom duration-300`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle for touch */}
        <div className="flex justify-center pt-3 pb-1 sm:hidden cursor-grab active:cursor-grabbing">
          <div className="w-12 h-1.5 bg-slate-300 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold text-slate-800">{title}</h3>
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  );
};

export default MobileBottomSheet;
