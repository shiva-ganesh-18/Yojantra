import React from 'react';

export function SkeletonBox({ className = '' }) {
  return (
    <div className={`bg-slate-200/80 rounded-lg skeleton-shimmer ${className}`} />
  );
}

export function SkeletonCard({ lines = 3, hasBadge = true }) {
  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-gov space-y-4">
      <div className="flex justify-between items-start">
        <div className="space-y-2 flex-1 mr-4">
          <SkeletonBox className="h-5 w-3/4" />
          <SkeletonBox className="h-3.5 w-1/3" />
        </div>
        {hasBadge && <SkeletonBox className="h-6 w-16 rounded-full" />}
      </div>
      <div className="space-y-2 pt-2">
        {Array.from({ length: lines }).map((_, i) => (
          <SkeletonBox 
            key={i} 
            className={`h-3.5 ${i === lines - 1 ? 'w-1/2' : 'w-full'}`} 
          />
        ))}
      </div>
      <div className="flex gap-3 pt-2">
        <SkeletonBox className="h-9 flex-1 rounded-lg" />
        <SkeletonBox className="h-9 w-10 rounded-lg" />
      </div>
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-gov space-y-2">
          <SkeletonBox className="h-4 w-1/2" />
          <SkeletonBox className="h-7 w-2/3" />
          <SkeletonBox className="h-3 w-3/4" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 4, cols = 4 }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 shadow-gov overflow-hidden">
      <div className="p-4 border-b border-slate-100 flex gap-4 bg-slate-50/50">
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonBox key={i} className="h-4 flex-1" />
        ))}
      </div>
      <div className="divide-y divide-slate-100 p-2">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="p-3 flex gap-4 items-center">
            {Array.from({ length: cols }).map((_, c) => (
              <SkeletonBox key={c} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default {
  Box: SkeletonBox,
  Card: SkeletonCard,
  Stats: SkeletonStats,
  Table: SkeletonTable,
};
