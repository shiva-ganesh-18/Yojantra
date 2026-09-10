import React from 'react';
import { SearchX, ArrowRight, RefreshCw } from 'lucide-react';

/**
 * Reusable EmptyState component with contextual action and illustration.
 */
export const EmptyState = ({
  icon: Icon = SearchX,
  title = 'No Results Found',
  description = 'Try adjusting your filters, searching with different terms, or resetting your selection.',
  actionText,
  onAction,
  secondaryText,
  onSecondary,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm ${className}`}>
      <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 mb-4 shadow-inner">
        <Icon className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 max-w-md mb-6 leading-relaxed">
        {description}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {actionText && onAction && (
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white text-sm font-semibold shadow-sm transition-colors"
          >
            {actionText}
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
        {secondaryText && onSecondary && (
          <button
            onClick={onSecondary}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            {secondaryText}
          </button>
        )}
      </div>
    </div>
  );
};

export default EmptyState;
