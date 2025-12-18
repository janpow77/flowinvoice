import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertCircle, RefreshCw, Loader2, Filter, FolderOpen } from 'lucide-react'
import { api } from '@/lib/api'

const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6']

interface Project {
  id: string
  title: string
  ruleset_id?: string
}

interface FeatureInfo {
  name_de: string
  name_en: string
  category: string
  required_level: string
  legal_basis: string
}

export default function Statistics() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all')

  // Fetch projects for filter
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  // Fetch all feature names from all rulesets
  const { data: allFeatureNames } = useQuery({
    queryKey: ['all-feature-names'],
    queryFn: () => api.getAllFeatureNames(),
  })

  // Helper function to get feature name based on language and ruleset
  const getFeatureName = (featureId: string, rulesetId: string = 'DE_USTG'): string => {
    const rulesets = allFeatureNames?.rulesets || {}
    const features = rulesets[rulesetId] || rulesets['DE_USTG'] || {}
    const feature = features[featureId] as FeatureInfo | undefined

    if (feature) {
      return lang === 'de' ? feature.name_de : feature.name_en
    }

    // Fallback: Return feature_id formatted
    return featureId.replace(/_/g, ' ')
  }

  // Fetch global stats
  const { data: globalStats, isLoading: isLoadingGlobal, error: globalError, refetch: refetchGlobal } = useQuery({
    queryKey: ['statistics'],
    queryFn: () => api.getDetailedStats(),
    retry: 2,
    enabled: selectedProjectId === 'all',
  })

  // Fetch project-specific stats
  const { data: projectStats, isLoading: isLoadingProject, error: projectError, refetch: refetchProject } = useQuery({
    queryKey: ['project-stats', selectedProjectId],
    queryFn: () => api.getProjectStats(selectedProjectId),
    retry: 2,
    enabled: selectedProjectId !== 'all',
  })

  const stats = selectedProjectId === 'all' ? globalStats : null
  const projStats = selectedProjectId !== 'all' ? projectStats : null
  const isLoading = selectedProjectId === 'all' ? isLoadingGlobal : isLoadingProject
  const error = selectedProjectId === 'all' ? globalError : projectError
  const refetch = selectedProjectId === 'all' ? refetchGlobal : refetchProject

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

  // Extract data from API response - NO MOCK DATA FALLBACK
  const feedbackStats = stats?.feedback?.summary || {}
  const llmStats = stats?.llm || {}
  const ragStats = stats?.rag || {}

  // Get feature errors from API (no fallback)
  const feedbackErrors = stats?.feedback?.errors_by_feature as { feature_id: string; error_count: number }[] | undefined
  const errorByFeature = feedbackErrors && feedbackErrors.length > 0
    ? feedbackErrors.map((f) => ({
        name: getFeatureName(f.feature_id),
        count: f.error_count,
      }))
    : []

  // Rating distribution - actual values only (0 if no data)
  const ratingDist = feedbackStats.rating_distribution || {}
  const totalRatings = (ratingDist.CORRECT || 0) + (ratingDist.PARTIAL || 0) + (ratingDist.WRONG || 0)
  const assessmentDistribution = totalRatings > 0
    ? [
        { name: 'OK', value: ratingDist.CORRECT || 0 },
        { name: lang === 'de' ? 'Prüfung' : 'Review', value: ratingDist.PARTIAL || 0 },
        { name: lang === 'de' ? 'Abgelehnt' : 'Rejected', value: ratingDist.WRONG || 0 },
      ]
    : []

  // Error source breakdown from API (0 if no data)
  const errorsBySource = stats?.feedback?.errors_by_source || {}
  const taxLawErrors = errorsBySource.TAX_LAW?.percentage || 0
  const beneficiaryErrors = errorsBySource.BENEFICIARY_DATA?.percentage || 0
  const locationErrors = errorsBySource.LOCATION_VALIDATION?.percentage || 0

  // Summary stats (actual values)
  const totalFeedback = feedbackStats.total_feedback_entries || 0
  const totalLlmRequests = llmStats.local_model_stats?.total_requests || 0
  const totalRagExamples = ragStats.collection_stats?.total_examples || 0

  // Project-specific counters
  const projectCounters = projStats?.counters || {}

  return (
    <div className="space-y-6">
      {/* Header with Project Filter */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          {lang === 'de' ? 'Statistiken' : 'Statistics'}
        </h2>

        <div className="flex items-center gap-3">
          <Filter className="h-5 w-5 text-gray-400" />
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">{lang === 'de' ? 'Alle Projekte' : 'All Projects'}</option>
            {projects?.map((project: Project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Project-specific Stats (when a project is selected) */}
      {selectedProjectId !== 'all' && projStats && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <FolderOpen className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              {lang === 'de' ? 'Projekt-Übersicht' : 'Project Overview'}
            </h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{projectCounters.documents_total || 0}</p>
              <p className="text-sm text-gray-600">{lang === 'de' ? 'Dokumente' : 'Documents'}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-700">{projectCounters.accepted || 0}</p>
              <p className="text-sm text-green-600">{lang === 'de' ? 'Akzeptiert' : 'Accepted'}</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-700">{projectCounters.review_pending || 0}</p>
              <p className="text-sm text-yellow-600">{lang === 'de' ? 'Prüfung' : 'Review'}</p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-700">{projectCounters.rejected || 0}</p>
              <p className="text-sm text-red-600">{lang === 'de' ? 'Abgelehnt' : 'Rejected'}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error by Feature */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {lang === 'de' ? 'Fehler nach Merkmal' : 'Errors by Feature'}
          </h3>
          {errorByFeature.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={errorByFeature}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <p>{lang === 'de' ? 'Keine Fehler erfasst' : 'No errors recorded'}</p>
            </div>
          )}
        </div>

        {/* Assessment Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {lang === 'de' ? 'Bewertungsverteilung' : 'Assessment Distribution'}
          </h3>
          {assessmentDistribution.length > 0 && totalRatings > 0 ? (
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
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <p>{lang === 'de' ? 'Keine Bewertungen vorhanden' : 'No assessments available'}</p>
            </div>
          )}
        </div>

        {/* Summary Stats */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {lang === 'de' ? 'Übersicht' : 'Overview'}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalFeedback}</p>
              <p className="text-sm text-gray-600">{lang === 'de' ? 'Feedback-Einträge' : 'Feedback Entries'}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalLlmRequests}</p>
              <p className="text-sm text-gray-600">{lang === 'de' ? 'LLM-Anfragen' : 'LLM Requests'}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{totalRagExamples}</p>
              <p className="text-sm text-gray-600">{lang === 'de' ? 'RAG-Beispiele' : 'RAG Examples'}</p>
            </div>
          </div>
        </div>

        {/* Error Source Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {lang === 'de' ? 'Fehlerquellen' : 'Error Sources'}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-700">{taxLawErrors}%</p>
              <p className="text-sm text-blue-600">
                {lang === 'de' ? 'Steuerrechtliche Fehler' : 'Tax Law Errors'}
              </p>
              <p className="text-xs text-blue-500 mt-1">
                {lang === 'de' ? 'Fehlende Pflichtangaben, Formatfehler' : 'Missing required fields, format errors'}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-2xl font-bold text-purple-700">{beneficiaryErrors}%</p>
              <p className="text-sm text-purple-600">
                {lang === 'de' ? 'Begünstigtendaten' : 'Beneficiary Data'}
              </p>
              <p className="text-xs text-purple-500 mt-1">
                {lang === 'de' ? 'Name/Adresse stimmt nicht überein' : 'Name/address mismatch'}
              </p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-700">{locationErrors}%</p>
              <p className="text-sm text-orange-600">
                {lang === 'de' ? 'Standortvalidierung' : 'Location Validation'}
              </p>
              <p className="text-xs text-orange-500 mt-1">
                {lang === 'de' ? 'Durchführungsort weicht ab' : 'Implementation location differs'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
