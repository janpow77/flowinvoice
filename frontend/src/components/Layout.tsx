import { ReactNode, useMemo } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Book,
  FileOutput,
  BarChart3,
  Settings,
  Users,
  LogOut,
  GraduationCap,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'
import type { UserRole } from '../lib/types'

interface LayoutProps {
  children: ReactNode
}

interface NavItem {
  key: string
  href: string
  icon: typeof LayoutDashboard
  /** Welche Rollen dürfen diesen Menüpunkt sehen? Leer = alle */
  allowedRoles?: UserRole[]
}

// Navigation items with translation keys and role restrictions
const navigationItems: NavItem[] = [
  { key: 'dashboard', href: '/', icon: LayoutDashboard, allowedRoles: ['admin', 'schueler'] },
  { key: 'projects', href: '/projects', icon: FolderOpen },
  { key: 'documents', href: '/documents', icon: FileText, allowedRoles: ['admin', 'schueler'] },
  { key: 'rulesets', href: '/rulesets', icon: Book, allowedRoles: ['admin', 'schueler'] },
  { key: 'generator', href: '/generator', icon: FileOutput },
  { key: 'statistics', href: '/statistics', icon: BarChart3, allowedRoles: ['admin'] },
  { key: 'training', href: '/training', icon: GraduationCap, allowedRoles: ['admin', 'schueler'] },
  { key: 'users', href: '/users', icon: Users, allowedRoles: ['admin'] },
  { key: 'settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user, logout, hasRole } = useAuth()

  // Filter navigation based on user role
  const navigation = useMemo(() => {
    return navigationItems.filter((item) => {
      // Wenn keine Rollen-Einschränkung, für alle sichtbar
      if (!item.allowedRoles || item.allowedRoles.length === 0) {
        return true
      }
      // Prüfe ob Benutzer eine der erlaubten Rollen hat
      return hasRole(item.allowedRoles)
    })
  }, [hasRole])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Rollen-Label für Anzeige
  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator'
      case 'schueler':
        return 'Schüler'
      case 'extern':
        return 'Externer Zugang'
      default:
        return role
    }
  }

  return (
    <div className="min-h-screen flex bg-theme-app">
      {/* Sidebar - Panel-Ebene */}
      <aside className="w-64 bg-theme-panel border-r border-theme-border-default flex flex-col">
        {/* Logo - UNVERÄNDERT, ignoriert Theme */}
        <Link
          to="/"
          className="h-16 flex items-center px-4 border-b border-theme-border-default hover:bg-theme-hover transition-colors"
        >
          {/* Logo ist CI-geschützt und bleibt immer unverändert */}
          <img
            src="/auditlogo.png"
            alt="FlowAudit Logo"
            className="h-10 w-10 object-contain"
          />
          <span className="ml-3 text-xl font-bold text-theme-text-primary">
            FlowAudit
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
                {t(`nav.${item.key}`)}
              </Link>
            )
          })}

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors text-theme-text-secondary hover:bg-theme-hover hover:text-theme-text-primary"
          >
            <LogOut className="h-5 w-5 mr-3 text-theme-text-muted" />
            {t('nav.logout', 'Abmelden')}
          </button>
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-theme-border-default">
          <div className="text-xs text-theme-text-muted">
            FlowAudit v0.1.0
            <br />
            Seminarsystem
          </div>
          <div className="mt-3 pt-3 border-t border-theme-border-subtle text-xs">
            <div className="font-medium text-theme-text-muted">Kontakt</div>
            <div className="text-theme-text-muted">Jan Riener</div>
            <a
              href="mailto:jan.riener@vwvg.de"
              className="text-theme-text-link hover:text-theme-text-link-hover hover:underline"
            >
              jan.riener@vwvg.de
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header - Panel-Ebene */}
        <header className="h-16 bg-theme-panel border-b border-theme-border-default flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-theme-text-primary">
            {t(`nav.${navigation.find(n =>
              location.pathname === n.href ||
              (n.href !== '/' && location.pathname.startsWith(n.href))
            )?.key || 'dashboard'}`)}
          </h1>

          {/* Platzhalter für zukünftige Header-Aktionen */}
          <div className="flex items-center space-x-4">
          </div>
        </header>

        {/* Page Content - App-Hintergrund */}
        <div className="flex-1 p-6 overflow-auto bg-theme-app">
          {children}
        </div>
      </main>
    </div>
  )
}
