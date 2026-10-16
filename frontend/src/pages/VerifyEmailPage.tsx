import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Activity, Mail, CheckCircle2, AlertCircle, Clock, ArrowRight, RefreshCw } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { api } from '../services/api';

type VerificationStatus = 'LOADING' | 'SUCCESS' | 'ALREADY_VERIFIED' | 'EXPIRED' | 'INVALID' | 'ERROR';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<VerificationStatus>('LOADING');
  const [statusMessage, setStatusMessage] = useState<string>('Verifying your email...');
  const [resendEmail, setResendEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendFeedback, setResendFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);

  const isMountedRef = useRef(true);
  const tokenRequestRef = useRef<{ token: string; promise: Promise<any> } | null>(null);

  useEffect(() => {
    let timer: any;
    if (resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCooldown]);

  useEffect(() => {
    isMountedRef.current = true;

    if (!token || !token.trim()) {
      setStatus('INVALID');
      setStatusMessage('This verification link is invalid. No verification token was provided.');
      return;
    }

    const cleanToken = token.trim();

    // Cache the verification promise per token to prevent React StrictMode double-execution from consuming single-use tokens twice
    if (!tokenRequestRef.current || tokenRequestRef.current.token !== cleanToken) {
      tokenRequestRef.current = {
        token: cleanToken,
        promise: api.auth.verifyEmail(cleanToken),
      };
    }

    tokenRequestRef.current.promise
      .then((res) => {
        if (!isMountedRef.current) return;
        if (res.already_verified) {
          setStatus('ALREADY_VERIFIED');
          setStatusMessage('Your email address is already verified.');
        } else {
          setStatus('SUCCESS');
          setStatusMessage('Email verified successfully. Your ProjectPulse account is now verified.');
        }
      })
      .catch((err: any) => {
        if (!isMountedRef.current) return;
        const msg = String(err?.message || '');

        if (msg.toLowerCase().includes('expired')) {
          setStatus('EXPIRED');
          setStatusMessage('This verification link has expired. Please request a new one below.');
        } else if (
          msg.toLowerCase().includes('already verified') ||
          msg.toLowerCase().includes('already been used') ||
          msg.toLowerCase().includes('already used')
        ) {
          setStatus('ALREADY_VERIFIED');
          setStatusMessage('Your email address is already verified or this verification link has already been used.');
        } else {
          setStatus('INVALID');
          setStatusMessage(msg || 'This verification link is invalid.');
        }
      });

    return () => {
      isMountedRef.current = false;
    };
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResendFeedback(null);

    const email = resendEmail.trim();
    if (!email) {
      setResendFeedback({ type: 'error', text: 'Please enter your email address.' });
      return;
    }

    setResendLoading(true);
    try {
      const res = await api.auth.resendVerification(email);
      setResendCooldown(60);
      setResendFeedback({
        type: 'success',
        text: res.message || 'If an account exists, a new verification link has been sent.',
      });
    } catch (err: any) {
      setResendFeedback({
        type: 'error',
        text: err?.message || 'Failed to send verification email. Please try again.',
      });
    } finally {
      setResendLoading(false);
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
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-gray-200 rounded-lg sm:px-10 animate-slide-up">
          {/* 1. LOADING STATE */}
          {status === 'LOADING' && (
            <div className="text-center py-8 space-y-4">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-blue-50 text-blue-600 animate-spin">
                <RefreshCw className="h-6 w-6" />
              </div>
              <h2 className="text-base font-bold text-gray-900">Verifying your email...</h2>
              <p className="text-xs text-gray-500">
                Please wait while we validate your verification token.
              </p>
            </div>
          )}

          {/* 2. SUCCESS STATE */}
          {status === 'SUCCESS' && (
            <div className="text-center py-4 space-y-4">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-emerald-50 text-emerald-600">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">Email Verified Successfully</h2>
                <p className="mt-1 text-xs text-gray-600 leading-relaxed">
                  {statusMessage}
                </p>
              </div>
              <Button
                onClick={() => navigate('/login')}
                className="w-full mt-4"
                icon={<ArrowRight className="h-4 w-4" />}
              >
                Continue to ProjectPulse
              </Button>
            </div>
          )}

          {/* 3. ALREADY VERIFIED STATE */}
          {status === 'ALREADY_VERIFIED' && (
            <div className="text-center py-4 space-y-4">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-blue-50 text-blue-600">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">Already Verified</h2>
                <p className="mt-1 text-xs text-gray-600 leading-relaxed">
                  Your email address is already verified. You can sign in to your workspace.
                </p>
              </div>
              <Button
                onClick={() => navigate('/login')}
                className="w-full mt-4"
                icon={<ArrowRight className="h-4 w-4" />}
              >
                Continue to ProjectPulse
              </Button>
            </div>
          )}

          {/* 4. EXPIRED STATE */}
          {status === 'EXPIRED' && (
            <div className="py-2 space-y-4">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-amber-50 text-amber-600">
                  <Clock className="h-7 w-7" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Verification Link Expired</h2>
                <p className="text-xs text-gray-600 leading-relaxed">
                  This verification link has expired. Enter your email address below to receive a fresh verification link.
                </p>
              </div>

              {resendFeedback && (
                <div
                  className={`p-3 rounded-md text-xs font-medium border ${
                    resendFeedback.type === 'success'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  {resendFeedback.text}
                </div>
              )}

              <form onSubmit={handleResend} className="space-y-3 pt-2">
                <Input
                  label="Registered Email Address"
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="Enter your email address"
                  icon={<Mail className="h-4 w-4" />}
                  required
                />
                <Button
                  type="submit"
                  className="w-full"
                  isLoading={resendLoading}
                  disabled={resendCooldown > 0}
                >
                  {resendCooldown > 0
                    ? `Resend in ${resendCooldown}s`
                    : 'Resend Verification Email'}
                </Button>
              </form>

              <div className="text-center pt-2">
                <Link
                  to="/login"
                  className="text-xs font-medium text-blue-600 hover:text-blue-500 hover:underline"
                >
                  Back to Sign In
                </Link>
              </div>
            </div>
          )}

          {/* 5. INVALID STATE */}
          {(status === 'INVALID' || status === 'ERROR') && (
            <div className="py-2 space-y-4">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-red-50 text-red-600">
                  <AlertCircle className="h-7 w-7" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Invalid Verification Link</h2>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {statusMessage}
                </p>
              </div>

              {resendFeedback && (
                <div
                  className={`p-3 rounded-md text-xs font-medium border ${
                    resendFeedback.type === 'success'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}
                >
                  {resendFeedback.text}
                </div>
              )}

              <form onSubmit={handleResend} className="space-y-3 pt-2">
                <Input
                  label="Request New Verification Link"
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="Enter your email address"
                  icon={<Mail className="h-4 w-4" />}
                  required
                />
                <Button
                  type="submit"
                  className="w-full"
                  isLoading={resendLoading}
                  disabled={resendCooldown > 0}
                >
                  {resendCooldown > 0
                    ? `Resend in ${resendCooldown}s`
                    : 'Resend Verification Email'}
                </Button>
              </form>

              <div className="text-center pt-2">
                <Link
                  to="/login"
                  className="text-xs font-medium text-blue-600 hover:text-blue-500 hover:underline"
                >
                  Back to Sign In
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
