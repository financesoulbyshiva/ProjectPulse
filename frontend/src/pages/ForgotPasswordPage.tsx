import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Mail, ArrowRight, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { api } from '../services/api';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [devCode, setDevCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setDevCode(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('Email address is required.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.auth.forgotPassword(trimmedEmail);
      setSuccessMessage(res.message);
      if (res.dev_code) {
        setDevCode(res.dev_code);
      }
      sessionStorage.setItem('reset_email', trimmedEmail);

      // Transition smoothly to code verification
      setTimeout(() => {
        navigate(`/verify-reset-code?email=${encodeURIComponent(trimmedEmail)}`);
      }, 1400);
    } catch (err: any) {
      setError(err?.message || 'Unable to process your request. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 animate-fade-in">
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
          Forgot Password
        </h2>
        <p className="mt-1 text-center text-xs text-gray-500">
          Enter your registered email address and we'll send you a verification code.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-gray-200 rounded-lg sm:px-10 animate-slide-up">
          {error && (
            <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-3 rounded-md bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                <span>{successMessage}</span>
              </div>
              {devCode && (
                <div className="text-[11px] font-mono bg-white p-2 rounded border border-emerald-200 text-emerald-950">
                  Dev OTP: <strong>{devCode}</strong>
                </div>
              )}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Registered Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              icon={<Mail className="h-4 w-4" />}
              required
            />

            <Button
              type="submit"
              className="w-full mt-2"
              isLoading={isLoading}
              icon={<ArrowRight className="h-4 w-4" />}
            >
              Send Verification Code
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
        </div>
      </div>
    </div>
  );
};
