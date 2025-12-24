/**
 * Authentication Context (Simplified Template)
 *
 * This is a simplified version for the UI Kit template.
 * For full authentication with Google OAuth, see the login-template.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'

type UserRole = 'admin' | 'user' | 'guest'

interface UserInfo {
  id: string
  username: string
  email: string
  role: UserRole
  full_name?: string
}

interface AuthContextType {
  isAuthenticated: boolean
  user: UserInfo | null
  login: (token: string) => Promise<void>
  logout: () => void
  loading: boolean
  hasRole: (role: UserRole | UserRole[]) => boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserInfo | null>(() => {
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (token: string) => {
    localStorage.setItem(TOKEN_KEY, token)
    setLoading(true)

    try {
      // Fetch user info from your API
      const response = await fetch('/api/users/me', {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (response.ok) {
        const userInfo = await response.json()
        setUser(userInfo)
        localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }, [])

  const hasRole = useCallback(
    (role: UserRole | UserRole[]): boolean => {
      if (!user) return false
      if (Array.isArray(role)) {
        return role.includes(user.role)
      }
      return user.role === role
    },
    [user]
  )

  const value: AuthContextType = {
    isAuthenticated: !!user,
    user,
    login,
    logout,
    loading,
    hasRole,
    isAdmin: user?.role === 'admin',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Protected Route wrapper
 */
interface ProtectedRouteProps {
  children: ReactNode
  allowedRoles?: UserRole[]
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, hasRole, user } = useAuth()
  const navigate = useNavigate()

  if (!isAuthenticated) {
    navigate('/login', { replace: true })
    return null
  }

  if (allowedRoles && !hasRole(allowedRoles)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-theme-app">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-status-danger">Access Denied</h1>
          <p className="mt-2 text-theme-text-muted">
            You don't have permission to view this page.
          </p>
          <p className="mt-1 text-sm text-theme-text-muted">
            Your role: {user?.role}
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export default AuthContext
