import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  Home, Search, Sparkles, FileText, FolderUp, MessageSquare, 
  MapPin, Bell, User, ShieldCheck, LogOut, Menu, X, ChevronRight,
  Building2, Users, BookOpen, Globe, Compass, Flame, Award, Languages
} from 'lucide-react';
import NotificationBell from './NotificationBell';
import SearchCommand from './SearchCommand';
import IndiaLocationCommand from './IndiaLocationCommand';

export default function Layout({ children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchCommandOpen, setSearchCommandOpen] = useState(false);
  const [locationCommandOpen, setLocationCommandOpen] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);

  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { language, setLanguage, t, supportedLanguages } = useLanguage();

  const isOfficerOrAdmin = ['admin', 'super_admin', 'partner_officer', 'nodal_officer'].includes(user?.role);

  // Load saved location if any
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('yojantra_user_hierarchy') || 'null');
      if (saved) setCurrentLocation(saved);
    } catch {}
  }, []);

  // Global Ctrl+K / Cmd+K shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setSearchCommandOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Citizen / Entrepreneur Navigation
  const citizenNavItems = [
    { path: '/', icon: Home, label: t('nav_dashboard', 'Dashboard') },
    { path: '/schemes', icon: Search, label: t('nav_find_schemes', 'Find Schemes') },
    { path: '/matches', icon: Sparkles, label: t('nav_matches', 'My Matches'), badge: 'AI' },
    { path: '/applications', icon: FileText, label: t('nav_applications', 'Applications') },
    { path: '/documents', icon: FolderUp, label: t('nav_documents', 'Documents') },
    { path: '/csc', icon: MapPin, label: t('nav_csc_locator', 'CSC Locator') },
    { path: '/institutions', icon: Building2, label: t('nav_channel_partners', 'Channel Partners') },
  ];

  const assistanceNavItems = [
    { path: '/chat', icon: MessageSquare, label: t('nav_ai_chat', 'Yojantra AI Chat') },
  ];

  const bottomNavItems = [
    { path: '/', icon: Home, label: t('nav_dashboard', 'Home') },
    { path: '/schemes', icon: Search, label: t('nav_find_schemes', 'Schemes') },
    { path: '/matches', icon: Sparkles, label: t('nav_matches', 'Matches') },
    { path: '/documents', icon: FolderUp, label: t('nav_documents', 'Documents') },
    { path: '/applications', icon: FileText, label: t('nav_applications', 'Applications') },
    { path: '/chat', icon: MessageSquare, label: t('nav_ai_chat', 'AI Chat') },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    // Use exact match for short paths to avoid /csc matching /csc-locator
    if (path.length <= 5) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* WCAG 2.1 AA Accessible Skip-to-content Link */}
      <a href="#main-content" className="skip-to-content">
        {t('a11y_skip_to_content', 'Skip to main content')}
      </a>

      {/* Search Command Palette (Ctrl+K) */}
      <SearchCommand
        isOpen={searchCommandOpen}
        onClose={() => setSearchCommandOpen(false)}
      />

      {/* Location Navigator Modal */}
      {locationCommandOpen && (
        <div 
          role="dialog" 
          aria-modal="true" 
          aria-label={t('nav_india_navigator', 'India Navigator')} 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in"
        >
          <IndiaLocationCommand
            initialState={currentLocation?.state || user?.state || ''}
            initialDistrict={currentLocation?.district || user?.district || ''}
            initialCity={currentLocation?.city || ''}
            initialInstitution={currentLocation?.institution || null}
            initialDepartment={currentLocation?.department || ''}
            onComplete={(loc) => {
              setCurrentLocation(loc);
              localStorage.setItem('yojantra_user_hierarchy', JSON.stringify(loc));
              setLocationCommandOpen(false);
            }}
            onClose={() => setLocationCommandOpen(false)}
          />
        </div>
      )}

      {/* Top Bar for Desktop and Mobile */}
      <header role="banner" className="sticky top-0 z-40 bg-slate-950 text-white border-b border-slate-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          
          {/* Logo Brand Treatment */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-900 transition-colors focus-visible:ring-2 focus-visible:ring-orange-500"
              aria-label={mobileMenuOpen ? t('a11y_close', 'Close') : t('a11y_toggle_menu', 'Toggle navigation menu')}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation-drawer"
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            <Link to="/" className="flex items-center gap-2.5 group focus-visible:ring-2 focus-visible:ring-orange-500 rounded-xl p-1">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-slate-800 via-orange-500 to-amber-400 p-0.5 shadow-sm">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center font-black text-sm tracking-tight text-white">
                  Y
                </div>
              </div>
              <div className="flex flex-col text-left">
                <span className="font-extrabold text-base sm:text-lg tracking-tight text-white group-hover:text-orange-300 transition-colors">
                  Yojantra
                </span>
                <span className="text-[10px] font-medium text-slate-400 hidden sm:block tracking-normal">
                  National Schemes & Innovation Engine
                </span>
              </div>
            </Link>
          </div>

          {/* Center: Global Search Bar Trigger (Search Yojantra) */}
          <div className="hidden md:flex flex-1 max-w-md mx-2">
            <button
              type="button"
              onClick={() => setSearchCommandOpen(true)}
              aria-label={t('a11y_open_search', 'Open search palette')}
              className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 text-slate-400 text-xs shadow-inner transition-all group focus-visible:ring-2 focus-visible:ring-orange-500"
            >
              <div className="flex items-center gap-2 truncate">
                <Search size={14} className="text-slate-400 group-hover:text-orange-400 transition-colors flex-shrink-0" />
                <span className="truncate">{t('nav_search_trigger', 'Search Schemes, Subsidies, Channel Partners...')}</span>
              </div>
              <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-400 border border-slate-700 flex-shrink-0">
                Ctrl K
              </kbd>
            </button>
          </div>

          {/* Right Area: Location Switcher, Language Selector, Notifications & User Profile */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* Quick Location Button */}
            <button
              type="button"
              onClick={() => setLocationCommandOpen(true)}
              aria-label={t('a11y_open_location', 'Open location navigator')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition-colors focus-visible:ring-2 focus-visible:ring-orange-500"
              title={t('nav_change_location', 'Change Location')}
            >
              <Globe size={13} className="text-orange-400" />
              <span className="max-w-[110px] truncate hidden sm:inline">
                {currentLocation?.institution?.short_name || currentLocation?.district || currentLocation?.state || '🇮🇳 India'}
              </span>
              <span className="sm:hidden text-xs">🇮🇳</span>
            </button>

            {/* Language Selector Dropdown with Accessible Label & Visible Focus */}
            <div className="relative flex items-center">
              <Languages size={13} className="text-orange-400 absolute left-2.5 pointer-events-none" />
              <label htmlFor="header-language-select" className="sr-only">
                {t('a11y_select_language', 'Select UI Language')}
              </label>
              <select
                id="header-language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                aria-label={t('a11y_select_language', 'Select UI Language')}
                className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl pl-7 pr-3 py-1.5 text-xs font-bold focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 cursor-pointer appearance-none hover:bg-slate-850 transition-colors"
              >
                {supportedLanguages.map((l) => (
                  <option key={l.code} value={l.code} className="bg-slate-950 text-white">
                    {l.label} ({l.englishName})
                  </option>
                ))}
              </select>
            </div>

            <NotificationBell />

            <div className="h-5 w-px bg-slate-800 hidden sm:block" />

            {/* Profile Pill */}
            <Link
              to="/profile"
              aria-label={t('nav_profile', 'Profile')}
              className="flex items-center gap-2 p-1 sm:px-2.5 sm:py-1.5 rounded-xl hover:bg-slate-900 transition-colors border border-transparent hover:border-slate-800 focus-visible:ring-2 focus-visible:ring-orange-500"
            >
              <div className="w-8 h-8 rounded-full bg-orange-600 text-white font-bold flex items-center justify-center text-xs shadow-inner uppercase">
                {user?.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-bold text-white leading-tight">
                  {user?.full_name ? user.full_name.split(' ')[0] : t('guest_citizen', 'Citizen')}
                </span>
                <span className="text-[10px] text-slate-400 leading-tight">
                  {user?.role === 'admin' ? t('administrator', 'Administrator') : t('verified_user', 'Verified User')}
                </span>
              </div>
            </Link>

            <button
              onClick={handleLogout}
              aria-label={t('nav_logout', 'Logout')}
              title={t('nav_logout', 'Logout')}
              className="hidden lg:flex p-2 text-slate-400 hover:text-red-400 hover:bg-slate-900 rounded-xl transition-colors focus-visible:ring-2 focus-visible:ring-red-500"
            >
              <LogOut size={18} />
            </button>
          </div>

        </div>
      </header>

      {/* Main Container: Sidebar + Content */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 flex gap-6 lg:gap-8">
        
        {/* Desktop Left Sidebar */}
        <aside aria-label="Desktop Navigation" className="hidden lg:flex flex-col w-64 flex-shrink-0 text-left">
          <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm p-3 sticky top-22 flex flex-col gap-1 max-h-[calc(100vh-6rem)] overflow-y-auto custom-scrollbar">
            
            {/* Citizen & Schemes Section */}
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              {t('nav_govt_schemes', 'Government Schemes')}
            </div>

            {citizenNavItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    active
                      ? 'bg-slate-950 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon size={16} className={active ? 'text-orange-400' : 'text-slate-400'} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                      active ? 'bg-orange-500 text-white' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* Assistance Section */}
            <div className="mt-3 pt-3 border-t border-slate-100 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              {t('nav_ai_assistance', 'AI Assistance')}
            </div>

            {assistanceNavItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    active
                      ? 'bg-slate-950 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                  }`}
                >
                  <Icon size={16} className={active ? 'text-orange-400' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* Admin & Partner Section */}
            {isOfficerOrAdmin && (
              <>
                <div className="mt-3 pt-3 border-t border-slate-100 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>{user?.role === 'partner_officer' ? t('nav_partner_queue', 'Partner Desk') : user?.role === 'nodal_officer' ? t('nav_nodal_queue', 'Nodal Desk') : t('nav_admin_desk', 'Administration')}</span>
                  <span className="text-[9px] px-1 bg-slate-200 text-slate-700 rounded font-bold">Gov</span>
                </div>
                <Link
                  to="/admin"
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    isActive('/admin')
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <ShieldCheck size={16} className="text-orange-400" />
                  <span>{user?.role === 'partner_officer' ? t('nav_partner_queue', 'Partner Queue') : user?.role === 'nodal_officer' ? t('nav_nodal_queue', 'Nodal Queue') : t('nav_admin_desk', 'Admin & Partner Desk')}</span>
                </Link>
              </>
            )}

            {/* Location Hierarchy Trigger Card */}
            <div className="mt-3 p-3 bg-gradient-to-br from-slate-50 to-orange-50/40 border border-slate-200/80 rounded-2xl">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-bold text-slate-800 flex items-center gap-1">
                  <span>🇮🇳</span> {t('nav_india_navigator', 'India Navigator')}
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mb-2 leading-relaxed">
                {t('nav_india_navigator_sub', 'State, District, City & College hierarchy selector.')}
              </p>
              <button
                type="button"
                onClick={() => setLocationCommandOpen(true)}
                className="w-full py-1.5 rounded-lg bg-white border border-slate-200 text-[11px] font-bold text-slate-700 hover:border-orange-400 hover:text-orange-600 transition-colors shadow-2xs focus-visible:ring-2 focus-visible:ring-orange-500"
              >
                {t('nav_open_navigator', 'Open Navigator')}
              </button>
            </div>

          </div>
        </aside>

        {/* Main Content Area with Landmark Role & Skip Target */}
        <main id="main-content" tabIndex="-1" role="main" aria-label="Main Content" className="flex-1 min-w-0 pb-20 lg:pb-8 focus:outline-none">
          {children}
        </main>

      </div>

      {/* Mobile Slide-Over Drawer with accessible dialog role */}
      {mobileMenuOpen && (
        <div 
          id="mobile-navigation-drawer"
          role="dialog" 
          aria-modal="true" 
          aria-label={t('a11y_toggle_menu', 'Mobile Navigation')} 
          className="fixed inset-0 z-50 lg:hidden text-left"
        >
          <div 
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 max-w-xs w-full bg-white shadow-2xl z-50 p-5 flex flex-col justify-between overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-950 text-white flex items-center justify-center font-bold text-xs">
                    Y
                  </div>
                  <span className="font-bold text-slate-950">Yojantra</span>
                </div>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  aria-label={t('a11y_close', 'Close')}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-700 focus-visible:ring-2 focus-visible:ring-orange-500"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Mobile Language Selector inside drawer */}
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <label htmlFor="mobile-language-select" className="text-[11px] font-bold text-slate-600 block mb-1">
                  {t('a11y_select_language', 'Select Language')}
                </label>
                <select
                  id="mobile-language-select"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full bg-white text-slate-800 border border-slate-300 rounded-lg p-2 text-xs font-bold focus-visible:ring-2 focus-visible:ring-orange-500"
                >
                  {supportedLanguages.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.label} ({l.englishName})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mobile search bar trigger */}
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  setSearchCommandOpen(true);
                }}
                className="w-full flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500 focus-visible:ring-2 focus-visible:ring-orange-500"
              >
                <Search size={15} />
                <span className="truncate">{t('nav_search_trigger', 'Search Schemes, Subsidies...')}</span>
              </button>

              {/* Citizen Links */}
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3">
                  {t('nav_govt_schemes', 'Schemes')}
                </span>
                {citizenNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 min-h-[44px] rounded-xl text-xs font-semibold focus-visible:ring-2 focus-visible:ring-orange-500 ${
                        active ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <Icon size={16} className={active ? 'text-orange-400' : 'text-slate-400'} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>

              {/* AI Assistance Section */}
              <div className="pt-3 mt-3 border-t border-slate-100 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3">
                  {t('nav_ai_assistance', 'AI Assistance')}
                </span>
                {assistanceNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 min-h-[44px] rounded-xl text-xs font-semibold focus-visible:ring-2 focus-visible:ring-orange-500 ${
                        active ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <Icon size={16} className={active ? 'text-orange-400' : 'text-slate-400'} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>

              {/* Admin & Partner Section */}
              {isOfficerOrAdmin && (
                <div className="pt-3 mt-3 border-t border-slate-100 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 flex items-center justify-between">
                    <span>{user?.role === 'partner_officer' ? t('nav_partner_queue', 'Partner Desk') : user?.role === 'nodal_officer' ? t('nav_nodal_queue', 'Nodal Desk') : t('nav_admin_desk', 'Administration')}</span>
                    <span className="text-[9px] px-1 bg-slate-200 text-slate-700 rounded font-bold">Gov</span>
                  </span>
                  <Link
                    to="/admin"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 min-h-[44px] rounded-xl text-xs font-semibold focus-visible:ring-2 focus-visible:ring-orange-500 ${
                      isActive('/admin')
                        ? 'bg-slate-900 text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <ShieldCheck size={16} className="text-orange-400" />
                    <span>{user?.role === 'partner_officer' ? t('nav_partner_queue', 'Partner Queue') : user?.role === 'nodal_officer' ? t('nav_nodal_queue', 'Nodal Queue') : t('nav_admin_desk', 'Admin & Partner Desk')}</span>
                  </Link>
                </div>
              )}

              {/* Location Hierarchy Trigger Card */}
              <div className="pt-3 mt-3 border-t border-slate-100">
                <div className="p-3 bg-gradient-to-br from-slate-50 to-orange-50/40 border border-slate-200/80 rounded-2xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-bold text-slate-800 flex items-center gap-1">
                      <span>🇮🇳</span> {t('nav_india_navigator', 'India Navigator')}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 mb-2 leading-relaxed">
                    {t('nav_india_navigator_sub', 'State, District, City & College hierarchy selector.')}
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setLocationCommandOpen(true);
                      setMobileMenuOpen(false);
                    }}
                    className="w-full py-1.5 rounded-lg bg-white border border-slate-200 text-[11px] font-bold text-slate-700 hover:border-orange-400 hover:text-orange-600 transition-colors shadow-2xs focus-visible:ring-2 focus-visible:ring-orange-500"
                  >
                    {t('nav_open_navigator', 'Open Navigator')}
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 p-3 min-h-[44px] rounded-xl bg-red-50 text-red-700 text-xs font-bold hover:bg-red-100 transition-colors focus-visible:ring-2 focus-visible:ring-red-500"
              >
                <LogOut size={16} />
                <span>{t('nav_logout', 'Log Out')}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation Bar with WCAG min-touch target & navigation landmark */}
      <nav role="navigation" aria-label="Mobile Bottom Navigation" className="fixed bottom-0 left-0 right-0 z-40 lg:hidden bg-white/95 backdrop-blur-md border-t border-slate-200 shadow-lg px-2 py-1.5 flex justify-around">
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center py-1 px-3 min-h-[44px] rounded-xl text-center transition-all focus-visible:ring-2 focus-visible:ring-orange-500 ${
                active 
                  ? 'text-slate-950 font-bold scale-105' 
                  : 'text-slate-500 hover:text-slate-800 font-medium'
              }`}
            >
              <div className={`p-1 rounded-lg ${active ? 'bg-slate-100 text-slate-950' : ''}`}>
                <Icon size={19} />
              </div>
              <span className="text-[10px] mt-0.5">{item.label}</span>
            </Link>
          );
        })}
      </nav>

    </div>
  );
}
