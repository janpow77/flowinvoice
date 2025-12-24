/**
 * Layout Component Template
 *
 * Main application layout with sidebar navigation and header.
 * Includes role-based navigation filtering.
 *
 * Customize:
 * - Update navigationItems with your routes
 * - Replace logo path and brand name
 * - Adjust role labels in getRoleLabel()
 */

import { ReactNode, useMemo } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Settings,
  Users,
  LogOut,
  LucideIcon,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'

interface LayoutProps {
  children: ReactNode
}

// User role type - customize as needed
type UserRole = 'admin' | 'user' | 'guest'

interface NavItem {
  key: string
  label: string
  href: string
  icon: LucideIcon
  /** Which roles can see this item? Empty = all */
  allowedRoles?: UserRole[]
}

// Navigation items - CUSTOMIZE THIS
const navigationItems: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { key: 'projects', label: 'Projects', href: '/projects', icon: FolderOpen },
  { key: 'documents', label: 'Documents', href: '/documents', icon: FileText },
  { key: 'users', label: 'Users', href: '/users', icon: Users, allowedRoles: ['admin'] },
  { key: 'settings', label: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, hasRole } = useAuth()

  // Filter navigation based on user role
  const navigation = useMemo(() => {
    return navigationItems.filter((item) => {
      if (!item.allowedRoles || item.allowedRoles.length === 0) {
        return true
      }
      return hasRole(item.allowedRoles)
    })
  }, [hasRole])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Role labels - CUSTOMIZE THIS
  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator'
      case 'user':
        return 'User'
      case 'guest':
        return 'Guest'
      default:
        return role
    }
  }

  // Get current page title
  const currentPage = navigation.find(n =>
    location.pathname === n.href ||
    (n.href !== '/' && location.pathname.startsWith(n.href))
  )

  return (
    <div className="min-h-screen flex bg-theme-app">
      {/* Sidebar */}
      <aside className="w-64 bg-theme-panel border-r border-theme-border-default flex flex-col">
        {/* Logo */}
        <Link
          to="/"
          className="h-16 flex items-center px-4 border-b border-theme-border-default hover:bg-theme-hover transition-colors"
        >
          <img
            src="/auditlogo.png"  // <-- Replace with your logo
            alt="Logo"
            className="h-10 w-10 object-contain"
          />
          <span className="ml-3 text-xl font-bold text-theme-text-primary">
            YourBrand  {/* <-- Replace with your brand */}
          </span>
        </Link>

        {/* User Info */}
        {user && (
          <div className="px-4 py-3 border-b border-theme-border-default">
            <div className="text-sm font-medium text-theme-text-primary">
              {user.username}
            </div>
            <div className="text-xs text-theme-text-muted">
              {getRoleLabel(user.role)}
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href))

            return (
              <Link
                key={item.key}
                to={item.href}
                className={clsx(
                  'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-theme-selected text-accent-primary'
                    : 'text-theme-text-secondary hover:bg-theme-hover hover:text-theme-text-primary'
                )}
              >
                <item.icon className={clsx(
                  'h-5 w-5 mr-3',
                  isActive ? 'text-accent-primary' : 'text-theme-text-muted'
                )} />
                {item.label}
              </Link>
            )
          })}

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors text-theme-text-secondary hover:bg-theme-hover hover:text-theme-text-primary"
          >
            <LogOut className="h-5 w-5 mr-3 text-theme-text-muted" />
            Logout
          </button>
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-theme-border-default">
          <div className="text-xs text-theme-text-muted">
            YourApp v1.0.0  {/* <-- Replace */}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-theme-panel border-b border-theme-border-default flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-theme-text-primary">
            {currentPage?.label || 'Dashboard'}
          </h1>

          {/* Header actions placeholder */}
          <div className="flex items-center space-x-4">
            {/* Add theme toggle, notifications, etc. here */}
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-6 overflow-auto bg-theme-app">
          {children}
        </div>
      </main>
    </div>
  )
}
