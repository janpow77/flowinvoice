import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  Eye,
  FolderOpen,
  Download,
  MapPin,
  Hash,
  ListTodo,
  BarChart3,
  Clock,
  RefreshCw,
  XCircle,
  PauseCircle,
  Trash2,
  FileCheck,
  Plus,
  Rocket,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { BatchJob } from '@/lib/types'

type TabId = 'generate' | 'batch-jobs' | 'results'

interface Template {
  template_id: string
  name: string
  preview_url: string
}

interface GeneratorConfig {
  project_id: string
  ruleset_id: string
  count: number
  templates_enabled: string[]
  error_rate_total: number
  severity: number
  alias_noise_probability: number
  beneficiary_source: 'manual' | 'project'
  beneficiary_name: string
  street: string
  zip: string
  city: string
  country: string
  vat_id: string
  execution_location: string
  project_number: string
}

// Template-spezifische Vorschaudaten
const templatePreviews: Record<string, { supplier: string; amount: string; type: string }> = {
  'T1_HANDWERK': { supplier: 'Meister Müller', amount: '2.450,00', type: 'Handwerk' },
  'T2_CONSULTING': { supplier: 'Beratung AG', amount: '8.500,00', type: 'Beratung' },
  'T3_CORPORATE': { supplier: 'TechSolutions', amount: '15.200,00', type: 'IT-Service' },
  'T4_FREELANCER': { supplier: 'M. Mustermann', amount: '1.800,00', type: 'Freelance' },
  'T5_INTERNATIONAL': { supplier: 'Global Corp', amount: '25.000,00', type: 'International' },
}

// Job-Status Badge
function JobStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    PENDING: { color: 'bg-gray-100 text-gray-600', icon: <Clock className="h-3 w-3" /> },
    QUEUED: { color: 'bg-blue-100 text-blue-600', icon: <ListTodo className="h-3 w-3" /> },
    RUNNING: { color: 'bg-yellow-100 text-yellow-600', icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    COMPLETED: { color: 'bg-green-100 text-green-600', icon: <CheckCircle className="h-3 w-3" /> },
    FAILED: { color: 'bg-red-100 text-red-600', icon: <XCircle className="h-3 w-3" /> },
    CANCELLED: { color: 'bg-gray-100 text-gray-500', icon: <PauseCircle className="h-3 w-3" /> },
  }
  const config = statusConfig[status] || statusConfig.PENDING

  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', config.color)}>
      {config.icon}
      {status}
    </span>
  )
}

// Job-Type Label
function JobTypeLabel({ type }: { type: string }) {
  const labels: Record<string, string> = {
    BATCH_ANALYZE: 'Analyse',
    BATCH_VALIDATE: 'Validierung',
    BATCH_EXPORT: 'Export',
    SOLUTION_APPLY: 'Lösung anwenden',
    RAG_REBUILD: 'RAG neu aufbauen',
  }
  return <span className="text-sm">{labels[type] || type}</span>
}

