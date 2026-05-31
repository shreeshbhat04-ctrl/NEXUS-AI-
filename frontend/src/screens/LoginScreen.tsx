import React, { useCallback, useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Heart, Mail, HardDrive, Calendar, CheckCircle2 } from 'lucide-react';
import logo from '../assets/logo.png';
import { exchangeGoogleAuth, patient2Image, type GoogleAuthResponse, DEMO_PATIENT_ID } from '../lib/api';

// Google OAuth Client ID — loaded from env or hardcoded fallback
const GOOGLE_CLIENT_ID = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID ?? '';

interface LoginScreenProps {
  onLogin: (patientId: number) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [googleReady, setGoogleReady] = useState(false);
  const [authResult, setAuthResult] = useState<GoogleAuthResponse | null>(null);

  // Load Google Identity Services script
  useEffect(() => {
    if (document.getElementById('google-gis-script')) {
      setGoogleReady(true);
      return;
    }
    const script = document.createElement('script');
    script.id = 'google-gis-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleReady(true);
    document.head.appendChild(script);
  }, []);

  const handleGoogleSignIn = useCallback(() => {
    if (!GOOGLE_CLIENT_ID) {
      setAuthError('Google OAuth Client ID not configured. Set VITE_GOOGLE_CLIENT_ID in your .env.');
      return;
    }
    if (!(window as any).google?.accounts?.oauth2) {
      setAuthError('Google Identity Services not loaded yet. Try again in a moment.');
      return;
    }

    setIsLoggingIn(true);
    setAuthError(null);

    const client = (window as any).google.accounts.oauth2.initCodeClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: [
        'openid',
        'email',
        'profile',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
      ].join(' '),
      ux_mode: 'popup',
      callback: async (response: any) => {
        if (response.error) {
          setAuthError(response.error);
          setIsLoggingIn(false);
          return;
        }
        try {
          const result = await exchangeGoogleAuth(response.code);
          setAuthResult(result);
          // Brief pause to show success state
          setTimeout(() => onLogin(result.patient_id), 800);
        } catch (e) {
          setAuthError(e instanceof Error ? e.message : 'Authentication failed.');
          setIsLoggingIn(false);
        }
      },
    });
    client.requestCode();
  }, [onLogin]);

  const handleDevLogin = () => {
    setIsLoggingIn(true);
    setTimeout(() => onLogin(DEMO_PATIENT_ID), 600);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-surface overflow-hidden">
      {/* Ambient background blobs */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(66,133,244,0.12),transparent_40%),radial-gradient(circle_at_75%_70%,rgba(52,168,83,0.1),transparent_35%)]" />
      <div className="pointer-events-none absolute right-[-8rem] top-[-6rem] h-96 w-96 rounded-full bg-primary-fixed/20 blur-[80px]" />
      <div className="pointer-events-none absolute left-[-5rem] bottom-[10%] h-80 w-80 rounded-full bg-tertiary-container/15 blur-[80px]" />

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 flex w-full max-w-[440px] flex-col items-center px-6"
      >
        {/* Logo */}
        <div className="mb-10 flex flex-col items-center gap-4">
          <div className="flex h-20 w-20 items-center justify-center rounded-[1.75rem] bg-surface-container-lowest shadow-[0_16px_40px_-8px_rgba(60,64,67,0.2)] overflow-hidden">
            <img src={logo} alt="nexus_ai Logo" className="h-14 w-14 object-contain" />
          </div>
          <div className="text-center">
            <h1 className="font-serif text-[2.4rem] font-semibold tracking-[-0.03em] text-primary">
              nexus_ai
            </h1>
            <p className="mt-1 text-[1rem] leading-7 text-on-surface/55">
              Your Digital Sanctuary
            </p>
          </div>
        </div>

        {/* Login Card */}
        <div className="w-full rounded-[2.25rem] bg-surface-container-lowest/85 p-8 shadow-[0_24px_54px_-12px_rgba(60,64,67,0.1)] backdrop-blur-[20px]">
          {/* Patient Profile Preview */}
          <div className="mb-6 flex items-center gap-4 rounded-[1.75rem] bg-surface-container-low px-5 py-5 border border-outline-variant/10">
            <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-full border-2 border-primary/20 shadow-sm">
              <img src={patient2Image} alt="Patient" className="h-full w-full object-cover" />
            </div>
            <div>
              <p className="font-serif text-[1.15rem] font-medium text-on-surface">
                {authResult ? authResult.name : 'Shreesha'}
              </p>
              <p className="text-[0.88rem] leading-5 text-on-surface/50">
                {authResult ? authResult.email : `Patient ID: ${DEMO_PATIENT_ID}`}
              </p>
            </div>
          </div>

          {/* Connected Services Badges */}
          {authResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-6 flex flex-wrap gap-2"
            >
              {[
                { icon: HardDrive, label: 'Drive' },
                { icon: Calendar, label: 'Calendar' },
                { icon: Mail, label: 'Gmail' },
              ].map(({ icon: Icon, label }) => (
                <span key={label} className="inline-flex items-center gap-1.5 rounded-full bg-primary-fixed/35 px-3 py-1.5 text-[0.82rem] font-medium text-primary">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {label}
                </span>
              ))}
            </motion.div>
          )}

          {/* Welcome Text */}
          <div className="mb-6 text-center">
            <p className="text-[1.02rem] leading-7 text-on-surface/65">
              {authResult
                ? 'All Google services connected. Entering your sanctuary...'
                : 'Sign in with your Google account to connect Drive, Calendar, and Gmail.'}
            </p>
          </div>

          {/* Google Sign-In Button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={isLoggingIn || !googleReady}
            className="river-stone-btn mb-3 flex w-full items-center justify-center gap-3 bg-surface-container-low px-6 py-[1.1rem] text-[1.02rem] font-semibold text-on-surface shadow-[0_8px_20px_-8px_rgba(60,64,67,0.08)] hover:shadow-[0_12px_28px_-8px_rgba(60,64,67,0.12)] disabled:opacity-60"
          >
            {isLoggingIn ? (
              <span className="flex items-center gap-2">
                <motion.span
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  className="inline-block"
                >
                  ✦
                </motion.span>
                {authResult ? 'Entering your sanctuary...' : 'Connecting Google...'}
              </span>
            ) : (
              <>
                <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Sign in with Google
              </>
            )}
          </button>

          {/* Dev mode fallback */}
          <button
            onClick={handleDevLogin}
            disabled={isLoggingIn}
            className="w-full rounded-[1.75rem] px-6 py-3 text-[0.88rem] text-on-surface/45 transition-colors hover:bg-surface-container-low hover:text-on-surface/65 disabled:opacity-50"
          >
            Skip (Dev mode — enter as Patient {DEMO_PATIENT_ID})
          </button>

          {/* Error message */}
          {authError && (
            <p className="mt-4 rounded-[1.25rem] bg-secondary-container/30 px-4 py-3 text-[0.85rem] leading-7 text-secondary">
              {authError}
            </p>
          )}
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-[0.82rem] leading-6 text-on-surface/35">
          Protected by Google Cloud • HIPAA Compliant
        </p>
      </motion.div>
    </div>
  );
};
