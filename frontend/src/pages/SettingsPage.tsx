import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Shield,
  Bell,
  Sun,
  Moon,
  LogOut,
  Save,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { useProject } from '../context/ProjectContext';
import { useTheme } from '../context/ThemeContext';

export const SettingsPage: React.FC = () => {
  const { user, logout, updateProfile } = useAuth();
  const { theme, setTheme } = useTheme();
  const { showToast } = useProject();
  const navigate = useNavigate();

  // Profile Form state
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [role, setRole] = useState(user?.role || 'Member');

  useEffect(() => {
    if (user?.name) setName(user.name);
    if (user?.email) setEmail(user.email);
    if (user?.role) setRole(user.role);
  }, [user]);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Notification toggles
  const [projectUpdates, setProjectUpdates] = useState(true);
  const [taskReminders, setTaskReminders] = useState(true);
  const [riskAlerts, setRiskAlerts] = useState(true);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile(name, email);
    showToast('Profile information updated successfully.');
  };

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      alert('Please fill in both current and new password.');
      return;
    }
    setCurrentPassword('');
    setNewPassword('');
    showToast('Password changed successfully.');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* 1. Profile Section */}
      <Card
        title="Profile Settings"
        subtitle="Manage your personal profile and display preferences"
      >
        <form onSubmit={handleSaveProfile} className="space-y-4 pt-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Please enter your name"
              icon={<User className="h-4 w-4" />}
              required
            />

            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
              Assigned Role
            </label>
            <input
              type="text"
              disabled
              value={role}
              className="w-full text-xs p-2 rounded-md border border-gray-200 bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="text-[11px] text-gray-400 mt-1">
              Roles are managed by your organization administrator.
            </p>
          </div>

          <div className="flex justify-end pt-2">
            <Button type="submit" size="sm" icon={<Save className="h-4 w-4" />}>
              Save Profile Changes
            </Button>
          </div>
        </form>
      </Card>

      {/* 2. Account & Security */}
      <Card
        title="Account & Security"
        subtitle="Update your authentication credentials"
      >
        <form onSubmit={handlePasswordChange} className="space-y-4 pt-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Current Password"
              type="password"
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              icon={<Shield className="h-4 w-4" />}
            />

            <Input
              label="New Password"
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              icon={<Shield className="h-4 w-4" />}
            />
          </div>

          <div className="flex justify-end pt-2">
            <Button type="submit" size="sm" variant="outline">
              Update Password
            </Button>
          </div>
        </form>
      </Card>

      {/* 3. Notification Preferences */}
      <Card
        title="Notification Preferences"
        subtitle="Configure alerts and automated system telemetry reminders"
      >
        <div className="space-y-3 pt-1">
          <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50/50 cursor-pointer transition-colors">
            <div className="flex items-start gap-3">
              <Bell className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <span className="text-xs font-semibold text-gray-900 block">Project Updates</span>
                <span className="text-[11px] text-gray-500 block">
                  Receive notifications when milestones are completed or deadlines shift.
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={projectUpdates}
              onChange={(e) => {
                setProjectUpdates(e.target.checked);
                showToast('Notification preference saved.');
              }}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50/50 cursor-pointer transition-colors">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5" />
              <div>
                <span className="text-xs font-semibold text-gray-900 block">Task Reminders</span>
                <span className="text-[11px] text-gray-500 block">
                  Daily digest of tasks nearing their estimated completion dates.
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={taskReminders}
              onChange={(e) => {
                setTaskReminders(e.target.checked);
                showToast('Notification preference saved.');
              }}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          </label>

          <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50/50 cursor-pointer transition-colors">
            <div className="flex items-start gap-3">
              <Shield className="h-4 w-4 text-rose-600 mt-0.5" />
              <div>
                <span className="text-xs font-semibold text-gray-900 block">ML Risk Alerts</span>
                <span className="text-[11px] text-gray-500 block">
                  Immediate alerts when a project transitions into HIGH risk ($\ge 70\%$).
                </span>
              </div>
            </div>
            <input
              type="checkbox"
              checked={riskAlerts}
              onChange={(e) => {
                setRiskAlerts(e.target.checked);
                showToast('Notification preference saved.');
              }}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
          </label>
        </div>
      </Card>

      {/* 4. Appearance */}
      <Card
        title="Appearance"
        subtitle="Choose a light or dark interface theme"
      >
        <div className="flex items-center gap-4 pt-1">
          <button
            type="button"
            onClick={() => setTheme('light')}
            aria-pressed={theme === 'light'}
            className={`flex items-center gap-2 px-4 py-2 rounded-md border text-xs font-semibold transition-colors ${
              theme === 'light'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Sun className="h-4 w-4 text-amber-500" />
            <span>Light Mode</span>
          </button>

          <button
            type="button"
            onClick={() => setTheme('dark')}
            aria-pressed={theme === 'dark'}
            className={`flex items-center gap-2 px-4 py-2 rounded-md border text-xs font-semibold transition-colors ${
              theme === 'dark'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Moon className="h-4 w-4 text-blue-500" />
            <span>Dark Mode</span>
          </button>
        </div>
      </Card>

      {/* 5. Account Actions */}
      <Card title="Account Actions">
        <div className="flex items-center justify-between pt-1">
          <div>
            <h4 className="text-xs font-semibold text-gray-900">Sign Out of Session</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">
              Securely disconnect your local session from this browser.
            </p>
          </div>
          <Button
            variant="danger"
            size="sm"
            onClick={handleLogout}
            icon={<LogOut className="h-4 w-4" />}
          >
            Logout
          </Button>
        </div>
      </Card>
    </div>
  );
};
