import React from 'react';
import { Menu, Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ThemeToggle } from '../common/ThemeToggle';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onOpenSidebar: () => void;
  actions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onOpenSidebar,
  actions,
}) => {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-gray-200 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="lg:hidden text-gray-500 hover:text-gray-700 p-1.5 rounded-md hover:bg-gray-100"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-base sm:text-lg font-semibold text-gray-900 leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-gray-500 hidden sm:block">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {actions && <div className="flex items-center gap-2">{actions}</div>}
        <ThemeToggle />

        {/* Notifications */}
        <div className="relative">
          <button
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 transition-colors relative"
            title="Notifications"
          >
            <Bell className="h-4 w-4" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-blue-600 ring-2 ring-white" />
          </button>
        </div>

        {/* User avatar chip */}
        <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
          <div className="h-7 w-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-semibold">
            {user?.name?.trim() ? user.name.trim().slice(0, 1).toUpperCase() : 'U'}
          </div>
          <span className="text-xs font-medium text-gray-700 hidden md:block">
            {user?.name || 'User'}
          </span>
        </div>
      </div>
    </header>
  );
};
