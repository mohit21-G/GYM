import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../../config/api';
import {
  User,
  Shield,
  Activity,
  Calendar,
  Clock,
  ArrowLeft,
  Utensils,
  Flame,
  Droplets,
  Moon,
  Scale,
  MessageSquare,
  AlertCircle,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';
import { format } from 'date-fns';

export const AdminCustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [chats, setChats] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'CHATS' | 'LOGS'>('OVERVIEW');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status Change Dialog
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('ACTIVE');
  const [statusReason, setStatusReason] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [statusSuccess, setStatusSuccess] = useState<string | null>(null);

  const fetchCustomerDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const [detailRes, chatRes] = await Promise.all([
        apiClient.get(`/admin/customers/${id}`),
        apiClient.get(`/admin/customers/${id}/chats`),
      ]);
      setData(detailRes.data);
      setNewStatus(detailRes.data.customer?.status || 'ACTIVE');
      setChats(chatRes.data.items || []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch customer details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchCustomerDetails();
  }, [id]);

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setUpdatingStatus(true);
    try {
      await apiClient.patch(`/admin/customers/${id}/status`, {
        status: newStatus,
        reason: statusReason || 'Admin updated account status',
      });
      setStatusSuccess(`Customer status updated to ${newStatus}`);
      setShowStatusModal(false);
      setStatusReason('');
      fetchCustomerDetails();
      setTimeout(() => setStatusSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to update status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center space-x-2 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
          <span>Loading customer inspection data...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-rose-300">
        <p>{error || 'Customer not found.'}</p>
        <Link
          to="/admin/customers"
          className="mt-4 inline-block px-4 py-2 bg-slate-800 text-white rounded-xl text-xs"
        >
          Back to Customers
        </Link>
      </div>
    );
  }

  const { customer, profile, counts, recentActivity } = data;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back button & Title */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-3">
          <Link
            to="/admin/customers"
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
              <span>{customer.name}</span>
              <span
                className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                  customer.status === 'ACTIVE'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : customer.status === 'SUSPENDED'
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    : 'bg-slate-700 text-slate-300'
                }`}
              >
                {customer.status}
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              {customer.email} • ID: {customer.id}
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowStatusModal(true)}
          className="px-4 py-2.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
        >
          Change Account Status
        </button>
      </div>

      {statusSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{statusSuccess}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'OVERVIEW'
              ? 'bg-amber-500 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Customer Overview & Goals
        </button>
        <button
          onClick={() => setActiveTab('CHATS')}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'CHATS'
              ? 'bg-amber-500 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          AI Chat History ({counts?.chatMessages ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('LOGS')}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'LOGS'
              ? 'bg-amber-500 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Recent Health Logs
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Meals</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">{counts.foodLogs}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Workouts</div>
              <div className="text-xl font-bold text-amber-400 mt-1">{counts.activityLogs}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Hydration</div>
              <div className="text-xl font-bold text-cyan-400 mt-1">{counts.hydrationLogs}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Sleep</div>
              <div className="text-xl font-bold text-indigo-400 mt-1">{counts.sleepLogs}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Weights</div>
              <div className="text-xl font-bold text-teal-400 mt-1">{counts.weightLogs}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Messages</div>
              <div className="text-xl font-bold text-purple-400 mt-1">{counts.chatMessages}</div>
            </div>
          </div>

          {/* Profile & Target Specs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-2">
                Account Metadata
              </h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400">Registered:</span>{' '}
                  <span className="text-slate-200">
                    {format(new Date(customer.createdAt), 'MMM d, yyyy')}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Last Login:</span>{' '}
                  <span className="text-slate-200">
                    {customer.lastLoginAt
                      ? format(new Date(customer.lastLoginAt), 'MMM d, yyyy')
                      : 'Never'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Timezone:</span>{' '}
                  <span className="text-slate-200">{customer.timezone}</span>
                </div>
                <div>
                  <span className="text-slate-400">Preferred Language:</span>{' '}
                  <span className="text-slate-200 uppercase">{customer.preferredLanguage}</span>
                </div>
                <div>
                  <span className="text-slate-400">Unit Preference:</span>{' '}
                  <span className="text-slate-200">{profile?.unitPreference || 'Metric'}</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
              <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-2">
                Health Targets & Biometrics
              </h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400">Height:</span>{' '}
                  <span className="text-slate-200">{profile?.heightCm ? `${profile.heightCm} cm` : 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400">Current Weight:</span>{' '}
                  <span className="text-slate-200">
                    {profile?.currentWeightKg ? `${profile.currentWeightKg} kg` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Target Weight:</span>{' '}
                  <span className="text-slate-200">
                    {profile?.targetWeightKg ? `${profile.targetWeightKg} kg` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Gender:</span>{' '}
                  <span className="text-slate-200">{profile?.gender || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400">Daily Calorie Target:</span>{' '}
                  <span className="text-slate-200">{profile?.dailyCalorieTarget || 2000} kcal</span>
                </div>
                <div>
                  <span className="text-slate-400">Daily Water Target:</span>{' '}
                  <span className="text-slate-200">{profile?.dailyWaterMlTarget || 2500} ml</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CHATBOT HISTORY */}
      {activeTab === 'CHATS' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Customer Chat Sessions ({chats.length})
            </h2>
            <span className="text-[11px] text-slate-400">
              Read-only inspection for compliance and diagnostic review
            </span>
          </div>

          {chats.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-6 text-center">
              Customer has not engaged with the AI assistant yet.
            </p>
          ) : (
            <div className="space-y-6">
              {chats.map((session) => (
                <div
                  key={session.id}
                  className="border border-slate-800 rounded-xl p-4 bg-slate-950/60"
                >
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-300 border-b border-slate-800/80 pb-2 mb-3">
                    <span className="flex items-center space-x-2">
                      <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
                      <span>{session.title || 'Conversation'}</span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      {format(new Date(session.createdAt), 'MMM d, yyyy h:mm a')}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {session.messages?.map((msg: any) => (
                      <div
                        key={msg.id}
                        className={`p-3 rounded-xl text-xs ${
                          msg.sender === 'USER'
                            ? 'bg-slate-800/80 text-slate-200 ml-4'
                            : 'bg-emerald-950/30 border border-emerald-500/20 text-emerald-200 mr-4'
                        }`}
                      >
                        <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                          <span className="font-semibold uppercase">
                            {msg.sender === 'USER' ? customer.name : 'AI Assistant'}
                          </span>
                          <span>{format(new Date(msg.createdAt), 'h:mm a')}</span>
                        </div>
                        <p className="whitespace-pre-wrap">{msg.message}</p>
                        {msg.detectedIntent && (
                          <div className="mt-1.5 inline-block text-[9px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-700 font-mono">
                            Intent: {msg.detectedIntent}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: LOGS */}
      {activeTab === 'LOGS' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          <h2 className="text-sm font-bold text-white border-b border-slate-800 pb-3">
            Recent Health Records (Read-Only)
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Meals */}
            <div className="border border-slate-800 rounded-xl p-4 space-y-2">
              <span className="text-xs font-semibold text-emerald-400 uppercase">
                Recent Meals
              </span>
              {recentActivity.food?.map((f: any) => (
                <div key={f.id} className="text-xs p-2 bg-slate-800/50 rounded flex justify-between">
                  <span>{f.foodName} ({f.quantity} {f.unit})</span>
                  <span className="font-bold text-emerald-400">{f.calories} kcal</span>
                </div>
              ))}
              {recentActivity.food?.length === 0 && (
                <p className="text-xs text-slate-500 italic">No meals logged</p>
              )}
            </div>

            {/* Workouts */}
            <div className="border border-slate-800 rounded-xl p-4 space-y-2">
              <span className="text-xs font-semibold text-amber-400 uppercase">
                Recent Workouts
              </span>
              {recentActivity.activity?.map((a: any) => (
                <div key={a.id} className="text-xs p-2 bg-slate-800/50 rounded flex justify-between">
                  <span>{a.activityName} ({a.durationMinutes}m)</span>
                  <span className="font-bold text-amber-400">{a.caloriesBurned} kcal</span>
                </div>
              ))}
              {recentActivity.activity?.length === 0 && (
                <p className="text-xs text-slate-500 italic">No workouts logged</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Status Change Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Update Customer Account Status</h3>
            <p className="text-xs text-slate-400">
              Modifying account status creates an immutable record in the administrative audit log.
              Suspending or deactivating will revoke active customer tokens.
            </p>

            <form onSubmit={handleUpdateStatus} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Status
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                  <option value="SUSPENDED">SUSPENDED</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Audit Reason (Required for accountability)
                </label>
                <textarea
                  required
                  rows={3}
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder="Explain why this account status is being changed..."
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStatusModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updatingStatus}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-medium disabled:opacity-50"
                >
                  {updatingStatus ? 'Updating...' : 'Confirm Status Change'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
