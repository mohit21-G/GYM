import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/api';
import {
  Cpu,
  RefreshCw,
  Search,
  DollarSign,
  Clock,
  CheckCircle2,
  XCircle,
  BarChart2,
} from 'lucide-react';
import { format } from 'date-fns';

export const AdminAIUsagePage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [provider, setProvider] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);

  const fetchAIUsage = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/ai/usage', {
        params: {
          page,
          limit: 15,
          provider: provider || undefined,
          status: status || undefined,
        },
      });
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch AI telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAIUsage();
  }, [page, provider, status]);

  const { summary, items, meta } = data || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            AI & Token Telemetry
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time inference tracking, latency monitoring, token consumption, and cost estimates
          </p>
        </div>

        <button
          onClick={fetchAIUsage}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-medium text-slate-300 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span>Total Invocations</span>
            <Cpu className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {summary?.totalRequests ?? 0}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1">
            {summary?.successCount ?? 0} successful
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span>Total Tokens</span>
            <BarChart2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-extrabold text-blue-400">
            {summary?.totalTokens?.toLocaleString() ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            In: {summary?.promptTokens?.toLocaleString() ?? 0} | Out:{' '}
            {summary?.completionTokens?.toLocaleString() ?? 0}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span>Avg Latency</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold text-purple-400">
            {summary?.avgLatencyMs ?? 0} ms
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Response turnaround</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span>Estimated Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">
            ${summary?.estimatedCostUsd ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Blended provider rate</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span>Failures</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-extrabold text-rose-400">
            {summary?.failureCount ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {summary?.totalRequests > 0
              ? `${Math.round((summary.failureCount / summary.totalRequests) * 1000) / 10}% rate`
              : '0% rate'}
          </div>
        </div>
      </div>

      {/* Filter controls */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-wrap gap-4 items-center shadow-lg">
        <div className="text-xs text-slate-400 font-semibold uppercase">Filter by:</div>

        <select
          value={provider}
          onChange={(e) => {
            setProvider(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2"
        >
          <option value="">All Providers</option>
          <option value="cloudflare">Cloudflare Workers AI (GLM-4.7-Flash)</option>
          <option value="openai">OpenAI (GPT-4o)</option>
          <option value="mistral">Mistral AI</option>
          <option value="gemini">Google Gemini</option>
        </select>

        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2"
        >
          <option value="">All Statuses</option>
          <option value="SUCCESS">SUCCESS</option>
          <option value="FAILED">FAILED</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
            <span>Fetching AI telemetry logs...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-300">{error}</div>
        ) : items?.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Cpu className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-300">No telemetry records found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Provider / Model</th>
                  <th className="py-3.5 px-4">Customer</th>
                  <th className="py-3.5 px-4">Tokens (In / Out / Total)</th>
                  <th className="py-3.5 px-4">Latency</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {items?.map((log: any) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 text-slate-300">
                      {format(new Date(log.createdAt), 'MMM d, h:mm:ss a')}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200 capitalize">
                        {log.provider}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate max-w-xs">
                        {log.model}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {log.user?.name || log.user?.email || 'Anonymous'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-200 font-mono">
                      {log.promptTokens} / {log.completionTokens} /{' '}
                      <span className="font-bold text-amber-400">{log.totalTokens}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono">
                      {log.latencyMs} ms
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {meta?.totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
            <span>
              Page {meta.page} of {meta.totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={meta.page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={meta.page >= meta.totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
