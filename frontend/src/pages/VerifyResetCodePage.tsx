import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Activity, KeyRound, ArrowRight, ArrowLeft, AlertTriangle, CheckCircle2, RotateCw } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { api } from '../services/api';

export const VerifyResetCodePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const initialEmail = searchParams.get('email') || sessionStorage.getItem('reset_email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    let timer: any;
    if (resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const trimmedEmail = email.trim();
    const cleanCode = code.trim();

    if (!trimmedEmail) {
      setError('Please provide the registered email address.');
      return;
    }

    if (!cleanCode) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    if (!/^\d{6}$/.test(cleanCode)) {
      setError('The verification code must be exactly 6 digits.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await api.auth.verifyResetCode(trimmedEmail, cleanCode);
      setSuccess('Verification successful! Proceeding to reset password...');
      sessionStorage.setItem('reset_token', res.reset_token);

      setTimeout(() => {
        navigate(`/reset-password?token=${encodeURIComponent(res.reset_token)}`);
      }, 900);
    } catch (err: any) {
      setError(err?.message || 'The verification code is invalid.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0 || isResending) return;
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('Please enter your email address to resend code.');
      return;
    }

    setIsResending(true);
    setError('');
    try {
      const res = await api.auth.forgotPassword(trimmedEmail);
      setSuccess('A new verification code has been dispatched.');
      setResendCooldown(30); // 30-second cooldown
      if (res.dev_code) {
        setSuccess(`New verification code generated (Dev OTP: ${res.dev_code})`);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to resend code. Please try again.');
    } finally {
      setIsResending(false);
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
          Verify Security Code
        </h2>
        <p className="mt-1 text-center text-xs text-gray-500">
          Code expires in approximately 10 minutes.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-gray-200 rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-xs text-red-700 font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 rounded-md bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>{success}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleVerify}>
            {!initialEmail && (
              <Input
                label="Registered Email address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
              />
            )}

            <Input
              label="Verification Code (6-digits)"
              type="text"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              placeholder="482731"
              icon={<KeyRound className="h-4 w-4" />}
              required
            />

            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-gray-500">
                Sent to: <strong className="text-gray-800">{email || 'your email'}</strong>
              </span>

              <button
                type="button"
                onClick={handleResend}
                disabled={resendCooldown > 0 || isResending}
                className={`font-semibold inline-flex items-center gap-1 ${
                  resendCooldown > 0
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-blue-600 hover:text-blue-500 hover:underline'
                }`}
              >
                <RotateCw className={`h-3 w-3 ${isResending ? 'animate-spin' : ''}`} />
                {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend Code'}
              </button>
            </div>

            <Button
              type="submit"
              className="w-full mt-3"
              isLoading={isLoading}
              icon={<ArrowRight className="h-4 w-4" />}
            >
              Verify Code
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-gray-100 flex items-center justify-between text-xs">
            <Link
              to="/forgot-password"
              className="inline-flex items-center gap-1 font-semibold text-gray-500 hover:text-gray-800"
            >
              <ArrowLeft className="h-3 w-3" /> Change Email
            </Link>

            <Link
              to="/login"
              className="font-semibold text-blue-600 hover:text-blue-500 hover:underline"
            >
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
