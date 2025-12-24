// Datei: frontend/context/AuthContext.tsx
/**
 * Authentication Context
 *
 * Provides:
 * - Login/Logout functionality
 * - JWT token management
 * - User info caching
 * - Inactivity timeout (10 minutes)
 * - Role-based access control
 * - Protected route wrapper
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

// User roles - customize as needed
type UserRole = 'admin' | 'user' | 'guest';

interface UserInfo {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  full_name?: string;
  is_admin: boolean;
  permissions: string[];
}

// Storage keys
const TOKEN_KEY = 'auth_token';
const TOKEN_EXPIRY_KEY = 'auth_token_expiry';
const USER_INFO_KEY = 'auth_user_info';

// Inactivity timeout (10 minutes)
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: UserInfo | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: UserRole | UserRole[]) => boolean;
  isAdmin: boolean;
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

  // Fetch user info from API
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

      return await response.json();
    } catch (error) {
      console.error('Error fetching user info:', error);
      return null;
    }
  }, []);

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedExpiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
      const storedUserInfo = localStorage.getItem(USER_INFO_KEY);

      if (storedToken && storedExpiry) {
        const expiryTime = parseInt(storedExpiry, 10);
        if (Date.now() < expiryTime) {
          setToken(storedToken);

          if (storedUserInfo) {
            try {
              setUser(JSON.parse(storedUserInfo));
            } catch {
              const userInfo = await fetchUserInfo(storedToken);
              if (userInfo) {
                setUser(userInfo);
                localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
              }
            }
          } else {
            const userInfo = await fetchUserInfo(storedToken);
            if (userInfo) {
              setUser(userInfo);
              localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
            }
          }
        } else {
          // Token expired
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(TOKEN_EXPIRY_KEY);
          localStorage.removeItem(USER_INFO_KEY);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [fetchUserInfo]);

  // Login
  const login = useCallback(async (newToken: string) => {
    const expiryTime = Date.now() + 24 * 60 * 60 * 1000; // 24 hours
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    setToken(newToken);
    setLastActivity(Date.now());

    const userInfo = await fetchUserInfo(newToken);
    if (userInfo) {
      setUser(userInfo);
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
    }
  }, [fetchUserInfo]);

  // Logout
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem(USER_INFO_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Refresh user info
  const refreshUserInfo = useCallback(async () => {
    if (token) {
      const userInfo = await fetchUserInfo(token);
      if (userInfo) {
        setUser(userInfo);
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
      }
    }
  }, [token, fetchUserInfo]);

  // Permission check
  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false;
      return user.permissions.includes(permission);
    },
    [user]
  );

  // Role check
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

  // Activity tracking
  useEffect(() => {
    if (!token) return;

    const updateActivity = () => setLastActivity(Date.now());
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];

    events.forEach((event) => window.addEventListener(event, updateActivity));
    return () => {
      events.forEach((event) => window.removeEventListener(event, updateActivity));
    };
  }, [token]);

  // Inactivity timeout
  useEffect(() => {
    if (!token) return;

    const checkInactivity = () => {
      if (Date.now() - lastActivity >= INACTIVITY_TIMEOUT) {
        console.log('Inactivity timeout: Auto logout');
        logout();
      }
    };

    const intervalId = setInterval(checkInactivity, 30 * 1000);
    return () => clearInterval(intervalId);
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

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Protected Route wrapper
interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: UserRole[];
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="mt-2 text-gray-600">You don't have permission to view this page.</p>
          <p className="mt-1 text-sm text-gray-500">Your role: {user?.role}</p>
        </div>
      </div>
    );
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="mt-2 text-gray-600">Missing permission: {requiredPermission}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function AdminRoute({ children }: { children: ReactNode }) {
  return <ProtectedRoute allowedRoles={['admin']}>{children}</ProtectedRoute>;
}

export default AuthContext;
