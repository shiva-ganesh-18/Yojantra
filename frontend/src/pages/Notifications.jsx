import React, { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { useAuthStore } from '../hooks/useAuth';
import { 
  Bell, CheckCircle2, AlertCircle, FileText, Sparkles, 
  Check, Filter, ArrowLeft, Trash2, Clock
} from 'lucide-react';
import { Link } from 'react-router-dom';
import SkeletonLoader from '../components/SkeletonLoader';

export default function Notifications() {
  const { api } = useAuthStore();
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState('all');

  const { data: notifications = [], isLoading } = useQuery('notifications_full', () =>
    api().get('/notifications').then(r => r.data || [])
  );

  const markAsRead = async (id) => {
    try {
      await api().put(`/notifications/${id}/read`);
      queryClient.invalidateQueries('notifications_full');
      queryClient.invalidateQueries('notifications');
    } catch (e) {
      console.error(e);
    }
  };

  const markAllRead = async () => {
    try {
      const unread = notifications.filter(n => !n.is_read);
      await Promise.all(unread.map(n => api().put(`/notifications/${n.id}/read`)));
      queryClient.invalidateQueries('notifications_full');
      queryClient.invalidateQueries('notifications');
    } catch (e) {
      console.error(e);
    }
  };

  const categories = [
    { id: 'all', label: 'All Notifications' },
    { id: 'applications', label: 'Applications', keyword: 'application' },
    { id: 'documents', label: 'Documents', keyword: 'document' },
    { id: 'schemes', label: 'Schemes', keyword: 'scheme' },
    { id: 'system', label: 'System', keyword: 'system' },
  ];

  const filtered = notifications.filter(n => {
    if (selectedCategory === 'all') return true;
    const text = (n.title + ' ' + (n.body || '') + ' ' + (n.type || '')).toLowerCase();
    const cat = categories.find(c => c.id === selectedCategory);
    return cat ? text.includes(cat.keyword) : true;
  });

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-gov">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-2 rounded-xl bg-gov-navy-100 text-gov-navy-900">
              <Bell size={20} />
            </span>
            <h1 className="text-xl sm:text-2xl font-bold text-gov-navy-950">Notification Center</h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500">
            Real-time updates regarding your scheme eligibility, document verification, and official submissions.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs sm:text-sm font-semibold transition-colors"
          >
            <Check size={16} />
            <span>Mark All as Read</span>
          </button>
        )}
      </div>

      {/* Categories Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar">
        {categories.map(c => {
          const count = c.id === 'all' 
            ? notifications.length 
            : notifications.filter(n => (n.title + ' ' + (n.body || '')).toLowerCase().includes(c.keyword)).length;

          return (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium whitespace-nowrap transition-all flex items-center gap-1.5 border ${
                selectedCategory === c.id
                  ? 'bg-gov-navy-900 text-white border-gov-navy-900 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>{c.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedCategory === c.id ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'
              }`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="space-y-3">
          <SkeletonLoader.Card lines={2} />
          <SkeletonLoader.Card lines={2} />
          <SkeletonLoader.Card lines={2} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-gov">
          <Bell size={48} className="mx-auto text-slate-300 mb-3" />
          <h3 className="text-base font-bold text-gov-navy-900">No notifications in this category</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            You're all caught up! As government ministries review your filings or match new schemes, updates will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(n => (
            <div
              key={n.id}
              onClick={() => !n.is_read && markAsRead(n.id)}
              className={`bg-white rounded-xl p-4 sm:p-5 border transition-all shadow-gov flex items-start gap-4 ${
                !n.is_read
                  ? 'border-gov-saffron-300/80 bg-gradient-to-r from-gov-saffron-50/20 via-white to-white'
                  : 'border-slate-200/80 hover:border-slate-300'
              }`}
            >
              <div className={`p-2.5 rounded-xl flex-shrink-0 ${
                !n.is_read ? 'bg-gov-saffron-100 text-gov-saffron-700' : 'bg-slate-100 text-slate-600'
              }`}>
                <Bell size={18} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h3 className={`text-sm sm:text-base font-bold ${!n.is_read ? 'text-gov-navy-950' : 'text-slate-800'}`}>
                      {n.title}
                    </h3>
                    {!n.is_read && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-saffron-500 text-white">
                        New
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-400 font-medium flex items-center gap-1 flex-shrink-0">
                    <Clock size={12} />
                    {n.created_at ? new Date(n.created_at).toLocaleDateString() : 'Today'}
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed">
                  {n.body}
                </p>

                {/* Contextual links based on notification text */}
                <div className="flex items-center gap-3 mt-3 pt-2 border-t border-slate-100">
                  {n.title?.toLowerCase().includes('application') && (
                    <Link to="/applications" className="text-xs font-semibold text-gov-navy-800 hover:text-gov-saffron-700">
                      View Application Tracking &rarr;
                    </Link>
                  )}
                  {n.title?.toLowerCase().includes('scheme') && (
                    <Link to="/matches" className="text-xs font-semibold text-gov-navy-800 hover:text-gov-saffron-700">
                      View Scheme Matches &rarr;
                    </Link>
                  )}
                  {n.title?.toLowerCase().includes('document') && (
                    <Link to="/documents" className="text-xs font-semibold text-gov-navy-800 hover:text-gov-saffron-700">
                      Go to Document Center &rarr;
                    </Link>
                  )}
                  {!n.is_read && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markAsRead(n.id);
                      }}
                      className="text-xs text-slate-400 hover:text-slate-600 ml-auto font-medium"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
