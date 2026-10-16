import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Lock, Mail, User, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { api } from '../services/api';
import type { UserRole } from '../types';
import { ThemeToggle } from '../components/common/ThemeToggle';

export const SignUpPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<UserRole>('Project Manager');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendMessage, setResendMessage] = useState<string | null>(null);

  const { signup } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    let timer: any;
    if (resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleResend = async () => {
    setResendMessage(null);
    setResendLoading(true);
    try {
      const res = await api.auth.resendVerification(email.trim());
      setResendCooldown(60);
      setResendMessage(res.message || 'Verification link resent successfully.');
    } catch (err: any) {
      setResendMessage(err?.message || 'Failed to resend verification email.');
    } finally {
      setResendLoading(false);
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!fullName.trim()) errs.fullName = 'Full Name is required.';
    if (!email.trim()) errs.email = 'Email address is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = 'Please enter a valid email address.';

    if (!password) {
      errs.password = 'Password is required.';
    } else if (password.length < 8) {
      errs.password = 'Password must be at least 8 characters.';
    } else if (!/[a-zA-Z]/.test(password)) {
      errs.password = 'Password must contain at least one letter.';
    } else if (!/[0-9]/.test(password)) {
      errs.password = 'Password must contain at least one number.';
    }

    if (!confirmPassword) {
      errs.confirmPassword = 'Confirm your password.';
    } else if (confirmPassword !== password) {
      errs.confirmPassword = 'Passwords do not match.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 400));
      await signup(fullName.trim(), email.trim(), password, role);
      setIsSuccess(true);
    } catch (err: any) {
      setErrors({ general: err?.message || 'Failed to create account. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="fixed right-4 top-4 z-50">
        <ThemeToggle />
      </div>
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
          Create an Account
        </h2>
        <p className="mt-1 text-center text-xs text-gray-500">
          Join your engineering workspace and start predicting delivery timelines
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-gray-200 rounded-lg sm:px-10">
          {isSuccess ? (
            <div className="p-4 text-center space-y-4">
              <div className="h-12 w-12 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 mx-auto">
                <Mail className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">Check your email</h3>
                <p className="mt-1.5 text-xs text-gray-600 leading-relaxed">
                  We&apos;ve sent a verification link to <span className="font-semibold text-gray-900">{email}</span>.
                  Please verify your email before signing in.
                </p>
              </div>

              {resendMessage && (
                <div className="p-2.5 rounded-md bg-blue-50 border border-blue-100 text-xs text-blue-700 font-medium">
                  {resendMessage}
                </div>
              )}

              <div className="pt-2 flex flex-col gap-2">
                <Button
                  onClick={() => navigate('/login')}
                  className="w-full text-xs"
                >
                  Proceed to Sign In
                </Button>
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resendLoading || resendCooldown > 0}
                  className="text-xs text-blue-600 hover:text-blue-500 font-medium hover:underline disabled:text-gray-400 disabled:no-underline"
                >
                  {resendLoading
                    ? 'Sending...'
                    : resendCooldown > 0
                    ? `Resend email in ${resendCooldown}s`
                    : "Didn't receive the email? Resend verification link"}
                </button>
              </div>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={handleSubmit} noValidate>
              {errors.general && (
                <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 font-medium">
                  {errors.general}
                </div>
              )}

              <Input
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Please enter your name"
                error={errors.fullName}
                icon={<User className="h-4 w-4" />}
                required
              />

              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                error={errors.email}
                icon={<Mail className="h-4 w-4" />}
                required
              />

              <Select
                label="Primary Role"
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                options={[
                  { value: 'Project Manager', label: 'Project Manager' },
                  { value: 'Team Member', label: 'Team Member / Engineer' },
                ]}
              />

              <Input
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                error={errors.password}
                icon={<Lock className="h-4 w-4" />}
                helperText="Must be at least 8 characters"
                required
              />

              <Input
                label="Confirm Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                error={errors.confirmPassword}
                icon={<ShieldCheck className="h-4 w-4" />}
                required
              />

              <Button
                type="submit"
                className="w-full mt-2"
                isLoading={isLoading}
              >
                Create Account
              </Button>

              <div className="pt-2 text-center text-xs text-gray-500">
                Already registered?{' '}
                <Link to="/login" className="font-semibold text-blue-600 hover:text-blue-500 hover:underline">
                  Sign in here
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
