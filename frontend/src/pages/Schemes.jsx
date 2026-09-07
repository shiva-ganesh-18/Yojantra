import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { 
  Search, Filter, Building2, Calendar, ExternalLink, 
  IndianRupee, ChevronRight, Sparkles, ArrowRight, ShieldCheck 
} from 'lucide-react';
import SchemeDetailModal from '../components/SchemeDetailModal';
import SkeletonLoader from '../components/SkeletonLoader';

export default function Schemes() {
  const { api } = useAuthStore();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [selectedScheme, setSelectedScheme] = useState(null);

  const { data: schemes = [], isLoading } = useQuery(['schemes_browse', search, filter], () =>
    api().get('/schemes', { params: { q: search, scheme_type: filter } }).then(r => r.data || [])
  );

  const filters = [
    { value: '', label: 'All Schemes' },
    { value: 'loan', label: 'Bank Loans' },
    { value: 'subsidy', label: 'Capital Subsidies' },
    { value: 'grant', label: 'Grants & Assistance' },
    { value: 'guarantee', label: 'Credit Guarantees' },
  ];

  return (
    <div className="space-y-6 text-left">
      
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-2 rounded-xl bg-gov-navy-100 text-gov-navy-900">
                <Building2 size={20} />
              </span>
              <h1 className="text-2xl font-extrabold text-gov-navy-950">
                National Scheme Directory
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-500">
              Browse official central and state government schemes, guidelines, subsidy rates, and nodal ministries.
            </p>
          </div>
          <span className="self-start sm:self-auto text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
            {schemes.length} Active Schemes Indexed
          </span>
        </div>

        {/* Search Bar */}
        <div className="mt-5 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={19} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by scheme name, ministry, subsidy, or sector (e.g., PMEGP, Mudra, Women)..."
            className="w-full pl-11 pr-4 py-3.5 border border-slate-300 rounded-2xl text-sm sm:text-base text-slate-900 bg-slate-50/50 focus:bg-white focus:border-gov-navy-950 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none transition-all"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex gap-2 overflow-x-auto mt-4 pb-1 custom-scrollbar">
          {filters.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold whitespace-nowrap transition-all border ${
                filter === f.value
                  ? 'bg-gov-navy-950 text-white border-gov-navy-950 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Schemes Grid / List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
          <SkeletonLoader.Card lines={3} />
        </div>
      ) : schemes.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 shadow-gov text-center">
          <Building2 size={48} className="mx-auto text-slate-300 mb-3" />
          <h3 className="text-base font-bold text-gov-navy-950">No schemes found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            We couldn't find any schemes matching "{search}". Try searching for broader terms like "Loan", "MSME", or "Subsidy".
          </p>
          <button
            onClick={() => { setSearch(''); setFilter(''); }}
            className="mt-4 px-5 py-2.5 rounded-xl bg-gov-navy-950 text-white text-xs font-bold"
          >
            Clear Search & Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {schemes.map((scheme) => (
            <div
              key={scheme.id}
              className="bg-white rounded-3xl p-5 sm:p-6 border border-slate-200 hover:border-gov-navy-900/40 hover:shadow-gov-hover transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                      {scheme.ministry || 'Government of India'}
                    </span>
                    <h3 className="font-bold text-base sm:text-lg text-gov-navy-950 mt-0.5 leading-snug">
                      {scheme.name}
                    </h3>
                  </div>

                  <span className="px-2.5 py-1 rounded-xl text-[11px] font-bold bg-gov-navy-50 text-gov-navy-900 border border-gov-navy-200 capitalize flex-shrink-0">
                    {scheme.scheme_type || 'Scheme'}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                  {scheme.description}
                </p>

                {scheme.benefit_description && (
                  <div className="flex items-start gap-2 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <IndianRupee size={15} className="text-gov-saffron-600 flex-shrink-0 mt-0.5" />
                    <p className="text-slate-800 text-[11px] font-medium leading-snug">
                      <strong>Benefit:</strong> {scheme.benefit_description}
                    </p>
                  </div>
                )}

                {scheme.application_deadline && (
                  <div className="flex items-center gap-1.5 text-[11px] text-red-600 font-medium">
                    <Calendar size={13} />
                    <span>Deadline: {new Date(scheme.application_deadline).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => setSelectedScheme(scheme)}
                  className="px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-gov-navy-950 text-xs font-bold transition-colors"
                >
                  View Scheme Details
                </button>

                <div className="flex items-center gap-1.5">
                  {scheme.official_url && (
                    <a
                      href={scheme.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-gov-navy-950 transition-colors"
                      title="Open Official Ministry Portal"
                    >
                      <ExternalLink size={16} />
                    </a>
                  )}

                  <button
                    onClick={() => setSelectedScheme(scheme)}
                    className="px-4 py-2 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1"
                  >
                    <span>Check Eligibility</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scheme Detail Deep-Dive Modal */}
      {selectedScheme && (
        <SchemeDetailModal
          scheme={selectedScheme}
          isOpen={!!selectedScheme}
          onClose={() => setSelectedScheme(null)}
          onApply={async (id) => {
            await api().post('/applications', { scheme_id: id });
          }}
        />
      )}

    </div>
  );
}
