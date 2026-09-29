import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/api';
import {
  ShieldAlert,
  RefreshCw,
  Search,
  Filter,
  Eye,
  FileCode,
  Calendar,
} from 'lucide-react';
import { format } from 'date-fns';

export const AdminAuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState('');
  const [targetResource, setTargetResource] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Selected Changes Dialog
  const [selectedChanges, setSelectedChanges] = useState<any | null>(null);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/admin/audit-logs', {
        params: {
          page,
          limit: 15,
          action: actionFilter || undefined,
          targetResource: targetResource || undefined,
        },
      });
      setLogs(res.data.items || []);
      setTotalPages(res.data.meta?.totalPages || 1);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [page, actionFilter, targetResource]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Administrative Audit Trail
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Immutable log of all administrative actions, customer status modifications, and master changes
          </p>
        </div>

        <button
          onClick={fetchAuditLogs}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-medium text-slate-300 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Audit Trail</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-wrap gap-4 items-center shadow-lg">
        <div className="text-xs text-slate-400 font-semibold uppercase">Filters:</div>

        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2"
        >
          <option value="">All Actions</option>
          <option value="UPDATE_CUSTOMER_STATUS">UPDATE_CUSTOMER_STATUS</option>
          <option value="CREATE_FOOD">CREATE_FOOD</option>
          <option value="DELETE_FOOD">DELETE_FOOD</option>
          <option value="CREATE_ACTIVITY">CREATE_ACTIVITY</option>
          <option value="DELETE_ACTIVITY">DELETE_ACTIVITY</option>
        </select>

        <select
          value={targetResource}
          onChange={(e) => {
            setTargetResource(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2"
        >
          <option value="">All Resources</option>
          <option value="USER">USER</option>
          <option value="FOOD">FOOD</option>
          <option value="ACTIVITY">ACTIVITY</option>
          <option value="FOOD_CATEGORY">FOOD_CATEGORY</option>
          <option value="ACTIVITY_CATEGORY">ACTIVITY_CATEGORY</option>
        </select>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
            <span>Loading audit log records...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-300">{error}</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <ShieldAlert className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-300">No audit log records found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Admin User</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Target Resource</th>
                  <th className="py-3.5 px-4">Target ID</th>
                  <th className="py-3.5 px-4">Client IP</th>
                  <th className="py-3.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 text-slate-300">
                      {format(new Date(log.createdAt), 'MMM d, h:mm:ss a')}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200">
                        {log.admin?.name || 'Administrator'}
                      </div>
                      <div className="text-[10px] text-slate-500">{log.admin?.email}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-bold text-amber-400 px-2 py-0.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">{log.targetResource}</td>
                    <td className="py-3.5 px-4 font-mono text-[10px] text-slate-400">
                      {log.targetId ? log.targetId.slice(0, 8) + '...' : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                      {log.ipAddress || '127.0.0.1'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {log.changes ? (
                        <button
                          onClick={() => setSelectedChanges(log)}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]"
                        >
                          <FileCode className="w-3.5 h-3.5 text-amber-400" />
                          <span>View Payload</span>
                        </button>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Changes Payload Modal */}
      {selectedChanges && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-white">
                Audit Payload: {selectedChanges.action}
              </h3>
              <button
                onClick={() => setSelectedChanges(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕ Close
              </button>
            </div>

            <div className="text-xs text-slate-400 space-y-1">
              <div>
                <strong>Admin:</strong> {selectedChanges.admin?.name} ({selectedChanges.admin?.email})
              </div>
              <div>
                <strong>Resource:</strong> {selectedChanges.targetResource} (ID: {selectedChanges.targetId})
              </div>
              <div>
                <strong>Client:</strong> {selectedChanges.ipAddress} • {selectedChanges.userAgent}
              </div>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto max-h-60">
              <pre className="text-[11px] font-mono text-emerald-400 whitespace-pre-wrap">
                {(() => {
                  try {
                    return JSON.stringify(JSON.parse(selectedChanges.changes), null, 2);
                  } catch {
                    return selectedChanges.changes;
                  }
                })()}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
