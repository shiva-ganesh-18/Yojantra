import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { schemeService, institutionsService, cscService } from '../services';
import { 
  Search, X, Sparkles, Building2, ArrowRight, 
  ExternalLink, Command, ShieldCheck, MapPin, Tag
} from 'lucide-react';

export default function SearchCommand({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all'); // 'all' | 'schemes' | 'partners'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState({
    schemes: [],
    partners: []
  });
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setResults({ schemes: [], partners: [] });
    }
  }, [isOpen]);

  // Global keydown listener for Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Debounced search across domains
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults({ schemes: [], partners: [] });
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const [schemesRes, partnersRes] = await Promise.allSettled([
          schemeService.listSchemes({ q: query, page_size: 6 }),
          institutionsService.getInstitutions({ q: query, page_size: 6 })
        ]);

        setResults({
          schemes: schemesRes.status === 'fulfilled' ? schemesRes.value : [],
          partners: partnersRes.status === 'fulfilled' ? partnersRes.value : []
        });
      } catch (err) {
        console.warn('SearchCommand query failed:', err);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const totalResults = results.schemes.length + results.partners.length;

  const handleSelectScheme = (scheme) => {
    onClose();
    navigate(`/schemes?q=${encodeURIComponent(scheme.name)}`);
  };

  const handleSelectPartner = (partner) => {
    onClose();
    navigate(`/institutions?q=${encodeURIComponent(partner.name)}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-gov-navy-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Search Input */}
        <div className="p-4 border-b border-slate-100 flex items-center gap-3 bg-white">
          <Search size={20} className="text-gov-navy-800 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across government schemes, subsidies, and channel partners..."
            className="w-full text-base font-medium text-slate-900 placeholder-slate-400 bg-transparent focus:outline-none"
          />
          {query && (
            <button 
              onClick={() => setQuery('')}
              className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <X size={16} />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 text-[11px] font-mono text-slate-400 bg-slate-100 border border-slate-200 rounded">
            ESC
          </kbd>
        </div>

        {/* Category Filters */}
        <div className="px-4 py-2 border-b border-slate-100 bg-slate-50/70 flex items-center gap-2 overflow-x-auto text-xs font-semibold">
          <button
            onClick={() => setCategory('all')}
            className={`px-3 py-1 rounded-full transition-colors ${category === 'all' ? 'bg-gov-navy-950 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'}`}
          >
            All Results {totalResults > 0 && `(${totalResults})`}
          </button>
          <button
            onClick={() => setCategory('schemes')}
            className={`px-3 py-1 rounded-full transition-colors flex items-center gap-1.5 ${category === 'schemes' ? 'bg-gov-navy-950 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'}`}
          >
            <ShieldCheck size={12} />
            <span>Schemes {results.schemes.length > 0 && `(${results.schemes.length})`}</span>
          </button>
          <button
            onClick={() => setCategory('partners')}
            className={`px-3 py-1 rounded-full transition-colors flex items-center gap-1.5 ${category === 'partners' ? 'bg-gov-navy-950 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'}`}
          >
            <Building2 size={12} />
            <span>Channel Partners {results.partners.length > 0 && `(${results.partners.length})`}</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 divide-y divide-slate-100 space-y-4">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
              <span className="w-6 h-6 border-2 border-gov-navy-900 border-t-transparent rounded-full animate-spin" />
              <span>Searching Yojantra Database...</span>
            </div>
          ) : !query.trim() ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              <p className="font-semibold text-slate-600 text-sm mb-1">Explore Yojantra Schemes</p>
              <p>Type keywords like "Mudra", "PMEGP", "Vishwakarma", "Subsidy", "SC/ST", or "Women"</p>
            </div>
          ) : totalResults === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              <p className="font-semibold text-slate-700 text-sm mb-1">No matches found</p>
              <p>Try searching for a different scheme keyword or partner name.</p>
            </div>
          ) : (
            <>
              {/* Government Schemes Section */}
              {(category === 'all' || category === 'schemes') && results.schemes.length > 0 && (
                <div className="pt-2 text-left">
                  <div className="flex items-center gap-1.5 text-xs font-bold uppercase text-gov-navy-900 mb-2">
                    <ShieldCheck size={14} className="text-gov-emerald-600" />
                    <span>Government Schemes</span>
                  </div>
                  <div className="space-y-1.5">
                    {results.schemes.map((s) => (
                      <div
                        key={s.id}
                        onClick={() => handleSelectScheme(s)}
                        className="p-2.5 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors flex items-center justify-between group"
                      >
                        <div className="truncate">
                          <h4 className="text-xs font-bold text-slate-900 group-hover:text-gov-navy-900 truncate">
                            {s.name}
                          </h4>
                          <p className="text-[11px] text-slate-500 truncate">
                            {s.ministry} • {s.scheme_type || 'Welfare'}
                          </p>
                        </div>
                        <ArrowRight size={14} className="text-slate-300 group-hover:text-gov-navy-900 flex-shrink-0 transition-transform group-hover:translate-x-0.5" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Channel Partners Section */}
              {(category === 'all' || category === 'partners') && results.partners.length > 0 && (
                <div className="pt-2 text-left">
                  <div className="flex items-center gap-1.5 text-xs font-bold uppercase text-gov-navy-900 mb-2">
                    <Building2 size={14} className="text-gov-saffron-600" />
                    <span>Channel Partners & Institutions</span>
                  </div>
                  <div className="space-y-1.5">
                    {results.partners.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => handleSelectPartner(c)}
                        className="p-2.5 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors flex items-center justify-between group"
                      >
                        <div className="truncate">
                          <div className="flex items-center gap-2">
                            <h4 className="text-xs font-bold text-slate-900 group-hover:text-gov-navy-900 truncate">
                              {c.name}
                            </h4>
                            {c.short_name && (
                              <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-100 font-bold text-slate-600">
                                {c.short_name}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-500 truncate flex items-center gap-1">
                            <MapPin size={10} />
                            <span>{c.city || c.district}, {c.state}</span>
                            {c.institution_type && <span>• {c.institution_type}</span>}
                          </p>
                        </div>
                        <ArrowRight size={14} className="text-slate-300 group-hover:text-gov-navy-900 flex-shrink-0 transition-transform group-hover:translate-x-0.5" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>Search Yojantra National Schemes & Partners Database</span>
          <button 
            onClick={onClose}
            className="font-semibold text-slate-500 hover:text-slate-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
