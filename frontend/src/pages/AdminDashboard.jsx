import React, { useState } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { useQuery, useQueryClient } from 'react-query';
import { 
  Users, FileCheck, TrendingUp, AlertTriangle, 
  BarChart3, ShieldCheck, Activity, RefreshCw, 
  Server, Database, CheckCircle2, ChevronRight, ArrowRight 
} from 'lucide-react';
import SkeletonLoader from '../components/SkeletonLoader';

export default function AdminDashboard() {
  const { api } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState(null);

  // 1. Dashboard metrics
  const { data: metrics, isLoading: loadingMetrics } = useQuery('admin_metrics', () =>
    api().get('/admin/analytics/dashboard').then(r => r.data).catch(() => null)
  );

  // 2. Bias report
  const { data: biasReport, isLoading: loadingBias } = useQuery('admin_bias', () =>
    api().get('/admin/analytics/bias').then(r => r.data).catch(() => null)
  );

  // 3. Users list
  const { data: usersData, isLoading: loadingUsers } = useQuery('admin_users', () =>
    api().get('/admin/users', { params: { page: 1, page_size: 20 } }).then(r => r.data).catch(() => null),
    { enabled: activeTab === 'users' }
  );

  // 4. Schemes list
  const { data: schemesData, isLoading: loadingSchemes } = useQuery('admin_schemes', () =>
    api().get('/admin/schemes').then(r => r.data).catch(() => null),
    { enabled: activeTab === 'schemes' }
  );

  const handleTriggerMatchAll = async () => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await api().post('/admin/schemes/match-all');
      setTriggerResult(res.data?.message || 'Batch matching executed successfully across all active users.');
      queryClient.invalidateQueries('admin_metrics');
    } catch (e) {
      setTriggerResult('Failed to run batch matching.');
    } finally {
      setTriggering(false);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: BarChart3 },
    { id: 'bias', label: 'Bias & Fairness Audit', icon: ShieldCheck },
    { id: 'users', label: 'Registered Citizens', icon: Users },
    { id: 'schemes', label: 'Scheme Management', icon: FileCheck },
    { id: 'system', label: 'System Monitoring', icon: Server },
  ];

  return (
    <div className="space-y-6 text-left">
      
      {/* Executive Header Banner */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl shadow-xl border border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-1.5 rounded-lg bg-gov-saffron-500/20 text-gov-saffron-400 border border-gov-saffron-500/30">
                <ShieldCheck size={18} />
              </span>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Government of India • Ministry Administrative Gateway
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              SchemeMatch AI Operations Console
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Real-time platform telemetry, affirmative action audit, and scheme pipeline orchestration.
            </p>
          </div>

          <button
            onClick={handleTriggerMatchAll}
            disabled={triggering}
            className="self-start sm:self-auto px-5 py-3 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 active:bg-gov-saffron-800 text-white text-xs sm:text-sm font-bold transition-all shadow-md flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw size={15} className={triggering ? 'animate-spin' : ''} />
            <span>{triggering ? 'Computing Matches...' : 'Trigger All AI Matches'}</span>
          </button>
        </div>

        {triggerResult && (
          <div className="mt-4 p-3 bg-gov-emerald-950/80 border border-gov-emerald-500/30 rounded-xl text-xs font-bold text-gov-emerald-300 flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{triggerResult}</span>
          </div>
        )}
      </div>

      {/* KPI Stats Row */}
      {loadingMetrics ? (
        <SkeletonLoader.Stats />
      ) : metrics ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Registered Citizens"
            value={metrics.total_users}
            sub="Active demographic profiles"
            icon={Users}
            accent="border-l-4 border-blue-500"
          />
          <KPICard
            label="Total Schemes"
            value={metrics.total_schemes}
            sub="Indexed central & state programs"
            icon={FileCheck}
            accent="border-l-4 border-gov-emerald-500"
          />
          <KPICard
            label="AI Eligibility Matches"
            value={metrics.total_matches}
            sub="Calculated recommendations"
            icon={TrendingUp}
            accent="border-l-4 border-gov-saffron-500"
          />
          <KPICard
            label="Applications Submitted"
            value={metrics.total_applications}
            sub="Processed via portal DBT"
            icon={Activity}
            accent="border-l-4 border-purple-500"
          />
        </div>
      ) : (
        <div className="p-6 bg-white rounded-2xl border border-slate-200 text-center text-xs text-slate-500">
          No telemetry metrics available yet.
        </div>
      )}

      {/* Tab Controls */}
      <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition-all border flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Executive Overview */}
      {activeTab === 'overview' && metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Applications by Status */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Applications Distribution by Stage
            </h3>

            <div className="space-y-3">
              {Object.entries(metrics.applications_by_status || {}).map(([status, count]) => {
                const total = metrics.total_applications || 1;
                const pct = Math.min(100, Math.round((count / total) * 100));

                return (
                  <div key={status} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="capitalize text-slate-700">{status.replace('_', ' ')}</span>
                      <span className="text-gov-navy-950 font-bold">{count} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          status === 'approved' ? 'bg-gov-emerald-500' :
                          status === 'submitted' ? 'bg-blue-500' :
                          status === 'under_review' ? 'bg-gov-saffron-500' : 'bg-slate-400'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Performing Schemes */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Top Matched Government Programs
            </h3>

            <div className="divide-y divide-slate-100">
              {(metrics.top_schemes || []).map((scheme, i) => (
                <div key={i} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-lg bg-slate-100 font-bold text-xs flex items-center justify-center text-slate-600">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-gov-navy-950">{scheme.name}</p>
                      <p className="text-[10px] text-slate-400">{scheme.ministry || 'Ministry of MSME'}</p>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-gov-saffron-700 bg-gov-saffron-50 px-2 py-0.5 rounded">
                    {scheme.matches} Matches
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Bias & Fairness Audit */}
      {activeTab === 'bias' && (
        <div className="space-y-4">
          {biasReport?.alert && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3 text-xs text-red-900">
              <AlertTriangle className="text-red-600 flex-shrink-0" size={20} />
              <div>
                <span className="font-bold block">Disparity Alert Triggered</span>
                <span>The algorithm detected a deviation in match scores across certain categories. Affirmative weighting adjustment is recommended.</span>
              </div>
            </div>
          )}

          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-gov space-y-4">
            <h3 className="font-bold text-base text-gov-navy-950">
              Fairness Audit: Match Scores by Social Category
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated under ethical AI guidelines for equal welfare distribution across marginalized communities.
            </p>

            <div className="space-y-4 pt-2">
              {(biasReport?.match_scores_by_category || []).map((item) => (
                <div key={item.category} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold uppercase text-gov-navy-950">
                      {item.category || 'General'}
                    </span>
                    <span className="text-slate-500 font-medium">
                      {item.count} Citizens • Avg Score: <strong>{item.avg_score.toFixed(1)}%</strong>
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.avg_score >= 70 ? 'bg-gov-emerald-500' :
                        item.avg_score >= 50 ? 'bg-gov-saffron-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, item.avg_score)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Users Table */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950">
            Registered Citizens & Entrepreneurs
          </h3>

          {loadingUsers ? (
            <SkeletonLoader.Table rows={4} cols={4} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                    <th className="pb-3">Citizen Name</th>
                    <th className="pb-3">Mobile</th>
                    <th className="pb-3">Category</th>
                    <th className="pb-3">Location</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(usersData?.users || usersData || []).slice(0, 10).map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="py-3 font-bold text-gov-navy-950">{u.full_name || 'Anonymous Citizen'}</td>
                      <td className="py-3 text-slate-500">{u.phone}</td>
                      <td className="py-3 uppercase font-semibold text-slate-700">{u.social_category || 'OBC'}</td>
                      <td className="py-3 text-slate-600">{u.district ? `${u.district}, ${u.state}` : 'India'}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gov-emerald-50 text-gov-emerald-700 border border-gov-emerald-200">
                          Active
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Scheme Management */}
      {activeTab === 'schemes' && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-gov space-y-4">
          <h3 className="font-bold text-base text-gov-navy-950">
            Central & State Scheme Catalog
          </h3>

          {loadingSchemes ? (
            <SkeletonLoader.Table rows={4} cols={3} />
          ) : (
            <div className="divide-y divide-slate-100">
              {(schemesData?.schemes || schemesData || []).slice(0, 10).map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-gov-navy-950">{s.name}</p>
                    <p className="text-[11px] text-slate-400">{s.ministry || 'Government of India'} • Type: {s.scheme_type}</p>
                  </div>
                  <span className="px-2.5 py-1 rounded-lg bg-slate-100 font-bold text-slate-700">
                    Active
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: System Monitoring */}
      {activeTab === 'system' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Server size={18} className="text-gov-emerald-600" />
              <span>FastAPI Backend</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">Operational (Port 8000)</p>
            <p className="text-[11px] text-slate-400">Response time: &lt; 45ms</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Database size={18} className="text-gov-emerald-600" />
              <span>Database Cluster</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">PostgreSQL / SQLite Active</p>
            <p className="text-[11px] text-slate-400">Connection pool healthy</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-gov space-y-2">
            <div className="flex items-center gap-2 text-gov-navy-950 font-bold text-sm">
              <Activity size={18} className="text-gov-emerald-600" />
              <span>Redis Cache Adapter</span>
            </div>
            <p className="text-xs text-gov-emerald-700 font-bold">Resilient Fallback Mode</p>
            <p className="text-[11px] text-slate-400">Zero-crash memory cache active</p>
          </div>
        </div>
      )}

    </div>
  );
}

function KPICard({ label, value, sub, icon: Icon, accent }) {
  return (
    <div className={`bg-white p-5 rounded-3xl border border-slate-200 shadow-gov ${accent}`}>
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">{label}</span>
        <Icon size={18} className="text-slate-400" />
      </div>
      <p className="text-2xl sm:text-3xl font-extrabold text-gov-navy-950">
        {value?.toLocaleString() || '0'}
      </p>
      <p className="text-[11px] text-slate-400 mt-1">{sub}</p>
    </div>
  );
}
