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
} from 'lucide-react'
import { api } from '@/lib/api'
import { TaxSystemSelector } from '@/components/tax-selector'
import { RulesetId, getRuleset } from '@/lib/rulesets'
import { useTranslation } from 'react-i18next'

interface ProjectData {
  id: string
  title: string
  description?: string
  ruleset_id?: RulesetId
  start_date?: string
  end_date?: string
  created_at: string
  document_count?: number
  // Extended fields from beneficiary/project JSONB
  beneficiary?: {
    name?: string
    street?: string
    zip?: string
    city?: string
    country?: string
    vat_id?: string
    tax_number?: string
  }
  project?: {
    project_title?: string
    project_description?: string
    file_reference?: string
    application_number?: string
    implementation?: {
      location_name?: string
      street?: string
      zip?: string
      city?: string
    }
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

interface UploadedFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'done' | 'error'
  documentId?: string
  error?: string
}

interface AnalysisSettings {
  useOcr: boolean
  confidenceThreshold: number
  maxRuns: number
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const lang = i18n.language as 'de' | 'en'

  const [showTaxSelector, setShowTaxSelector] = useState(false)
  const [showFeatures, setShowFeatures] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<UploadedFile[]>([])
  const [settings, setSettings] = useState<AnalysisSettings>({
    useOcr: true,
    confidenceThreshold: 0.7,
    maxRuns: 1,
  })

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
    mutationFn: async ({ file, fileId }: { file: File; fileId: string }) => {
      setUploadQueue(prev =>
        prev.map(f => (f.id === fileId ? { ...f, status: 'uploading' as const } : f))
      )
      const result = await api.uploadDocument(file, id!)
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

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.slice(0, 20 - uploadQueue.length).map(file => ({
        file,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        status: 'pending' as const,
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

  const uploadAllFiles = async () => {
    const pendingFiles = uploadQueue.filter(f => f.status === 'pending')
    for (const uploadFile of pendingFiles) {
      await uploadMutation.mutateAsync({ file: uploadFile.file, fileId: uploadFile.id })
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

  const currentRuleset = project.ruleset_id ? getRuleset(project.ruleset_id) : null

  // Show tax selector if no ruleset is set
  if (!project.ruleset_id || showTaxSelector) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link to="/projects" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <TaxSystemSelector
            currentRuleset={project.ruleset_id}
            onSelect={rulesetId => updateRulesetMutation.mutate(rulesetId)}
          />
          {showTaxSelector && project.ruleset_id && (
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
        <div className="flex items-center gap-4 mb-4">
          <Link to="/projects" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
        </div>

        {/* Project Details Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          {project.beneficiary?.name && (
            <div>
              <span className="text-gray-500">{t('projectDetail.beneficiaryName')}:</span>
              <span className="ml-2 font-medium">{project.beneficiary.name}</span>
            </div>
          )}
          {project.beneficiary?.tax_number && (
            <div>
              <span className="text-gray-500">{t('projectDetail.taxNumber')}:</span>
              <span className="ml-2 font-medium">{project.beneficiary.tax_number}</span>
            </div>
          )}
          {project.project?.application_number && (
            <div>
              <span className="text-gray-500">{t('projectDetail.applicationNumber')}:</span>
              <span className="ml-2 font-medium">{project.project.application_number}</span>
            </div>
          )}
          {project.beneficiary?.street && (
            <div className="col-span-2">
              <span className="text-gray-500">{t('projectDetail.address')}:</span>
              <span className="ml-2 font-medium">
                {project.beneficiary.street}, {project.beneficiary.zip} {project.beneficiary.city}
              </span>
            </div>
          )}
          {project.project?.implementation?.location_name && (
            <div className="col-span-2">
              <span className="text-gray-500">{t('projectDetail.executionLocation')}:</span>
              <span className="ml-2 font-medium">
                {project.project.implementation.location_name}
                {project.project.implementation.city && `, ${project.project.implementation.city}`}
              </span>
            </div>
          )}
        </div>

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
              <div className="mb-4 space-y-2 max-h-60 overflow-y-auto">
                {uploadQueue.map((file, index) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                  >
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
