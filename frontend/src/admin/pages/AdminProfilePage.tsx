import React from 'react';
import { useAuthStore } from '../../store/authStore';
import { Shield, User, Lock, CheckCircle2, AlertTriangle, Key } from 'lucide-react';

export const AdminProfilePage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Admin Account & Governance
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Administrative role credentials, RBAC clearance, and data privacy safeguards
        </p>
      </div>

      {/* Admin Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center space-x-4 border-b border-slate-800 pb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-amber-500/20">
            <Shield className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{user?.name}</h2>
            <p className="text-xs text-slate-400">{user?.email}</p>
            <div className="mt-1 flex items-center space-x-2">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                ROLE: {user?.role}
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                STATUS: {user?.status}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
          <div>
            <span className="text-slate-400">Account ID:</span>{' '}
            <span className="font-mono text-slate-200">{user?.id}</span>
          </div>
          <div>
            <span className="text-slate-400">Clearance Level:</span>{' '}
            <span className="text-emerald-400 font-semibold">Tier 1 Superuser</span>
          </div>
        </div>
      </div>

      {/* Privacy & Security Governance Policies */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center space-x-2">
          <Lock className="w-5 h-5 text-amber-400" />
          <span>Health Data Privacy & Compliance Guardrails</span>
        </h2>

        <div className="space-y-3 text-xs text-slate-300">
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start space-x-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Read-Only Customer Health Data:</strong>{' '}
              All health metrics, meals, workouts, sleep, and hydration logs entered by
              customers are strictly read-only for administrators.
            </div>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start space-x-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Strict No-Impersonation Policy:</strong>{' '}
              Administrators cannot generate sessions pretending to be customers or post
              messages into customer conversations.
            </div>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start space-x-3">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Immutable Audit Logging:</strong>{' '}
              Every administrative mutation (food master, activity master, customer status change)
              is automatically logged with timestamps, client IP, and request details.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
