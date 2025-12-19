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
} from 'lucide-react'
import { api } from '@/lib/api'
import { TaxSystemSelector } from '@/components/tax-selector'
import { RulesetId, getRuleset, isDocumentTypeSupported } from '@/lib/rulesets'
import { useTranslation } from 'react-i18next'

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
  analysis_result?: {
    overall_assessment?: string
    confidence?: number
  }
  extracted_data?: {
    supplier_name_address?: { value?: string }
    invoice_date?: { value?: string }
    gross_amount?: { value?: string }
  }
}

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
    implementation_city: string
  }
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const lang = i18n.language as 'de' | 'en'

  const [showTaxSelector, setShowTaxSelector] = useState(false)
  const [showFeatures, setShowFeatures] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<UploadedFile[]>([])
  const [settings, setSettings] = useState<AnalysisSettings>({
    useOcr: true,
    confidenceThreshold: 0.7,
    maxRuns: 1,
  })
  const [editForm, setEditForm] = useState<EditFormData | null>(null)

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
          implementation: data.project.implementation_location || data.project.implementation_city
            ? {
                location_name: data.project.implementation_location || undefined,
                city: data.project.implementation_city || undefined,
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
          implementation_city: project.project.implementation?.city || '',
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
        <Loader2 className="h-12 w-12 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-500">{t('errors.notFound')}</p>
        <Link to="/projects" className="mt-4 text-primary-600 hover:underline">
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
          <Link to="/projects" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.project.project_title}</h1>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <TaxSystemSelector
            currentRuleset={project.ruleset_id_hint}
            onSelect={rulesetId => updateRulesetMutation.mutate(rulesetId)}
          />
          {showTaxSelector && project.ruleset_id_hint && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button onClick={() => setShowTaxSelector(false)} className="text-gray-500 hover:text-gray-700">
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
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <Link to="/projects" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <ArrowLeft className="h-5 w-5 text-gray-500" />
            </Link>
            {isEditing && editForm ? (
              <input
                type="text"
                value={editForm.project.project_title}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, project_title: e.target.value }
                })}
                className="text-2xl font-bold text-gray-900 border-b-2 border-primary-500 focus:outline-none bg-transparent"
              />
            ) : (
              <h1 className="text-2xl font-bold text-gray-900">{project.project.project_title}</h1>
            )}
          </div>
          {/* Edit/Save Buttons */}
          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={saveEditing}
                  disabled={updateProjectMutation.isPending}
                  className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
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
                className="flex items-center gap-2 px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
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
              <label className="block text-gray-500 mb-1">{t('projectDetail.beneficiaryName')}</label>
              <input
                type="text"
                value={editForm.beneficiary.name}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, name: e.target.value }
                })}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Street */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.street')}</label>
              <input
                type="text"
                value={editForm.beneficiary.street}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, street: e.target.value }
                })}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* ZIP + City */}
            <div className="flex gap-2">
              <div className="w-1/3">
                <label className="block text-gray-500 mb-1">{t('projectDetail.zip')}</label>
                <input
                  type="text"
                  value={editForm.beneficiary.zip}
                  onChange={e => setEditForm({
                    ...editForm,
                    beneficiary: { ...editForm.beneficiary, zip: e.target.value }
                  })}
                  className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="w-2/3">
                <label className="block text-gray-500 mb-1">{t('projectDetail.city')}</label>
                <input
                  type="text"
                  value={editForm.beneficiary.city}
                  onChange={e => setEditForm({
                    ...editForm,
                    beneficiary: { ...editForm.beneficiary, city: e.target.value }
                  })}
                  className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* VAT ID */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.vatId')}</label>
              <input
                type="text"
                value={editForm.beneficiary.vat_id}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, vat_id: e.target.value }
                })}
                placeholder="DE123456789"
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Tax Number */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.taxNumber')}</label>
              <input
                type="text"
                value={editForm.beneficiary.tax_number}
                onChange={e => setEditForm({
                  ...editForm,
                  beneficiary: { ...editForm.beneficiary, tax_number: e.target.value }
                })}
                placeholder="123/456/78901"
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* File Reference */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.fileReference')}</label>
              <input
                type="text"
                value={editForm.project.file_reference}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, file_reference: e.target.value }
                })}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Execution Location */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.executionLocation')}</label>
              <input
                type="text"
                value={editForm.project.implementation_location}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, implementation_location: e.target.value }
                })}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Execution City */}
            <div>
              <label className="block text-gray-500 mb-1">{t('projectDetail.executionCity')}</label>
              <input
                type="text"
                value={editForm.project.implementation_city}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, implementation_city: e.target.value }
                })}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Project Description */}
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-gray-500 mb-1">{t('projectDetail.projectDescription')}</label>
              <textarea
                value={editForm.project.project_description}
                onChange={e => setEditForm({
                  ...editForm,
                  project: { ...editForm.project, project_description: e.target.value }
                })}
                rows={3}
                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        ) : (
          /* Project Details Grid - View Mode */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3 text-sm">
            {/* Beneficiary Name */}
            <div>
              <span className="text-gray-500">{t('projectDetail.beneficiaryName')}:</span>
              <span className="ml-2 font-medium">{project.beneficiary.name}</span>
            </div>

            {/* Address */}
            <div className="md:col-span-2">
              <span className="text-gray-500">{t('projectDetail.address')}:</span>
              <span className="ml-2 font-medium">
                {project.beneficiary.street}, {project.beneficiary.zip} {project.beneficiary.city}
              </span>
            </div>

            {/* VAT ID */}
            <div>
              <span className="text-gray-500">{t('projectDetail.vatId')}:</span>
              <span className="ml-2 font-medium">{project.beneficiary.vat_id || '-'}</span>
            </div>

            {/* Tax Number */}
            <div>
              <span className="text-gray-500">{t('projectDetail.taxNumber')}:</span>
              <span className="ml-2 font-medium">{project.beneficiary.tax_number || '-'}</span>
            </div>

            {/* File Reference (Aktenzeichen) */}
            <div>
              <span className="text-gray-500">{t('projectDetail.fileReference')}:</span>
              <span className="ml-2 font-medium">{project.project.file_reference || '-'}</span>
            </div>

            {/* Execution Location (Durchführungsort) */}
            <div className="md:col-span-2">
              <span className="text-gray-500">{t('projectDetail.executionLocation')}:</span>
              <span className="ml-2 font-medium">
                {project.project.implementation
                  ? `${project.project.implementation.location_name || ''}${project.project.implementation.city ? `, ${project.project.implementation.city}` : ''}`
                  : '-'}
              </span>
            </div>

            {/* Project Description */}
            <div className="md:col-span-3">
              <span className="text-gray-500">{t('projectDetail.projectDescription')}:</span>
              <p className="mt-1 text-gray-700">{project.project.project_description || '-'}</p>
            </div>

            {/* Project Period */}
            {project.project.project_period && (
              <div>
                <span className="text-gray-500">{t('projectDetail.projectPeriod')}:</span>
                <span className="ml-2 font-medium">
                  {project.project.project_period.start && new Date(project.project.project_period.start).toLocaleDateString('de-DE')}
                  {project.project.project_period.end && ` - ${new Date(project.project.project_period.end).toLocaleDateString('de-DE')}`}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Ruleset Badge */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{currentRuleset?.flag}</span>
            <span className="font-medium">{lang === 'de' ? currentRuleset?.title_de : currentRuleset?.title_en}</span>
          </div>
          <button
            onClick={() => setShowTaxSelector(true)}
            className="text-sm text-primary-600 hover:underline"
          >
            {t('taxSelector.changeSystem')}
          </button>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Belegliste */}
        <div className="lg:col-span-2 space-y-4">
          {/* Collapsible Features */}
          <div className="bg-white rounded-lg border border-gray-200">
            <button
              onClick={() => setShowFeatures(!showFeatures)}
              className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50"
            >
              <span className="font-medium text-gray-900">{t('projectDetail.showFeatures')}</span>
              {showFeatures ? (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-400" />
              )}
            </button>
            {showFeatures && currentRuleset && (
              <div className="px-4 pb-4 border-t border-gray-100">
                <div className="mt-3 space-y-2 text-sm max-h-60 overflow-y-auto">
                  {currentRuleset.features.map(feature => (
                    <div key={feature.feature_id} className="flex items-center justify-between py-1">
                      <span className="text-gray-600">
                        {lang === 'de' ? feature.name_de : feature.name_en}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-xs rounded ${
                          feature.required_level === 'REQUIRED'
                            ? 'bg-red-100 text-red-700'
                            : feature.required_level === 'CONDITIONAL'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {feature.required_level}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Belegliste (Processed Documents) */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">{t('projectDetail.documentList')}</h3>
            </div>

            {processedDocs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-500 font-medium">Nr.</th>
                      <th className="px-4 py-2 text-left text-gray-500 font-medium">
                        {t('projectDetail.supplier')}
                      </th>
                      <th className="px-4 py-2 text-left text-gray-500 font-medium">
                        {t('projectDetail.date')}
                      </th>
                      <th className="px-4 py-2 text-right text-gray-500 font-medium">
                        {t('projectDetail.amount')}
                      </th>
                      <th className="px-4 py-2 text-center text-gray-500 font-medium">Status</th>
                      <th className="px-4 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {processedDocs.map((doc, index) => (
                      <tr key={doc.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-gray-900">{index + 1}</td>
                        <td className="px-4 py-3 text-gray-900">
                          {doc.extracted_data?.supplier_name_address?.value?.split('\n')[0] || '-'}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {doc.extracted_data?.invoice_date?.value || '-'}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">
                          {doc.extracted_data?.gross_amount?.value
                            ? `${parseFloat(doc.extracted_data.gross_amount.value).toLocaleString('de-DE', { minimumFractionDigits: 2 })} €`
                            : '-'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {doc.analysis_result?.overall_assessment === 'ok' ? (
                            <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                          ) : doc.analysis_result?.overall_assessment === 'rejected' ? (
                            <AlertCircle className="h-5 w-5 text-red-500 mx-auto" />
                          ) : (
                            <Clock className="h-5 w-5 text-yellow-500 mx-auto" />
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            to={`/documents/${doc.id}`}
                            className="text-primary-600 hover:text-primary-700"
                          >
                            <FileText className="h-5 w-5" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-gray-500">
                <FileText className="h-10 w-10 text-gray-300 mx-auto mb-2" />
                {t('projectDetail.noProcessedDocuments')}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Upload & Actions */}
        <div className="space-y-4">
          {/* Upload Area */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-3">{t('projectDetail.uploadedFiles')}</h3>

            {/* File List */}
            {uploadQueue.length > 0 && (
              <div className="mb-4 space-y-2 max-h-80 overflow-y-auto">
                {uploadQueue.map((file, index) => (
                  <div
                    key={file.id}
                    className="p-2 bg-gray-50 rounded text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-gray-400 w-5">{index + 1}.</span>
                        <span className="truncate">{file.file.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {file.status === 'uploading' && <Loader2 className="h-4 w-4 animate-spin text-primary-600" />}
                        {file.status === 'done' && <CheckCircle className="h-4 w-4 text-green-500" />}
                        {file.status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
                        {file.status === 'pending' && (
                          <button onClick={() => removeFromQueue(file.id)} className="text-gray-400 hover:text-red-500">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                    {/* Document Type Selector */}
                    {file.status === 'pending' && (
                      <div className="mt-2 pl-7">
                        <select
                          value={file.documentType}
                          onChange={e => updateDocumentType(file.id, e.target.value as DocumentType)}
                          className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                        >
                          <option value="INVOICE">{t('documentTypes.invoice')}</option>
                          <option value="BANK_STATEMENT">{t('documentTypes.bankStatement')}</option>
                          <option value="PROCUREMENT">{t('documentTypes.procurement')}</option>
                          <option value="CONTRACT">{t('documentTypes.contract')}</option>
                          <option value="OTHER">{t('documentTypes.other')}</option>
                        </select>
                        {/* Warning if document type not supported by ruleset */}
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
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
              } ${uploadQueue.length >= 20 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <input {...getInputProps()} />
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">{t('projectDetail.dropzoneText')}</p>
              <p className="text-xs text-gray-400 mt-1">
                {t('projectDetail.maxFiles', { count: 20 - uploadQueue.length })}
              </p>
            </div>

            {/* Upload Button */}
            {uploadQueue.some(f => f.status === 'pending') && (
              <button
                onClick={uploadAllFiles}
                disabled={uploadMutation.isPending}
                className="mt-3 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploadMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                <Upload className="h-4 w-4" />
                {t('documents.uploadDocument')}
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                title={t('projectDetail.analysisSettings')}
              >
                <Settings className="h-5 w-5" />
              </button>

              <button
                onClick={analyzeAllDocuments}
                disabled={analyzeMutation.isPending || !uploadQueue.some(f => f.status === 'done')}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analyzeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                <Search className="h-4 w-4" />
                {t('projectDetail.recognizeDocuments')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50" onClick={() => setShowSettings(false)} />
            <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{t('projectDetail.analysisSettings')}</h3>
                <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-700">{t('projectDetail.useOcr')}</label>
                  <input
                    type="checkbox"
                    checked={settings.useOcr}
                    onChange={e => setSettings({ ...settings, useOcr: e.target.checked })}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-700 mb-1">
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
                  <span className="text-sm text-gray-500">{Math.round(settings.confidenceThreshold * 100)}%</span>
                </div>

                <div>
                  <label className="block text-sm text-gray-700 mb-1">{t('projectDetail.maxRuns')}</label>
                  <select
                    value={settings.maxRuns}
                    onChange={e => setSettings({ ...settings, maxRuns: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
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
