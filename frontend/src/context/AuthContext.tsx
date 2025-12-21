// Datei: frontend/src/context/AuthContext.tsx
/**
 * AuthContext - Authentifizierungs-Kontext für FlowAudit
 *
 * Stellt Login/Logout-Funktionalität, Benutzerinformationen,
 * Berechtigungsprüfung und Inaktivitäts-Timer bereit.
 *
 * Rollen:
 * - admin: Vollzugriff auf alle Funktionen
 * - schueler: Arbeitet an zugewiesenem Projekt
 * - extern: Eingeschränkter Gastzugang
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
import type { UserInfo, UserRole } from '../lib/types';

// Token-Speicher Key
const TOKEN_KEY = 'flowaudit_token';
const TOKEN_EXPIRY_KEY = 'flowaudit_token_expiry';
const USER_INFO_KEY = 'flowaudit_user_info';

// Inaktivitäts-Timeout in Millisekunden (10 Minuten gemäß Nutzerkonzept)
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;

interface AuthContextType {
  /** Ist der Benutzer eingeloggt? */
  isAuthenticated: boolean;
  /** Das aktuelle JWT-Token (oder null) */
  token: string | null;
  /** Benutzerinformationen (oder null) */
  user: UserInfo | null;
  /** Login-Funktion - speichert Token und lädt User-Info */
  login: (token: string) => Promise<void>;
  /** Logout-Funktion - entfernt Token und User-Info */
  logout: () => void;
  /** Lädt gerade (z.B. beim Token-Check) */
  loading: boolean;
  /** Prüft ob der Benutzer eine bestimmte Berechtigung hat */
  hasPermission: (permission: string) => boolean;
  /** Prüft ob der Benutzer eine bestimmte Rolle hat */
  hasRole: (role: UserRole | UserRole[]) => boolean;
  /** Prüft ob der Benutzer Admin ist */
  isAdmin: boolean;
  /** Aktualisiert die Benutzerinformationen */
  refreshUserInfo: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastActivity, setLastActivity] = useState<number>(Date.now());

  // Lädt Benutzerinformationen vom Server
  const fetchUserInfo = useCallback(async (authToken: string): Promise<UserInfo | null> => {
    try {
      const response = await fetch('/api/users/me', {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        console.error('Failed to fetch user info:', response.status);
        return null;
      }

      const userInfo: UserInfo = await response.json();
      return userInfo;
    } catch (error) {
      console.error('Error fetching user info:', error);
      return null;
    }
  }, []);

  // Prüfe beim Start ob ein gültiges Token existiert
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedExpiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
      const storedUserInfo = localStorage.getItem(USER_INFO_KEY);

      if (storedToken && storedExpiry) {
        const expiryTime = parseInt(storedExpiry, 10);
        if (Date.now() < expiryTime) {
          setToken(storedToken);

          // Versuche gespeicherte User-Info zu laden
          if (storedUserInfo) {
            try {
              const userInfo = JSON.parse(storedUserInfo) as UserInfo;
              setUser(userInfo);
            } catch {
              // Bei Fehler: User-Info vom Server laden
              const userInfo = await fetchUserInfo(storedToken);
              if (userInfo) {
                setUser(userInfo);
                localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
              }
            }
          } else {
            // Keine gespeicherte User-Info: vom Server laden
            const userInfo = await fetchUserInfo(storedToken);
            if (userInfo) {
              setUser(userInfo);
              localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
            }
          }
        } else {
          // Token abgelaufen - entfernen
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(TOKEN_EXPIRY_KEY);
          localStorage.removeItem(USER_INFO_KEY);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [fetchUserInfo]);

  // Login-Funktion
  const login = useCallback(async (newToken: string) => {
    // Token für 24 Stunden speichern
    const expiryTime = Date.now() + 24 * 60 * 60 * 1000;
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    setToken(newToken);
    setLastActivity(Date.now());

    // User-Info laden
    const userInfo = await fetchUserInfo(newToken);
    if (userInfo) {
      setUser(userInfo);
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
    }
  }, [fetchUserInfo]);

  // Logout-Funktion
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem(USER_INFO_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // User-Info aktualisieren
  const refreshUserInfo = useCallback(async () => {
    if (token) {
      const userInfo = await fetchUserInfo(token);
      if (userInfo) {
        setUser(userInfo);
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
      }
    }
  }, [token, fetchUserInfo]);

  // Berechtigungsprüfung
  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false;
      return user.permissions.includes(permission);
    },
    [user]
  );

  // Rollenprüfung
  const hasRole = useCallback(
    (role: UserRole | UserRole[]): boolean => {
      if (!user) return false;
      if (Array.isArray(role)) {
        return role.includes(user.role);
      }
      return user.role === role;
    },
    [user]
  );

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
    user,
    login,
    logout,
    loading,
    hasPermission,
    hasRole,
    isAdmin: user?.is_admin ?? false,
    refreshUserInfo,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook um auf den Auth-Context zuzugreifen
 */
// eslint-disable-next-line react-refresh/only-export-components
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
  /** Optionale Rollenprüfung - nur diese Rollen haben Zugriff */
  allowedRoles?: UserRole[];
  /** Optionale Berechtigungsprüfung */
  requiredPermission?: string;
}

export function ProtectedRoute({
  children,
  allowedRoles,
  requiredPermission,
}: ProtectedRouteProps) {
  const { isAuthenticated, loading, hasRole, hasPermission, user } = useAuth();
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
      </div>
    );
  }

  // Zeige nichts wenn nicht authentifiziert (Redirect passiert)
  if (!isAuthenticated) {
    return null;
  }

  // Rollenprüfung
  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-status-danger">Zugriff verweigert</h1>
          <p className="mt-2 text-theme-text-muted">
            Sie haben keine Berechtigung für diese Seite.
          </p>
          <p className="mt-1 text-sm text-theme-text-muted">
            Ihre Rolle: {user?.role}
          </p>
        </div>
      </div>
    );
  }

  // Berechtigungsprüfung
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-status-danger">Zugriff verweigert</h1>
          <p className="mt-2 text-theme-text-muted">
            Fehlende Berechtigung: {requiredPermission}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * AdminRoute - Nur für Admins zugänglich
 */
export function AdminRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      {children}
    </ProtectedRoute>
  );
}

export default AuthContext;
