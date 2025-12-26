// Datei: frontend/src/pages/GoogleCallback.tsx
/**
 * Google OAuth Callback Page
 *
 * Verarbeitet den Redirect von Google nach erfolgreicher Authentifizierung.
 * Tauscht den Authorization Code gegen ein JWT Token.
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import axios from 'axios'; // Only for isAxiosError check

export default function GoogleCallback() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');

      // Handle error from Google
      if (errorParam) {
        setError(`Google Login fehlgeschlagen: ${errorParam}`);
        setProcessing(false);
        return;
      }

      // Verify we have the required parameters
      if (!code || !state) {
        setError('Ungültige Callback-Parameter.');
        setProcessing(false);
        return;
      }

      // Verify state matches (CSRF protection)
      const storedState = sessionStorage.getItem('google_oauth_state');
      if (state !== storedState) {
        setError('Sicherheitsfehler: State-Parameter stimmt nicht überein.');
        setProcessing(false);
        return;
      }

      // Clean up stored state
      sessionStorage.removeItem('google_oauth_state');

      try {
        // Exchange code for JWT token
        const { access_token } = await api.googleCallback(code, state);

        // Login with the received token
        await login(access_token);
        navigate('/');
      } catch (err) {
        if (axios.isAxiosError(err)) {
          const message = err.response?.data?.detail || 'Authentifizierung fehlgeschlagen.';
          setError(message);
        } else {
          setError('Ein unerwarteter Fehler ist aufgetreten.');
        }
        setProcessing(false);
      }
    };

    processCallback();
  }, [searchParams, login, navigate]);

  // Processing state
  if (processing) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white text-lg font-medium">Google Login wird verarbeitet...</p>
          <p className="text-blue-200/60 text-sm mt-2">Bitte warten Sie einen Moment.</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 flex items-center justify-center px-4">
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Login fehlgeschlagen</h2>
          <p className="text-blue-200/80 mb-6">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition-colors"
          >
            Zurück zum Login
          </button>
        </div>
      </div>
    );
  }

  return null;
}
