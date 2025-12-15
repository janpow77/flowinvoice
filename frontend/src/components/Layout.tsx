import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  BarChart3,
  Settings,
} from 'lucide-react'
import clsx from 'clsx'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projekte', href: '/projects', icon: FolderOpen },
  { name: 'Dokumente', href: '/documents', icon: FileText },
  { name: 'Statistik', href: '/statistics', icon: BarChart3 },
  { name: 'Einstellungen', href: '/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <Link to="/" className="h-16 flex items-center px-4 border-b border-gray-200 hover:bg-gray-50 transition-colors">
          <img
            src="/auditlogo.png"
            alt="FlowAudit Logo"
            className="h-10 w-10 object-contain"
            onError={(e) => {
              // Fallback zu Text wenn Logo nicht gefunden
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
          <span className="ml-3 text-xl font-bold text-gray-900">FlowAudit</span>
        </Link>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href))

            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <item.icon className={clsx(
                  'h-5 w-5 mr-3',
                  isActive ? 'text-primary-600' : 'text-gray-400'
                )} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            FlowAudit v0.1.0
            <br />
            Seminarsystem
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold text-gray-900">
            {navigation.find(n =>
              location.pathname === n.href ||
              (n.href !== '/' && location.pathname.startsWith(n.href))
            )?.name || 'FlowAudit'}
          </h1>

          <div className="flex items-center space-x-4">
            {/* Provider Status */}
            <div className="flex items-center text-sm text-gray-500">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Ollama Online
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-6 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
