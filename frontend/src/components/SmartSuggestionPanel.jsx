import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Award, Zap, Building } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * SmartSuggestionPanel: Contextual intelligence panel guiding user to personalized schemes,
 * problem statements, and nodal institutions.
 */
export const SmartSuggestionPanel = ({
  userState = 'National',
  onSelectAction,
  className = '',
}) => {
  const navigate = useNavigate();

  const suggestions = [
    {
      id: 'mudra',
      badge: 'Top Micro-Credit',
      title: 'Pradhan Mantri MUDRA Yojana',
      org: 'Up to ₹10 Lakhs Collateral-Free Credit',
      actionText: 'Check Eligibility',
      link: '/schemes',
      icon: ShieldCheck,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
    {
      id: 'standup',
      badge: 'Targeted Support',
      title: 'Stand-Up India Scheme',
      org: 'SC/ST & Women Entrepreneurs',
      actionText: 'View Benefits',
      link: '/matches',
      icon: Award,
      color: 'text-orange-600 bg-orange-50 border-orange-100',
    },
    {
      id: 'csc-locate',
      badge: 'Offline Assistance',
      title: 'Common Service Centers (CSC)',
      org: `Find village-level kiosk & channel partner in ${userState}`,
      actionText: 'Locate CSC',
      link: '/csc-locator',
      icon: Building,
      color: 'text-sky-600 bg-sky-50 border-sky-100',
    },
  ];

  return (
    <div className={`bg-gradient-to-r from-orange-50/70 via-white to-amber-50/70 rounded-3xl border border-orange-100/90 p-6 shadow-xs ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-orange-500 text-white flex items-center justify-center shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Yojantra Smart Suggestions</h3>
            <p className="text-[11px] text-slate-500">Personalized opportunities in {userState}</p>
          </div>
        </div>
        <span className="text-[11px] font-bold text-orange-600 uppercase tracking-wider">
          AI Guided
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {suggestions.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.id}
              className="bg-white/90 backdrop-blur rounded-2xl border border-slate-200/80 p-4 hover:border-orange-300 hover:shadow-sm transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${item.color}`}>
                    {item.badge}
                  </span>
                  <Icon className="w-4 h-4 text-slate-400" />
                </div>
                <h4 className="text-xs font-bold text-slate-900 leading-snug mb-1">
                  {item.title}
                </h4>
                <p className="text-[11px] text-slate-500 leading-normal">
                  {item.org}
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  if (onSelectAction) onSelectAction(item);
                  else navigate(item.link);
                }}
                className="mt-3.5 inline-flex items-center gap-1.5 text-xs font-bold text-orange-600 hover:text-orange-700 transition-colors"
              >
                <span>{item.actionText}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SmartSuggestionPanel;
