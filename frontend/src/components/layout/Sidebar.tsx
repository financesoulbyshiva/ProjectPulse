import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderKanban,
  CheckSquare,
  Users,
  BarChart3,
  BrainCircuit,
  Settings,
  LogOut,
  Activity,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Projects', path: '/projects', icon: FolderKanban },
    { name: 'Tasks', path: '/tasks', icon: CheckSquare },
    { name: 'Team', path: '/team', icon: Users },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'AI Risk Analysis', path: '/risk-analysis', icon: BrainCircuit },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white border-r border-gray-200 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-16 px-5 flex items-center justify-between border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <span className="text-base font-bold text-gray-900 tracking-tight block leading-tight">
                ProjectPulse
              </span>
              <span className="text-[10px] text-gray-400 font-medium block">
                AI Project Risk Intelligence
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-gray-400 hover:text-gray-600 p-1 rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  `group relative flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 motion-press ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold shadow-2xs'
                      : 'text-gray-600 hover:bg-gray-50/80 hover:text-gray-900'
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-105" />
                <span className="transition-transform duration-150 group-hover:translate-x-0.5">{item.name}</span>
              </NavLink>
            );
          })}
        </div>

        {/* User profile & logout footer */}
        <div className="border-t border-gray-200 p-3 bg-gray-50/50">
          <div className="flex items-center justify-between p-2 rounded-md bg-white border border-gray-200 shadow-2xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-semibold shrink-0">
                {user?.name?.trim() ? user.name.trim().slice(0, 2).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-gray-900 truncate">{user?.name || 'User'}</p>
                <p className="text-[11px] text-gray-500 truncate">{user?.role || 'Member'}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="text-gray-400 hover:text-red-600 p-1.5 rounded-md hover:bg-gray-100 transition-all duration-150 motion-press shrink-0"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Subtle Noveraa Brand Attribution */}
        <div className="px-4 py-2.5 border-t border-gray-100 bg-white flex items-center justify-between text-[10px] text-gray-400 select-none">
          <span className="font-semibold tracking-wider text-gray-500 uppercase">NOVERAA</span>
          <span>Real World Tech</span>
        </div>
      </aside>
    </>
  );
};
