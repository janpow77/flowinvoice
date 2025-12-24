// Datei: frontend/pages/Login.tsx
/**
 * Animated Login Page Template
 *
 * Features:
 * - Jumping fish animation (uses your logo)
 * - Binary data "water" effect
 * - Glassmorphism login card
 * - Google OAuth support
 * - Form-based login
 *
 * Customize:
 * - Replace /your-logo.png with your logo
 * - Update brand name and tagline
 * - Modify color scheme (blue gradients)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import axios from 'axios';

// --- CSS Animations (inline for portability) ---
const cssAnimations = `
  @keyframes fishJump {
    0% {
      transform: translateY(150px) translateX(-80px) rotate(-15deg) scaleX(-1);
      opacity: 0;
    }
    15% {
      opacity: 1;
    }
    50% {
      transform: translateY(-200px) translateX(0px) rotate(5deg) scaleX(-1);
    }
    85% {
      opacity: 1;
    }
    100% {
      transform: translateY(150px) translateX(80px) rotate(25deg) scaleX(-1);
      opacity: 0;
    }
  }

  .animate-fish-jump {
    animation: fishJump 7s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    filter: drop-shadow(0 0 25px rgba(96, 165, 250, 0.7));
  }

  @keyframes waveMove {
    0% { transform: translateX(0); }
    50% { transform: translateX(-25px); }
    100% { transform: translateX(0); }
  }

  .wave-animation {
    animation: waveMove 6s ease-in-out infinite;
  }

  .wave-animation-reverse {
    animation: waveMove 8s ease-in-out infinite reverse;
  }

  @keyframes dataFlow {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  .data-flow {
    animation: dataFlow 20s linear infinite;
  }

  .data-flow-fast {
    animation: dataFlow 15s linear infinite;
  }

  .data-flow-slow {
    animation: dataFlow 25s linear infinite reverse;
  }

  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.8; }
  }

  .binary-pulse {
    animation: binaryPulse 3s ease-in-out infinite;
  }
`;

// Jumping Logo/Fish - Replace with your logo
const JumpingFish = () => (
  <img
    src="/your-logo.png"  // <-- Replace with your logo path
    alt="Jumping Logo"
    className="w-full h-full object-contain"
  />
);

// Static binary sequences (prevents flickering)
const BINARY_LINES = [
  '0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1',
  '1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0',
  '0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0',
  '1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1',
  '0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0',
];

// Binary Data Water Effect
const BinaryDataWater = () => {
  const binaryLines = BINARY_LINES;

  return (
    <div className="absolute bottom-0 left-0 right-0 h-48 overflow-hidden pointer-events-none">
      {/* Wave clip path */}
      <svg className="absolute bottom-0 left-0 right-0 h-full w-full" preserveAspectRatio="none">
        <defs>
          <clipPath id="waveClip">
            <path d="M0,60 Q180,20 360,50 T720,40 T1080,55 T1440,45 L1440,200 L0,200 Z" />
          </clipPath>
        </defs>
      </svg>

      {/* Back data layer (darker, slower) */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-blue-950/90 via-blue-900/70 to-transparent">
        <div className="data-flow-slow whitespace-nowrap font-mono text-xs leading-relaxed pt-8">
          <span className="text-blue-400/40">{binaryLines[0]} {binaryLines[0]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-xs leading-relaxed">
          <span className="text-cyan-400/30">{binaryLines[1]} {binaryLines[1]}</span>
        </div>
      </div>

      {/* Middle data layer */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-800/80 via-blue-700/50 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-sm leading-relaxed pt-4">
          <span className="text-blue-300/50">{binaryLines[2]} {binaryLines[2]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-sm leading-relaxed">
          <span className="text-cyan-300/40">{binaryLines[3]} {binaryLines[3]}</span>
        </div>
      </div>

      {/* Front data layer (brighter, faster) */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-blue-600/90 via-blue-500/60 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-base leading-relaxed pt-2 binary-pulse">
          <span className="text-blue-200/70">{binaryLines[4]} {binaryLines[4]}</span>
        </div>
      </div>

      {/* Wave surface */}
      <div className="absolute bottom-16 left-0 right-0 wave-animation">
        <svg className="w-full h-12" viewBox="0 0 1440 48" preserveAspectRatio="none">
          <path
            fill="rgba(96, 165, 250, 0.3)"
            d="M0,24 Q180,8 360,20 T720,16 T1080,22 T1440,18 L1440,48 L0,48 Z"
          />
        </svg>
      </div>
      <div className="absolute bottom-12 left-0 right-0 wave-animation-reverse">
        <svg className="w-full h-10" viewBox="0 0 1440 40" preserveAspectRatio="none">
          <path
            fill="rgba(59, 130, 246, 0.4)"
            d="M0,20 Q180,4 360,16 T720,12 T1080,18 T1440,14 L1440,40 L0,40 Z"
          />
        </svg>
      </div>
    </div>
  );
};

// Google Icon SVG
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  // Check if Google OAuth is enabled
  useEffect(() => {
    const checkGoogleAuth = async () => {
      try {
        const response = await axios.get('/api/auth/google/enabled');
        setGoogleEnabled(response.data.enabled);
      } catch {
        setGoogleEnabled(false);
      }
    };
    checkGoogleAuth();
  }, []);

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Handle Google OAuth
  const handleGoogleLogin = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      const response = await axios.get('/api/auth/google/url');
      const { auth_url, state } = response.data;
      sessionStorage.setItem('google_oauth_state', state);
      window.location.href = auth_url;
    } catch {
      setError('Google Login could not be started.');
      setGoogleLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      login(response.data.access_token);
      navigate('/');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError('Invalid credentials.');
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 relative overflow-hidden flex flex-col justify-center items-center py-12 sm:px-6 lg:px-8">
      <style>{cssAnimations}</style>

      {/* Binary Data Water */}
      <BinaryDataWater />

      {/* Jumping Logo */}
      <div className="absolute bottom-20 left-1/2 -ml-16 z-20 w-32 h-20 animate-fish-jump pointer-events-none">
        <JumpingFish />
      </div>

      {/* Login Area */}
      <div className="relative z-30 sm:mx-auto sm:w-full sm:max-w-md px-4">

        {/* Logo and Title */}
        <div className="text-center mb-8">
          <img
            src="/your-logo.png"  // <-- Replace with your logo
            alt="Logo"
            className="h-24 w-auto mx-auto mb-4 drop-shadow-lg"
          />
          <h1 className="text-5xl sm:text-6xl font-extrabold text-white drop-shadow-lg tracking-tight">
            YourBrand  {/* <-- Replace with your brand */}
          </h1>
          <p className="mt-2 text-blue-200 text-sm uppercase tracking-widest font-medium">
            Your Tagline Here  {/* <-- Replace with your tagline */}
          </p>
        </div>

        {/* Login Card (Glassmorphism) */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-blue-100 mb-2">
                Username
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-white/10 border-white/30 text-white placeholder-blue-200/60 focus:border-blue-300 focus:ring-2 focus:ring-blue-300/50 h-12 rounded-lg"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-blue-100 mb-2">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/10 border-white/30 text-white placeholder-blue-200/60 focus:border-blue-300 focus:ring-2 focus:ring-blue-300/50 h-12 rounded-lg"
                placeholder="********"
              />
            </div>

            {error && (
              <div className="text-sm text-center text-red-100 bg-red-500/30 py-3 px-4 rounded-lg border border-red-400/30">
                {error}
              </div>
            )}

            <div>
              <Button
                type="submit"
                fullWidth
                loading={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 h-12 shadow-lg shadow-blue-900/50 border-none text-base rounded-lg transition-all duration-200 hover:shadow-xl hover:shadow-blue-800/50"
              >
                Login
              </Button>
            </div>
          </form>

          {/* Google OAuth */}
          {googleEnabled && (
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-blue-200/60">or</span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={googleLoading}
                className="mt-4 w-full flex items-center justify-center gap-3 px-4 py-3 h-12 bg-white/95 hover:bg-white text-gray-700 font-semibold rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {googleLoading ? (
                  <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                ) : (
                  <GoogleIcon />
                )}
                <span>Sign in with Google</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Decorative bubbles */}
      <div className="absolute bottom-40 left-1/4 w-3 h-3 bg-blue-300/30 rounded-full animate-bounce" style={{ animationDelay: '0s', animationDuration: '3s' }} />
      <div className="absolute bottom-52 left-1/3 w-2 h-2 bg-blue-200/20 rounded-full animate-bounce" style={{ animationDelay: '1s', animationDuration: '4s' }} />
      <div className="absolute bottom-36 right-1/4 w-4 h-4 bg-blue-300/25 rounded-full animate-bounce" style={{ animationDelay: '0.5s', animationDuration: '3.5s' }} />
      <div className="absolute bottom-60 right-1/3 w-2 h-2 bg-blue-200/30 rounded-full animate-bounce" style={{ animationDelay: '1.5s', animationDuration: '4.5s' }} />
    </div>
  );
}
