import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/api';
import {
  Users,
  Activity,
  Cpu,
  ShieldCheck,
  RefreshCw,
  TrendingUp,
  UserPlus,
  AlertTriangle,
  FileText,
  Calendar,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';

export const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/dashboard');
      setStats(res.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load admin dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center space-x-3 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
          <span>Aggregating system statistics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-300 text-center">
        <p className="mb-3">{error}</p>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-amber-500 text-white rounded-xl text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  const { customers, healthLogs, chatAndAI, recentRegistrations, recentAuditLogs, chartData } =
    stats || {};

  return (
    <div className="space-y-8">
      {/* Top Title Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            System Overview & Metrics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Global customer health logs, AI telemetry, and security audit trail
          </p>
        </div>

        <button
          onClick={fetchStats}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-medium text-slate-300 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Customers */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Total Customers
            </span>
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{customers?.total ?? 0}</span>
            <span className="text-xs text-emerald-400 font-semibold">
              +{customers?.newLast7Days ?? 0} this week
            </span>
          </div>
          <div className="mt-3 flex space-x-2 text-xs text-slate-400">
            <span className="text-emerald-400">{customers?.active ?? 0} active</span>
            <span>•</span>
            <span className="text-rose-400">{customers?.suspended ?? 0} suspended</span>
          </div>
        </div>

        {/* Total Health Logs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Logged Health Events
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-emerald-400">
              {healthLogs?.total ?? 0}
            </span>
            <span className="text-xs text-slate-400">total records</span>
          </div>
          <div className="mt-3 text-xs text-slate-400 flex space-x-2">
            <span>{healthLogs?.food ?? 0} meals</span>
            <span>•</span>
            <span>{healthLogs?.activity ?? 0} workouts</span>
          </div>
        </div>

        {/* AI Telemetry */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              AI Requests
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-amber-400">
              {chatAndAI?.aiRequests ?? 0}
            </span>
            <span className="text-xs text-slate-400">calls</span>
          </div>
          <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
            <span>Failures: {chatAndAI?.aiFailures ?? 0}</span>
            <span className="text-xs font-semibold text-emerald-400">
              {100 - (chatAndAI?.failureRate ?? 0)}% success
            </span>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Chat Interactions
            </span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {chatAndAI?.chatMessages ?? 0}
            </span>
            <span className="text-xs text-slate-400">messages</span>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            Across English, Hindi, and Gujarati
          </div>
        </div>
      </div>

      {/* Chart: 7-Day Registrations vs Logs */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-base font-bold text-white">Platform Activity (Past 7 Days)</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Daily customer sign-ups and total health event logging volume
            </p>
          </div>
          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-blue-400" />
              <span className="text-slate-300">New Registrations</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span className="text-slate-300">Health Logs</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-2 h-44 items-end pt-4 border-b border-slate-800">
          {chartData?.map((item: any, i: number) => {
            const regHeight = Math.min(100, Math.max(10, item.registrations * 20));
            const logHeight = Math.min(100, Math.max(10, item.logs * 10));
            return (
              <div key={i} className="flex flex-col items-center h-full justify-end group">
                <div className="w-full flex justify-center items-end space-x-1.5 h-32">
                  <div
                    className="w-3.5 bg-blue-500/80 group-hover:bg-blue-400 rounded-t transition-all"
                    style={{ height: `${regHeight}%` }}
                    title={`Registrations: ${item.registrations}`}
                  />
                  <div
                    className="w-3.5 bg-emerald-500/80 group-hover:bg-emerald-400 rounded-t transition-all"
                    style={{ height: `${logHeight}%` }}
                    title={`Health Logs: ${item.logs}`}
                  />
                </div>
                <span className="text-[11px] text-slate-400 mt-2 font-medium">
                  {item.date?.slice(5)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Section: Recent Registrations & Recent Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Registrations */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-bold text-white">Recent Customer Sign-ups</h2>
            <Link
              to="/admin/customers"
              className="text-xs text-amber-400 hover:text-amber-300 font-medium"
            >
              View all customers →
            </Link>
          </div>

          <div className="divide-y divide-slate-800">
            {recentRegistrations?.map((u: any) => (
              <div key={u.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-slate-200">{u.name}</div>
                  <div className="text-xs text-slate-400">{u.email}</div>
                </div>
                <div className="text-right">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      u.status === 'ACTIVE'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    {u.status}
                  </span>
                  <div className="text-[10px] text-slate-500 mt-1">
                    {format(new Date(u.createdAt), 'MMM d, yyyy')}
                  </div>
                </div>
              </div>
            ))}
            {(!recentRegistrations || recentRegistrations.length === 0) && (
              <p className="text-xs text-slate-500 italic py-4">No recent registrations</p>
            )}
          </div>
        </div>

        {/* Recent Audit Trail */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-base font-bold text-white">Recent Administrative Actions</h2>
            <Link
              to="/admin/audit-logs"
              className="text-xs text-amber-400 hover:text-amber-300 font-medium"
            >
              View audit trail →
            </Link>
          </div>

          <div className="divide-y divide-slate-800">
            {recentAuditLogs?.map((a: any) => (
              <div key={a.id} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-200">{a.action}</div>
                  <div className="text-[11px] text-slate-400">
                    By {a.admin?.name || 'Admin'} on {a.targetResource}
                  </div>
                </div>
                <div className="text-[10px] text-slate-500">
                  {format(new Date(a.createdAt), 'MMM d, h:mm a')}
                </div>
              </div>
            ))}
            {(!recentAuditLogs || recentAuditLogs.length === 0) && (
              <p className="text-xs text-slate-500 italic py-4">No recent audit log entries</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
