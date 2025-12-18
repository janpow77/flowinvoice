import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Book,
  FileOutput,
  BarChart3,
  Settings,
} from 'lucide-react'
import clsx from 'clsx'

interface LayoutProps {
  children: ReactNode
}

// Navigation items with translation keys
const navigation = [
  { key: 'dashboard', href: '/', icon: LayoutDashboard },
  { key: 'projects', href: '/projects', icon: FolderOpen },
  { key: 'documents', href: '/documents', icon: FileText },
  { key: 'rulesets', href: '/rulesets', icon: Book },
  { key: 'generator', href: '/generator', icon: FileOutput },
  { key: 'statistics', href: '/statistics', icon: BarChart3 },
  { key: 'settings', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { t } = useTranslation()

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Logo */}
        <Link to="/" className="h-16 flex items-center px-4 border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
          <img
            src="/auditlogo.png"
            alt="FlowAudit Logo"
            className="h-10 w-10 object-contain"
          />
          <span className="ml-3 text-xl font-bold text-gray-900 dark:text-white">FlowAudit</span>
        </Link>

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
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                )}
              >
                <item.icon className={clsx(
                  'h-5 w-5 mr-3',
                  isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'
                )} />
                {t(`nav.${item.key}`)}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            FlowAudit v0.1.0
            <br />
            Seminarsystem
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-400 dark:text-gray-500">
            <div className="font-medium text-gray-500 dark:text-gray-400">Kontakt</div>
            <div className="dark:text-gray-400">Jan Riener</div>
            <a
              href="mailto:jan.riener@vwvg.de"
              className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 hover:underline"
            >
              jan.riener@vwvg.de
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t(`nav.${navigation.find(n =>
              location.pathname === n.href ||
              (n.href !== '/' && location.pathname.startsWith(n.href))
            )?.key || 'dashboard'}`)}
          </h1>

          {/* Platzhalter für zukünftige Header-Aktionen */}
          <div className="flex items-center space-x-4">
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-6 overflow-auto bg-gray-50 dark:bg-gray-900">
          {children}
        </div>
      </main>
    </div>
  )
}
