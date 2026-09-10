import React from 'react';

/**
 * LoadingSkeleton component supporting card, table, list, text, and avatar variants.
 */
export const LoadingSkeleton = ({ variant = 'card', count = 1, className = '' }) => {
  const items = Array.from({ length: count });

  if (variant === 'card') {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
        {items.map((_, i) => (
          <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="h-6 w-24 bg-slate-200 rounded-full"></div>
              <div className="h-5 w-16 bg-slate-200 rounded-full"></div>
            </div>
            <div className="h-6 w-3/4 bg-slate-200 rounded mb-3"></div>
            <div className="h-4 w-full bg-slate-100 rounded mb-2"></div>
            <div className="h-4 w-2/3 bg-slate-100 rounded mb-6"></div>
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <div className="h-5 w-20 bg-slate-200 rounded"></div>
              <div className="h-8 w-24 bg-slate-200 rounded-lg"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className={`space-y-3 ${className}`}>
        {items.map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4 animate-pulse">
            <div className="w-10 h-10 rounded-lg bg-slate-200 shrink-0"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded w-1/3"></div>
              <div className="h-3 bg-slate-100 rounded w-1/2"></div>
            </div>
            <div className="h-8 w-20 bg-slate-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className={`w-full bg-white rounded-xl border border-slate-200 overflow-hidden ${className}`}>
        <div className="h-12 bg-slate-100 border-b border-slate-200 animate-pulse"></div>
        {items.map((_, i) => (
          <div key={i} className="h-14 border-b border-slate-100 flex items-center px-6 gap-6 animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-1/4"></div>
            <div className="h-4 bg-slate-100 rounded w-1/4"></div>
            <div className="h-4 bg-slate-200 rounded w-1/6"></div>
            <div className="h-4 bg-slate-100 rounded w-1/6 ml-auto"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-2 animate-pulse ${className}`}>
      {items.map((_, i) => (
        <div key={i} className="h-4 bg-slate-200 rounded w-full"></div>
      ))}
    </div>
  );
};

export default LoadingSkeleton;
