import React from 'react';
import { ChevronRight, Globe, MapPin, Building, GraduationCap, User, RotateCcw } from 'lucide-react';

/**
 * LocationBreadcrumb: Interactive hierarchy breadcrumb for India-scale navigation.
 * Levels: India -> State -> District -> City -> Institution -> Department -> Student
 */
export const LocationBreadcrumb = ({
  state,
  district,
  city,
  institution,
  department,
  student,
  onSelectLevel,
  onResetAll,
  className = '',
}) => {
  const steps = [
    { key: 'india', label: 'India', icon: Globe, value: 'India', active: true },
    { key: 'state', label: 'State / UT', icon: MapPin, value: state, active: !!state },
    { key: 'district', label: 'District', icon: MapPin, value: district, active: !!district },
    { key: 'city', label: 'City / Town', icon: Building, value: city, active: !!city },
    { key: 'institution', label: 'College / Institute', icon: GraduationCap, value: typeof institution === 'object' ? institution?.name || institution?.short_name : institution, active: !!institution },
    { key: 'department', label: 'Department', icon: Building, value: department, active: !!department },
    { key: 'student', label: 'Student / Team', icon: User, value: student, active: !!student },
  ];

  // Only show levels up to the latest selected + 1 available level
  const activeLevels = steps.filter((step, index) => {
    if (index === 0) return true;
    return steps[index - 1].active;
  });

  return (
    <div className={`flex items-center justify-between gap-3 p-3 bg-white/90 backdrop-blur border border-slate-200 rounded-2xl shadow-xs overflow-x-auto text-xs ${className}`}>
      <div className="flex items-center gap-1.5 shrink-0">
        {activeLevels.map((step, idx) => {
          const Icon = step.icon;
          const isLast = idx === activeLevels.length - 1;
          const isConfigured = !!step.value && step.value !== 'India';

          return (
            <React.Fragment key={step.key}>
              {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
              <button
                onClick={() => onSelectLevel && onSelectLevel(step.key)}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all font-medium ${
                  isLast
                    ? 'bg-orange-50 text-orange-700 border border-orange-200/80 font-semibold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
                title={`Jump to ${step.label}`}
              >
                <Icon className={`w-3.5 h-3.5 ${isLast ? 'text-orange-600' : 'text-slate-400'}`} />
                <span className="max-w-[140px] truncate">
                  {step.value || step.label}
                </span>
              </button>
            </React.Fragment>
          );
        })}
      </div>

      {state && onResetAll && (
        <button
          onClick={onResetAll}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors shrink-0 font-medium"
          title="Reset entire hierarchy to All-India"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset</span>
        </button>
      )}
    </div>
  );
};

export default LocationBreadcrumb;
