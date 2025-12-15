import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6']

export default function Statistics() {
  const { t } = useTranslation()
  const { data: _stats, isLoading, error, refetch } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => api.getDetailedStats(),
    retry: 2,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        <span className="ml-3 text-gray-600">{t('common.loading')}</span>
      </div>
    )
  }

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

  // Mock data for demonstration
  const errorByFeature = [
    { name: 'invoice_number', count: 12 },
    { name: 'vat_id', count: 8 },
    { name: 'supply_date', count: 6 },
    { name: 'net_amount', count: 4 },
    { name: 'calculation', count: 3 },
  ]

  const assessmentDistribution = [
    { name: 'OK', value: 65 },
    { name: 'Prüfung', value: 25 },
    { name: 'Abgelehnt', value: 10 },
  ]

  const learningCurve = [
    { day: 'Mo', correct: 60, total: 80 },
    { day: 'Di', correct: 70, total: 85 },
    { day: 'Mi', correct: 75, total: 82 },
    { day: 'Do', correct: 82, total: 90 },
    { day: 'Fr', correct: 88, total: 95 },
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Statistiken & Lernkurve</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error by Feature */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fehler nach Merkmal</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorByFeature}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Assessment Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Bewertungsverteilung</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={assessmentDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {assessmentDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Learning Curve */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Lernkurve</h3>
          <p className="text-sm text-gray-500 mb-4">
            Zeigt die Verbesserung der KI-Analyse über Zeit
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={learningCurve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="correct"
                  stroke="#22c55e"
                  strokeWidth={2}
                  name="Korrekt"
                />
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Gesamt"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Error Source Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fehlerquellen</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">45%</p>
              <p className="text-sm text-blue-600">Steuerrechtliche Fehler</p>
              <p className="text-xs text-blue-500 mt-1">
                Fehlende Pflichtangaben, Formatfehler
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-700">30%</p>
              <p className="text-sm text-purple-600">Begünstigtendaten</p>
              <p className="text-xs text-purple-500 mt-1">
                Name/Adresse stimmt nicht überein
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-700">25%</p>
              <p className="text-sm text-orange-600">Standortvalidierung</p>
              <p className="text-xs text-orange-500 mt-1">
                Durchführungsort weicht ab
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
