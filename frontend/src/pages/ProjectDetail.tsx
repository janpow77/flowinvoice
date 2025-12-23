import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import {
  ArrowLeft,
  FileText,
  Upload,
  Settings,
  ChevronDown,
  ChevronRight,
  Search,
  Trash2,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
  Pencil,
  Save,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Lock,
  Eye,
  List,
  FolderOpen,
  FileJson,
} from 'lucide-react'
import { api } from '@/lib/api'
import { TaxSystemSelector } from '@/components/tax-selector'
import { RulesetId, getRuleset, isDocumentTypeSupported } from '@/lib/rulesets'
import { useTranslation } from 'react-i18next'
import { SolutionFileUpload } from '@/components/documents'

interface ProjectData {
  id: string
  ruleset_id_hint?: RulesetId
  ui_language_hint?: string
  is_active: boolean
  created_at: string
  updated_at?: string
  beneficiary: {
    name: string
    legal_form?: string
    street: string
    zip: string
    city: string
    country?: string
    vat_id?: string
    tax_number?: string
    input_tax_deductible?: boolean
    aliases?: string[]
  }
  project: {
    project_title: string
    file_reference?: string
    project_description?: string
    implementation?: {
      location_name?: string
      street?: string
      zip?: string
      city?: string
    }
    total_budget?: number
    funding_type?: string
    funding_rate_percent?: number
    project_period?: {
      start?: string
      end?: string
    }
    approval_date?: string
    approving_authority?: string
  }
}

interface DocumentItem {
  id: string
  filename: string
  status: string
  created_at: string
  ruleset_id?: string
  document_type?: string
  analysis_result?: {
    id?: string
    overall_assessment?: string
    confidence?: number
    provider?: string
  }
  extracted_data?: {
    supplier_name_address?: { value?: string; confidence?: number }
    invoice_date?: { value?: string; confidence?: number }
    gross_amount?: { value?: string; confidence?: number }
    invoice_number?: { value?: string; confidence?: number }
    net_amount?: { value?: string; confidence?: number }
    vat_amount?: { value?: string; confidence?: number }
    vat_rate?: { value?: string; confidence?: number }
    [key: string]: { value?: string; confidence?: number } | undefined
  }
}

interface FeedbackItem {
  feedback_id: string
  rating: string
  override_count: number
  created_at: string
}

interface FinalResult {
  final_result_id: string
  document_id: string
  status: string
  fields: Array<{
    feature_id: string
    value: unknown
    confidence?: number
  }>
  overall?: {
    traffic_light?: string
    missing_required_features?: string[]
    conflicts?: string[]
  }
}

interface LlmRunItem {
  id: string
  provider: string
  model_name: string
  status: string
  stats: {
    duration_ms?: number
    input_tokens?: number
    output_tokens?: number
  }
  error_message?: string
  created_at: string
  completed_at?: string
}

type TabType = 'overview' | 'documents' | 'upload' | 'solutions'

type DocumentType = 'INVOICE' | 'BANK_STATEMENT' | 'PROCUREMENT' | 'CONTRACT' | 'OTHER'

interface UploadedFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'done' | 'error'
  documentType: DocumentType
  documentId?: string
  error?: string
}

interface AnalysisSettings {
  useOcr: boolean
  confidenceThreshold: number
  maxRuns: number
}

interface CheckerSettings {
  ruleset_id: string
  risk_checker: {
    enabled: boolean
    severity_threshold: string
    check_self_invoice: boolean
    check_duplicate_invoice: boolean
    check_round_amounts: boolean
    check_weekend_dates: boolean
    round_amount_threshold: number
  }
  semantic_checker: {
    enabled: boolean
    severity_threshold: string
    check_project_relevance: boolean
    check_description_quality: boolean
    min_relevance_score: number
    use_rag_context: boolean
  }
  economic_checker: {
    enabled: boolean
    severity_threshold: string
    check_budget_limits: boolean
    check_unit_prices: boolean
    check_funding_rate: boolean
    max_deviation_percent: number
  }
}

interface EditFormData {
  beneficiary: {
    name: string
    street: string
    zip: string
    city: string
    vat_id: string
    tax_number: string
  }
  project: {
    project_title: string
    file_reference: string
    project_description: string
    implementation_location: string
    period_start: string
    period_end: string
  }
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const lang = i18n.language as 'de' | 'en'

