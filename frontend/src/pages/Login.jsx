import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../hooks/useAuth';
import { authService } from '../services';
import { 
  CheckCircle2, ShieldCheck, ArrowRight, Smartphone, KeyRound, 
  RefreshCw, Lock, Sparkles, Building2, HelpCircle, Check
} from 'lucide-react';

export default function Login() {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone'); // 'phone' | 'otp'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [devOtpHint, setDevOtpHint] = useState('');
  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const { setToken, setUser } = useAuthStore();

  // Timer countdown for OTP resend
  useEffect(() => {
    let interval = null;
    if (step === 'otp' && timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    } else if (timer === 0) {
      setCanResend(true);
      if (interval) clearInterval(interval);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [step, timer]);

  const handleSendOtp = async (inputPhone = phone) => {
    const rawNumber = inputPhone.replace(/\D/g, '').slice(0, 10);
    if (rawNumber.length !== 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setDevOtpHint('');
      const fullPhone = `+91${rawNumber}`;
      const data = await authService.sendOtp(fullPhone);
      
      if (data.dev_otp) {
        setDevOtpHint(data.dev_otp);
        // Pre-fill dev OTP for rapid hackathon testing if user wishes
      }
      setStep('otp');
      setTimer(60);
      setCanResend(false);
    } catch (err) {
      setError(err.message || 'Failed to send OTP. Please check your phone number and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const fullPhone = `+91${phone}`;
      const data = await authService.verifyOtp(fullPhone, otp);

      if (data.access_token) {
        setToken(data.access_token);
        setUser(data.user);
      }
    } catch (err) {
      setError(err.message || 'Invalid or expired OTP. Please enter the correct verification code.');
    } finally {
      setLoading(false);
    }
  };

  const selectDemoAccount = (demoPhone, defaultOtp = '123456') => {
    setPhone(demoPhone);
    setOtp(defaultOtp);
    setError('');
    handleSendOtp(demoPhone);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between font-sans">
      {/* Top Banner */}
      <header className="bg-gov-navy-950 text-white py-3 px-4 sm:px-8 border-b border-gov-navy-800">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-gov-navy-800 via-gov-saffron-600 to-gov-emerald-500 p-0.5">
              <div className="w-full h-full bg-gov-navy-950 rounded-[6px] flex items-center justify-center font-black text-xs text-white">
                SM
              </div>
            </div>
            <span className="font-bold text-base tracking-tight">SchemeMatch AI</span>
            <span className="hidden sm:inline-block text-[11px] text-slate-400 border-l border-slate-700 pl-2 ml-1">
              Ministry of MSME & Social Justice Initiative Gateway
            </span>
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
              AI-Powered Citizen Platform
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gov-navy-950 tracking-tight leading-tight">
              Find the government schemes <br className="hidden sm:block" />
              <span className="bg-gradient-to-r from-gov-saffron-600 to-gov-navy-900 bg-clip-text text-transparent">
                made for you.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-xl">
              AI-powered scheme discovery, eligibility guidance, and direct application support for marginalized entrepreneurs and citizens across India.
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
                    Never miss capital subsidies, soft loans, or training grants from central & state ministries.
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
                    Our AI explains complex government criteria in plain language with zero technical jargon.
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
                    Automated document OCR extraction, direct DBT application filing, and Common Service Center routing.
                  </p>
                </div>
              </div>
            </div>

            {/* Institutional Trust Indicators */}
            <div className="pt-4 flex flex-wrap items-center gap-6 text-xs font-semibold text-slate-500 border-t border-slate-200">
              <div className="flex items-center gap-1.5">
                <Building2 size={16} className="text-gov-navy-700" />
                <span>200+ Central & State Schemes</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Lock size={15} className="text-gov-navy-700" />
                <span>256-Bit Data Encryption</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={15} className="text-gov-emerald-600" />
                <span>Zero Intermediary Fees</span>
              </div>
            </div>

          </div>

          {/* Right Area: Login Card */}
          <div className="lg:col-span-5 w-full max-w-md mx-auto">
            <div className="bg-white rounded-3xl shadow-xl border border-slate-200/90 p-6 sm:p-8 relative overflow-hidden">
              {/* Subtle top saffron accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-gov-navy-900 via-gov-saffron-500 to-gov-emerald-500" />

              <div className="mb-6 text-left">
                <h2 className="text-2xl font-bold text-gov-navy-950">
                  {step === 'phone' ? 'Sign In / Register' : 'Verify Mobile OTP'}
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  {step === 'phone' 
                    ? 'Enter your mobile number to check eligibility' 
                    : `We sent a 6-digit verification code to +91 ${phone}`}
                </p>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm mb-4 text-left leading-snug">
                  {error}
                </div>
              )}

              {/* Development OTP Banner */}
              {devOtpHint && (
                <div className="bg-amber-50 border border-amber-300 text-amber-900 px-4 py-2.5 rounded-xl text-xs mb-4 text-left font-mono flex items-center justify-between">
                  <span>Dev OTP Code: <strong className="text-sm text-gov-saffron-700">{devOtpHint}</strong></span>
                  <button 
                    type="button"
                    onClick={() => setOtp(devOtpHint)}
                    className="text-[11px] font-sans font-bold text-gov-saffron-700 underline hover:text-gov-saffron-800"
                  >
                    Auto-Fill
                  </button>
                </div>
              )}

              {step === 'phone' ? (
                /* Step 1: Phone Input Form */
                <form onSubmit={(e) => { e.preventDefault(); handleSendOtp(); }} className="space-y-4">
                  <div className="text-left">
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wide">
                      Mobile Number
                    </label>
                    <div className="flex rounded-xl border border-slate-300 focus-within:border-gov-navy-900 focus-within:ring-2 focus-within:ring-gov-navy-900/10 transition-all overflow-hidden bg-slate-50">
                      <span className="inline-flex items-center px-3.5 text-sm font-semibold text-slate-700 border-r border-slate-200 bg-slate-100">
                        🇮🇳 +91
                      </span>
                      <input
                        type="tel"
                        autoFocus
                        value={phone}
                        onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                        placeholder="Enter 10-digit number"
                        className="flex-1 bg-white px-4 py-3 text-sm sm:text-base font-medium text-slate-900 focus:outline-none"
                      />
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">
                      An OTP will be sent via SMS for passwordless login.
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={phone.length !== 10 || loading}
                    className="w-full py-3.5 px-4 rounded-xl bg-gov-navy-950 hover:bg-gov-navy-900 active:bg-gov-navy-900 text-white font-bold text-sm sm:text-base shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Sending OTP...</span>
                      </>
                    ) : (
                      <>
                        <span>Continue</span>
                        <ArrowRight size={17} />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                /* Step 2: OTP Verification Form */
                <form onSubmit={(e) => { e.preventDefault(); handleVerifyOtp(); }} className="space-y-4">
                  <div className="text-left">
                    <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wide">
                      Enter 6-Digit OTP
                    </label>
                    <input
                      type="text"
                      autoFocus
                      maxLength={6}
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="• • • • • •"
                      className="w-full border border-slate-300 rounded-xl px-4 py-3 text-center text-2xl font-bold tracking-widest text-gov-navy-950 focus:border-gov-navy-900 focus:ring-2 focus:ring-gov-navy-900/10 focus:outline-none"
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      {timer > 0 ? (
                        `Resend OTP in ${timer}s`
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleSendOtp(phone)}
                          className="text-gov-saffron-700 font-bold hover:underline"
                        >
                          Resend OTP
                        </button>
                      )}
                    </span>
                    <button
                      type="button"
                      onClick={() => { setStep('phone'); setError(''); setOtp(''); setDevOtpHint(''); }}
                      className="text-slate-500 hover:text-gov-navy-900 font-medium"
                    >
                      Change Number
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={otp.length !== 6 || loading}
                    className="w-full py-3.5 px-4 rounded-xl bg-gov-saffron-600 hover:bg-gov-saffron-700 text-white font-bold text-sm sm:text-base shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Verifying...</span>
                      </>
                    ) : (
                      <>
                        <span>Verify & Sign In</span>
                        <ArrowRight size={17} />
                      </>
                    )}
                  </button>
                </form>
              )}

              {/* Demo Account Fast Switcher for Judges / Evaluators */}
              <div className="mt-6 pt-5 border-t border-slate-100 text-left">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Fast Demo Logins (SIH Evaluator)</span>
                  <span className="text-[10px] lowercase text-gov-emerald-700 bg-gov-emerald-50 px-1.5 py-0.2 rounded font-mono">
                    click to test
                  </span>
                </p>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => selectDemoAccount('9876543210', '123456')}
                    className="p-2 rounded-xl border border-slate-200 hover:border-gov-navy-900 hover:bg-slate-50 transition-all text-left"
                  >
                    <p className="font-bold text-gov-navy-950 truncate">Ramesh K.</p>
                    <p className="text-[10px] text-slate-500">OBC / Micro</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => selectDemoAccount('9123456780', '123456')}
                    className="p-2 rounded-xl border border-slate-200 hover:border-gov-navy-900 hover:bg-slate-50 transition-all text-left"
                  >
                    <p className="font-bold text-gov-navy-950 truncate">Sunita D.</p>
                    <p className="text-[10px] text-slate-500">Woman MSME</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => selectDemoAccount('9999999999', '123456')}
                    className="p-2 rounded-xl border border-slate-200 hover:border-gov-navy-900 hover:bg-slate-50 transition-all text-left bg-slate-50/50"
                  >
                    <p className="font-bold text-gov-saffron-700 truncate">Admin</p>
                    <p className="text-[10px] text-slate-500">Executive</p>
                  </button>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-xs text-slate-400 border-t border-slate-200 bg-white">
        <p>
          SchemeMatch AI &copy; 2026. Designed for India's Smart India Hackathon. Citizen data encrypted in compliance with Digital Personal Data Protection Act.
        </p>
      </footer>
    </div>
  );
}
