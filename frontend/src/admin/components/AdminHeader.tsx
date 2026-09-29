import React from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Menu, LogOut, Shield, ChevronRight } from 'lucide-react';

interface HeaderProps {
  onToggleMobileMenu: () => void;
}

export const AdminHeader: React.FC<HeaderProps> = ({ onToggleMobileMenu }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const pathParts = location.pathname.split('/').filter(Boolean);

  return (
    <header className="h-16 bg-slate-900/90 border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 backdrop-blur-sm">
      <div className="flex items-center space-x-3">
        {/* Mobile toggle */}
        <button
          onClick={onToggleMobileMenu}
          className="p-2 text-slate-400 hover:text-white rounded-lg md:hidden hover:bg-slate-800"
          title="Open Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumbs */}
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <Link to="/admin/dashboard" className="hover:text-slate-200">
            Admin
          </Link>
          {pathParts.slice(1).map((part, index) => (
            <React.Fragment key={index}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="capitalize text-slate-200 font-medium">
                {part.replace('-', ' ')}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Admin user info & actions */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center font-bold text-xs">
            <Shield className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left text-xs">
            <div className="font-semibold text-slate-200">{user?.name || 'Administrator'}</div>
            <div className="text-[10px] text-amber-400 font-medium">System Admin</div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors cursor-pointer"
          title="Logout of Admin Portal"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
