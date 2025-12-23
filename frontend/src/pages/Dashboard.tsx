import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { FileText, CheckCircle, AlertTriangle, XCircle, Loader2, AlertCircle, FolderOpen, BarChart3, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import clsx from 'clsx'

// CSS für elegante Animationen
const cssAnimations = `
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  @keyframes pulse-soft {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }

  .animate-float {
    animation: float 6s ease-in-out infinite;
  }

  .animate-float-delayed {
    animation: float 6s ease-in-out infinite;
    animation-delay: 2s;
  }

  .glass-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .glass-card-strong {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.18);
  }

  .stat-glow-blue {
    box-shadow: 0 0 30px rgba(96, 165, 250, 0.2), 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .stat-glow-green {
    box-shadow: 0 0 30px rgba(52, 211, 153, 0.2), 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .stat-glow-yellow {
    box-shadow: 0 0 30px rgba(251, 191, 36, 0.2), 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .stat-glow-red {
    box-shadow: 0 0 30px rgba(248, 113, 113, 0.2), 0 4px 20px rgba(0, 0, 0, 0.1);
  }
`

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
      gradient: 'from-blue-400 to-blue-600',
      glowClass: 'stat-glow-blue',
      iconBg: 'bg-blue-500/20',
      iconColor: 'text-blue-300',
    },
    {
      name: t('audit.compliant'),
      value: stats?.approved || 0,
      icon: CheckCircle,
      gradient: 'from-emerald-400 to-emerald-600',
      glowClass: 'stat-glow-green',
      iconBg: 'bg-emerald-500/20',
      iconColor: 'text-emerald-300',
    },
    {
      name: t('audit.needsReview'),
      value: stats?.pending_review || 0,
      icon: AlertTriangle,
      gradient: 'from-amber-400 to-amber-600',
      glowClass: 'stat-glow-yellow',
      iconBg: 'bg-amber-500/20',
      iconColor: 'text-amber-300',
    },
    {
      name: t('audit.nonCompliant'),
      value: stats?.rejected || 0,
      icon: XCircle,
      gradient: 'from-red-400 to-red-600',
      glowClass: 'stat-glow-red',
      iconBg: 'bg-red-500/20',
      iconColor: 'text-red-300',
    },
  ]

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-600 p-6">
        <style>{cssAnimations}</style>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 text-blue-300 animate-spin" />
          <span className="ml-3 text-blue-200">{t('common.loading')}</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-600 p-6">
        <style>{cssAnimations}</style>
        <div className="glass-card-strong rounded-2xl p-6 max-w-md mx-auto mt-20">
          <div className="flex items-center">
            <div className="p-3 bg-red-500/20 rounded-xl">
              <AlertCircle className="h-6 w-6 text-red-300" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-white">{t('common.error')}</h3>
              <p className="text-sm text-red-200 mt-1">
                {t('errors.network')}
              </p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="mt-4 w-full px-4 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            {t('common.retry')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-800 to-blue-600 relative overflow-hidden">
      <style>{cssAnimations}</style>

      {/* Decorative Elements */}
      <div className="absolute top-20 right-20 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl animate-float pointer-events-none" />
      <div className="absolute bottom-40 left-20 w-48 h-48 bg-cyan-400/10 rounded-full blur-3xl animate-float-delayed pointer-events-none" />

      {/* Floating Logo */}
      <div className="absolute top-6 right-6 z-10 animate-float pointer-events-none opacity-30">
        <img src="/auditlogo.png" alt="FlowAudit" className="w-16 h-16 object-contain" />
      </div>

      <div className="relative z-10 p-6 space-y-6">
        {/* Welcome Header */}
        <div className="glass-card-strong rounded-2xl p-8">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-2xl shadow-lg">
              <img src="/auditlogo.png" alt="FlowAudit" className="w-12 h-12 object-contain" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{t('dashboard.welcome')}</h1>
              <p className="text-blue-200 mt-1">
                KI-gestütztes Rechnungsprüfungssystem für den Seminarbetrieb
              </p>
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((stat, index) => (
            <div
              key={stat.name}
              className={clsx(
                'glass-card rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02]',
                stat.glowClass
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-center">
                <div className={clsx('p-4 rounded-xl', stat.iconBg)}>
                  <stat.icon className={clsx('h-7 w-7', stat.iconColor)} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-200">{stat.name}</p>
                  <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="glass-card-strong rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-5">{t('dashboard.quickActions')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/documents"
              className="group flex items-center p-5 glass-card rounded-xl hover:bg-white/15 transition-all duration-300"
            >
              <div className="p-3 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <FileText className="h-7 w-7 text-white" />
              </div>
              <div className="ml-4">
                <p className="font-semibold text-white">{t('dashboard.uploadInvoice')}</p>
                <p className="text-sm text-blue-200/80 mt-0.5">PDF-Dokument prüfen</p>
              </div>
            </Link>

            <Link
              to="/projects"
              className="group flex items-center p-5 glass-card rounded-xl hover:bg-white/15 transition-all duration-300"
            >
              <div className="p-3 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <FolderOpen className="h-7 w-7 text-white" />
              </div>
              <div className="ml-4">
                <p className="font-semibold text-white">{t('projects.createProject')}</p>
                <p className="text-sm text-blue-200/80 mt-0.5">Projektstruktur anlegen</p>
              </div>
            </Link>

            <Link
              to="/statistics"
              className="group flex items-center p-5 glass-card rounded-xl hover:bg-white/15 transition-all duration-300"
            >
              <div className="p-3 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl shadow-lg group-hover:scale-110 transition-transform">
                <BarChart3 className="h-7 w-7 text-white" />
              </div>
              <div className="ml-4">
                <p className="font-semibold text-white">{t('dashboard.viewStatistics')}</p>
                <p className="text-sm text-blue-200/80 mt-0.5">Lernkurve anzeigen</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass-card-strong rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">{t('dashboard.recentDocuments')}</h2>
          <div className="text-sm text-blue-200/70 p-4 glass-card rounded-xl text-center">
            {t('common.noData')}. {t('dashboard.uploadInvoice')}, um zu beginnen.
          </div>
        </div>
      </div>
    </div>
  )
}
