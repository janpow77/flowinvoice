import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { FileText, CheckCircle, AlertTriangle, XCircle, Loader2, AlertCircle, FolderOpen, BarChart3, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

export default function Dashboard() {
  const { t } = useTranslation()

  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getStats(),
    retry: 2,
  })

  const statCards = [
    {
      name: t('dashboard.totalDocuments'),
      value: stats?.total_documents || 0,
      icon: FileText,
      color: 'text-status-info bg-status-info-bg',
    },
    {
      name: t('audit.compliant'),
      value: stats?.approved || 0,
      icon: CheckCircle,
      color: 'text-status-success bg-status-success-bg',
    },
    {
      name: t('audit.needsReview'),
      value: stats?.pending_review || 0,
      icon: AlertTriangle,
      color: 'text-status-warning bg-status-warning-bg',
    },
    {
      name: t('audit.nonCompliant'),
      value: stats?.rejected || 0,
      icon: XCircle,
      color: 'text-status-danger bg-status-danger-bg',
    },
  ]

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
        <span className="ml-3 text-theme-text-muted">{t('common.loading')}</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-status-danger" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-status-danger">{t('common.error')}</h3>
            <p className="text-sm text-status-danger mt-1">
              {t('errors.network')}
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-status-danger-bg text-status-danger rounded-lg hover:opacity-80 transition-colors flex items-center"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('common.retry')}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="bg-gradient-to-r from-accent-primary to-accent-primary-hover rounded-lg p-6 text-white">
        <h2 className="text-xl font-semibold">{t('dashboard.welcome')}</h2>
        <p className="text-white/80 mt-1">
          KI-gestütztes Rechnungsprüfungssystem für den Seminarbetrieb
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div
            key={stat.name}
            className="bg-theme-card rounded-lg border border-theme-border-default p-6"
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-theme-text-muted">{stat.name}</p>
                <p className="text-2xl font-semibold text-theme-text-primary">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <h2 className="text-lg font-semibold text-theme-text-primary mb-4">{t('dashboard.quickActions')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/documents"
            className="flex items-center p-4 bg-accent-primary/10 rounded-lg hover:bg-accent-primary/20 transition-colors"
          >
            <FileText className="h-8 w-8 text-accent-primary" />
            <div className="ml-4">
              <p className="font-medium text-accent-primary">{t('dashboard.uploadInvoice')}</p>
              <p className="text-sm text-accent-primary/70">PDF-Dokument prüfen</p>
            </div>
          </Link>

          <Link
            to="/projects"
            className="flex items-center p-4 bg-theme-hover rounded-lg hover:bg-theme-selected transition-colors"
          >
            <FolderOpen className="h-8 w-8 text-theme-text-muted" />
            <div className="ml-4">
              <p className="font-medium text-theme-text-primary">{t('projects.createProject')}</p>
              <p className="text-sm text-theme-text-muted">Projektstruktur anlegen</p>
            </div>
          </Link>

          <Link
            to="/statistics"
            className="flex items-center p-4 bg-theme-hover rounded-lg hover:bg-theme-selected transition-colors"
          >
            <BarChart3 className="h-8 w-8 text-theme-text-muted" />
            <div className="ml-4">
              <p className="font-medium text-theme-text-primary">{t('dashboard.viewStatistics')}</p>
              <p className="text-sm text-theme-text-muted">Lernkurve anzeigen</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <h2 className="text-lg font-semibold text-theme-text-primary mb-4">{t('dashboard.recentDocuments')}</h2>
        <div className="text-sm text-theme-text-muted">
          {t('common.noData')}. {t('dashboard.uploadInvoice')}, um zu beginnen.
        </div>
      </div>
    </div>
  )
}