export default function Generator() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabId>('generate')
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(['T1_HANDWERK', 'T3_CORPORATE'])
  const [previewTemplate, setPreviewTemplate] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  const [config, setConfig] = useState<GeneratorConfig>({
    project_id: '',
    ruleset_id: 'DE_USTG',
    count: 20,
    templates_enabled: ['T1_HANDWERK', 'T3_CORPORATE'],
    error_rate_total: 5.0,
    severity: 2,
    alias_noise_probability: 10.0,
    beneficiary_source: 'manual',
    beneficiary_name: '',
    street: '',
    zip: '',
    city: '',
    country: 'DE',
    vat_id: '',
    execution_location: '',
    project_number: '',
  })

  // New batch job form state
  const [newJobType, setNewJobType] = useState<string>('BATCH_ANALYZE')
  const [newJobProjectId, setNewJobProjectId] = useState<string>('')
  const [showNewJobForm, setShowNewJobForm] = useState(false)

  // Fetch templates
  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['generator-templates'],
    queryFn: () => api.getGeneratorTemplates(),
  })

  // Fetch projects for selection
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  // Fetch job status
  const { data: jobStatus } = useQuery({
    queryKey: ['generator-job', currentJobId],
    queryFn: () => currentJobId ? api.getGeneratorJob(currentJobId) : null,
    enabled: !!currentJobId,
    refetchInterval: currentJobId ? 2000 : false,
  })

  // Fetch batch jobs
  const { data: batchJobsData, isLoading: batchJobsLoading } = useQuery({
    queryKey: ['batch-jobs', config.project_id],
    queryFn: () => api.getBatchJobs({
      project_id: config.project_id || undefined,
      limit: 50,
    }),
    enabled: activeTab === 'batch-jobs',
  })

  // Get selected project data
  const selectedProject = projects?.find((p: { id: string }) => p.id === config.project_id)

  // Determine beneficiary data based on source
  const getBeneficiaryData = () => {
    if (config.beneficiary_source === 'project' && selectedProject?.beneficiary) {
      const b = selectedProject.beneficiary
      return {
        beneficiary_name: b.beneficiary_name || '',
        street: b.street || '',
        zip: b.zip || '',
        city: b.city || '',
        country: b.country || 'DE',
        vat_id: b.vat_id || undefined,
      }
    }
    if (config.beneficiary_source === 'manual' && config.beneficiary_name) {
      return {
        beneficiary_name: config.beneficiary_name,
        street: config.street,
        zip: config.zip,
        city: config.city,
        country: config.country,
        vat_id: config.vat_id || undefined,
      }
    }
    return undefined
  }

  // Run generator mutation
  const runGeneratorMutation = useMutation({
    mutationFn: () => api.runGenerator({
      project_id: config.project_id || undefined,
      ruleset_id: config.ruleset_id,
      count: config.count,
      templates_enabled: selectedTemplates,
      error_rate_total: config.error_rate_total,
      severity: config.severity,
      alias_noise_probability: config.alias_noise_probability,
      beneficiary_data: getBeneficiaryData(),
      project_context: config.project_number || config.execution_location ? {
        project_number: config.project_number || undefined,
        execution_location: config.execution_location || undefined,
      } : undefined,
    }),
    onSuccess: (data) => {
      setCurrentJobId(data.generator_job_id)
    },
  })

  // Cancel batch job mutation
  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => api.cancelBatchJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch-jobs'] })
    },
  })

  // Retry batch job mutation
  const retryJobMutation = useMutation({
    mutationFn: (jobId: string) => api.retryBatchJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch-jobs'] })
    },
  })

  // Create batch job mutation
  const createBatchJobMutation = useMutation({
    mutationFn: (data: { job_type: string; project_id?: string }) =>
      api.createBatchJob({
        job_type: data.job_type,
        project_id: data.project_id || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batch-jobs'] })
      setShowNewJobForm(false)
      setNewJobType('BATCH_ANALYZE')
      setNewJobProjectId('')
    },
  })

  const toggleTemplate = (templateId: string) => {
    setSelectedTemplates(prev =>
      prev.includes(templateId)
        ? prev.filter(id => id !== templateId)
        : [...prev, templateId]
    )
  }

  const handleRun = () => {
    runGeneratorMutation.mutate()
  }

  const handleCreateBatchJob = () => {
    createBatchJobMutation.mutate({
      job_type: newJobType,
      project_id: newJobProjectId || undefined,
    })
  }

  const isRunning = runGeneratorMutation.isPending || (jobStatus?.status === 'RUNNING' || jobStatus?.status === 'PENDING')

  // Tabs configuration
  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: 'generate', label: t('generator.tabGenerate', 'Generieren'), icon: <FileText className="h-4 w-4" /> },
    { id: 'batch-jobs', label: t('generator.tabBatchJobs', 'Batch-Jobs'), icon: <ListTodo className="h-4 w-4" /> },
    { id: 'results', label: t('generator.tabResults', 'Ergebnisse'), icon: <BarChart3 className="h-4 w-4" /> },
  ]

  // Calculate stats for results tab
  const batchJobs = batchJobsData?.jobs || []
  const completedJobs = batchJobs.filter((j: BatchJob) => j.status === 'COMPLETED')
  const totalProcessed = completedJobs.reduce((sum: number, j: BatchJob) => sum + (j.processed_items || 0), 0)
  const totalSuccessful = completedJobs.reduce((sum: number, j: BatchJob) => sum + (j.successful_items || 0), 0)
  const totalFailed = completedJobs.reduce((sum: number, j: BatchJob) => sum + (j.failed_items || 0), 0)
  const successRate = totalProcessed > 0 ? ((totalSuccessful / totalProcessed) * 100).toFixed(1) : '0'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-theme-text-primary flex items-center gap-2">
          <FileText className="h-7 w-7 text-accent-primary" />
          {t('generator.title', 'Rechnungs-Generator')}
        </h1>
        <p className="text-theme-text-muted mt-1">
          {t('generator.description', 'Generieren Sie Test-Rechnungen für Seminare und Schulungen')}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-theme-border-default">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-accent-primary text-accent-primary'
                  : 'border-transparent text-theme-text-muted hover:text-theme-text-primary hover:border-theme-border-strong'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'generate' && (
        <>
          {/* Job Status */}
          {currentJobId && jobStatus && (
            <div className={clsx(
              'p-4 rounded-lg border',
              jobStatus.status === 'COMPLETED' ? 'bg-status-success-bg border-status-success-border' :
              jobStatus.status === 'ERROR' ? 'bg-status-danger-bg border-status-danger-border' :
              'bg-status-info-bg border-status-info-border'
            )}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {jobStatus.status === 'COMPLETED' ? (
                    <CheckCircle className="h-6 w-6 text-status-success" />
                  ) : jobStatus.status === 'ERROR' ? (
                    <AlertCircle className="h-6 w-6 text-status-danger" />
                  ) : (
                    <Loader2 className="h-6 w-6 text-status-info animate-spin" />
                  )}
                  <div>
                    <p className="font-medium text-theme-text-primary">
                      {jobStatus.status === 'COMPLETED' ? t('generator.completed', 'Generierung abgeschlossen') :
                       jobStatus.status === 'ERROR' ? t('generator.error', 'Fehler bei der Generierung') :
                       t('generator.inProgress', 'Generierung läuft...')}
                    </p>
                    {jobStatus.generated_files && (
                      <p className="text-sm text-theme-text-muted">
                        {jobStatus.generated_files.length} {t('generator.filesGenerated', 'Dateien generiert')}
                      </p>
                    )}
                  </div>
                </div>
                {jobStatus.status === 'COMPLETED' && jobStatus.generated_files && jobStatus.generated_files.length > 0 && (
                  <a
                    href={`/api/generator/jobs/${currentJobId}/download`}
                    download
                    className="flex items-center gap-2 px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    {t('generator.downloadAll', 'Alle herunterladen')}
                  </a>
                )}
              </div>

              {/* File list */}
              {jobStatus.status === 'COMPLETED' && jobStatus.generated_files && jobStatus.generated_files.length > 0 && (
                <div className="mt-4 pt-4 border-t border-status-success-border">
                  <h4 className="text-sm font-medium text-theme-text-secondary mb-2">
                    {t('generator.generatedFiles', 'Generierte Dateien')}
                  </h4>
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    {jobStatus.generated_files.map((file: string, index: number) => {
                      const filename = file.split('/').pop() || file
                      return (
                        <div key={index} className="flex items-center justify-between py-1 px-2 rounded hover:bg-status-success-bg">
                          <span className="text-sm text-theme-text-muted flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            {filename}
                          </span>
                          <a
                            href={`/api/generator/jobs/${currentJobId}/files/${encodeURIComponent(filename)}`}
                            download={filename}
                            className="text-accent-primary hover:text-accent-primary-hover"
                            title={t('generator.download', 'Herunterladen')}
                          >
                            <Download className="h-4 w-4" />
                          </a>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Inputs */}
            <div className="lg:col-span-2 space-y-6">

              {/* 1. Project Selection */}
              <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
                <h2 className="text-lg font-semibold text-theme-text-primary mb-4 flex items-center gap-2">
                  <FolderOpen className="h-5 w-5" />
                  {t('generator.projectSelection', 'Projektauswahl')}
                </h2>
                <select
                  value={config.project_id}
                  onChange={(e) => setConfig({ ...config, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                >
                  <option value="">{t('generator.noProject', 'Kein Projekt ausgewählt')}</option>
                  {(projects || []).map((project: { id: string; title: string }) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* 2. Beneficiary Data + Project Context */}
              <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
                <h2 className="text-lg font-semibold text-theme-text-primary mb-4">
                  {t('generator.beneficiaryAndContext', 'Begünstigter & Projektkontext')}
                </h2>

                {/* Source Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                    {t('generator.beneficiarySource', 'Datenquelle Begünstigter')}
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="beneficiary_source"
                        value="manual"
                        checked={config.beneficiary_source === 'manual'}
                        onChange={() => setConfig({ ...config, beneficiary_source: 'manual' })}
                        className="text-accent-primary"
                      />
                      <span className="text-sm text-theme-text-secondary">
                        {t('generator.manualInput', 'Manuelle Eingabe')}
                      </span>
                    </label>
                    <label className={clsx(
                      'flex items-center gap-2',
                      config.project_id ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
                    )}>
                      <input
                        type="radio"
                        name="beneficiary_source"
                        value="project"
                        checked={config.beneficiary_source === 'project'}
                        onChange={() => setConfig({ ...config, beneficiary_source: 'project' })}
                        disabled={!config.project_id}
                        className="text-accent-primary"
                      />
                      <span className="text-sm text-theme-text-secondary">
                        {t('generator.fromProject', 'Aus Projekt übernehmen')}
                      </span>
                    </label>
                  </div>
                  {config.beneficiary_source === 'project' && !selectedProject?.beneficiary && config.project_id && (
                    <p className="text-sm text-status-warning mt-2">
                      {t('generator.noBeneficiaryInProject', 'Das gewählte Projekt enthält keine Begünstigtendaten.')}
                    </p>
                  )}
                </div>

                {/* Manual Input Fields */}
                {config.beneficiary_source === 'manual' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.beneficiaryName', 'Name / Firma')}
                      </label>
                      <input
                        type="text"
                        value={config.beneficiary_name}
                        onChange={(e) => setConfig({ ...config, beneficiary_name: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="Muster GmbH"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.street', 'Straße')}
                      </label>
                      <input
                        type="text"
                        value={config.street}
                        onChange={(e) => setConfig({ ...config, street: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="Musterstraße 1"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.zip', 'PLZ')}
                      </label>
                      <input
                        type="text"
                        value={config.zip}
                        onChange={(e) => setConfig({ ...config, zip: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="12345"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.city', 'Stadt')}
                      </label>
                      <input
                        type="text"
                        value={config.city}
                        onChange={(e) => setConfig({ ...config, city: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="Musterstadt"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.vatId', 'USt-IdNr. (optional)')}
                      </label>
                      <input
                        type="text"
                        value={config.vat_id}
                        onChange={(e) => setConfig({ ...config, vat_id: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="DE123456789"
                      />
                    </div>
                  </div>
                )}

                {/* Project Data Preview */}
                {config.beneficiary_source === 'project' && selectedProject?.beneficiary && (
                  <div className="bg-theme-hover rounded-lg p-4 mb-6">
                    <h4 className="text-sm font-medium text-theme-text-secondary mb-2">
                      {t('generator.beneficiaryPreview', 'Begünstigtendaten aus Projekt')}
                    </h4>
                    <div className="text-sm text-theme-text-muted space-y-1">
                      <p><strong className="text-theme-text-primary">{selectedProject.beneficiary.beneficiary_name}</strong></p>
                      <p>{selectedProject.beneficiary.street}</p>
                      <p>{selectedProject.beneficiary.zip} {selectedProject.beneficiary.city}</p>
                      {selectedProject.beneficiary.vat_id && (
                        <p>USt-IdNr.: {selectedProject.beneficiary.vat_id}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Project Context */}
                <div className="border-t border-theme-border-default pt-4">
                  <h3 className="text-sm font-medium text-theme-text-secondary mb-3">
                    {t('generator.projectContext', 'Projektkontext (optional)')}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1 flex items-center gap-2">
                        <Hash className="h-4 w-4" />
                        {t('generator.projectNumber', 'Projektnummer')}
                      </label>
                      <input
                        type="text"
                        value={config.project_number}
                        onChange={(e) => setConfig({ ...config, project_number: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="PRJ-2025-001"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1 flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        {t('generator.executionLocation', 'Durchführungsort')}
                      </label>
                      <input
                        type="text"
                        value={config.execution_location}
                        onChange={(e) => setConfig({ ...config, execution_location: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                        placeholder="Berlin"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. Template Selection */}
              <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
                <h2 className="text-lg font-semibold text-theme-text-primary mb-4">
                  {t('generator.templates', 'Rechnungs-Templates')}
                </h2>

                {templatesLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
                  </div>
                ) : (
                  <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-3">
                    {(templates || []).map((template: Template) => {
                      const preview = templatePreviews[template.template_id] || { supplier: 'Firma', amount: '1.000,00', type: 'Standard' }
                      return (
                        <div
                          key={template.template_id}
                          className={clsx(
                            'relative border-2 rounded-lg overflow-hidden cursor-pointer transition-all group',
                            selectedTemplates.includes(template.template_id)
                              ? 'border-accent-primary ring-2 ring-accent-primary/30'
                              : 'border-theme-border-default hover:border-theme-border-strong'
                          )}
                          onClick={() => toggleTemplate(template.template_id)}
                        >
                          {/* Realistische Rechnungsvorschau - 50% kleiner */}
                          <div className="relative aspect-[3/4] bg-theme-hover p-1">
                            <div className="w-full h-full bg-theme-card shadow-sm rounded border border-theme-border-default p-1.5 text-[5px] leading-tight">
                              {/* Header */}
                              <div className="text-center mb-1">
                                <div className="font-bold text-[7px] text-theme-text-primary">RECHNUNG</div>
                                <div className="text-theme-text-muted">Nr. 2025-001</div>
                              </div>

                              {/* Rechnungssteller */}
                              <div className="border-t border-theme-border-subtle pt-0.5 mb-1">
                                <div className="font-semibold text-theme-text-secondary">{preview.supplier}</div>
                                <div className="text-theme-text-muted">Musterstr. 1</div>
                              </div>

                              {/* Empfänger */}
                              <div className="bg-theme-hover rounded p-0.5 mb-1">
                                <div className="text-theme-text-muted">An: Kunde GmbH</div>
                              </div>

                              {/* Leistung */}
                              <div className="mb-1">
                                <div className="text-theme-text-muted">{preview.type}</div>
                              </div>

                              {/* Beträge */}
                              <div className="border-t border-theme-border-default pt-0.5 mt-auto">
                                <div className="flex justify-between">
                                  <span className="text-theme-text-muted">Netto:</span>
                                  <span className="text-theme-text-secondary">{preview.amount}</span>
                                </div>
                                <div className="flex justify-between font-bold text-[6px]">
                                  <span>Brutto:</span>
                                  <span className="text-accent-primary">{preview.amount} EUR</span>
                                </div>
                              </div>
                            </div>

                            {/* Vorschau-Button Overlay */}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setPreviewTemplate(template.template_id)
                                }}
                                className="opacity-0 group-hover:opacity-100 transition-opacity bg-theme-card/90 rounded-full p-1.5 shadow-lg hover:bg-theme-hover"
                                title={t('generator.preview', 'Vorschau')}
                              >
                                <Eye className="h-3 w-3 text-theme-text-secondary" />
                              </button>
                            </div>

                            {/* Ausgewählt-Marker */}
                            {selectedTemplates.includes(template.template_id) && (
                              <div className="absolute top-1 right-1 bg-accent-primary rounded-full p-0.5">
                                <CheckCircle className="h-3 w-3 text-white" />
                              </div>
                            )}
                          </div>

                          {/* Template-Name klein unter dem Bild */}
                          <div className="py-1 px-1 text-center bg-theme-hover">
                            <p className="text-[9px] text-theme-text-muted truncate">
                              {template.name}
                            </p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Settings */}
            <div className="space-y-6">
              {/* Basic Settings */}
              <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
                <h2 className="text-lg font-semibold text-theme-text-primary mb-4 flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  {t('generator.settings', 'Einstellungen')}
                </h2>

                <div className="space-y-4">
                  {/* Count */}
                  <div>
                    <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                      {t('generator.count', 'Anzahl Rechnungen')}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={config.count}
                      onChange={(e) => setConfig({ ...config, count: parseInt(e.target.value) || 20 })}
                      className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                    />
                  </div>

                  {/* Ruleset */}
                  <div>
                    <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                      {t('generator.ruleset', 'Regelwerk')}
                    </label>
                    <select
                      value={config.ruleset_id}
                      onChange={(e) => setConfig({ ...config, ruleset_id: e.target.value })}
                      className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                    >
                      <option value="DE_USTG">DE_USTG (Deutsches UStG)</option>
                      <option value="EU_VAT">EU_VAT (EU-Mehrwertsteuer)</option>
                      <option value="CH_MWSTG">CH_MWSTG (Schweizer MwSt)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Advanced Settings */}
              <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="w-full flex items-center justify-between text-left"
                >
                  <h2 className="text-lg font-semibold text-theme-text-primary">
                    {t('generator.advanced', 'Erweiterte Einstellungen')}
                  </h2>
                  <span className="text-theme-text-muted">
                    {showAdvanced ? '−' : '+'}
                  </span>
                </button>

                {showAdvanced && (
                  <div className="mt-4 space-y-4">
                    {/* Error Rate */}
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.errorRate', 'Fehlerrate')} ({config.error_rate_total}%)
                      </label>
                      <input
                        type="range"
                        min={0}
                        max={50}
                        step={1}
                        value={config.error_rate_total}
                        onChange={(e) => setConfig({ ...config, error_rate_total: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-theme-text-muted mt-1">
                        {t('generator.errorRateHint', 'Prozentsatz der Rechnungen mit absichtlichen Fehlern')}
                      </p>
                    </div>

                    {/* Severity */}
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.severity', 'Schweregrad')} ({config.severity}/5)
                      </label>
                      <input
                        type="range"
                        min={1}
                        max={5}
                        step={1}
                        value={config.severity}
                        onChange={(e) => setConfig({ ...config, severity: parseInt(e.target.value) })}
                        className="w-full"
                      />
                    </div>

                    {/* Alias Noise */}
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('generator.aliasNoise', 'Alias-Rauschen')} ({config.alias_noise_probability}%)
                      </label>
                      <input
                        type="range"
                        min={0}
                        max={50}
                        step={1}
                        value={config.alias_noise_probability}
                        onChange={(e) => setConfig({ ...config, alias_noise_probability: parseFloat(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-theme-text-muted mt-1">
                        {t('generator.aliasNoiseHint', 'Variationen bei Firmennamen und Adressen')}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Summary */}
              <div className="bg-theme-hover rounded-xl p-4 border border-theme-border-default">
                <h3 className="text-sm font-medium text-theme-text-secondary mb-2">
                  {t('generator.summary', 'Zusammenfassung')}
                </h3>
                <ul className="text-sm text-theme-text-muted space-y-1">
                  <li>• {config.count} {t('generator.invoices', 'Rechnungen')}</li>
                  <li>• {selectedTemplates.length} {t('generator.templatesSelected', 'Templates ausgewählt')}</li>
                  <li>• {config.error_rate_total}% {t('generator.withErrors', 'mit Fehlern')}</li>
                  <li>• Regelwerk: {config.ruleset_id}</li>
                  {config.beneficiary_name && (
                    <li>• {t('generator.to', 'An')}: {config.beneficiary_name}</li>
                  )}
                </ul>
              </div>

              {/* Start Button */}
              <button
                onClick={handleRun}
                disabled={isRunning || selectedTemplates.length === 0}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 px-6 py-4 rounded-lg font-medium transition-colors text-lg',
                  isRunning || selectedTemplates.length === 0
                    ? 'bg-theme-hover text-theme-text-disabled cursor-not-allowed'
                    : 'bg-accent-primary text-white hover:bg-accent-primary-hover'
                )}
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-6 w-6 animate-spin" />
                    {t('generator.running', 'Generiere...')}
                  </>
                ) : (
                  <>
                    <Play className="h-6 w-6" />
                    {t('generator.run', 'Generator starten')}
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}

      {activeTab === 'batch-jobs' && (
        <div className="space-y-6">
          {/* Header with New Job and Refresh buttons */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-theme-text-primary">
              {t('generator.batchJobsList', 'Batch-Jobs')}
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowNewJobForm(!showNewJobForm)}
                className={clsx(
                  'flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors',
                  showNewJobForm
                    ? 'bg-accent-primary text-white'
                    : 'bg-accent-primary text-white hover:bg-accent-primary-hover'
                )}
              >
                <Plus className="h-4 w-4" />
                {t('generator.newBatchJob', 'Neuer Job')}
              </button>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ['batch-jobs'] })}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-theme-text-secondary hover:text-theme-text-primary border border-theme-border-default rounded-lg hover:bg-theme-hover"
              >
                <RefreshCw className="h-4 w-4" />
                {t('common.refresh', 'Aktualisieren')}
              </button>
            </div>
          </div>

          {/* New Job Form */}
          {showNewJobForm && (
            <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
              <h3 className="text-md font-semibold text-theme-text-primary mb-4 flex items-center gap-2">
                <Rocket className="h-5 w-5 text-accent-primary" />
                {t('generator.createBatchJob', 'Batch-Job erstellen')}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Job Type */}
                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    {t('generator.jobType', 'Job-Typ')}
                  </label>
                  <select
                    value={newJobType}
                    onChange={(e) => setNewJobType(e.target.value)}
                    className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                  >
                    <option value="BATCH_ANALYZE">{t('generator.jobTypeAnalyze', 'Dokumente analysieren')}</option>
                    <option value="BATCH_VALIDATE">{t('generator.jobTypeValidate', 'Dokumente validieren')}</option>
                    <option value="BATCH_EXPORT">{t('generator.jobTypeExport', 'Ergebnisse exportieren')}</option>
                    <option value="RAG_REBUILD">{t('generator.jobTypeRagRebuild', 'RAG-Index neu aufbauen')}</option>
                  </select>
                </div>

                {/* Project Selection */}
                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    {t('generator.project', 'Projekt')} <span className="text-theme-text-muted">({t('common.optional', 'optional')})</span>
                  </label>
                  <select
                    value={newJobProjectId}
                    onChange={(e) => setNewJobProjectId(e.target.value)}
                    className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary"
                  >
                    <option value="">{t('generator.allProjects', 'Alle Projekte')}</option>
                    {(projects || []).map((project: { id: string; title: string }) => (
                      <option key={project.id} value={project.id}>
                        {project.title}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Submit Button */}
                <div className="flex items-end">
                  <button
                    onClick={handleCreateBatchJob}
                    disabled={createBatchJobMutation.isPending}
                    className={clsx(
                      'flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors w-full',
                      createBatchJobMutation.isPending
                        ? 'bg-theme-hover text-theme-text-disabled cursor-not-allowed'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    )}
                  >
                    {createBatchJobMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        {t('common.creating', 'Erstelle...')}
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        {t('generator.startJob', 'Job starten')}
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Job Type Description */}
              <div className="mt-4 p-3 bg-theme-hover rounded-lg">
                <p className="text-sm text-theme-text-muted">
                  {newJobType === 'BATCH_ANALYZE' && t('generator.jobDescAnalyze', 'Analysiert alle validierten Dokumente des Projekts mit dem LLM.')}
                  {newJobType === 'BATCH_VALIDATE' && t('generator.jobDescValidate', 'Validiert alle Dokumente gegen das konfigurierte Regelwerk.')}
                  {newJobType === 'BATCH_EXPORT' && t('generator.jobDescExport', 'Exportiert alle Prüfergebnisse als CSV/Excel.')}
                  {newJobType === 'RAG_REBUILD' && t('generator.jobDescRagRebuild', 'Baut den RAG-Vektorindex mit allen Beispielen neu auf.')}
                </p>
              </div>

              {/* Error message */}
              {createBatchJobMutation.isError && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {t('generator.jobCreateError', 'Fehler beim Erstellen des Jobs')}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Jobs Table */}
          <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default overflow-hidden">
            {batchJobsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
              </div>
            ) : batchJobs.length === 0 ? (
              <div className="text-center py-12 text-theme-text-muted">
                <ListTodo className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>{t('generator.noBatchJobs', 'Keine Batch-Jobs vorhanden')}</p>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-theme-border-default">
                <thead className="bg-theme-hover">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                      {t('generator.jobType', 'Typ')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                      {t('generator.jobStatus', 'Status')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                      {t('generator.jobProgress', 'Fortschritt')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                      {t('generator.jobCreated', 'Erstellt')}
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider">
                      {t('generator.jobActions', 'Aktionen')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-theme-border-default">
                  {batchJobs.map((job: BatchJob) => (
                    <tr key={job.id} className="hover:bg-theme-hover">
                      <td className="px-4 py-3">
                        <JobTypeLabel type={job.job_type} />
                      </td>
                      <td className="px-4 py-3">
                        <JobStatusBadge status={job.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-theme-hover rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-accent-primary h-full transition-all"
                              style={{ width: `${job.progress_percent || 0}%` }}
                            />
                          </div>
                          <span className="text-xs text-theme-text-muted w-12 text-right">
                            {(job.progress_percent || 0).toFixed(0)}%
                          </span>
                        </div>
                        <div className="text-xs text-theme-text-muted mt-1">
                          {job.processed_items}/{job.total_items} -
                          <span className="text-green-600 ml-1">{job.successful_items} OK</span>
                          {job.failed_items > 0 && (
                            <span className="text-red-600 ml-1">{job.failed_items} Fehler</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-theme-text-muted">
                        {new Date(job.created_at).toLocaleString('de-DE')}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {(job.status === 'PENDING' || job.status === 'QUEUED' || job.status === 'RUNNING') && (
                            <button
                              onClick={() => cancelJobMutation.mutate(job.id)}
                              disabled={cancelJobMutation.isPending}
                              className="p-1.5 text-theme-text-muted hover:text-red-600 hover:bg-red-50 rounded"
                              title={t('generator.cancelJob', 'Abbrechen')}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                          {job.status === 'FAILED' && (
                            <button
                              onClick={() => retryJobMutation.mutate(job.id)}
                              disabled={retryJobMutation.isPending}
                              className="p-1.5 text-theme-text-muted hover:text-accent-primary hover:bg-accent-primary/10 rounded"
                              title={t('generator.retryJob', 'Erneut versuchen')}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {activeTab === 'results' && (
        <div className="space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileCheck className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-theme-text-primary">{totalProcessed}</p>
                  <p className="text-sm text-theme-text-muted">{t('generator.totalProcessed', 'Verarbeitet')}</p>
                </div>
              </div>
            </div>

            <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-theme-text-primary">{totalSuccessful}</p>
                  <p className="text-sm text-theme-text-muted">{t('generator.totalSuccessful', 'Erfolgreich')}</p>
                </div>
              </div>
            </div>

            <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg">
                  <XCircle className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-theme-text-primary">{totalFailed}</p>
                  <p className="text-sm text-theme-text-muted">{t('generator.totalFailed', 'Fehlgeschlagen')}</p>
                </div>
              </div>
            </div>

            <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-theme-text-primary">{successRate}%</p>
                  <p className="text-sm text-theme-text-muted">{t('generator.successRate', 'Erfolgsrate')}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Jobs Summary */}
          <div className="bg-theme-card rounded-xl shadow-sm border border-theme-border-default p-6">
            <h3 className="text-lg font-semibold text-theme-text-primary mb-4">
              {t('generator.recentJobs', 'Letzte Jobs')}
            </h3>
            {completedJobs.length === 0 ? (
              <p className="text-theme-text-muted">{t('generator.noCompletedJobs', 'Keine abgeschlossenen Jobs')}</p>
            ) : (
              <div className="space-y-3">
                {completedJobs.slice(0, 5).map((job: BatchJob) => (
                  <div key={job.id} className="flex items-center justify-between p-3 bg-theme-hover rounded-lg">
                    <div className="flex items-center gap-3">
                      <JobTypeLabel type={job.job_type} />
                      <span className="text-sm text-theme-text-muted">
                        {new Date(job.completed_at || job.created_at).toLocaleString('de-DE')}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-green-600">{job.successful_items} OK</span>
                      {job.failed_items > 0 && (
                        <span className="text-red-600">{job.failed_items} Fehler</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Preview Modal - zeigt Muster-PDF (50% kleiner) */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-theme-elevated rounded-xl shadow-xl max-w-2xl w-full max-h-[70vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-theme-border-default">
              <div>
                <h3 className="text-lg font-semibold text-theme-text-primary">
                  {t('generator.samplePreview', 'Muster-Rechnung')}
                </h3>
                <p className="text-sm text-theme-text-muted">
                  Template: {previewTemplate}
                </p>
              </div>
              <button
                onClick={() => setPreviewTemplate(null)}
                className="p-2 text-theme-text-muted hover:text-theme-text-primary rounded-lg hover:bg-theme-hover"
              >
                ✕
              </button>
            </div>
            <div className="p-4 overflow-auto" style={{ maxHeight: 'calc(70vh - 80px)' }}>
              {/* PDF-Vorschau über iframe - 50% kleiner */}
              <div className="bg-theme-hover rounded-lg p-2">
                <iframe
                  src={`/api/generator/templates/${previewTemplate}/sample.pdf`}
                  className="w-full bg-white rounded shadow"
                  style={{ height: '45vh' }}
                  title="Muster-PDF"
                />
              </div>
              <div className="mt-3 flex justify-end gap-3">
                <a
                  href={`/api/generator/templates/${previewTemplate}/sample.pdf`}
                  download={`Muster_${previewTemplate}.pdf`}
                  className="flex items-center gap-2 px-3 py-1.5 bg-theme-hover text-theme-text-secondary rounded-lg hover:bg-theme-card text-sm"
                >
                  <Download className="h-4 w-4" />
                  {t('generator.downloadSample', 'Muster herunterladen')}
                </a>
                <button
                  onClick={() => setPreviewTemplate(null)}
                  className="px-3 py-1.5 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover text-sm"
                >
                  {t('common.close', 'Schließen')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
