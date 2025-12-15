// Datei: frontend/src/context/AuthContext.tsx
/**
 * AuthContext - Authentifizierungs-Kontext für FlowAudit
 *
 * Stellt Login/Logout-Funktionalität und Inaktivitäts-Timer bereit.
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';

// Token-Speicher Key
const TOKEN_KEY = 'flowaudit_token';
const TOKEN_EXPIRY_KEY = 'flowaudit_token_expiry';

// Inaktivitäts-Timeout in Millisekunden (10 Minuten gemäß Nutzerkonzept)
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;

interface AuthContextType {
  /** Ist der Benutzer eingeloggt? */
  isAuthenticated: boolean;
  /** Das aktuelle JWT-Token (oder null) */
  token: string | null;
  /** Login-Funktion - speichert Token */
  login: (token: string) => void;
  /** Logout-Funktion - entfernt Token */
  logout: () => void;
  /** Lädt gerade (z.B. beim Token-Check) */
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastActivity, setLastActivity] = useState<number>(Date.now());

  // Prüfe beim Start ob ein gültiges Token existiert
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedExpiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (storedToken && storedExpiry) {
      const expiryTime = parseInt(storedExpiry, 10);
      if (Date.now() < expiryTime) {
        setToken(storedToken);
      } else {
        // Token abgelaufen - entfernen
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
      }
    }
    setLoading(false);
  }, []);

  // Login-Funktion
  const login = useCallback((newToken: string) => {
    // Token für 24 Stunden speichern
    const expiryTime = Date.now() + 24 * 60 * 60 * 1000;
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    setToken(newToken);
    setLastActivity(Date.now());
  }, []);

  // Logout-Funktion
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    setToken(null);
  }, []);

  // Aktivitäts-Tracker: Aktualisiere lastActivity bei Benutzeraktionen
  useEffect(() => {
    if (!token) return;

    const updateActivity = () => {
      setLastActivity(Date.now());
    };

    // Events die als Aktivität zählen
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((event) => {
      window.addEventListener(event, updateActivity);
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, updateActivity);
      });
    };
  }, [token]);

  // Inaktivitäts-Timer: Logout nach 10 Minuten Inaktivität
  useEffect(() => {
    if (!token) return;

    const checkInactivity = () => {
      const timeSinceLastActivity = Date.now() - lastActivity;
      if (timeSinceLastActivity >= INACTIVITY_TIMEOUT) {
        console.log('Inaktivitäts-Timeout: Automatischer Logout');
        logout();
      }
    };

    // Prüfe alle 30 Sekunden
    const intervalId = setInterval(checkInactivity, 30 * 1000);

    return () => {
      clearInterval(intervalId);
    };
  }, [token, lastActivity, logout]);

  const value: AuthContextType = {
    isAuthenticated: !!token,
    token,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook um auf den Auth-Context zuzugreifen
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * ProtectedRoute - Wrapper für geschützte Routen
 * Leitet nicht-authentifizierte Benutzer zur Login-Seite um.
 */
interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  // Zeige nichts während der Token-Prüfung
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Zeige nichts wenn nicht authentifiziert (Redirect passiert)
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

export default AuthContext;
