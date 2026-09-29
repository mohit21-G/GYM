import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UtensilsCrossed,
  Activity,
  Cpu,
  ShieldAlert,
  UserCheck,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  onCloseMobile?: () => void;
}

export const AdminSidebar: React.FC<SidebarProps> = ({ onCloseMobile }) => {
  const navItems = [
    { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/customers', label: 'Customers', icon: Users },
    { to: '/admin/foods', label: 'Food Masters', icon: UtensilsCrossed },
    { to: '/admin/activities', label: 'Activity Masters', icon: Activity },
    { to: '/admin/ai-usage', label: 'AI & Token Telemetry', icon: Cpu },
    { to: '/admin/audit-logs', label: 'Audit Trail', icon: ShieldAlert },
    { to: '/admin/profile', label: 'Admin Settings', icon: UserCheck },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full flex-shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/20 text-white font-bold">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-white text-base tracking-tight">Admin Portal</span>
          <span className="block text-[10px] text-amber-400 uppercase font-semibold tracking-wider">
            Superuser Control
          </span>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Management
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer link back to customer app */}
      <div className="p-4 border-t border-slate-800">
        <NavLink
          to="/dashboard"
          className="flex items-center space-x-2 text-xs text-slate-400 hover:text-white px-3 py-2 rounded-xl hover:bg-slate-800/80 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Customer Dashboard</span>
        </NavLink>
      </div>
    </aside>
  );
};
