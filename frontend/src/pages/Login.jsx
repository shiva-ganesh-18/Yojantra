import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../hooks/useAuth';
import { authService } from '../services';
import { signInWithGooglePopup } from '../config/firebase';
import {
  CheckCircle2, ShieldCheck,
  Lock, Sparkles, Building2, Check, AlertCircle, Clock
} from 'lucide-react';

function GoogleIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleLoadingState, setGoogleLoadingState] = useState(''); // 'Connecting to Google...' | 'Signing in...'
  const [error, setError] = useState('');
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState(false);
  const { setToken, setUser } = useAuthStore();

  useEffect(() => {
    if (searchParams.get('session') === 'expired') {
      setSessionExpiredNotice(true);
    }
  }, [searchParams]);

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      setGoogleLoading(true);
      setGoogleLoadingState('Connecting to Google...');

      const { idToken } = await signInWithGooglePopup();

      setGoogleLoadingState('Signing in to Yojantra...');
      const data = await authService.loginWithGoogle(idToken);

      if (data.access_token) {
        setToken(data.access_token);
        setUser(data.user);
        navigate(data.user?.onboarding_completed ? '/dashboard' : '/onboarding');
      }
    } catch (err) {
      const serverMessage = err.details?.detail || err.response?.data?.detail;
      if (err.userMessage) {
        setError(err.userMessage);
      } else if (serverMessage) {
        if (typeof serverMessage === 'string' && serverMessage.toLowerCase().includes('not configured')) {
          setError('Google Sign-In is not configured on this server. Please contact your system administrator.');
        } else {
          setError(typeof serverMessage === 'string' ? serverMessage : 'Google sign-in failed. Please try again.');
        }
      } else if (err.message === 'FIREBASE_NOT_CONFIGURED') {
        setError('Google Sign-In requires Firebase configuration. Please check Firebase client settings.');
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Google sign-in failed. Please try again.');
      }
    } finally {
      setGoogleLoading(false);
      setGoogleLoadingState('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between font-sans">
      {/* Top Banner */}
      <header className="bg-gov-navy-950 text-white py-3 px-4 sm:px-8 border-b border-gov-navy-800">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-gov-navy-800 via-gov-saffron-600 to-gov-emerald-500 p-0.5 shadow-sm">
              <div className="w-full h-full bg-gov-navy-950 rounded-[6px] flex items-center justify-center font-black text-xs text-white">
                Y
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-baseline sm:gap-2">
              <span className="font-bold text-base tracking-tight text-white">Yojantra</span>
              <span className="text-[11px] text-slate-400 font-normal hidden sm:inline-block">
                Your intelligent path to government schemes
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <ShieldCheck size={16} className="text-gov-emerald-400" />
            <span className="hidden sm:inline">Secure Citizen Auth</span>
          </div>
        </div>
      </header>

      {/* Main Split Screen Area */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex items-center justify-center">
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">

          {/* Left Content Area: Value Propositions */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gov-saffron-500/10 border border-gov-saffron-500/20 text-gov-saffron-700 text-xs font-bold uppercase tracking-wider">
              <Sparkles size={14} className="text-gov-saffron-600" />
              National GovTech Platform
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gov-navy-950 tracking-tight leading-tight">
              Find the government schemes <br className="hidden sm:block" />
              <span className="bg-gradient-to-r from-gov-saffron-600 to-gov-navy-900 bg-clip-text text-transparent">
                made for you.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-xl">
              Yojantra provides AI-powered scheme discovery, clear eligibility guidance, and direct application support for entrepreneurs and citizens across India.
            </p>

            {/* 3 Simple Benefits */}
            <div className="space-y-4 pt-2">
              <div className="flex items-start gap-3.5">
                <div className="w-7 h-7 rounded-full bg-gov-emerald-100 text-gov-emerald-800 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold shadow-sm">
                  <Check size={16} />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-gov-navy-950">
                    Discover schemes you're eligible for
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-500">
                    Never miss capital subsidies, soft loans, or training grants from central and state ministries.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-7 h-7 rounded-full bg-gov-emerald-100 text-gov-emerald-800 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold shadow-sm">
                  <Check size={16} />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-gov-navy-950">
                    Understand why you qualify
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-500">
                    Our AI explains government criteria in plain language with transparent rules and zero jargon.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-7 h-7 rounded-full bg-gov-emerald-100 text-gov-emerald-800 flex items-center justify-center flex-shrink-0 mt-0.5 font-bold shadow-sm">
                  <Check size={16} />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-gov-navy-950">
                    Apply and track in one place
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-500">
                    Secure document vault, Aadhaar masking privacy, direct portal links, and Common Service Center routing.
                  </p>
                </div>
              </div>
            </div>

            {/* Institutional Trust Indicators */}
            <div className="pt-4 flex flex-wrap items-center gap-6 text-xs font-semibold text-slate-500 border-t border-slate-200">
              <div className="flex items-center gap-1.5">
                <Building2 size={16} className="text-gov-navy-700" />
                <span>50+ Verified Central & State Schemes</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Lock size={15} className="text-gov-navy-700" />
                <span>256-Bit Data Encryption</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={15} className="text-gov-emerald-600" />
                <span>Privacy Safeguards Enabled</span>
              </div>
            </div>

          </div>

          {/* Right Area: Login Card */}
          <div className="lg:col-span-5 w-full max-w-md mx-auto">
            <div className="bg-white rounded-3xl shadow-xl border border-slate-200/90 p-6 sm:p-8 relative overflow-hidden">
              {/* Top tri-color accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-gov-navy-900 via-gov-saffron-500 to-gov-emerald-500" />

              {/* Header with Yojantra branding */}
              <div className="mb-6 text-left">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-lg bg-gov-navy-950 flex items-center justify-center text-white font-black text-xs">
                    Y
                  </div>
                  <span className="text-lg font-extrabold text-gov-navy-950 tracking-tight">Yojantra</span>
                </div>
                <h2 className="text-2xl font-bold text-gov-navy-950">
                  Welcome to Yojantra
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Sign in with your Google account to access your matched government schemes.
                </p>
              </div>

              {/* Session Expired Notice */}
              {sessionExpiredNotice && !error && (
                <div className="bg-amber-50 border border-amber-200 text-amber-900 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm mb-4 text-left leading-snug flex items-start gap-2">
                  <Clock size={16} className="text-amber-700 flex-shrink-0 mt-0.5" />
                  <span>Your session has expired. Please sign in with Google again to continue.</span>
                </div>
              )}

              {/* Error Banner */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm mb-4 text-left leading-snug flex items-start gap-2">
                  <AlertCircle size={16} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-4">
                {/* Google Authentication Button */}
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={googleLoading}
                  className="w-full py-3.5 px-4 rounded-xl border border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50 text-slate-800 font-semibold text-sm sm:text-base shadow-sm hover:shadow transition-all flex items-center justify-center gap-3 disabled:opacity-60 disabled:cursor-not-allowed group cursor-pointer"
                >
                  {googleLoading ? (
                    <>
                      <span className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                      <span className="text-slate-600">{googleLoadingState || 'Connecting to Google...'}</span>
                    </>
                  ) : (
                    <>
                      <GoogleIcon className="w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-105" />
                      <span>Continue with Google</span>
                    </>
                  )}
                </button>

                <div className="pt-2 text-center text-xs text-slate-500 leading-relaxed">
                  <p>
                    By signing in, you agree to Yojantra's terms of service and acknowledge that your data is protected under standard citizen data protection safeguards.
                  </p>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-xs text-slate-400 border-t border-slate-200 bg-white">
        <p>
          Yojantra &copy; 2026. Your intelligent path to government schemes. Built with privacy safeguards and encrypted storage.
        </p>
      </footer>
    </div>
  );
}
