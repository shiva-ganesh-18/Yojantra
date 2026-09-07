import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { 
  Home, Search, Sparkles, FileText, FolderUp, MessageSquare, 
  MapPin, Bell, User, ShieldCheck, LogOut, Menu, X, ChevronRight,
  ExternalLink, Building2, CheckCircle2
} from 'lucide-react';
import NotificationBell from './NotificationBell';

export default function Layout({ children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/schemes', icon: Search, label: 'Find Schemes' },
    { path: '/matches', icon: Sparkles, label: 'My Matches', badge: 'AI' },
    { path: '/applications', icon: FileText, label: 'Applications' },
    { path: '/documents', icon: FolderUp, label: 'Documents' },
    { path: '/chat', icon: MessageSquare, label: 'AI Assistant' },
    { path: '/csc', icon: MapPin, label: 'CSC Locator' },
    { path: '/notifications', icon: Bell, label: 'Notifications' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  const adminNavItems = [
    { path: '/admin', icon: ShieldCheck, label: 'Admin Console' },
  ];

  const bottomNavItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/matches', icon: Sparkles, label: 'Matches' },
    { path: '/schemes', icon: Search, label: 'Schemes' },
    { path: '/applications', icon: FileText, label: 'Apply' },
    { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
      {/* Top Bar for Desktop and Mobile */}
      <header className="sticky top-0 z-40 bg-gov-navy-950 text-white border-b border-gov-navy-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo Brand Treatment */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-gov-navy-900 transition-colors"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            <Link to="/" className="flex items-center gap-2.5 group">
              {/* Emblem / Badge */}
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-gov-navy-800 via-gov-saffron-600 to-gov-emerald-500 p-0.5 shadow-sm">
                <div className="w-full h-full bg-gov-navy-950 rounded-[10px] flex items-center justify-center font-black text-sm tracking-tighter text-white">
                  <span className="text-gov-saffron-400">S</span>
                  <span className="text-gov-emerald-400">M</span>
                </div>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-base sm:text-lg tracking-tight text-white group-hover:text-gov-saffron-300 transition-colors">
                    SchemeMatch
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-extrabold bg-gov-saffron-500/20 text-gov-saffron-300 border border-gov-saffron-500/30 tracking-wider">
                    AI
                  </span>
                </div>
                <span className="text-[10px] font-medium text-slate-400 hidden sm:block tracking-normal">
                  National Entrepreneurship & Welfare Gateway
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Top Nav Quick Access */}
          <div className="hidden md:flex items-center gap-1 text-xs font-semibold text-slate-300">
            <Link to="/" className={`px-3 py-1.5 rounded-lg transition-colors ${location.pathname === '/' ? 'text-white bg-gov-navy-800' : 'hover:text-white hover:bg-gov-navy-900'}`}>
              Dashboard
            </Link>
            <Link to="/schemes" className={`px-3 py-1.5 rounded-lg transition-colors ${location.pathname === '/schemes' ? 'text-white bg-gov-navy-800' : 'hover:text-white hover:bg-gov-navy-900'}`}>
              Schemes
            </Link>
            <Link to="/applications" className={`px-3 py-1.5 rounded-lg transition-colors ${location.pathname === '/applications' ? 'text-white bg-gov-navy-800' : 'hover:text-white hover:bg-gov-navy-900'}`}>
              Applications
            </Link>
          </div>

          {/* Right Area: Notifications & User Profile */}
          <div className="flex items-center gap-3">
            <NotificationBell />

            <div className="h-6 w-px bg-gov-navy-800 hidden sm:block" />

            {/* Profile Dropdown / Pill */}
            <Link
              to="/profile"
              className="flex items-center gap-2.5 p-1 sm:px-2.5 sm:py-1.5 rounded-xl hover:bg-gov-navy-900 transition-colors border border-transparent hover:border-gov-navy-800"
            >
              <div className="w-8 h-8 rounded-full bg-gov-saffron-600 text-white font-bold flex items-center justify-center text-xs shadow-inner uppercase">
                {user?.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-bold text-white leading-tight">
                  {user?.full_name ? user.full_name.split(' ')[0] : 'User'}
                </span>
                <span className="text-[10px] text-slate-400 leading-tight">
                  {user?.district ? `${user.district}` : 'Citizen'}
                </span>
              </div>
            </Link>

            <button
              onClick={handleLogout}
              aria-label="Logout"
              title="Logout"
              className="hidden lg:flex p-2 text-slate-400 hover:text-red-400 hover:bg-gov-navy-900 rounded-xl transition-colors"
            >
              <LogOut size={18} />
            </button>
          </div>

        </div>
      </header>

      {/* Main Container: Sidebar + Content */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 flex gap-6 lg:gap-8">
        
        {/* Desktop Left Sidebar */}
        <aside className="hidden lg:flex flex-col w-64 flex-shrink-0">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-gov p-3 sticky top-22 flex flex-col gap-1">
            
            <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Navigation
            </div>

            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    active
                      ? 'bg-gov-navy-950 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-gov-navy-950'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={17} className={active ? 'text-gov-saffron-400' : 'text-slate-400'} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full ${
                      active ? 'bg-gov-saffron-500 text-white' : 'bg-gov-emerald-100 text-gov-emerald-800'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* Admin Section (Strictly role-gated) */}
            {isAdmin && (
              <>
                <div className="mt-3 pt-3 border-t border-slate-100 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>Administration</span>
                  <span className="text-[9px] px-1 bg-slate-200 text-slate-600 rounded">Gov</span>
                </div>
                {adminNavItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                        active
                          ? 'bg-slate-800 text-white shadow-sm'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }`}
                    >
                      <Icon size={17} className={active ? 'text-gov-saffron-400' : 'text-slate-400'} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </>
            )}

            {/* Help & Support Helpline Callout */}
            <div className="mt-4 p-3 bg-gradient-to-br from-gov-navy-50 to-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-gov-navy-950 flex items-center gap-1.5">
                <Building2 size={13} className="text-gov-saffron-600" />
                CSC Citizen Helpline
              </p>
              <p className="text-[10px] text-slate-500 mt-1 leading-snug">
                Need application assistance? Locate a CSC or dial 1800-3000-3468.
              </p>
              <Link to="/csc" className="mt-2 inline-flex items-center gap-1 text-[11px] font-bold text-gov-saffron-700 hover:text-gov-saffron-800">
                Find Nearest Center &rarr;
              </Link>
            </div>

          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 pb-20 lg:pb-8">
          {children}
        </main>

      </div>

      {/* Mobile Slide-Over Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className="fixed inset-0 bg-gov-navy-950/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 max-w-xs w-full bg-white shadow-2xl z-50 p-5 flex flex-col justify-between overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-gov-navy-950 text-white flex items-center justify-center font-bold text-xs">
                    SM
                  </div>
                  <span className="font-bold text-gov-navy-950">SchemeMatch AI</span>
                </div>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-700"
                >
                  <X size={20} />
                </button>
              </div>

              {/* User summary in drawer */}
              <div className="p-3 bg-slate-50 rounded-xl flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gov-saffron-600 text-white font-bold flex items-center justify-center text-sm uppercase">
                  {user?.full_name ? user.full_name.charAt(0) : 'U'}
                </div>
                <div className="overflow-hidden">
                  <p className="text-xs font-bold text-gov-navy-950 truncate">{user?.full_name || 'Citizen'}</p>
                  <p className="text-[11px] text-slate-500">{user?.phone || '+91'}</p>
                </div>
              </div>

              {/* Nav links in drawer */}
              <div className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold ${
                        active ? 'bg-gov-navy-950 text-white' : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <Icon size={17} className={active ? 'text-gov-saffron-400' : 'text-slate-400'} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}

                {isAdmin && (
                  <>
                    <div className="pt-3 border-t border-slate-100 px-3 text-[11px] font-bold uppercase text-slate-400">
                      Administration
                    </div>
                    {adminNavItems.map((item) => {
                      const Icon = item.icon;
                      const active = isActive(item.path);
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => setMobileMenuOpen(false)}
                          className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold ${
                            active ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'
                          }`}
                        >
                          <Icon size={17} className={active ? 'text-gov-saffron-400' : 'text-slate-400'} />
                          <span>{item.label}</span>
                        </Link>
                      );
                    })}
                  </>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 p-2.5 rounded-xl bg-red-50 text-red-700 text-xs font-bold hover:bg-red-100 transition-colors"
              >
                <LogOut size={16} />
                <span>Log Out</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation Bar (High Touch-Target) */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 lg:hidden bg-white/95 backdrop-blur-md border-t border-slate-200 shadow-lg px-2 py-1.5 flex justify-around">
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center py-1 px-3 rounded-xl text-center transition-all ${
                active 
                  ? 'text-gov-navy-950 font-bold scale-105' 
                  : 'text-slate-400 hover:text-slate-600 font-medium'
              }`}
            >
              <div className={`p-1 rounded-lg ${active ? 'bg-gov-navy-100 text-gov-navy-950' : ''}`}>
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
