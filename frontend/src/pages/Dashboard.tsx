import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { FileText, CheckCircle, AlertTriangle, XCircle, Loader2, AlertCircle, FolderOpen, BarChart3, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

export default function Dashboard() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

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
      color: 'text-blue-600 bg-blue-50',
    },
    {
      name: t('audit.compliant'),
      value: stats?.approved || 0,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-50',
    },
    {
      name: t('audit.needsReview'),
      value: stats?.pending_review || 0,
      icon: AlertTriangle,
      color: 'text-yellow-600 bg-yellow-50',
    },
    {
      name: t('audit.nonCompliant'),
      value: stats?.rejected || 0,
      icon: XCircle,
      color: 'text-red-600 bg-red-50',
    },
  ]

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        <span className="ml-3 text-gray-600">{t('common.loading')}</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-red-600" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-red-800">{t('common.error')}</h3>
            <p className="text-sm text-red-600 mt-1">
              {t('errors.network')}
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center"
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
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
        <h2 className="text-xl font-semibold">{t('dashboard.welcome')}</h2>
        <p className="text-primary-100 mt-1">
          KI-gestütztes Rechnungsprüfungssystem für den Seminarbetrieb
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-lg border border-gray-200 p-6"
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.quickActions')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/documents"
            className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
          >
            <FileText className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <p className="font-medium text-primary-900">{t('dashboard.uploadInvoice')}</p>
              <p className="text-sm text-primary-600">PDF-Dokument prüfen</p>
            </div>
          </Link>

          <Link
            to="/projects"
            className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <FolderOpen className="h-8 w-8 text-gray-600" />
            <div className="ml-4">
              <p className="font-medium text-gray-900">{t('projects.createProject')}</p>
              <p className="text-sm text-gray-600">Projektstruktur anlegen</p>
            </div>
          </Link>

          <Link
            to="/statistics"
            className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <BarChart3 className="h-8 w-8 text-gray-600" />
            <div className="ml-4">
              <p className="font-medium text-gray-900">{t('dashboard.viewStatistics')}</p>
              <p className="text-sm text-gray-600">Lernkurve anzeigen</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.recentDocuments')}</h2>
        <div className="text-sm text-gray-500">
          {t('common.noData')}. {t('dashboard.uploadInvoice')}, um zu beginnen.
        </div>
      </div>
    </div>
  )
}
