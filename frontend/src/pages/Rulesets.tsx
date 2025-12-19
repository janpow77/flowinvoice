import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Book,
  Plus,
  Edit2,
  Eye,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Loader2,
  X,
  Save,
  Trash2,
  FileText,
  Code2,
  Copy,
  Check,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

// Alle unterstützten Dokumenttypen
const DOCUMENT_TYPES = [
  'standard_invoice',
  'small_amount_invoice',
  'receipt',
  'credit_note',
  'delivery_note',
  'proforma_invoice',
  'expense_report',
  'contract',
  'offer',
  'order_confirmation',
] as const

type DocumentType = typeof DOCUMENT_TYPES[number]

interface Feature {
  feature_id: string
  name_de: string
  name_en: string
  legal_basis: string
  required_level: 'REQUIRED' | 'CONDITIONAL' | 'OPTIONAL'
  category: string
  explanation_de: string
  explanation_en: string
  applies_to?: Partial<Record<DocumentType, boolean>>
}

interface LegalReference {
  law: string
  section: string
  description_de: string
  description_en: string
}

interface Ruleset {
  ruleset_id: string
  version: string
  jurisdiction: string
  title_de: string
  title_en: string
  legal_references: LegalReference[]
  features: Feature[]
  default_language: string
  supported_ui_languages: string[]
  currency_default: string
  special_rules?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

interface RulesetListItem {
  ruleset_id: string
  version: string
  title: string
  language_support?: string[]
}

type ViewMode = 'list' | 'detail' | 'edit' | 'create'

const REQUIRED_LEVEL_COLORS = {
  REQUIRED: 'bg-red-100 text-red-700 border-red-200',
  CONDITIONAL: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  OPTIONAL: 'bg-gray-100 text-gray-600 border-gray-200',
}

const CATEGORY_ICONS: Record<string, string> = {
  IDENTITY: '🏢',
  DATE: '📅',
  AMOUNT: '💰',
  TAX: '📊',
  TEXT: '📝',
}

export default function Rulesets() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const lang = i18n.language as 'de' | 'en'

  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedRuleset, setSelectedRuleset] = useState<Ruleset | null>(null)
  const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(new Set())
  const [editForm, setEditForm] = useState<Partial<Ruleset>>({})
  const [showLlmSchema, setShowLlmSchema] = useState(false)
  const [copiedField, setCopiedField] = useState<string | null>(null)

  // Fetch rulesets list
  const { data: rulesets, isLoading, error } = useQuery({
    queryKey: ['rulesets'],
    queryFn: () => api.getRulesets(),
  })

  // Fetch single ruleset detail
  const { data: rulesetDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['ruleset', selectedRuleset?.ruleset_id],
    queryFn: () => api.getRuleset(selectedRuleset!.ruleset_id),
    enabled: !!selectedRuleset?.ruleset_id && (viewMode === 'detail' || viewMode === 'edit'),
  })

  // Fetch LLM schema
  const { data: llmSchema, isLoading: isLoadingSchema } = useQuery({
    queryKey: ['ruleset-llm-schema', selectedRuleset?.ruleset_id, selectedRuleset?.version],
    queryFn: () => api.getRulesetLlmSchema(selectedRuleset!.ruleset_id, selectedRuleset?.version),
    enabled: !!selectedRuleset?.ruleset_id && showLlmSchema,
  })

  // Create ruleset mutation
  const createMutation = useMutation({
    mutationFn: (data: Partial<Ruleset>) => api.createRuleset(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rulesets'] })
      setViewMode('list')
      setEditForm({})
    },
  })

  // Update ruleset mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, version, data }: { id: string; version: string; data: Partial<Ruleset> }) =>
      api.updateRuleset(id, version, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rulesets'] })
      queryClient.invalidateQueries({ queryKey: ['ruleset', selectedRuleset?.ruleset_id] })
      setViewMode('detail')
    },
  })

  const toggleFeature = (featureId: string) => {
    const newExpanded = new Set(expandedFeatures)
    if (newExpanded.has(featureId)) {
      newExpanded.delete(featureId)
    } else {
      newExpanded.add(featureId)
    }
    setExpandedFeatures(newExpanded)
  }

  const handleViewDetail = (ruleset: RulesetListItem) => {
    setSelectedRuleset({ ruleset_id: ruleset.ruleset_id, version: ruleset.version } as Ruleset)
    setViewMode('detail')
  }

  const handleEdit = () => {
    if (rulesetDetail) {
      setEditForm(rulesetDetail)
      setViewMode('edit')
    }
  }

  const handleCreate = () => {
    setEditForm({
      ruleset_id: '',
      version: '1.0.0',
      jurisdiction: 'DE',
      title_de: '',
      title_en: '',
      default_language: 'de',
      supported_ui_languages: ['de', 'en'],
      currency_default: 'EUR',
      legal_references: [],
      features: [],
    })
    setViewMode('create')
  }

  const handleSave = () => {
    if (viewMode === 'create') {
      createMutation.mutate(editForm)
    } else if (viewMode === 'edit' && selectedRuleset) {
      updateMutation.mutate({
        id: selectedRuleset.ruleset_id,
        version: selectedRuleset.version,
        data: editForm,
      })
    }
  }

  const handleAddFeature = () => {
    // Initialisiere applies_to mit allen Dokumenttypen (Standard aktiv)
    const defaultAppliesTo = DOCUMENT_TYPES.reduce((acc, docType) => {
      acc[docType] = docType === 'standard_invoice'
      return acc
    }, {} as Record<DocumentType, boolean>)

    const newFeature: Feature = {
      feature_id: `feature_${Date.now()}`,
      name_de: 'Neues Merkmal',
      name_en: 'New Feature',
      legal_basis: '',
      required_level: 'REQUIRED',
      category: 'TEXT',
      explanation_de: '',
      explanation_en: '',
      applies_to: defaultAppliesTo,
    }
    setEditForm({
      ...editForm,
      features: [...(editForm.features || []), newFeature],
    })
  }

  const handleUpdateFeature = (index: number, updates: Partial<Feature>) => {
    const features = [...(editForm.features || [])]
    features[index] = { ...features[index], ...updates }
    setEditForm({ ...editForm, features })
  }

  const handleDeleteFeature = (index: number) => {
    const features = [...(editForm.features || [])]
    features.splice(index, 1)
    setEditForm({ ...editForm, features })
  }

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

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
            <p className="text-sm text-red-600 mt-1">{(error as Error).message}</p>
          </div>
        </div>
      </div>
    )
  }

  // Render list view
  if (viewMode === 'list') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{t('rulesets.title')}</h2>
            <p className="text-sm text-gray-500 mt-1">{t('rulesets.description')}</p>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-5 w-5 mr-2" />
            {t('rulesets.createRuleset')}
          </button>
        </div>

        {/* Rulesets Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rulesets?.map((ruleset: RulesetListItem) => (
            <div
              key={`${ruleset.ruleset_id}-${ruleset.version}`}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary-50 rounded-lg">
                    <Book className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{ruleset.title}</h3>
                    <p className="text-sm text-gray-500">
                      {ruleset.ruleset_id} v{ruleset.version}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => handleViewDetail(ruleset)}
                  className="flex items-center px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  {t('rulesets.view')}
                </button>
                <button
                  onClick={() => {
                    setSelectedRuleset({ ruleset_id: ruleset.ruleset_id, version: ruleset.version } as Ruleset)
                    setViewMode('edit')
                  }}
                  className="flex items-center px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <Edit2 className="h-4 w-4 mr-1" />
                  {t('rulesets.edit')}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Empty state */}
        {(!rulesets || rulesets.length === 0) && (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <Book className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">{t('rulesets.noRulesets')}</h3>
            <p className="mt-2 text-sm text-gray-500">{t('rulesets.noRulesetsDesc')}</p>
            <button
              onClick={handleCreate}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              {t('rulesets.createRuleset')}
            </button>
          </div>
        )}
      </div>
    )
  }

  // Render detail view
  if (viewMode === 'detail') {
    const ruleset = rulesetDetail

    if (isLoadingDetail || !ruleset) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        </div>
      )
    }

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setViewMode('list')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ChevronRight className="h-5 w-5 text-gray-500 rotate-180" />
            </button>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {lang === 'de' ? ruleset.title_de : ruleset.title_en}
              </h2>
              <p className="text-sm text-gray-500">
                {ruleset.ruleset_id} v{ruleset.version} • {ruleset.jurisdiction}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowLlmSchema(true)}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Code2 className="h-5 w-5 mr-2" />
              {t('rulesets.llmSchema')}
            </button>
            <button
              onClick={handleEdit}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Edit2 className="h-5 w-5 mr-2" />
              {t('rulesets.edit')}
            </button>
          </div>
        </div>

        {/* Legal References */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('rulesets.legalReferences')}</h3>
          <div className="space-y-2">
            {ruleset.legal_references?.map((ref: LegalReference, idx: number) => (
              <div key={idx} className="flex items-start gap-2 text-sm">
                <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
                <div>
                  <span className="font-medium">{ref.law} {ref.section}</span>
                  <span className="text-gray-500 ml-2">
                    {lang === 'de' ? ref.description_de : ref.description_en}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Features List */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{t('rulesets.features')}</h3>
            <span className="text-sm text-gray-500">
              {ruleset.features?.length || 0} {t('rulesets.featuresCount')}
            </span>
          </div>

          <div className="space-y-2">
            {ruleset.features?.map((feature: Feature) => (
              <div
                key={feature.feature_id}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleFeature(feature.feature_id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{CATEGORY_ICONS[feature.category] || '📋'}</span>
                    <div className="text-left">
                      <p className="font-medium text-gray-900">
                        {lang === 'de' ? feature.name_de : feature.name_en}
                      </p>
                      <p className="text-sm text-gray-500">{feature.legal_basis}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        'px-2 py-0.5 text-xs font-medium rounded border',
                        REQUIRED_LEVEL_COLORS[feature.required_level]
                      )}
                    >
                      {t(`rulesets.${feature.required_level.toLowerCase()}`)}
                    </span>
                    {expandedFeatures.has(feature.feature_id) ? (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </button>

                {expandedFeatures.has(feature.feature_id) && (
                  <div className="px-4 pb-4 bg-gray-50 border-t border-gray-200">
                    <div className="pt-3 space-y-2 text-sm">
                      <p className="text-gray-600">
                        {lang === 'de' ? feature.explanation_de : feature.explanation_en}
                      </p>
                      <div className="flex items-center gap-2 flex-wrap text-xs text-gray-500">
                        <span>ID: {feature.feature_id}</span>
                        <span>Kategorie: {feature.category}</span>
                      </div>
                      {feature.applies_to && Object.entries(feature.applies_to).some(([, v]) => v) && (
                        <div className="flex items-center gap-1 flex-wrap mt-2">
                          <span className="text-xs text-gray-500 mr-1">{t('rulesets.appliesTo')}:</span>
                          {Object.entries(feature.applies_to).map(([docType, enabled]) =>
                            enabled && (
                              <span
                                key={docType}
                                className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded"
                              >
                                {t(`rulesets.documentTypes.${docType}`)}
                              </span>
                            )
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* LLM Schema Modal */}
        {showLlmSchema && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <Code2 className="h-6 w-6 text-primary-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {t('rulesets.llmSchemaTitle')}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {ruleset.ruleset_id} v{ruleset.version}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowLlmSchema(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-auto p-6 space-y-6">
                {isLoadingSchema ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
                    <span className="ml-3 text-gray-600">{t('common.loading')}</span>
                  </div>
                ) : llmSchema ? (
                  <>
                    {/* Info */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-700">
                        {t('rulesets.llmSchemaInfo')}
                      </p>
                    </div>

                    {/* System Prompt */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{t('rulesets.systemPrompt')}</h4>
                        <button
                          onClick={() => copyToClipboard(llmSchema.llm_schema.system_prompt, 'system')}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                        >
                          {copiedField === 'system' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {t('common.copy')}
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                        {llmSchema.llm_schema.system_prompt}
                      </pre>
                    </div>

                    {/* User Prompt Structure */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{t('rulesets.userPromptStructure')}</h4>
                        <button
                          onClick={() => copyToClipboard(llmSchema.llm_schema.user_prompt_structure, 'user')}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                        >
                          {copiedField === 'user' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {t('common.copy')}
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                        {llmSchema.llm_schema.user_prompt_structure}
                      </pre>
                    </div>

                    {/* Response JSON Schema */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{t('rulesets.responseSchema')}</h4>
                        <button
                          onClick={() => copyToClipboard(JSON.stringify(llmSchema.llm_schema.response_json_schema, null, 2), 'response')}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                        >
                          {copiedField === 'response' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {t('common.copy')}
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto font-mono">
                        {JSON.stringify(llmSchema.llm_schema.response_json_schema, null, 2)}
                      </pre>
                    </div>

                    {/* Features Schema */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">
                          {t('rulesets.featuresSchema')} ({llmSchema.features_count} {t('rulesets.featuresCount')})
                        </h4>
                        <button
                          onClick={() => copyToClipboard(JSON.stringify(llmSchema.llm_schema.features_json_schema, null, 2), 'features')}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                        >
                          {copiedField === 'features' ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          {t('common.copy')}
                        </button>
                      </div>
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto font-mono">
                        {JSON.stringify(llmSchema.llm_schema.features_json_schema, null, 2)}
                      </pre>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    {t('rulesets.noSchemaData')}
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end px-6 py-4 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={() => setShowLlmSchema(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  {t('common.close')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Render edit/create view
  if (viewMode === 'edit' || viewMode === 'create') {
    const isSaving = createMutation.isPending || updateMutation.isPending

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setViewMode(viewMode === 'create' ? 'list' : 'detail')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
            <h2 className="text-xl font-semibold text-gray-900">
              {viewMode === 'create' ? t('rulesets.createRuleset') : t('rulesets.editRuleset')}
            </h2>
          </div>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
            ) : (
              <Save className="h-5 w-5 mr-2" />
            )}
            {t('common.save')}
          </button>
        </div>

        {/* Error Display */}
        {(createMutation.error || updateMutation.error) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center text-sm text-red-600">
            <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
            {((createMutation.error || updateMutation.error) as Error).message}
          </div>
        )}

        {/* Basic Info */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('rulesets.basicInfo')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.rulesetId')} *
              </label>
              <input
                type="text"
                value={editForm.ruleset_id || ''}
                onChange={(e) => setEditForm({ ...editForm, ruleset_id: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="DE_USTG"
                disabled={viewMode === 'edit'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.version')} *
              </label>
              <input
                type="text"
                value={editForm.version || ''}
                onChange={(e) => setEditForm({ ...editForm, version: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="1.0.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.titleDe')} *
              </label>
              <input
                type="text"
                value={editForm.title_de || ''}
                onChange={(e) => setEditForm({ ...editForm, title_de: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Deutschland – Umsatzsteuergesetz"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.titleEn')} *
              </label>
              <input
                type="text"
                value={editForm.title_en || ''}
                onChange={(e) => setEditForm({ ...editForm, title_en: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Germany – VAT Act"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.jurisdiction')}
              </label>
              <select
                value={editForm.jurisdiction || 'DE'}
                onChange={(e) => setEditForm({ ...editForm, jurisdiction: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="DE">Deutschland (DE)</option>
                <option value="AT">Österreich (AT)</option>
                <option value="CH">Schweiz (CH)</option>
                <option value="EU">Europäische Union (EU)</option>
                <option value="UK">Großbritannien (UK)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('rulesets.currency')}
              </label>
              <select
                value={editForm.currency_default || 'EUR'}
                onChange={(e) => setEditForm({ ...editForm, currency_default: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="EUR">Euro (EUR)</option>
                <option value="CHF">Schweizer Franken (CHF)</option>
                <option value="GBP">Britisches Pfund (GBP)</option>
                <option value="USD">US-Dollar (USD)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{t('rulesets.features')}</h3>
            <button
              onClick={handleAddFeature}
              className="flex items-center px-3 py-1.5 text-sm bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100 transition-colors"
            >
              <Plus className="h-4 w-4 mr-1" />
              {t('rulesets.addFeature')}
            </button>
          </div>

          <div className="space-y-4">
            {editForm.features?.map((feature, index) => (
              <div key={feature.feature_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-4">
                  <h4 className="font-medium text-gray-900">
                    {feature.name_de || `Merkmal ${index + 1}`}
                  </h4>
                  <button
                    onClick={() => handleDeleteFeature(index)}
                    className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Feature-ID
                    </label>
                    <input
                      type="text"
                      value={feature.feature_id}
                      onChange={(e) => handleUpdateFeature(index, { feature_id: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Kategorie
                    </label>
                    <select
                      value={feature.category}
                      onChange={(e) => handleUpdateFeature(index, { category: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="IDENTITY">Identität</option>
                      <option value="DATE">Datum</option>
                      <option value="AMOUNT">Betrag</option>
                      <option value="TAX">Steuer</option>
                      <option value="TEXT">Text</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Name (DE)
                    </label>
                    <input
                      type="text"
                      value={feature.name_de}
                      onChange={(e) => handleUpdateFeature(index, { name_de: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Name (EN)
                    </label>
                    <input
                      type="text"
                      value={feature.name_en}
                      onChange={(e) => handleUpdateFeature(index, { name_en: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Rechtsgrundlage
                    </label>
                    <input
                      type="text"
                      value={feature.legal_basis}
                      onChange={(e) => handleUpdateFeature(index, { legal_basis: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                      placeholder="§ 14 Abs. 4 Nr. 1 UStG"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Erforderlichkeit
                    </label>
                    <select
                      value={feature.required_level}
                      onChange={(e) => handleUpdateFeature(index, { required_level: e.target.value as Feature['required_level'] })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="REQUIRED">Pflicht</option>
                      <option value="CONDITIONAL">Bedingt</option>
                      <option value="OPTIONAL">Optional</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-gray-500 mb-1">
                      Erklärung (DE)
                    </label>
                    <textarea
                      value={feature.explanation_de}
                      onChange={(e) => handleUpdateFeature(index, { explanation_de: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500"
                      rows={2}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-gray-500 mb-2">
                      {t('rulesets.appliesTo')}
                    </label>
                    <div className="flex flex-wrap gap-3">
                      {DOCUMENT_TYPES.map((docType) => (
                        <label key={docType} className="flex items-center gap-1.5 text-sm">
                          <input
                            type="checkbox"
                            checked={feature.applies_to?.[docType] ?? (docType === 'standard_invoice')}
                            onChange={(e) => handleUpdateFeature(index, {
                              applies_to: {
                                ...feature.applies_to,
                                [docType]: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                          <span className="text-gray-700">{t(`rulesets.documentTypes.${docType}`)}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {(!editForm.features || editForm.features.length === 0) && (
              <div className="text-center py-8 text-gray-500">
                <p>{t('rulesets.noFeatures')}</p>
                <button
                  onClick={handleAddFeature}
                  className="mt-2 text-primary-600 hover:underline"
                >
                  {t('rulesets.addFirstFeature')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return null
}
