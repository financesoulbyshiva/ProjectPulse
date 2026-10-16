import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Activity, Lock, Eye, EyeOff, ArrowRight, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { api } from '../services/api';

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const resetToken = searchParams.get('token') || sessionStorage.getItem('reset_token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const validate = () => {
    const errs: Record<string, string> = {};

    if (!newPassword) {
      errs.newPassword = 'Password is required.';
    } else if (newPassword.length < 8) {
      errs.newPassword = 'Password must be at least 8 characters.';
    } else if (!/[a-zA-Z]/.test(newPassword)) {
      errs.newPassword = 'Password must contain at least one letter.';
    } else if (!/[0-9]/.test(newPassword)) {
      errs.newPassword = 'Password must contain at least one number.';
    }

    if (!confirmPassword) {
      errs.confirmPassword = 'Confirm your new password.';
    } else if (confirmPassword !== newPassword) {
      errs.confirmPassword = 'Passwords do not match.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError('');

    if (!resetToken) {
      setGeneralError('Invalid or expired password reset session. Please request a new verification code.');
      return;
    }

    if (!validate()) return;

    setIsLoading(true);
    try {
      await api.auth.resetPassword(resetToken, newPassword);
      setIsSuccess(true);
      sessionStorage.removeItem('reset_token');
      sessionStorage.removeItem('reset_email');

      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err: any) {
      setGeneralError(err?.message || 'Failed to update password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center items-center gap-2.5 mb-2">
          <div className="h-10 w-10 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Activity className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-gray-900">
            ProjectPulse
          </span>
        </div>
        <p className="text-center text-xs text-gray-500 font-medium tracking-wide uppercase">
          Track. Analyze. Predict. Deliver.
        </p>
        <h2 className="mt-6 text-center text-xl font-bold tracking-tight text-gray-900">
          Reset Your Password
        </h2>
        <p className="mt-1 text-center text-xs text-gray-500">
          Create a strong password with at least 8 characters, letters, and numbers.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-gray-200 rounded-lg sm:px-10">
          {isSuccess ? (
            <div className="py-4 text-center space-y-3">
              <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
              <h3 className="text-base font-semibold text-gray-900">
                Password updated successfully.
              </h3>
              <p className="text-xs text-gray-500">
                Your credentials have been securely updated. Redirecting to login...
              </p>
              <div className="pt-2">
                <Button
                  size="sm"
                  onClick={() => navigate('/login')}
                  icon={<ArrowRight className="h-4 w-4" />}
                >
                  Back to Login
                </Button>
              </div>
            </div>
          ) : (
            <>
              {generalError && (
                <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 font-medium flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
                  <span>{generalError}</span>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <Input
                  label="New Password"
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  error={errors.newPassword}
                  icon={<Lock className="h-4 w-4" />}
                  rightElement={
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-gray-400 hover:text-gray-600 focus:outline-none"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  required
                />

                <Input
                  label="Confirm New Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  error={errors.confirmPassword}
                  icon={<Lock className="h-4 w-4" />}
                  rightElement={
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="text-gray-400 hover:text-gray-600 focus:outline-none"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                  required
                />

                <div className="text-[11px] text-gray-500 space-y-1 bg-gray-50 p-2.5 rounded border border-gray-100">
                  <span className="font-semibold text-gray-700 block">Password Requirements:</span>
                  <div className="flex items-center gap-1.5">
                    <span className={newPassword.length >= 8 ? 'text-emerald-600 font-bold' : 'text-gray-400'}>
                      •
                    </span>
                    <span>Minimum 8 characters</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={/[a-zA-Z]/.test(newPassword) ? 'text-emerald-600 font-bold' : 'text-gray-400'}>
                      •
                    </span>
                    <span>At least one letter (a-z, A-Z)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={/[0-9]/.test(newPassword) ? 'text-emerald-600 font-bold' : 'text-gray-400'}>
                      •
                    </span>
                    <span>At least one number (0-9)</span>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full mt-2"
                  isLoading={isLoading}
                  icon={<ArrowRight className="h-4 w-4" />}
                >
                  Reset Password
                </Button>
              </form>

              <div className="mt-6 pt-5 border-t border-gray-100 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-500 hover:underline"
                >
                  <ArrowLeft className="h-3.5 w-3.5" /> Return to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
