import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  FileText,
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  Eye,
  FolderOpen
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

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
  beneficiary_name: string
  street: string
  zip: string
  city: string
  country: string
  vat_id: string
}


export default function Generator() {
  const { t } = useTranslation()
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
    beneficiary_name: '',
    street: '',
    zip: '',
    city: '',
    country: 'DE',
    vat_id: '',
  })

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
      beneficiary_data: config.beneficiary_name ? {
        beneficiary_name: config.beneficiary_name,
        street: config.street,
        zip: config.zip,
        city: config.city,
        country: config.country,
        vat_id: config.vat_id || undefined,
      } : undefined,
    }),
    onSuccess: (data) => {
      setCurrentJobId(data.generator_job_id)
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

  const isRunning = runGeneratorMutation.isPending || (jobStatus?.status === 'RUNNING' || jobStatus?.status === 'PENDING')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FileText className="h-7 w-7 text-primary-600" />
            {t('generator.title', 'Rechnungs-Generator')}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {t('generator.description', 'Generieren Sie Test-Rechnungen für Seminare und Schulungen')}
          </p>
        </div>

        <button
          onClick={handleRun}
          disabled={isRunning || selectedTemplates.length === 0}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors',
            isRunning || selectedTemplates.length === 0
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-primary-600 text-white hover:bg-primary-700'
          )}
        >
          {isRunning ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              {t('generator.running', 'Generiere...')}
            </>
          ) : (
            <>
              <Play className="h-5 w-5" />
              {t('generator.run', 'Generator starten')}
            </>
          )}
        </button>
      </div>

      {/* Job Status */}
      {currentJobId && jobStatus && (
        <div className={clsx(
          'p-4 rounded-lg border',
          jobStatus.status === 'COMPLETED' ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' :
          jobStatus.status === 'ERROR' ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' :
          'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800'
        )}>
          <div className="flex items-center gap-3">
            {jobStatus.status === 'COMPLETED' ? (
              <CheckCircle className="h-6 w-6 text-green-600" />
            ) : jobStatus.status === 'ERROR' ? (
              <AlertCircle className="h-6 w-6 text-red-600" />
            ) : (
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
            )}
            <div>
              <p className="font-medium">
                {jobStatus.status === 'COMPLETED' ? t('generator.completed', 'Generierung abgeschlossen') :
                 jobStatus.status === 'ERROR' ? t('generator.error', 'Fehler bei der Generierung') :
                 t('generator.inProgress', 'Generierung läuft...')}
              </p>
              {jobStatus.generated_files && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {jobStatus.generated_files.length} {t('generator.filesGenerated', 'Dateien generiert')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Templates */}
        <div className="lg:col-span-2 space-y-6">
          {/* Template Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('generator.templates', 'Rechnungs-Templates')}
            </h2>

            {templatesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {(templates || []).map((template: Template) => (
                  <div
                    key={template.template_id}
                    className={clsx(
                      'relative border-2 rounded-lg p-4 cursor-pointer transition-all',
                      selectedTemplates.includes(template.template_id)
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    )}
                    onClick={() => toggleTemplate(template.template_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {template.name}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {template.template_id}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setPreviewTemplate(template.template_id)
                          }}
                          className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          title={t('generator.preview', 'Vorschau')}
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {selectedTemplates.includes(template.template_id) && (
                          <CheckCircle className="h-5 w-5 text-primary-600" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Beneficiary Data */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('generator.beneficiary', 'Begünstigter (optional)')}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              {t('generator.beneficiaryHint', 'Wenn ausgefüllt, werden alle Rechnungen an diesen Empfänger adressiert.')}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.beneficiaryName', 'Name / Firma')}
                </label>
                <input
                  type="text"
                  value={config.beneficiary_name}
                  onChange={(e) => setConfig({ ...config, beneficiary_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Muster GmbH"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.street', 'Straße')}
                </label>
                <input
                  type="text"
                  value={config.street}
                  onChange={(e) => setConfig({ ...config, street: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Musterstraße 1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.zip', 'PLZ')}
                </label>
                <input
                  type="text"
                  value={config.zip}
                  onChange={(e) => setConfig({ ...config, zip: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="12345"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.city', 'Stadt')}
                </label>
                <input
                  type="text"
                  value={config.city}
                  onChange={(e) => setConfig({ ...config, city: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Musterstadt"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.vatId', 'USt-IdNr. (optional)')}
                </label>
                <input
                  type="text"
                  value={config.vat_id}
                  onChange={(e) => setConfig({ ...config, vat_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="DE123456789"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Configuration */}
        <div className="space-y-6">
          {/* Basic Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Settings className="h-5 w-5" />
              {t('generator.settings', 'Einstellungen')}
            </h2>

            <div className="space-y-4">
              {/* Project Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
                  <FolderOpen className="h-4 w-4" />
                  {t('generator.project', 'Projekt (optional)')}
                </label>
                <select
                  value={config.project_id}
                  onChange={(e) => setConfig({ ...config, project_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">{t('generator.noProject', 'Kein Projekt')}</option>
                  {(projects || []).map((project: { id: string; title: string }) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Count */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.count', 'Anzahl Rechnungen')}
                </label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={config.count}
                  onChange={(e) => setConfig({ ...config, count: parseInt(e.target.value) || 20 })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              {/* Ruleset */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('generator.ruleset', 'Regelwerk')}
                </label>
                <select
                  value={config.ruleset_id}
                  onChange={(e) => setConfig({ ...config, ruleset_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="DE_USTG">DE_USTG (Deutsches Umsatzsteuergesetz)</option>
                  <option value="EU_VAT">EU_VAT (EU-Mehrwertsteuer)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center justify-between text-left"
            >
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('generator.advanced', 'Erweiterte Einstellungen')}
              </h2>
              <span className="text-gray-400">
                {showAdvanced ? '−' : '+'}
              </span>
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4">
                {/* Error Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                  <p className="text-xs text-gray-500 mt-1">
                    {t('generator.errorRateHint', 'Prozentsatz der Rechnungen mit absichtlichen Fehlern')}
                  </p>
                </div>

                {/* Severity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                  <p className="text-xs text-gray-500 mt-1">
                    {t('generator.aliasNoiseHint', 'Variationen bei Firmennamen und Adressen')}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Selected Templates Summary */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('generator.summary', 'Zusammenfassung')}
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• {config.count} {t('generator.invoices', 'Rechnungen')}</li>
              <li>• {selectedTemplates.length} {t('generator.templatesSelected', 'Templates ausgewählt')}</li>
              <li>• {config.error_rate_total}% {t('generator.withErrors', 'mit Fehlern')}</li>
              {config.beneficiary_name && (
                <li>• {t('generator.to', 'An')}: {config.beneficiary_name}</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {t('generator.templatePreview', 'Template-Vorschau')}: {previewTemplate}
              </h3>
              <button
                onClick={() => setPreviewTemplate(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            <div className="p-4 overflow-auto max-h-[60vh]">
              <iframe
                src={`/api/generator/templates/${previewTemplate}/preview`}
                className="w-full h-96 border border-gray-200 dark:border-gray-700 rounded"
                title="Template Preview"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
