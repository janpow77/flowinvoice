import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, Globe, Cpu, AlertTriangle, RefreshCw, Thermometer, Zap, Moon, Sun, Key, Trash2, Play, Loader2, Server, Cloud } from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import { languages, changeLanguage, getCurrentLanguage, type LanguageCode } from '@/lib/i18n'
import type { ProviderInfo } from '@/lib/types'

interface ProviderConfig {
  id: string
  name: string
  type: 'local' | 'cloud'
  requiresApiKey: boolean
  models: string[]
}

const PROVIDER_CONFIGS: ProviderConfig[] = [
  { id: 'LOCAL_OLLAMA', name: 'Ollama (Lokal)', type: 'local', requiresApiKey: false, models: ['llama3.2', 'mistral', 'qwen2.5'] },
  { id: 'OPENAI', name: 'OpenAI', type: 'cloud', requiresApiKey: true, models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { id: 'ANTHROPIC', name: 'Anthropic (Claude)', type: 'cloud', requiresApiKey: true, models: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'] },
  { id: 'GEMINI', name: 'Google Gemini', type: 'cloud', requiresApiKey: true, models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
]

export default function Settings() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getCurrentLanguage())
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    // Check localStorage or system preference
    const saved = localStorage.getItem('flowaudit_theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  const [uvicornWorkers, setUvicornWorkers] = useState<number>(4)
  const [celeryWorkers, setCeleryWorkers] = useState<number>(4)
  const [showRestartHint, setShowRestartHint] = useState(false)

  // GPU Settings State
  const [gpuMemoryFraction, setGpuMemoryFraction] = useState<number>(0.8)
  const [numParallel, setNumParallel] = useState<number>(2)
  const [contextSize, setContextSize] = useState<number>(4096)
  const [thermalThrottleTemp, setThermalThrottleTemp] = useState<number>(80)

  // API Key State
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({})
  const [testingProvider, setTestingProvider] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { status: string; latency?: number; message?: string }>>({})
  const [savingApiKey, setSavingApiKey] = useState<string | null>(null)

  const { data: providers, isLoading } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => api.getLLMProviders(),
  })

  const { data: health } = useQuery({
    queryKey: ['llm-health'],
    queryFn: () => api.getLLMHealth(),
    refetchInterval: 30000,
  })

  const { data: performanceSettings } = useQuery({
    queryKey: ['performance-settings'],
    queryFn: () => api.getPerformanceSettings(),
  })

  // Sync performance settings to state
  useEffect(() => {
    if (performanceSettings) {
      setUvicornWorkers(performanceSettings.uvicorn_workers)
      setCeleryWorkers(performanceSettings.celery_concurrency)
    }
  }, [performanceSettings])

  // GPU Settings Query
  const { data: gpuSettings } = useQuery({
    queryKey: ['gpu-settings'],
    queryFn: () => api.getGpuSettings(),
  })

  // Sync GPU settings to state
  useEffect(() => {
    if (gpuSettings) {
      setGpuMemoryFraction(gpuSettings.gpu_memory_fraction)
      setNumParallel(gpuSettings.num_parallel)
      setContextSize(gpuSettings.context_size)
      setThermalThrottleTemp(gpuSettings.thermal_throttle_temp)
    }
  }, [gpuSettings])

  // System Metrics (live)
  const { data: systemMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: () => api.getSystemMetrics(),
    refetchInterval: 5000,
  })

  const setDefaultMutation = useMutation({
    mutationFn: (provider: string) => api.setDefaultProvider(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    },
  })

  const updatePerformanceMutation = useMutation({
    mutationFn: (settings: { uvicorn_workers?: number; celery_concurrency?: number }) =>
      api.updatePerformanceSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['performance-settings'] })
      setShowRestartHint(true)
    },
  })

  const handleLanguageChange = (lng: LanguageCode) => {
    changeLanguage(lng)
    setCurrentLang(lng)
  }

  const handleDarkModeToggle = () => {
    const newMode = !darkMode
    setDarkMode(newMode)
    localStorage.setItem('flowaudit_theme', newMode ? 'dark' : 'light')

    // Apply dark mode class to document
    if (newMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Apply dark mode on mount
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  const handlePerformanceSave = () => {
    updatePerformanceMutation.mutate({
      uvicorn_workers: uvicornWorkers,
      celery_concurrency: celeryWorkers,
    })
  }

  // GPU Settings Mutation
  const updateGpuMutation = useMutation({
    mutationFn: (settings: {
      gpu_memory_fraction?: number
      num_parallel?: number
      context_size?: number
      thermal_throttle_temp?: number
    }) => api.updateGpuSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gpu-settings'] })
      setShowRestartHint(true)
    },
  })

  // API Key Mutations
  const saveApiKeyMutation = useMutation({
    mutationFn: ({ provider, apiKey }: { provider: string; apiKey: string }) =>
      api.setProviderApiKey(provider, apiKey),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      queryClient.invalidateQueries({ queryKey: ['llm-health'] })
      setApiKeyInputs((prev) => ({ ...prev, [variables.provider]: '' }))
      setSavingApiKey(null)
    },
    onError: () => {
      setSavingApiKey(null)
    },
  })

  const deleteApiKeyMutation = useMutation({
    mutationFn: (provider: string) => api.deleteProviderApiKey(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      queryClient.invalidateQueries({ queryKey: ['llm-health'] })
    },
  })

  const handleTestConnection = async (provider: string) => {
    setTestingProvider(provider)
    try {
      const result = await api.testProvider(provider)
      setTestResults((prev) => ({
        ...prev,
        [provider]: {
          status: result.status,
          latency: result.latency_ms,
          message: result.message,
        },
      }))
    } catch {
      setTestResults((prev) => ({
        ...prev,
        [provider]: { status: 'error', message: 'Test fehlgeschlagen' },
      }))
    } finally {
      setTestingProvider(null)
    }
  }

  const handleSaveApiKey = (provider: string) => {
    const apiKey = apiKeyInputs[provider]
    if (apiKey && apiKey.trim()) {
      setSavingApiKey(provider)
      saveApiKeyMutation.mutate({ provider, apiKey: apiKey.trim() })
    }
  }

  const handleGpuSave = () => {
    updateGpuMutation.mutate({
      gpu_memory_fraction: gpuMemoryFraction,
      num_parallel: numParallel,
      context_size: contextSize,
      thermal_throttle_temp: thermalThrottleTemp,
    })
  }

  if (isLoading) {
    return <div className="animate-pulse">{t('common.loading')}</div>
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">{t('settings.title')}</h2>

      {/* Language Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.language')}</h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.languageDescription')}
        </p>

        <div className="flex gap-4">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-colors',
                currentLang === lang.code
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <span className="text-2xl">{lang.flag}</span>
              <span className={clsx(
                'font-medium',
                currentLang === lang.code ? 'text-primary-700' : 'text-gray-700'
              )}>
                {lang.name}
              </span>
              {currentLang === lang.code && (
                <CheckCircle className="h-5 w-5 text-primary-600" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Dark Mode Toggle */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          {darkMode ? (
            <Moon className="h-5 w-5 text-primary-600" />
          ) : (
            <Sun className="h-5 w-5 text-primary-600" />
          )}
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('settings.appearance')}</h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          {t('settings.appearanceDescription')}
        </p>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">{t('settings.darkMode')}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t('settings.darkModeDescription')}
            </p>
          </div>
          <button
            onClick={handleDarkModeToggle}
            className={clsx(
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              darkMode ? 'bg-primary-600' : 'bg-gray-200'
            )}
          >
            <span
              className={clsx(
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                darkMode ? 'translate-x-5' : 'translate-x-0'
              )}
            />
          </button>
        </div>
      </div>

      {/* LLM Provider */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('settings.llmProvider')}</h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          {t('settings.llmProviderDescription')}
        </p>

        <div className="space-y-4">
          {PROVIDER_CONFIGS.map((config) => {
            const providerData = providers?.find((p: ProviderInfo) => p.provider === config.id)
            const isHealthy = health?.[config.id]
            const isDefault = providerData?.is_default
            const testResult = testResults[config.id]

            return (
              <div
                key={config.id}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all',
                  isDefault
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {config.type === 'local' ? (
                      <Server className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                    ) : (
                      <Cloud className="h-5 w-5 text-blue-600" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{config.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {config.type === 'local' ? t('settings.localProvider') : t('settings.cloudProvider')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isHealthy ? (
                      <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        {t('common.online')}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                        {t('common.offline')}
                      </span>
                    )}
                    {isDefault && (
                      <span className="text-xs bg-primary-500 text-white px-2 py-1 rounded">
                        {t('settings.currentDefault')}
                      </span>
                    )}
                  </div>
                </div>

                {/* Models */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {config.models.map((model) => (
                    <span
                      key={model}
                      className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded"
                    >
                      {model}
                    </span>
                  ))}
                </div>

                {/* API Key Input for Cloud Providers */}
                {config.requiresApiKey && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex items-center gap-2 mb-2">
                      <Key className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t('settings.apiKey')}
                      </span>
                      {providerData?.is_default !== undefined && (
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded',
                          isHealthy
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                        )}>
                          {isHealthy ? t('settings.apiKeySet') : t('settings.apiKeyNotSet')}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder={t('settings.apiKeyPlaceholder')}
                        value={apiKeyInputs[config.id] || ''}
                        onChange={(e) => setApiKeyInputs((prev) => ({ ...prev, [config.id]: e.target.value }))}
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                      />
                      <button
                        onClick={() => handleSaveApiKey(config.id)}
                        disabled={!apiKeyInputs[config.id] || savingApiKey === config.id}
                        className="px-3 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        {savingApiKey === config.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircle className="h-4 w-4" />
                        )}
                        {t('common.save')}
                      </button>
                      {isHealthy && (
                        <button
                          onClick={() => deleteApiKeyMutation.mutate(config.id)}
                          className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                          title={t('settings.deleteApiKey')}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 flex items-center gap-2">
                  <button
                    onClick={() => handleTestConnection(config.id)}
                    disabled={testingProvider === config.id}
                    className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-1"
                  >
                    {testingProvider === config.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    {t('settings.testConnection')}
                  </button>
                  {!isDefault && (
                    <button
                      onClick={() => setDefaultMutation.mutate(config.id)}
                      className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      {t('settings.selectAsDefault')}
                    </button>
                  )}
                  {testResult && (
                    <span className={clsx(
                      'ml-auto text-xs px-2 py-1 rounded',
                      testResult.status === 'ok'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    )}>
                      {testResult.status === 'ok' ? t('settings.connectionSuccess') : t('settings.connectionFailed')}
                      {testResult.latency && ` (${testResult.latency}ms)`}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Ruleset Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('settings.defaultRuleset')}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          {t('settings.defaultRulesetDescription')}
        </p>

        <select className="w-full md:w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
          <option value="DE_USTG">{t('rulesets.DE_USTG')}</option>
          <option value="EU_VAT">{t('rulesets.EU_VAT')}</option>
          <option value="UK_VAT">{t('rulesets.UK_VAT')}</option>
        </select>
      </div>

      {/* RAG Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('settings.ragSettings')}</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          {t('settings.ragDescription')}
        </p>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{t('settings.autoLearning')}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('settings.autoLearningDescription')}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{t('settings.fewShotExamples')}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('settings.fewShotDescription')}
              </p>
            </div>
            <select className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
              <option value="3">3 {t('settings.examples')}</option>
              <option value="5">5 {t('settings.examples')}</option>
              <option value="10">10 {t('settings.examples')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Performance Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.performance')}</h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.performanceDescription')}
        </p>

        {showRestartHint && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">{t('settings.restartRequired')}</p>
              <p className="text-xs text-amber-600">{t('settings.restartHint')}</p>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.apiWorkers')}</p>
              <p className="text-sm text-gray-500">
                {t('settings.apiWorkersDescription')}
              </p>
            </div>
            <select
              value={uvicornWorkers}
              onChange={(e) => setUvicornWorkers(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                <option key={n} value={n}>
                  {n} {t('settings.workers')}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.backgroundWorkers')}</p>
              <p className="text-sm text-gray-500">
                {t('settings.backgroundWorkersDescription')}
              </p>
            </div>
            <select
              value={celeryWorkers}
              onChange={(e) => setCeleryWorkers(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                <option key={n} value={n}>
                  {n} {t('settings.workers')}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={handlePerformanceSave}
              disabled={updatePerformanceMutation.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              {updatePerformanceMutation.isPending && (
                <RefreshCw className="h-4 w-4 animate-spin" />
              )}
              {t('common.save')}
            </button>
          </div>
        </div>
      </div>

      {/* GPU & Thermal Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-orange-600" />
          <h3 className="text-lg font-semibold text-gray-900">{t('settings.gpuSettings')}</h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.gpuDescription')}
        </p>

        {/* Live System Status */}
        {systemMetrics && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Thermometer className="h-4 w-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">{t('settings.liveStatus')}</span>
              <span className={clsx(
                'text-xs px-2 py-0.5 rounded-full',
                systemMetrics.status === 'healthy' ? 'bg-green-100 text-green-700' :
                systemMetrics.status === 'warning' ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              )}>
                {systemMetrics.status === 'healthy' ? t('settings.statusHealthy') :
                 systemMetrics.status === 'warning' ? t('settings.statusWarning') :
                 t('settings.statusCritical')}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-gray-500">CPU</span>
                <p className="font-medium">{systemMetrics.cpu?.percent?.toFixed(1)}%</p>
                {systemMetrics.cpu?.temperature && (
                  <p className={clsx(
                    systemMetrics.cpu.temperature > 80 ? 'text-red-600' : 'text-gray-600'
                  )}>{systemMetrics.cpu.temperature.toFixed(1)}°C</p>
                )}
              </div>
              <div>
                <span className="text-gray-500">RAM</span>
                <p className="font-medium">{systemMetrics.ram?.percent?.toFixed(1)}%</p>
                <p className="text-gray-600">{systemMetrics.ram?.used_gb?.toFixed(1)} / {systemMetrics.ram?.total_gb?.toFixed(1)} GB</p>
              </div>
              {systemMetrics.gpu?.percent !== null && (
                <>
                  <div>
                    <span className="text-gray-500">GPU</span>
                    <p className="font-medium">{systemMetrics.gpu?.percent?.toFixed(1)}%</p>
                    {systemMetrics.gpu?.temperature && (
                      <p className={clsx(
                        systemMetrics.gpu.temperature > thermalThrottleTemp ? 'text-red-600' : 'text-gray-600'
                      )}>{systemMetrics.gpu.temperature.toFixed(1)}°C</p>
                    )}
                  </div>
                  <div>
                    <span className="text-gray-500">VRAM</span>
                    <p className="font-medium">
                      {systemMetrics.gpu?.memory_used_mb ? (systemMetrics.gpu.memory_used_mb / 1024).toFixed(1) : '?'} GB
                    </p>
                    <p className="text-gray-600">
                      / {systemMetrics.gpu?.memory_total_mb ? (systemMetrics.gpu.memory_total_mb / 1024).toFixed(1) : '?'} GB
                    </p>
                  </div>
                </>
              )}
            </div>
            {systemMetrics.throttle?.active && (
              <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700">
                <strong>{t('settings.throttleActive')}:</strong> {systemMetrics.throttle.reason}
              </div>
            )}
          </div>
        )}

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.gpuMemory')}</p>
              <p className="text-sm text-gray-500">{t('settings.gpuMemoryDescription')}</p>
            </div>
            <select
              value={gpuMemoryFraction}
              onChange={(e) => setGpuMemoryFraction(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value={0.5}>50%</option>
              <option value={0.6}>60%</option>
              <option value={0.7}>70%</option>
              <option value={0.8}>80%</option>
              <option value={0.9}>90%</option>
              <option value={1.0}>100%</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.parallelRequests')}</p>
              <p className="text-sm text-gray-500">{t('settings.parallelRequestsDescription')}</p>
            </div>
            <select
              value={numParallel}
              onChange={(e) => setNumParallel(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              {[1, 2, 3, 4].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.contextSize')}</p>
              <p className="text-sm text-gray-500">{t('settings.contextSizeDescription')}</p>
            </div>
            <select
              value={contextSize}
              onChange={(e) => setContextSize(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value={2048}>2048</option>
              <option value={4096}>4096</option>
              <option value={8192}>8192</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.thermalThrottle')}</p>
              <p className="text-sm text-gray-500">{t('settings.thermalThrottleDescription')}</p>
            </div>
            <select
              value={thermalThrottleTemp}
              onChange={(e) => setThermalThrottleTemp(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value={70}>70°C ({t('settings.conservative')})</option>
              <option value={75}>75°C</option>
              <option value={80}>80°C ({t('settings.default')})</option>
              <option value={85}>85°C</option>
              <option value={90}>90°C ({t('settings.aggressive')})</option>
            </select>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={handleGpuSave}
              disabled={updateGpuMutation.isPending}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 flex items-center gap-2"
            >
              {updateGpuMutation.isPending && (
                <RefreshCw className="h-4 w-4 animate-spin" />
              )}
              {t('common.save')}
            </button>
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.systemInfo')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <p className="text-gray-500">{t('settings.version')}</p>
            <p className="font-medium">0.1.0</p>
          </div>
          <div>
            <p className="text-gray-500">{t('settings.backend')}</p>
            <p className="font-medium text-green-600">{t('common.online')}</p>
          </div>
          <div>
            <p className="text-gray-500">Ollama (LLM)</p>
            {health?.LOCAL_OLLAMA ? (
              <p className="font-medium text-green-600 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                {t('common.online')}
              </p>
            ) : (
              <p className="font-medium text-red-600 flex items-center gap-1">
                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                {t('common.offline')}
              </p>
            )}
          </div>
          <div>
            <p className="text-gray-500">{t('settings.chromadb')}</p>
            <p className="font-medium text-green-600">{t('common.online')}</p>
          </div>
          <div>
            <p className="text-gray-500">{t('settings.redis')}</p>
            <p className="font-medium text-green-600">{t('common.online')}</p>
          </div>
        </div>
      </div>

      {/* Contact */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.contact')}</h3>
        <div className="text-sm">
          <p className="text-gray-500 mb-1">{t('settings.contactPerson')}</p>
          <p className="font-medium text-gray-900">Jan Riener</p>
          <a
            href="mailto:jan.riener@vwvg.de"
            className="text-primary-600 hover:text-primary-700 hover:underline"
          >
            jan.riener@vwvg.de
          </a>
        </div>
      </div>
    </div>
  )
}
