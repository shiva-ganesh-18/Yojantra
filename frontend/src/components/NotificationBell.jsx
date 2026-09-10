import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { 
  Bell, CheckCircle2, AlertCircle, FileText, Sparkles, 
  ChevronRight, Check, X, ShieldAlert 
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function NotificationBell() {
  const { api } = useAuthStore();
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const res = await api().get('/notifications');
      const list = res.data || [];
      setNotifications(list);
      setUnreadCount(list.filter(n => !n.is_read).length);
    } catch (e) {
      // Silently fail on network transient
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle outside click & Escape key
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function handleEscape(event) {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  const markRead = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      await api().put(`/notifications/${id}/read`);
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const markAllRead = async () => {
    try {
      await api().put('/notifications/read-all');
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const getNotificationIcon = (type, title = '') => {
    const text = (type + ' ' + title).toLowerCase();
    if (text.includes('application') || text.includes('approved') || text.includes('review')) {
      return <FileText size={15} className="text-blue-600" />;
    }
    if (text.includes('document') || text.includes('certificate') || text.includes('aadhaar')) {
      return <AlertCircle size={15} className="text-gov-saffron-600" />;
    }
    if (text.includes('scheme') || text.includes('match')) {
      return <Sparkles size={15} className="text-gov-emerald-600" />;
    }
    return <Bell size={15} className="text-gov-navy-600" />;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setOpen(!open)} 
        aria-label={`${t('a11y_notifications', 'Notifications')}${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        aria-expanded={open}
        aria-haspopup="dialog"
        className="relative p-2 rounded-xl text-slate-200 hover:text-white hover:bg-white/10 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-[-2px] right-[-2px] bg-gov-saffron-500 text-white text-[10px] font-bold h-[18px] min-w-[18px] px-1 rounded-full flex items-center justify-center ring-2 ring-gov-navy-950 animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div 
          role="dialog"
          aria-modal="true"
          aria-label={t('notif_center_title', 'Notifications')}
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden text-gov-navy-900 animate-in fade-in slide-in-from-top-2 duration-150"
        >
          {/* Header */}
          <div className="p-3.5 px-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-gov-navy-900">{t('notif_center_title', 'Notifications')}</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-gov-saffron-100 text-gov-saffron-800">
                  {unreadCount} {t('notif_filter_all', 'new')}
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button 
                onClick={markAllRead} 
                className="text-xs text-gov-saffron-700 hover:text-gov-saffron-800 font-medium flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-orange-500 rounded p-0.5"
              >
                <Check size={13} />
                <span>{t('notif_mark_all_read', 'Mark all read')}</span>
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 custom-scrollbar">
            {notifications.length === 0 ? (
              <div className="py-8 px-4 text-center">
                <Bell size={32} className="mx-auto text-slate-300 mb-2" />
                <p className="text-xs font-semibold text-slate-600">{t('notif_no_new', 'No new notifications')}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">{t('notif_empty_desc', 'We\'ll alert you about scheme matches and application updates.')}</p>
              </div>
            ) : (
              notifications.slice(0, 5).map((n) => (
                <div
                  key={n.id}
                  onClick={() => markRead(n.id)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') markRead(n.id); }}
                  tabIndex={0}
                  role="button"
                  aria-label={n.title}
                  className={`p-3.5 hover:bg-slate-50 transition-colors cursor-pointer flex gap-3 items-start focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    !n.is_read ? 'bg-gov-navy-50/40' : ''
                  }`}
                >
                  <div className="p-2 rounded-xl bg-slate-100 flex-shrink-0 mt-0.5">
                    {getNotificationIcon(n.type, n.title)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-1">
                      <p className={`text-xs font-semibold truncate ${!n.is_read ? 'text-gov-navy-900' : 'text-slate-600'}`}>
                        {n.title}
                      </p>
                      {!n.is_read && (
                        <span className="w-2 h-2 rounded-full bg-gov-saffron-500 flex-shrink-0 mt-1" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5 leading-snug">
                      {n.body}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1 font-medium">
                      {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-slate-50 border-t border-slate-100 text-center">
            <Link 
              to="/notifications" 
              onClick={() => setOpen(false)}
              className="text-xs font-semibold text-gov-navy-800 hover:text-gov-saffron-700 flex items-center justify-center gap-1 transition-colors focus-visible:ring-2 focus-visible:ring-orange-500 rounded p-1"
            >
              <span>{t('notif_view_all', 'View All Notifications')}</span>
              <ChevronRight size={14} />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
