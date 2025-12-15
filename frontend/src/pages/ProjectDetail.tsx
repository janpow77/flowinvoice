import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, Upload, Calendar, Settings } from 'lucide-react'
import { api } from '@/lib/api'
import { TaxSystemSelector } from '@/components/tax-selector'
import { RulesetId, getRuleset } from '@/lib/rulesets'
import { useTranslation } from 'react-i18next'

interface Project {
  id: string
  title: string
  description?: string
  ruleset_id?: RulesetId
  start_date?: string
  end_date?: string
  created_at: string
  document_count?: number
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const [showTaxSelector, setShowTaxSelector] = useState(false)
  const lang = i18n.language as 'de' | 'en'

  const { data: project, isLoading, error } = useQuery<Project>({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id!),
    enabled: !!id,
  })

  const { data: documents } = useQuery({
    queryKey: ['documents', id],
    queryFn: () => api.getDocuments(id),
    enabled: !!id,
  })

  const updateRulesetMutation = useMutation({
    mutationFn: (rulesetId: RulesetId) => api.updateProject(id!, { ruleset_id: rulesetId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      setShowTaxSelector(false)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{t('errors.notFound')}</p>
        <Link to="/projects" className="mt-4 text-primary-600 hover:underline">
          {t('common.back')}
        </Link>
      </div>
    )
  }

  const currentRuleset = project.ruleset_id ? getRuleset(project.ruleset_id) : null

  // Show tax selector if no ruleset is set or user wants to change it
  if (!project.ruleset_id || showTaxSelector) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link
            to="/projects"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            {project.description && (
              <p className="mt-1 text-gray-500">{project.description}</p>
            )}
          </div>
        </div>

        {/* Tax System Selector */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <TaxSystemSelector
            currentRuleset={project.ruleset_id}
            onSelect={(rulesetId) => updateRulesetMutation.mutate(rulesetId)}
          />

          {showTaxSelector && project.ruleset_id && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={() => setShowTaxSelector(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                {t('common.cancel')}
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/projects"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
            {project.description && (
              <p className="mt-1 text-gray-500">{project.description}</p>
            )}
          </div>
        </div>

        <Link
          to={`/documents?project=${id}`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Upload className="h-4 w-4" />
          {t('documents.uploadDocument')}
        </Link>
      </div>

      {/* Tax System Info Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{currentRuleset?.flag}</span>
            <div>
              <h3 className="font-semibold text-gray-900">
                {t('taxSelector.currentSystem')}
              </h3>
              <p className="text-gray-600">
                {lang === 'de' ? currentRuleset?.title_de : currentRuleset?.title_en}
              </p>
              <p className="text-sm text-gray-400 mt-1">
                {currentRuleset?.legal_references[0]?.section}
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowTaxSelector(true)}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Settings className="h-4 w-4" />
            {t('taxSelector.changeSystem')}
          </button>
        </div>

        {/* Feature Summary */}
        <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">{t('taxSelector.requiredFields')}:</span>
            <span className="ml-2 font-medium">
              {currentRuleset?.features.filter(f => f.required_level === 'REQUIRED').length}
            </span>
          </div>
          <div>
            <span className="text-gray-500">{t('taxSelector.conditionalFields')}:</span>
            <span className="ml-2 font-medium">
              {currentRuleset?.features.filter(f => f.required_level === 'CONDITIONAL').length}
            </span>
          </div>
          {currentRuleset?.small_amount_threshold && (
            <div>
              <span className="text-gray-500">{t('taxSelector.smallAmountLimit')}:</span>
              <span className="ml-2 font-medium">
                ≤ {currentRuleset.small_amount_threshold}€
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Project Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Documents Count */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <FileText className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('projects.documentCount')}</p>
              <p className="text-xl font-semibold text-gray-900">
                {documents?.length || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Date Range */}
        {(project.start_date || project.end_date) && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Calendar className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{t('projects.lastActivity')}</p>
                <p className="text-sm font-medium text-gray-900">
                  {project.start_date && new Date(project.start_date).toLocaleDateString(lang)}
                  {project.end_date && ` - ${new Date(project.end_date).toLocaleDateString(lang)}`}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Created At */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('projects.createdAt')}</p>
              <p className="text-sm font-medium text-gray-900">
                {new Date(project.created_at).toLocaleDateString(lang)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Documents */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">{t('dashboard.recentDocuments')}</h3>
        </div>

        {documents && documents.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {documents.slice(0, 5).map((doc: { id: string; filename: string; status: string; created_at: string }) => (
              <Link
                key={doc.id}
                to={`/documents/${doc.id}`}
                className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(doc.created_at).toLocaleDateString(lang)}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  doc.status === 'PROCESSED'
                    ? 'bg-green-100 text-green-700'
                    : doc.status === 'FAILED'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {t(`documents.${doc.status.toLowerCase()}`)}
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">{t('documents.noDocuments')}</p>
            <Link
              to={`/documents?project=${id}`}
              className="mt-4 inline-flex items-center gap-2 text-primary-600 hover:underline"
            >
              <Upload className="h-4 w-4" />
              {t('documents.uploadDocument')}
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