  const [showTaxSelector, setShowTaxSelector] = useState(false)
  const [showFeatures, setShowFeatures] = useState(false)
  const [showLegalRefs, setShowLegalRefs] = useState(false)
  const [showSpecialRules, setShowSpecialRules] = useState(false)
  const [showCheckers, setShowCheckers] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<UploadedFile[]>([])
  const [settings, setSettings] = useState<AnalysisSettings>({
    useOcr: true,
    confidenceThreshold: 0.7,
    maxRuns: 1,
  })
  const [editForm, setEditForm] = useState<EditFormData | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null)
  const [feedbackComment, setFeedbackComment] = useState('')

  const { data: project, isLoading, error } = useQuery<ProjectData>({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id!),
    enabled: !!id,
  })

  const { data: documents, refetch: refetchDocuments } = useQuery<DocumentItem[]>({
    queryKey: ['documents', id],
    queryFn: () => api.getDocuments(id),
    enabled: !!id,
  })

  // Query for selected document's feedback
  const { data: selectedDocFeedback } = useQuery<FeedbackItem[]>({
    queryKey: ['feedback', selectedDocument],
    queryFn: () => api.getDocumentFeedback(selectedDocument!),
    enabled: !!selectedDocument,
  })

  // Query for selected document's final result
  const { data: selectedDocFinal } = useQuery<FinalResult | null>({
    queryKey: ['final', selectedDocument],
    queryFn: () => api.getDocumentFinal(selectedDocument!).catch(() => null),
    enabled: !!selectedDocument,
  })

  // Query for selected document's LLM runs
  const { data: selectedDocLlmRuns } = useQuery<LlmRunItem[]>({
    queryKey: ['llm-runs', selectedDocument],
    queryFn: () => api.getDocumentLlmRuns(selectedDocument!),
    enabled: !!selectedDocument,
  })

  // Query for checker settings
  const { data: checkerSettings } = useQuery<CheckerSettings>({
    queryKey: ['checker-settings', project?.ruleset_id_hint],
    queryFn: () => api.getRulesetCheckerSettings(project!.ruleset_id_hint!),
    enabled: !!project?.ruleset_id_hint,
  })

  const updateRulesetMutation = useMutation({
    mutationFn: (rulesetId: RulesetId) => api.updateProject(id!, { ruleset_id: rulesetId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      setShowTaxSelector(false)
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async ({ file, fileId, documentType }: { file: File; fileId: string; documentType: DocumentType }) => {
      setUploadQueue(prev =>
        prev.map(f => (f.id === fileId ? { ...f, status: 'uploading' as const } : f))
      )
      const result = await api.uploadDocument(file, id!, documentType)
      return { fileId, result }
    },
    onSuccess: ({ fileId, result }) => {
      setUploadQueue(prev =>
        prev.map(f =>
          f.id === fileId ? { ...f, status: 'done' as const, documentId: result.document_id } : f
        )
      )
      refetchDocuments()
    },
    onError: (error, { fileId }) => {
      setUploadQueue(prev =>
        prev.map(f =>
          f.id === fileId ? { ...f, status: 'error' as const, error: (error as Error).message } : f
        )
      )
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: async (documentId: string) => {
      return api.analyzeDocument(documentId)
    },
    onSuccess: () => {
      refetchDocuments()
    },
  })

  const finalizeMutation = useMutation({
    mutationFn: async (documentId: string) => {
      return api.finalizeDocument(documentId)
    },
    onSuccess: () => {
      refetchDocuments()
      queryClient.invalidateQueries({ queryKey: ['final', selectedDocument] })
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: async ({ documentId, rating, acceptResult }: { documentId: string; rating: 'CORRECT' | 'INCORRECT'; acceptResult: boolean }) => {
      // First get the final result for the document
      const finalResult = await api.getDocumentFinal(documentId).catch(() => null)
      return api.submitFeedback({
        document_id: documentId,
        result_id: finalResult?.final_result_id || documentId,
        rating,
        comment: feedbackComment || undefined,
        accept_result: acceptResult,
      })
    },
    onSuccess: () => {
      setFeedbackComment('')
      refetchDocuments()
      queryClient.invalidateQueries({ queryKey: ['feedback', selectedDocument] })
      queryClient.invalidateQueries({ queryKey: ['final', selectedDocument] })
    },
  })

  const updateProjectMutation = useMutation({
    mutationFn: async (data: EditFormData) => {
      return api.updateProject(id!, {
        beneficiary: {
          name: data.beneficiary.name,
          street: data.beneficiary.street,
          zip: data.beneficiary.zip,
          city: data.beneficiary.city,
          vat_id: data.beneficiary.vat_id || undefined,
          tax_number: data.beneficiary.tax_number || undefined,
        },
        project: {
          project_title: data.project.project_title,
          file_reference: data.project.file_reference || undefined,
          project_description: data.project.project_description || undefined,
          implementation: data.project.implementation_location
            ? {
                location_name: data.project.implementation_location || undefined,
              }
            : undefined,
          project_period: data.project.period_start && data.project.period_end
            ? {
                start: data.project.period_start,
                end: data.project.period_end,
              }
            : undefined,
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      setIsEditing(false)
      setEditForm(null)
    },
  })

  const startEditing = () => {
    if (project) {
      setEditForm({
        beneficiary: {
          name: project.beneficiary.name || '',
          street: project.beneficiary.street || '',
          zip: project.beneficiary.zip || '',
          city: project.beneficiary.city || '',
          vat_id: project.beneficiary.vat_id || '',
          tax_number: project.beneficiary.tax_number || '',
        },
        project: {
          project_title: project.project.project_title || '',
          file_reference: project.project.file_reference || '',
          project_description: project.project.project_description || '',
          implementation_location: project.project.implementation?.location_name || '',
          period_start: project.project.project_period?.start || '',
          period_end: project.project.project_period?.end || '',
        },
      })
      setIsEditing(true)
    }
  }

  const saveEditing = () => {
    if (editForm) {
      updateProjectMutation.mutate(editForm)
    }
  }

  const cancelEditing = () => {
    setIsEditing(false)
    setEditForm(null)
  }

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.slice(0, 20 - uploadQueue.length).map(file => ({
        file,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        status: 'pending' as const,
        documentType: 'INVOICE' as DocumentType,
      }))
      setUploadQueue(prev => [...prev, ...newFiles])
    },
    [uploadQueue.length]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 20,
    disabled: uploadQueue.length >= 20,
  })

  const removeFromQueue = (fileId: string) => {
    setUploadQueue(prev => prev.filter(f => f.id !== fileId))
  }

  const updateDocumentType = (fileId: string, docType: DocumentType) => {
    setUploadQueue(prev =>
      prev.map(f => (f.id === fileId ? { ...f, documentType: docType } : f))
    )
  }

  const uploadAllFiles = async () => {
    const pendingFiles = uploadQueue.filter(f => f.status === 'pending')
    for (const uploadFile of pendingFiles) {
      await uploadMutation.mutateAsync({
        file: uploadFile.file,
        fileId: uploadFile.id,
        documentType: uploadFile.documentType,
      })
    }
  }

  const analyzeAllDocuments = async () => {
    // Analyze uploaded documents that aren't analyzed yet
    const uploadedIds = uploadQueue.filter(f => f.status === 'done' && f.documentId).map(f => f.documentId!)
    for (const docId of uploadedIds) {
      await analyzeMutation.mutateAsync(docId)
    }
    // Clear upload queue after analysis
    setUploadQueue([])
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 text-accent-primary animate-spin" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-status-danger mx-auto mb-4" />
        <p className="text-theme-text-muted">{t('errors.notFound')}</p>
        <Link to="/projects" className="mt-4 text-accent-primary hover:underline">
          {t('common.back')}
        </Link>
      </div>
    )
  }

  const currentRuleset = project.ruleset_id_hint ? getRuleset(project.ruleset_id_hint) : null

  // Show tax selector if no ruleset is set
  if (!project.ruleset_id_hint || showTaxSelector) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link to="/projects" className="p-2 hover:bg-theme-hover rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-theme-text-muted" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-theme-text-primary">{project.project.project_title}</h1>
          </div>
        </div>
        <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
          <TaxSystemSelector
            currentRuleset={project.ruleset_id_hint}
            onSelect={rulesetId => updateRulesetMutation.mutate(rulesetId)}
          />
          {showTaxSelector && project.ruleset_id_hint && (
            <div className="mt-4 pt-4 border-t border-theme-border-default">
              <button onClick={() => setShowTaxSelector(false)} className="text-theme-text-muted hover:text-theme-text-secondary">
                {t('common.cancel')}
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Processed documents (analyzed)
  const processedDocs = documents?.filter(d => d.status === 'ANALYZED') || []

  return (
    <div className="space-y-6">
      {/* Header with Project Data */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <Link to="/projects" className="p-2 hover:bg-theme-hover rounded-lg transition-colors">
              <ArrowLeft className="h-5 w-5 text-theme-text-muted" />
            </Link>
            {isEditing && editForm ? (
              <input
                type="text"
                value={editForm.project.project_title}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, project_title: e.target.value }
                })}
                className="text-2xl font-bold text-theme-text-primary border-b-2 border-accent-primary focus:outline-none bg-transparent"
              />
            ) : (
              <h1 className="text-2xl font-bold text-theme-text-primary">{project.project.project_title}</h1>
            )}
          </div>
          {/* Edit/Save Buttons */}
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1.5 text-theme-text-secondary hover:bg-theme-hover rounded-lg transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={saveEditing}
                  disabled={updateProjectMutation.isPending}
                  className="flex items-center gap-2 px-3 py-1.5 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover disabled:opacity-50"
                >
                  {updateProjectMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {t('common.save')}
                </button>
              </>
            ) : (
              <button
                onClick={startEditing}
                className="flex items-center gap-2 px-3 py-1.5 text-theme-text-secondary hover:bg-theme-hover rounded-lg transition-colors"
              >
                <Pencil className="h-4 w-4" />
                {t('common.edit')}
              </button>
            )}
          </div>
        </div>

        {/* Project Details Grid - Edit Mode */}
        {isEditing && editForm ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            {/* Beneficiary Name */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.beneficiaryName')}</label>
              <input
                type="text"
                value={editForm.beneficiary.name}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, name: e.target.value }
                })}
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* Street */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.street')}</label>
              <input
                type="text"
                value={editForm.beneficiary.street}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, street: e.target.value }
                })}
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* ZIP + City */}
            <div className="flex gap-2">
              <div className="w-1/3">
                <label className="block text-theme-text-muted mb-1">{t('projectDetail.zip')}</label>
                <input
                  type="text"
                  value={editForm.beneficiary.zip}
                  onChange={e => setEditForm({
                    ...editForm,
                    beneficiary: { ...editForm.beneficiary, zip: e.target.value }
                  })}
                  className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                />
              </div>
              <div className="w-2/3">
                <label className="block text-theme-text-muted mb-1">{t('projectDetail.city')}</label>
                <input
                  type="text"
                  value={editForm.beneficiary.city}
                  onChange={e => setEditForm({
                    ...editForm,
                    beneficiary: { ...editForm.beneficiary, city: e.target.value }
                  })}
                  className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                />
              </div>
            </div>

            {/* VAT ID */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.vatId')}</label>
              <input
                type="text"
                value={editForm.beneficiary.vat_id}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, vat_id: e.target.value }
                })}
                placeholder="DE123456789"
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* Tax Number */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.taxNumber')}</label>
              <input
                type="text"
                value={editForm.beneficiary.tax_number}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, tax_number: e.target.value }
                })}
                placeholder="123/456/78901"
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* File Reference */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.fileReference')}</label>
              <input
                type="text"
                value={editForm.project.file_reference}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, file_reference: e.target.value }
                })}
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* Execution Location */}
            <div>
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.executionLocation')}</label>
              <input
                type="text"
                value={editForm.project.implementation_location}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, implementation_location: e.target.value }
                })}
                placeholder="z.B. Berlin, Musterstraße 1"
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>

            {/* Execution Period */}
            <div className="md:col-span-2">
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.executionPeriod', 'Durchführungszeitraum')}</label>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={editForm.project.period_start}
                  onChange={e => setEditForm({
                    ...editForm,
                    project: { ...editForm.project, period_start: e.target.value }
                  })}
                  className="flex-1 px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                />
                <span className="text-theme-text-muted">{t('projectDetail.periodTo', 'bis')}</span>
                <input
                  type="date"
                  value={editForm.project.period_end}
                  onChange={e => setEditForm({
                    ...editForm,
                    project: { ...editForm.project, period_end: e.target.value }
                  })}
                  className="flex-1 px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                />
              </div>
            </div>

            {/* Project Description */}
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-theme-text-muted mb-1">{t('projectDetail.projectDescription')}</label>
              <textarea
                value={editForm.project.project_description}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, project_description: e.target.value }
                })}
                rows={3}
                className="w-full px-2 py-1 border border-theme-border-default rounded bg-theme-input text-theme-text-primary focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
              />
            </div>
          </div>
        ) : (
          /* Project Details Grid - View Mode */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3 text-sm">
            {/* Beneficiary Name */}
            <div>
              <span className="text-theme-text-muted">{t('projectDetail.beneficiaryName')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">{project.beneficiary.name}</span>
            </div>

            {/* Address */}
            <div className="md:col-span-2">
              <span className="text-theme-text-muted">{t('projectDetail.address')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">
                {project.beneficiary.street}, {project.beneficiary.zip} {project.beneficiary.city}
              </span>
            </div>

            {/* VAT ID */}
            <div>
              <span className="text-theme-text-muted">{t('projectDetail.vatId')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">{project.beneficiary.vat_id || '-'}</span>
            </div>

            {/* Tax Number */}
            <div>
              <span className="text-theme-text-muted">{t('projectDetail.taxNumber')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">{project.beneficiary.tax_number || '-'}</span>
            </div>

            {/* File Reference (Aktenzeichen) */}
            <div>
              <span className="text-theme-text-muted">{t('projectDetail.fileReference')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">{project.project.file_reference || '-'}</span>
            </div>

            {/* Execution Location (Durchführungsort) */}
            <div className="md:col-span-2">
              <span className="text-theme-text-muted">{t('projectDetail.executionLocation')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">
                {project.project.implementation?.location_name || '-'}
              </span>
            </div>

            {/* Execution Period (Durchführungszeitraum) */}
            <div className="md:col-span-2">
              <span className="text-theme-text-muted">{t('projectDetail.executionPeriod', 'Durchführungszeitraum')}:</span>
              <span className="ml-2 font-medium text-theme-text-primary">
                {project.project.project_period?.start && project.project.project_period?.end
                  ? `${new Date(project.project.project_period.start).toLocaleDateString('de-DE')} ${t('projectDetail.periodTo', 'bis')} ${new Date(project.project.project_period.end).toLocaleDateString('de-DE')}`
                  : '-'}
              </span>
            </div>

            {/* Project Description */}
            <div className="md:col-span-3">
              <span className="text-theme-text-muted">{t('projectDetail.projectDescription')}:</span>
              <p className="mt-1 text-theme-text-secondary">{project.project.project_description || '-'}</p>
            </div>

            {/* Project Period */}
            {project.project.project_period && (
              <div>
                <span className="text-theme-text-muted">{t('projectDetail.projectPeriod')}:</span>
                <span className="ml-2 font-medium text-theme-text-primary">
                  {project.project.project_period.start && new Date(project.project.project_period.start).toLocaleDateString('de-DE')}
                  {project.project.project_period.end && ` - ${new Date(project.project.project_period.end).toLocaleDateString('de-DE')}`}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Ruleset Badge */}
        <div className="mt-4 pt-4 border-t border-theme-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{currentRuleset?.flag}</span>
            <span className="font-medium text-theme-text-primary">{lang === 'de' ? currentRuleset?.title_de : currentRuleset?.title_en}</span>
          </div>
          <button
            onClick={() => setShowTaxSelector(true)}
            className="text-sm text-accent-primary hover:underline"
          >
            {t('taxSelector.changeSystem')}
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default">
        <div className="flex border-b border-theme-border-default">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-accent-primary text-accent-primary'
                : 'border-transparent text-theme-text-muted hover:text-theme-text-secondary hover:border-theme-border-default'
            }`}
          >
            <FolderOpen className="h-4 w-4" />
            {t('projectDetail.tabOverview', 'Übersicht')}
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'upload'
                ? 'border-accent-primary text-accent-primary'
                : 'border-transparent text-theme-text-muted hover:text-theme-text-secondary hover:border-theme-border-default'
            }`}
          >
            <Search className="h-4 w-4" />
            {t('projectDetail.tabAnalyze', 'Analysieren')}
            {uploadQueue.length > 0 && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-accent-primary/10 text-accent-primary rounded-full">
                {uploadQueue.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'documents'
                ? 'border-accent-primary text-accent-primary'
                : 'border-transparent text-theme-text-muted hover:text-theme-text-secondary hover:border-theme-border-default'
            }`}
          >
            <List className="h-4 w-4" />
            {t('projectDetail.tabDocuments', 'Belege & Feedback')}
            {processedDocs.length > 0 && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-theme-hover text-theme-text-secondary rounded-full">
                {processedDocs.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('solutions')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'solutions'
                ? 'border-accent-primary text-accent-primary'
                : 'border-transparent text-theme-text-muted hover:text-theme-text-secondary hover:border-theme-border-default'
            }`}
          >
            <FileJson className="h-4 w-4" />
            {t('projectDetail.tabSolutions', 'Lösungsdateien')}
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Belegliste */}
          <div className="lg:col-span-2 space-y-4">
            {/* Collapsible Features */}
            <div className="bg-theme-card rounded-lg border border-theme-border-default">
              <button
                onClick={() => setShowFeatures(!showFeatures)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-theme-hover"
              >
                <span className="font-medium text-theme-text-primary">{t('projectDetail.showFeatures')}</span>
                {showFeatures ? (
                  <ChevronDown className="h-5 w-5 text-theme-text-muted" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-theme-text-muted" />
                )}
              </button>
              {showFeatures && currentRuleset && (
                <div className="px-4 pb-4 border-t border-theme-border-subtle">
                  <div className="mt-3 space-y-2 text-sm max-h-60 overflow-y-auto">
                    {currentRuleset.features.map(feature => (
                      <div key={feature.feature_id} className="flex items-center justify-between py-1">
                        <span className="text-theme-text-muted">
                          {lang === 'de' ? feature.name_de : feature.name_en}
                        </span>
                        <span
                          className={`px-2 py-0.5 text-xs rounded ${
                            feature.required_level === 'REQUIRED'
                              ? 'bg-status-danger-bg text-status-danger'
                              : feature.required_level === 'CONDITIONAL'
                              ? 'bg-status-warning-bg text-status-warning'
                              : 'bg-theme-hover text-theme-text-muted'
                          }`}
                        >
                          {t(`rulesets.requiredLevel.${feature.required_level}`, feature.required_level)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Collapsible Legal References */}
            {currentRuleset && currentRuleset.legal_references && currentRuleset.legal_references.length > 0 && (
              <div className="bg-theme-card rounded-lg border border-theme-border-default">
                <button
                  onClick={() => setShowLegalRefs(!showLegalRefs)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-theme-hover"
                >
                  <span className="font-medium text-theme-text-primary">{t('projectDetail.showLegalReferences', 'Rechtsgrundlagen anzeigen')}</span>
                  {showLegalRefs ? (
                    <ChevronDown className="h-5 w-5 text-theme-text-muted" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-theme-text-muted" />
                  )}
                </button>
                {showLegalRefs && (
                  <div className="px-4 pb-4 border-t border-theme-border-subtle">
                    <div className="mt-3 space-y-2 text-sm max-h-60 overflow-y-auto">
                      {currentRuleset.legal_references.map((ref, idx) => (
                        <div key={idx} className="flex items-start justify-between py-2 border-b border-theme-border-subtle last:border-0">
                          <div className="flex-1">
                            <span className="font-medium text-theme-text-primary">
                              {ref.law} {ref.section}
                            </span>
                            <p className="text-theme-text-muted mt-0.5">
                              {lang === 'de' ? ref.description_de : ref.description_en}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Collapsible Special Rules */}
            {currentRuleset && currentRuleset.small_amount_threshold && (
              <div className="bg-theme-card rounded-lg border border-theme-border-default">
                <button
                  onClick={() => setShowSpecialRules(!showSpecialRules)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-theme-hover"
                >
                  <span className="font-medium text-theme-text-primary">{t('projectDetail.showSpecialRules', 'Sonderregeln anzeigen')}</span>
                  {showSpecialRules ? (
                    <ChevronDown className="h-5 w-5 text-theme-text-muted" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-theme-text-muted" />
                  )}
                </button>
                {showSpecialRules && (
                  <div className="px-4 pb-4 border-t border-theme-border-subtle">
                    <div className="mt-3 space-y-3 text-sm">
                      {/* Kleinbetragsrechnung */}
                      <div className="p-3 bg-theme-hover rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-4 w-4 text-status-warning" />
                          <span className="font-medium text-theme-text-primary">
                            {t('projectDetail.smallAmountInvoice', 'Kleinbetragsrechnung')}
                          </span>
                        </div>
                        <p className="text-theme-text-muted mb-2">
                          {t('projectDetail.smallAmountThreshold', 'Schwellenwert')}: <span className="font-medium">{currentRuleset.small_amount_threshold} {currentRuleset.small_amount_currency || 'EUR'}</span>
                        </p>
                        <p className="text-theme-text-muted text-xs">
                          {t('projectDetail.smallAmountDescription', 'Bei Rechnungen unter diesem Betrag gelten vereinfachte Anforderungen an Pflichtangaben.')}
                        </p>
                      </div>

                      {/* Reduced fields info */}
                      <div className="text-theme-text-muted">
                        <p className="font-medium text-theme-text-secondary mb-1">
                          {t('projectDetail.reducedFieldsLabel', 'Reduzierte Pflichtangaben bei Kleinbetragsrechnungen:')}
                        </p>
                        <ul className="list-disc list-inside space-y-0.5">
                          {currentRuleset.features
                            .filter(f => f.applies_to?.small_amount_invoice && f.required_level === 'REQUIRED')
                            .map(f => (
                              <li key={f.feature_id}>{lang === 'de' ? f.name_de : f.name_en}</li>
                            ))
                          }
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Collapsible Checkers (Prüfmodule) */}
            {checkerSettings && (
              <div className="bg-theme-card rounded-lg border border-theme-border-default">
                <button
                  onClick={() => setShowCheckers(!showCheckers)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-theme-hover"
                >
                  <span className="font-medium text-theme-text-primary">{t('projectDetail.showCheckers', 'Prüfmodule anzeigen')}</span>
                  {showCheckers ? (
                    <ChevronDown className="h-5 w-5 text-theme-text-muted" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-theme-text-muted" />
                  )}
                </button>
                {showCheckers && (
                  <div className="px-4 pb-4 border-t border-theme-border-subtle">
                    <div className="mt-3 space-y-4 text-sm">
                      {/* Projektzeitraum-Prüfung */}
                      <div className="p-3 bg-theme-hover rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock className="h-4 w-4 text-accent-primary" />
                          <span className="font-medium text-theme-text-primary">
                            {t('projectDetail.checkerPeriod', 'Projektzeitraum-Prüfung')}
                          </span>
                          <span className="px-2 py-0.5 text-xs bg-status-success-bg text-status-success rounded">
                            {t('projectDetail.checkerActive', 'Aktiv')}
                          </span>
                        </div>
                        <p className="text-theme-text-muted text-xs">
                          {t('projectDetail.checkerPeriodDesc', 'Prüft ob das Leistungsdatum innerhalb des Projektzeitraums liegt.')}
                        </p>
                      </div>

                      {/* Risk Checker */}
                      <div className="p-3 bg-theme-hover rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-4 w-4 text-status-warning" />
                          <span className="font-medium text-theme-text-primary">
                            {t('projectDetail.checkerRisk', 'Risiko-Prüfung')}
                          </span>
                          <span className={`px-2 py-0.5 text-xs rounded ${checkerSettings.risk_checker.enabled ? 'bg-status-success-bg text-status-success' : 'bg-theme-hover text-theme-text-muted'}`}>
                            {checkerSettings.risk_checker.enabled ? t('projectDetail.checkerActive', 'Aktiv') : t('projectDetail.checkerInactive', 'Inaktiv')}
                          </span>
                        </div>
                        {checkerSettings.risk_checker.enabled && (
                          <ul className="text-theme-text-muted text-xs space-y-0.5 ml-6">
                            {checkerSettings.risk_checker.check_self_invoice && <li>• {t('projectDetail.riskSelfInvoice', 'Selbstrechnung')}</li>}
                            {checkerSettings.risk_checker.check_duplicate_invoice && <li>• {t('projectDetail.riskDuplicate', 'Doppelte Rechnungen')}</li>}
                            {checkerSettings.risk_checker.check_round_amounts && <li>• {t('projectDetail.riskRoundAmounts', 'Runde Beträge')} (ab {checkerSettings.risk_checker.round_amount_threshold} EUR)</li>}
                            {checkerSettings.risk_checker.check_weekend_dates && <li>• {t('projectDetail.riskWeekend', 'Wochenend-Daten')}</li>}
                          </ul>
                        )}
                      </div>

                      {/* Semantic Checker */}
                      <div className="p-3 bg-theme-hover rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="h-4 w-4 text-accent-primary" />
                          <span className="font-medium text-theme-text-primary">
                            {t('projectDetail.checkerSemantic', 'Semantik-Prüfung')}
                          </span>
                          <span className={`px-2 py-0.5 text-xs rounded ${checkerSettings.semantic_checker.enabled ? 'bg-status-success-bg text-status-success' : 'bg-theme-hover text-theme-text-muted'}`}>
                            {checkerSettings.semantic_checker.enabled ? t('projectDetail.checkerActive', 'Aktiv') : t('projectDetail.checkerInactive', 'Inaktiv')}
                          </span>
                        </div>
                        {checkerSettings.semantic_checker.enabled && (
                          <ul className="text-theme-text-muted text-xs space-y-0.5 ml-6">
                            {checkerSettings.semantic_checker.check_project_relevance && <li>• {t('projectDetail.semanticRelevance', 'Projektrelevanz')} (min. {Math.round(checkerSettings.semantic_checker.min_relevance_score * 100)}%)</li>}
                            {checkerSettings.semantic_checker.check_description_quality && <li>• {t('projectDetail.semanticDescription', 'Beschreibungsqualität')}</li>}
                            {checkerSettings.semantic_checker.use_rag_context && <li>• {t('projectDetail.semanticRag', 'RAG-Kontext verwenden')}</li>}
                          </ul>
                        )}
                      </div>

                      {/* Economic Checker */}
                      <div className="p-3 bg-theme-hover rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Settings className="h-4 w-4 text-status-success" />
                          <span className="font-medium text-theme-text-primary">
                            {t('projectDetail.checkerEconomic', 'Wirtschaftlichkeits-Prüfung')}
                          </span>
                          <span className={`px-2 py-0.5 text-xs rounded ${checkerSettings.economic_checker.enabled ? 'bg-status-success-bg text-status-success' : 'bg-theme-hover text-theme-text-muted'}`}>
                            {checkerSettings.economic_checker.enabled ? t('projectDetail.checkerActive', 'Aktiv') : t('projectDetail.checkerInactive', 'Inaktiv')}
                          </span>
                        </div>
                        {checkerSettings.economic_checker.enabled && (
                          <ul className="text-theme-text-muted text-xs space-y-0.5 ml-6">
                            {checkerSettings.economic_checker.check_budget_limits && <li>• {t('projectDetail.economicBudget', 'Budgetgrenzen')}</li>}
                            {checkerSettings.economic_checker.check_unit_prices && <li>• {t('projectDetail.economicPrices', 'Einzelpreise')}</li>}
                            {checkerSettings.economic_checker.check_funding_rate && <li>• {t('projectDetail.economicFunding', 'Förderquote')} (max. {checkerSettings.economic_checker.max_deviation_percent}% Abweichung)</li>}
                          </ul>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Belegliste (Processed Documents) */}
            <div className="bg-theme-card rounded-lg border border-theme-border-default">
              <div className="px-4 py-3 border-b border-theme-border-default">
                <h3 className="font-semibold text-theme-text-primary">{t('projectDetail.documentList')}</h3>
              </div>

              {processedDocs.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-theme-hover">
                      <tr>
                        <th className="px-4 py-2 text-left text-theme-text-muted font-medium">Nr.</th>
                        <th className="px-4 py-2 text-left text-theme-text-muted font-medium">
                          {t('projectDetail.supplier')}
                        </th>
                        <th className="px-4 py-2 text-left text-theme-text-muted font-medium">
                          {t('projectDetail.date')}
                        </th>
                        <th className="px-4 py-2 text-right text-theme-text-muted font-medium">
                          {t('projectDetail.amount')}
                        </th>
                        <th className="px-4 py-2 text-center text-theme-text-muted font-medium">Status</th>
                        <th className="px-4 py-2"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-theme-border-subtle">
                      {processedDocs.map((doc, index) => (
                        <tr key={doc.id} className="hover:bg-theme-hover">
                          <td className="px-4 py-3 text-theme-text-primary">{index + 1}</td>
                          <td className="px-4 py-3 text-theme-text-primary">
                            {doc.extracted_data?.supplier_name_address?.value?.split('\n')[0] || '-'}
                          </td>
                          <td className="px-4 py-3 text-theme-text-muted">
                            {doc.extracted_data?.invoice_date?.value || '-'}
                          </td>
                          <td className="px-4 py-3 text-right font-medium text-theme-text-primary">
                            {doc.extracted_data?.gross_amount?.value
                              ? `${parseFloat(doc.extracted_data.gross_amount.value).toLocaleString('de-DE', { minimumFractionDigits: 2 })} €`
                              : '-'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {doc.analysis_result?.overall_assessment === 'ok' ? (
                              <CheckCircle className="h-5 w-5 text-status-success mx-auto" />
                            ) : doc.analysis_result?.overall_assessment === 'rejected' ? (
                              <AlertCircle className="h-5 w-5 text-status-danger mx-auto" />
                            ) : (
                              <Clock className="h-5 w-5 text-status-warning mx-auto" />
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => {
                                setSelectedDocument(doc.id)
                                setActiveTab('documents')
                              }}
                              className="text-accent-primary hover:text-accent-primary-hover"
                            >
                              <Eye className="h-5 w-5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="px-4 py-8 text-center text-theme-text-muted">
                  <FileText className="h-10 w-10 text-theme-text-disabled mx-auto mb-2" />
                  {t('projectDetail.noProcessedDocuments')}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Quick Stats */}
          <div className="space-y-4">
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
              <h3 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.quickStats', 'Schnellübersicht')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-theme-text-muted">{t('projectDetail.totalDocuments', 'Belege gesamt')}</span>
                  <span className="font-medium">{documents?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-theme-text-muted">{t('projectDetail.analyzedDocuments', 'Analysiert')}</span>
                  <span className="font-medium text-status-success">{processedDocs.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-theme-text-muted">{t('projectDetail.acceptedDocuments', 'Akzeptiert')}</span>
                  <span className="font-medium text-accent-primary">
                    {documents?.filter(d => d.status === 'ACCEPTED').length || 0}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setActiveTab('upload')}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover"
            >
              <Search className="h-5 w-5" />
              {t('projectDetail.analyzeDocuments', 'Belege analysieren')}
            </button>
          </div>
        </div>
      )}

      {/* Documents & Feedback Tab */}
      {activeTab === 'documents' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Document List */}
          <div className="lg:col-span-1 bg-theme-card rounded-lg border border-theme-border-default">
            <div className="px-4 py-3 border-b border-theme-border-default">
              <h3 className="font-semibold text-theme-text-primary">{t('projectDetail.documentList')}</h3>
            </div>
            <div className="divide-y divide-theme-border-subtle max-h-[600px] overflow-y-auto">
              {processedDocs.length > 0 ? (
                processedDocs.map((doc, index) => {
                  const isSelected = selectedDocument === doc.id
                  const isAccepted = doc.status === 'ACCEPTED'
                  return (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDocument(doc.id)}
                      className={`w-full text-left px-4 py-3 hover:bg-theme-hover transition-colors ${
                        isSelected ? 'bg-theme-selected border-l-4 border-accent-primary' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-theme-text-primary truncate">
                          {index + 1}. {doc.extracted_data?.supplier_name_address?.value?.split('\n')[0] || doc.filename}
                        </span>
                        <div className="flex items-center gap-1">
                          {isAccepted && <Lock className="h-4 w-4 text-status-success" />}
                          {doc.analysis_result?.overall_assessment === 'ok' ? (
                            <CheckCircle className="h-4 w-4 text-status-success" />
                          ) : doc.analysis_result?.overall_assessment === 'rejected' ? (
                            <AlertCircle className="h-4 w-4 text-status-danger" />
                          ) : (
                            <Clock className="h-4 w-4 text-status-warning" />
                          )}
                        </div>
                      </div>
                      <div className="text-sm text-theme-text-muted mt-1">
                        {doc.extracted_data?.invoice_date?.value || '-'} • {doc.extracted_data?.gross_amount?.value
                          ? `${parseFloat(doc.extracted_data.gross_amount.value).toLocaleString('de-DE', { minimumFractionDigits: 2 })} €`
                          : '-'}
                      </div>
                    </button>
                  )
                })
              ) : (
                <div className="px-4 py-8 text-center text-theme-text-muted">
                  <FileText className="h-8 w-8 text-theme-text-disabled mx-auto mb-2" />
                  {t('projectDetail.noProcessedDocuments')}
                </div>
              )}
            </div>
          </div>

          {/* Right: Document Details & Feedback */}
          <div className="lg:col-span-2 space-y-4">
            {selectedDocument ? (
              (() => {
                const doc = documents?.find(d => d.id === selectedDocument)
                if (!doc) return null
                const isAccepted = doc.status === 'ACCEPTED'
                const hasFeedback = selectedDocFeedback && selectedDocFeedback.length > 0

                return (
                  <>
                    {/* Document Header */}
                    <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-theme-text-primary">{doc.filename}</h3>
                        <div className="flex items-center gap-2">
                          {isAccepted ? (
                            <span className="flex items-center gap-1 px-2 py-1 text-xs bg-status-success-bg text-status-success rounded">
                              <Lock className="h-3 w-3" />
                              {t('projectDetail.accepted', 'Akzeptiert')}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 px-2 py-1 text-xs bg-status-warning-bg text-status-warning rounded">
                              <Clock className="h-3 w-3" />
                              {t('projectDetail.pendingReview', 'Prüfung ausstehend')}
                            </span>
                          )}
                          <Link
                            to={`/documents/${doc.id}`}
                            className="text-accent-primary hover:text-accent-primary-hover p-1"
                            title={t('projectDetail.viewDetails', 'Details anzeigen')}
                          >
                            <FileText className="h-5 w-5" />
                          </Link>
                        </div>
                      </div>

                      {/* Quick Info */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-theme-text-muted">{t('projectDetail.date')}</span>
                          <p className="font-medium">{doc.extracted_data?.invoice_date?.value || '-'}</p>
                        </div>
                        <div>
                          <span className="text-theme-text-muted">{t('projectDetail.amount')}</span>
                          <p className="font-medium">
                            {doc.extracted_data?.gross_amount?.value
                              ? `${parseFloat(doc.extracted_data.gross_amount.value).toLocaleString('de-DE', { minimumFractionDigits: 2 })} €`
                              : '-'}
                          </p>
                        </div>
                        <div>
                          <span className="text-theme-text-muted">{t('projectDetail.confidence', 'Konfidenz')}</span>
                          <p className="font-medium">
                            {doc.analysis_result?.confidence
                              ? `${Math.round(doc.analysis_result.confidence * 100)}%`
                              : '-'}
                          </p>
                        </div>
                        <div>
                          <span className="text-theme-text-muted">Status</span>
                          <p className={`font-medium ${
                            doc.analysis_result?.overall_assessment === 'ok' ? 'text-status-success' :
                            doc.analysis_result?.overall_assessment === 'rejected' ? 'text-status-danger' :
                            'text-status-warning'
                          }`}>
                            {doc.analysis_result?.overall_assessment === 'ok' ? t('projectDetail.ok', 'OK') :
                             doc.analysis_result?.overall_assessment === 'rejected' ? t('projectDetail.rejected', 'Abgelehnt') :
                             t('projectDetail.review', 'Prüfen')}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Extracted Features */}
                    <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
                      <h4 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.extractedFeatures', 'Erkannte Merkmale')}</h4>
                      {doc.extracted_data && Object.keys(doc.extracted_data).length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                          {Object.entries(doc.extracted_data).map(([key, val]) => {
                            const featureName = currentRuleset?.features.find(f => f.feature_id === key)
                            const displayName = featureName
                              ? (lang === 'de' ? featureName.name_de : featureName.name_en)
                              : key.replace(/_/g, ' ')
                            return (
                              <div key={key} className="flex justify-between items-start p-2 bg-theme-hover rounded">
                                <span className="text-theme-text-muted capitalize">{displayName}</span>
                                <div className="text-right">
                                  <span className="font-medium text-theme-text-primary block">
                                    {val?.value || '-'}
                                  </span>
                                  {val?.confidence !== undefined && (
                                    <span className="text-xs text-theme-text-muted">
                                      {Math.round(val.confidence * 100)}%
                                    </span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      ) : (
                        <p className="text-theme-text-muted">{t('projectDetail.noExtractedData', 'Keine Daten extrahiert')}</p>
                      )}
                    </div>

                    {/* LLM Runs History */}
                    {selectedDocLlmRuns && selectedDocLlmRuns.length > 0 && (
                      <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
                        <h4 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.llmRuns', 'Erkennungsläufe')}</h4>
                        <div className="space-y-3">
                          {selectedDocLlmRuns.map((run, index) => (
                            <div key={run.id} className="p-3 bg-theme-hover rounded-lg">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-theme-text-primary">
                                    Run #{selectedDocLlmRuns.length - index}
                                  </span>
                                  <span className={`px-2 py-0.5 text-xs rounded ${
                                    run.status === 'COMPLETED' ? 'bg-status-success-bg text-status-success' :
                                    run.status === 'FAILED' ? 'bg-status-danger-bg text-status-danger' :
                                    'bg-status-warning-bg text-status-warning'
                                  }`}>
                                    {run.status}
                                  </span>
                                </div>
                                <span className="text-xs text-theme-text-muted">
                                  {new Date(run.created_at).toLocaleString('de-DE')}
                                </span>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                                <div>
                                  <span className="text-theme-text-muted">{t('projectDetail.provider', 'Provider')}</span>
                                  <p className="font-medium">{run.provider}</p>
                                </div>
                                <div>
                                  <span className="text-theme-text-muted">{t('projectDetail.model', 'Modell')}</span>
                                  <p className="font-medium truncate" title={run.model_name}>{run.model_name}</p>
                                </div>
                                <div>
                                  <span className="text-theme-text-muted">{t('projectDetail.duration', 'Dauer')}</span>
                                  <p className="font-medium">
                                    {run.stats.duration_ms
                                      ? `${(run.stats.duration_ms / 1000).toFixed(2)}s`
                                      : '-'}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-theme-text-muted">{t('projectDetail.tokens', 'Tokens')}</span>
                                  <p className="font-medium">
                                    {run.stats.input_tokens && run.stats.output_tokens
                                      ? `${run.stats.input_tokens} → ${run.stats.output_tokens}`
                                      : '-'}
                                  </p>
                                </div>
                              </div>
                              {run.error_message && (
                                <div className="mt-2 p-2 bg-status-danger-bg rounded text-sm text-status-danger">
                                  {run.error_message}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Feedback History */}
                    {hasFeedback && (
                      <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
                        <h4 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.feedbackHistory', 'Feedback-Verlauf')}</h4>
                        <div className="space-y-2">
                          {selectedDocFeedback.map((fb) => (
                            <div key={fb.feedback_id} className="flex items-center justify-between p-2 bg-theme-hover rounded text-sm">
                              <div className="flex items-center gap-2">
                                {fb.rating === 'CORRECT' ? (
                                  <ThumbsUp className="h-4 w-4 text-status-success" />
                                ) : (
                                  <ThumbsDown className="h-4 w-4 text-status-danger" />
                                )}
                                <span>{fb.rating === 'CORRECT' ? t('feedback.correct', 'Korrekt') : t('feedback.incorrect', 'Fehlerhaft')}</span>
                                {fb.override_count > 0 && (
                                  <span className="text-xs text-theme-text-muted">({fb.override_count} {t('feedback.corrections', 'Korrekturen')})</span>
                                )}
                              </div>
                              <span className="text-theme-text-muted text-xs">
                                {new Date(fb.created_at).toLocaleString('de-DE')}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Feedback Actions - only if not accepted */}
                    {!isAccepted && (
                      <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
                        <h4 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.submitFeedback', 'Feedback abgeben')}</h4>

                        {/* Comment */}
                        <div className="mb-4">
                          <label className="block text-sm text-theme-text-muted mb-1">{t('projectDetail.comment', 'Kommentar (optional)')}</label>
                          <textarea
                            value={feedbackComment}
                            onChange={(e) => setFeedbackComment(e.target.value)}
                            className="w-full px-3 py-2 border border-theme-border-default rounded-lg text-sm focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                            rows={2}
                            placeholder={t('projectDetail.commentPlaceholder', 'Anmerkungen zur Prüfung...')}
                          />
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap gap-2">
                          {/* Finalize first if not finalized */}
                          {!selectedDocFinal && (
                            <button
                              onClick={() => finalizeMutation.mutate(doc.id)}
                              disabled={finalizeMutation.isPending}
                              className="flex items-center gap-2 px-4 py-2 bg-theme-hover text-theme-text-primary rounded-lg hover:bg-theme-card border border-theme-border-default disabled:opacity-50"
                            >
                              {finalizeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                              <CheckCircle className="h-4 w-4" />
                              {t('projectDetail.finalize', 'Finalisieren')}
                            </button>
                          )}

                          {/* Feedback buttons */}
                          <button
                            onClick={() => feedbackMutation.mutate({
                              documentId: doc.id,
                              rating: 'CORRECT',
                              acceptResult: false
                            })}
                            disabled={feedbackMutation.isPending}
                            className="flex items-center gap-2 px-4 py-2 border border-status-success-border text-status-success rounded-lg hover:bg-status-success-bg disabled:opacity-50"
                          >
                            {feedbackMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                            <ThumbsUp className="h-4 w-4" />
                            {t('feedback.correct', 'Korrekt')}
                          </button>

                          <button
                            onClick={() => feedbackMutation.mutate({
                              documentId: doc.id,
                              rating: 'INCORRECT',
                              acceptResult: false
                            })}
                            disabled={feedbackMutation.isPending}
                            className="flex items-center gap-2 px-4 py-2 border border-status-danger-border text-status-danger rounded-lg hover:bg-status-danger-bg disabled:opacity-50"
                          >
                            {feedbackMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                            <ThumbsDown className="h-4 w-4" />
                            {t('feedback.incorrect', 'Fehlerhaft')}
                          </button>

                          <button
                            onClick={() => feedbackMutation.mutate({
                              documentId: doc.id,
                              rating: 'CORRECT',
                              acceptResult: true
                            })}
                            disabled={feedbackMutation.isPending}
                            className="flex items-center gap-2 px-4 py-2 bg-status-success text-white rounded-lg hover:bg-status-success/90 disabled:opacity-50"
                          >
                            {feedbackMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                            <Lock className="h-4 w-4" />
                            {t('projectDetail.acceptAndFinalize', 'Akzeptieren & Abschließen')}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )
              })()
            ) : (
              <div className="bg-theme-card rounded-lg border border-theme-border-default p-8 text-center text-theme-text-muted">
                <FileText className="h-12 w-12 text-theme-text-disabled mx-auto mb-3" />
                <p>{t('projectDetail.selectDocument', 'Wählen Sie einen Beleg aus der Liste')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Upload queue */}
          <div className="lg:col-span-2 space-y-4">
            {/* Upload Area */}
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
              <h3 className="font-semibold text-theme-text-primary mb-4">{t('projectDetail.uploadedFiles')}</h3>

              {/* File List */}
              {uploadQueue.length > 0 && (
                <div className="mb-4 space-y-2 max-h-80 overflow-y-auto">
                  {uploadQueue.map((file, index) => (
                    <div
                      key={file.id}
                      className="p-3 bg-theme-hover rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="text-theme-text-muted w-6">{index + 1}.</span>
                          <span className="truncate font-medium">{file.file.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {file.status === 'uploading' && <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />}
                          {file.status === 'done' && <CheckCircle className="h-4 w-4 text-status-success" />}
                          {file.status === 'error' && <AlertCircle className="h-4 w-4 text-status-danger" />}
                          {file.status === 'pending' && (
                            <button onClick={() => removeFromQueue(file.id)} className="text-theme-text-muted hover:text-status-danger">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </div>
                      {/* Document Type Selector */}
                      {file.status === 'pending' && (
                        <div className="mt-2 pl-8">
                          <select
                            value={file.documentType}
                            onChange={e => updateDocumentType(file.id, e.target.value as DocumentType)}
                            className="w-full px-2 py-1 text-sm border border-theme-border-default rounded focus:ring-1 focus:ring-accent-primary focus:border-accent-primary"
                          >
                            <option value="INVOICE">{t('documentTypes.invoice')}</option>
                            <option value="BANK_STATEMENT">{t('documentTypes.bankStatement')}</option>
                            <option value="PROCUREMENT">{t('documentTypes.procurement')}</option>
                            <option value="CONTRACT">{t('documentTypes.contract')}</option>
                            <option value="OTHER">{t('documentTypes.other')}</option>
                          </select>
                          {project.ruleset_id_hint && !isDocumentTypeSupported(project.ruleset_id_hint, file.documentType) && (
                            <div className="mt-1 flex items-center gap-1 text-xs text-amber-600">
                              <AlertTriangle className="h-3 w-3" />
                              <span>{t('projectDetail.documentTypeNotSupported')}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive ? 'border-accent-primary bg-theme-selected' : 'border-theme-border-default hover:border-accent-primary'
                } ${uploadQueue.length >= 20 ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <input {...getInputProps()} />
                <Upload className="h-10 w-10 text-theme-text-muted mx-auto mb-3" />
                <p className="text-theme-text-muted">{t('projectDetail.dropzoneText')}</p>
                <p className="text-sm text-theme-text-muted mt-2">
                  {t('projectDetail.maxFiles', { count: 20 - uploadQueue.length })}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column - Actions */}
          <div className="space-y-4">
            {/* Upload Actions */}
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
              <h3 className="font-semibold text-theme-text-primary mb-4">{t('projectDetail.actions', 'Aktionen')}</h3>

              <div className="space-y-3">
                {/* Upload Button */}
                {uploadQueue.some(f => f.status === 'pending') && (
                  <button
                    onClick={uploadAllFiles}
                    disabled={uploadMutation.isPending}
                    className="w-full px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {uploadMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                    <Upload className="h-4 w-4" />
                    {t('documents.uploadDocument')}
                  </button>
                )}

                {/* Analyze Button */}
                <button
                  onClick={analyzeAllDocuments}
                  disabled={analyzeMutation.isPending || !uploadQueue.some(f => f.status === 'done')}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-status-success text-white rounded-lg hover:bg-status-success/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {analyzeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  <Search className="h-4 w-4" />
                  {t('projectDetail.recognizeDocuments')}
                </button>

                {/* Settings Button */}
                <button
                  onClick={() => setShowSettings(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-theme-border-default text-theme-text-secondary rounded-lg hover:bg-theme-hover"
                >
                  <Settings className="h-4 w-4" />
                  {t('projectDetail.analysisSettings')}
                </button>
              </div>
            </div>

            {/* Status Info */}
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
              <h3 className="font-semibold text-theme-text-primary mb-3">{t('projectDetail.uploadStatus', 'Upload-Status')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-theme-text-muted">{t('projectDetail.pending', 'Ausstehend')}</span>
                  <span className="font-medium">{uploadQueue.filter(f => f.status === 'pending').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-text-muted">{t('projectDetail.uploaded', 'Hochgeladen')}</span>
                  <span className="font-medium text-status-success">{uploadQueue.filter(f => f.status === 'done').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-theme-text-muted">{t('projectDetail.errors', 'Fehler')}</span>
                  <span className="font-medium text-status-danger">{uploadQueue.filter(f => f.status === 'error').length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Solutions Tab */}
      {activeTab === 'solutions' && id && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Solution File Upload */}
          <div className="lg:col-span-2">
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
              <h3 className="font-semibold text-theme-text-primary mb-4">
                {t('projectDetail.solutionFiles', 'Lösungsdateien')}
              </h3>
              <p className="text-sm text-theme-text-muted mb-4">
                {t(
                  'projectDetail.solutionFilesDescription',
                  'Laden Sie eine Lösungsdatei hoch, um erwartete Ergebnisse mit Dokumenten abzugleichen. Unterstützte Formate: JSON, JSONL, CSV.'
                )}
              </p>
              <SolutionFileUpload
                projectId={id}
                onApplied={() => {
                  refetchDocuments()
                  queryClient.invalidateQueries({ queryKey: ['documents', id] })
                }}
              />
            </div>
          </div>

          {/* Right Column - Instructions */}
          <div className="space-y-4">
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
              <h4 className="font-semibold text-theme-text-primary mb-3">
                {t('projectDetail.solutionFileFormat', 'Dateiformat')}
              </h4>
              <div className="space-y-3 text-sm text-theme-text-muted">
                <div>
                  <p className="font-medium text-theme-text-primary">JSON</p>
                  <p>Array von Objekten mit Feldern wie is_valid, errors, filename</p>
                </div>
                <div>
                  <p className="font-medium text-theme-text-primary">JSONL</p>
                  <p>Ein JSON-Objekt pro Zeile</p>
                </div>
                <div>
                  <p className="font-medium text-theme-text-primary">CSV</p>
                  <p>Spalten: position, filename, is_valid, errors (JSON-String)</p>
                </div>
              </div>
            </div>

            <div className="bg-theme-card rounded-lg border border-theme-border-default p-4">
              <h4 className="font-semibold text-theme-text-primary mb-3">
                {t('projectDetail.matchingStrategies', 'Matching-Strategien')}
              </h4>
              <div className="space-y-2 text-sm text-theme-text-muted">
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-status-success mt-0.5" />
                  <p>Dateiname (exakt oder ähnlich)</p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-status-success mt-0.5" />
                  <p>Dateiname + Position kombiniert</p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-status-success mt-0.5" />
                  <p>Nur Position (für sortierte Listen)</p>
                </div>
              </div>
            </div>

            <div className="bg-status-info-bg border border-status-info-border rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-status-info mt-0.5" />
                <div>
                  <p className="font-medium text-status-info">
                    {t('projectDetail.solutionFileTip', 'Tipp')}
                  </p>
                  <p className="text-sm text-status-info mt-1">
                    {t(
                      'projectDetail.solutionFileTipText',
                      'Verwenden Sie die Vorschau-Funktion, um Zuordnungen vor dem Anwenden zu überprüfen.'
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setShowSettings(false)} />
            <div className="relative bg-theme-card rounded-xl shadow-xl w-full max-w-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-theme-text-primary">{t('projectDetail.analysisSettings')}</h3>
                <button onClick={() => setShowSettings(false)} className="text-theme-text-muted hover:text-theme-text-muted">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-theme-text-secondary">{t('projectDetail.useOcr')}</label>
                  <input
                    type="checkbox"
                    checked={settings.useOcr}
                    onChange={e => setSettings({ ...settings, useOcr: e.target.checked })}
                    className="rounded border-theme-border-default text-accent-primary focus:ring-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm text-theme-text-secondary mb-1">
                    {t('projectDetail.confidenceThreshold')}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={settings.confidenceThreshold}
                    onChange={e => setSettings({ ...settings, confidenceThreshold: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <span className="text-sm text-theme-text-muted">{Math.round(settings.confidenceThreshold * 100)}%</span>
                </div>

                <div>
                  <label className="block text-sm text-theme-text-secondary mb-1">{t('projectDetail.maxRuns')}</label>
                  <select
                    value={settings.maxRuns}
                    onChange={e => setSettings({ ...settings, maxRuns: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-theme-border-default rounded-lg"
                  >
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowSettings(false)}
                  className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover"
                >
                  {t('common.save')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
