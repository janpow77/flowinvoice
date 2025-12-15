import { useQuery } from '@tanstack/react-query'
import { FileText, CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react'
import { api } from '@/lib/api'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getStats(),
  })

  const statCards = [
    {
      name: 'Dokumente gesamt',
      value: stats?.total_documents || 0,
      icon: FileText,
      color: 'text-blue-600 bg-blue-50',
    },
    {
      name: 'Geprüft (OK)',
      value: stats?.approved || 0,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-50',
    },
    {
      name: 'Zur Prüfung',
      value: stats?.pending_review || 0,
      icon: AlertTriangle,
      color: 'text-yellow-600 bg-yellow-50',
    },
    {
      name: 'Abgelehnt',
      value: stats?.rejected || 0,
      icon: XCircle,
      color: 'text-red-600 bg-red-50',
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Clock className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Schnellaktionen</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/documents"
            className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
          >
            <FileText className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <p className="font-medium text-primary-900">Rechnung hochladen</p>
              <p className="text-sm text-primary-600">PDF-Dokument prüfen</p>
            </div>
          </a>

          <a
            href="/projects"
            className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <FileText className="h-8 w-8 text-gray-600" />
            <div className="ml-4">
              <p className="font-medium text-gray-900">Neues Projekt</p>
              <p className="text-sm text-gray-600">Projektstruktur anlegen</p>
            </div>
          </a>

          <a
            href="/statistics"
            className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <FileText className="h-8 w-8 text-gray-600" />
            <div className="ml-4">
              <p className="font-medium text-gray-900">Statistiken</p>
              <p className="text-sm text-gray-600">Lernkurve anzeigen</p>
            </div>
          </a>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Letzte Aktivitäten</h2>
        <div className="text-sm text-gray-500">
          Noch keine Aktivitäten vorhanden. Laden Sie eine Rechnung hoch, um zu beginnen.
        </div>
      </div>
    </div>
  )
}
