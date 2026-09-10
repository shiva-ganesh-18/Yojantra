import React from 'react';
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Reusable ErrorState component with diagnosis and retry action.
 */
export const ErrorState = ({
  title = 'Failed to Load Data',
  message = 'An unexpected error occurred while communicating with the Yojantra server.',
  technicalDetails,
  onRetry,
  className = '',
}) => {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div className={`p-8 rounded-2xl bg-rose-50/70 border border-rose-200 text-center max-w-xl mx-auto shadow-sm ${className}`}>
      <div className="w-14 h-14 rounded-2xl bg-rose-100 flex items-center justify-center text-rose-600 mx-auto mb-4">
        <AlertTriangle className="w-7 h-7" />
      </div>
      <h4 className="text-base font-bold text-rose-900 mb-1.5">{title}</h4>
      <p className="text-sm text-rose-700/90 mb-5 leading-relaxed">{message}</p>

      {technicalDetails && (
        <div className="mb-5 text-left">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1.5 text-xs font-semibold text-rose-800 hover:text-rose-900 mx-auto"
          >
            <span>{showDetails ? 'Hide error details' : 'Show technical error details'}</span>
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {showDetails && (
            <div className="mt-2 p-3 rounded-lg bg-white border border-rose-200 text-xs font-mono text-slate-700 overflow-x-auto">
              {typeof technicalDetails === 'string' ? technicalDetails : JSON.stringify(technicalDetails, null, 2)}
            </div>
          )}
        </div>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold shadow-sm transition-all active:scale-95"
        >
          <RefreshCw className="w-4 h-4" />
          Retry Connection
        </button>
      )}
    </div>
  );
};

export default ErrorState;
