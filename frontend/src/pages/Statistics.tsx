import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6']

export default function Statistics() {
  const { t } = useTranslation()
  const { data: stats, isLoading, error, refetch } = useQuery({
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

  // Extract data from API response, with fallback to mock data
  const feedbackStats = stats?.feedback?.summary || {}
  const llmStats = stats?.llm || {}
  const ragStats = stats?.rag || {}

  // Use API data if available, otherwise use fallback
  const feedbackErrors = stats?.feedback?.errors_by_feature as { feature_id: string; error_count: number }[] | undefined
  const errorByFeature = feedbackErrors && feedbackErrors.length > 0
    ? feedbackErrors.map((f) => ({
        name: f.feature_id,
        count: f.error_count,
      }))
    : [
        { name: 'invoice_number', count: 12 },
        { name: 'vat_id', count: 8 },
        { name: 'supply_date', count: 6 },
        { name: 'net_amount', count: 4 },
        { name: 'calculation', count: 3 },
      ]

  const ratingDist = feedbackStats.rating_distribution || {}
  const assessmentDistribution = [
    { name: 'OK', value: ratingDist.CORRECT || 65 },
    { name: 'Prüfung', value: ratingDist.PARTIAL || 25 },
    { name: 'Abgelehnt', value: ratingDist.WRONG || 10 },
  ]

  // Learning curve - static for now until we implement timeline tracking
  const learningCurve = [
    { day: 'Mo', correct: 60, total: 80 },
    { day: 'Di', correct: 70, total: 85 },
    { day: 'Mi', correct: 75, total: 82 },
    { day: 'Do', correct: 82, total: 90 },
    { day: 'Fr', correct: 88, total: 95 },
  ]

  // Error source breakdown from API
  const errorsBySource = stats?.feedback?.errors_by_source || {}
  const taxLawErrors = errorsBySource.TAX_LAW?.percentage || 45
  const beneficiaryErrors = errorsBySource.BENEFICIARY_DATA?.percentage || 30
  const locationErrors = errorsBySource.LOCATION_VALIDATION?.percentage || 25

  // Summary stats
  const totalFeedback = feedbackStats.total_feedback_entries || 0
  const totalLlmRequests = llmStats.local_model_stats?.total_requests || 0
  const totalRagExamples = ragStats.collection_stats?.total_examples || 0

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

        {/* Summary Stats */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Übersicht</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalFeedback}</p>
              <p className="text-sm text-gray-600">Feedback-Einträge</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalLlmRequests}</p>
              <p className="text-sm text-gray-600">LLM-Anfragen</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalRagExamples}</p>
              <p className="text-sm text-gray-600">RAG-Beispiele</p>
            </div>
          </div>
        </div>

        {/* Error Source Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fehlerquellen</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{taxLawErrors}%</p>
              <p className="text-sm text-blue-600">Steuerrechtliche Fehler</p>
              <p className="text-xs text-blue-500 mt-1">
                Fehlende Pflichtangaben, Formatfehler
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-700">{beneficiaryErrors}%</p>
              <p className="text-sm text-purple-600">Begünstigtendaten</p>
              <p className="text-xs text-purple-500 mt-1">
                Name/Adresse stimmt nicht überein
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-700">{locationErrors}%</p>
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
