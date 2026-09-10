import React from 'react';
import { Award, ArrowRight, CheckCircle, Sparkles, TrendingUp, BookOpen } from 'lucide-react';

/**
 * RecommendationPanel: Displays top AI-matched recommendations with match percentages and fit criteria.
 */
export const RecommendationPanel = ({
  title = "AI Recommended Opportunities",
  subtitle = "Matched against your profile attributes, skills, and regional location",
  items = [], // [{ id, title, subtitle, score, tags, onAction, actionLabel }]
  onViewAll,
  className = '',
}) => {
  return (
    <div className={`bg-white rounded-3xl border border-slate-200/90 p-6 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            <h3 className="text-base font-bold text-slate-900">{title}</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
        </div>

        {onViewAll && (
          <button
            onClick={onViewAll}
            className="text-xs font-bold text-orange-600 hover:text-orange-700 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
          <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-500">
            Complete your profile or set your location to unlock AI-matched recommendations.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-2xl border border-slate-200/80 hover:border-orange-300 hover:bg-orange-50/20 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-900">{item.title}</span>
                  {item.score && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800">
                      {item.score}% Match
                    </span>
                  )}
                </div>
                {item.subtitle && (
                  <p className="text-xs text-slate-500">{item.subtitle}</p>
                )}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {item.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.2 rounded-md bg-slate-100 text-slate-600 text-[10px] font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {item.onAction && (
                <button
                  type="button"
                  onClick={item.onAction}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-orange-600 hover:bg-orange-700 text-white text-xs font-bold transition-colors shrink-0 shadow-xs"
                >
                  <span>{item.actionLabel || 'Apply'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecommendationPanel;
