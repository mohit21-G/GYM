import React, { useState, useEffect } from 'react';
import { apiClient } from '../config/api';
import {
  Utensils,
  Flame,
  Droplets,
  Moon,
  Scale,
  Trash2,
  Calendar,
  RefreshCw,
  PlusCircle,
  Filter,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';

type LogType = 'FOOD' | 'ACTIVITY' | 'HYDRATION' | 'SLEEP' | 'WEIGHT';

export const LogsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<LogType>('FOOD');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchLogs();
  }, [activeTab, dateFilter, page]);

  const getEndpoint = (type: LogType) => {
    switch (type) {
      case 'FOOD':
        return '/food-logs';
      case 'ACTIVITY':
        return '/activity-logs';
      case 'HYDRATION':
        return '/hydration-logs';
      case 'SLEEP':
        return '/sleep-logs';
      case 'WEIGHT':
        return '/weight-logs';
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = getEndpoint(activeTab);
      const params: any = { page, limit: 15 };
      if (dateFilter) {
        params.startDate = dateFilter;
        params.endDate = dateFilter;
      }
      const res = await apiClient.get(endpoint, { params });
      const data = res.data;
      setItems(data.items || []);
      setTotalPages(data.meta?.totalPages || 1);
    } catch (err: any) {
      setError(
        err.response?.data?.message ||
          'Failed to load health logs. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this log entry?')) return;
    try {
      const endpoint = getEndpoint(activeTab);
      await apiClient.delete(`${endpoint}/${id}`);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to delete log entry.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Health & Activity History
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse and manage all your meals, workouts, water, weight, and sleep logs
          </p>
        </div>

        <Link
          to="/chat"
          className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-medium rounded-xl shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Log via Assistant</span>
        </Link>
      </div>

      {/* Filter Tabs & Date Filter */}
      <div className="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-4 bg-slate-800/80 p-3 rounded-2xl border border-slate-700/60 shadow-md">
        {/* Tabs */}
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => {
              setActiveTab('FOOD');
              setPage(1);
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'FOOD'
                ? 'bg-emerald-500 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <Utensils className="w-3.5 h-3.5" />
            <span>Meals</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('ACTIVITY');
              setPage(1);
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'ACTIVITY'
                ? 'bg-amber-500 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Workouts</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('HYDRATION');
              setPage(1);
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'HYDRATION'
                ? 'bg-cyan-500 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <Droplets className="w-3.5 h-3.5" />
            <span>Water</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('SLEEP');
              setPage(1);
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'SLEEP'
                ? 'bg-indigo-500 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <Moon className="w-3.5 h-3.5" />
            <span>Sleep</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('WEIGHT');
              setPage(1);
            }}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'WEIGHT'
                ? 'bg-teal-500 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Weight</span>
          </button>
        </div>

        {/* Date Filter & Clear */}
        <div className="flex items-center space-x-2">
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => {
              setDateFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          {dateFilter && (
            <button
              onClick={() => {
                setDateFilter('');
                setPage(1);
              }}
              className="text-xs text-slate-400 hover:text-rose-400 underline"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Log List */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
            <span>Loading log history...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-300">{error}</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <p className="text-base font-medium text-slate-300">No logs found</p>
            <p className="text-xs text-slate-500 mt-1">
              Start logging your health activities with our AI assistant or select another tab.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {items.map((item) => {
              const loggedDate = item.loggedAt
                ? format(new Date(item.loggedAt), 'MMM d, yyyy h:mm a')
                : '';
              return (
                <div
                  key={item.id}
                  className="p-4 sm:p-5 flex items-center justify-between hover:bg-slate-700/20 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center flex-shrink-0 text-emerald-400">
                      {activeTab === 'FOOD' && <Utensils className="w-5 h-5 text-emerald-400" />}
                      {activeTab === 'ACTIVITY' && <Flame className="w-5 h-5 text-amber-400" />}
                      {activeTab === 'HYDRATION' && <Droplets className="w-5 h-5 text-cyan-400" />}
                      {activeTab === 'SLEEP' && <Moon className="w-5 h-5 text-indigo-400" />}
                      {activeTab === 'WEIGHT' && <Scale className="w-5 h-5 text-teal-400" />}
                    </div>

                    <div>
                      {/* Name or Title */}
                      <div className="font-semibold text-slate-200 text-sm">
                        {item.foodName ||
                          item.activityName ||
                          item.name ||
                          (activeTab === 'HYDRATION' &&
                            (item.beverageName && item.beverageName.toLowerCase() !== 'water'
                              ? `${item.beverageName} (${item.amountMl} ml)`
                              : `${item.amountMl} ml Water`)) ||
                          (activeTab === 'SLEEP' && `${Math.round((item.durationMinutes / 60) * 10) / 10} hrs Sleep`) ||
                          (activeTab === 'WEIGHT' && `${item.weightKg} kg`)}
                      </div>

                      {/* Details / Subtitle */}
                      <div className="text-xs text-slate-400 mt-0.5 flex flex-wrap gap-2">
                        <span>{loggedDate}</span>
                        {item.mealType && <span>• {item.mealType}</span>}
                        {item.quantity && (
                          <span>
                            • {item.quantity} {item.unit}
                          </span>
                        )}
                        {item.durationMinutes && activeTab === 'ACTIVITY' && (
                          <span>• {item.durationMinutes} mins</span>
                        )}
                        {item.quality && <span>• Quality: {item.quality}</span>}
                      </div>
                    </div>
                  </div>

                  {/* Badges and Delete Action */}
                  <div className="flex items-center space-x-4">
                    {item.calories !== undefined && (
                      <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {item.calories} kcal
                      </span>
                    )}
                    {item.caloriesBurned !== undefined && (
                      <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        -{item.caloriesBurned} kcal
                      </span>
                    )}

                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                      title="Delete entry"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-700/60 flex justify-between items-center text-xs text-slate-400">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg disabled:opacity-40"
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
