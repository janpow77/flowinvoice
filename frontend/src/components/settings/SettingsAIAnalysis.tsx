/**
 * SettingsAIAnalysis - KI-Analyse Einstellungen
 *
 * Provider, Profile und RAG-Einstellungen.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  Cpu,
  Server,
  Cloud,
  Globe,
  Key,
  Trash2,
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Zap,
  Lock,
  RefreshCw,
} from 'lucide-react'
import { api } from '@/lib/api'
import type { ProviderInfo } from '@/lib/types'
import type { OllamaStatus } from '@/lib/settings-types'

interface ProviderConfig {
  id: string
  name: string
  category: 'local' | 'western' | 'chinese'
  requiresApiKey: boolean
  requiresSecretKey?: boolean
  models: string[]
}

interface ProviderCategory {
  id: 'local' | 'western' | 'chinese'
  name: string
  icon: 'server' | 'cloud' | 'globe'
  description: string
}

const PROVIDER_CATEGORIES: ProviderCategory[] = [
  { id: 'local', name: 'Lokale Provider', icon: 'server', description: 'LLMs auf eigenem Server' },
  { id: 'western', name: 'Westliche Cloud-Provider', icon: 'cloud', description: 'OpenAI, Anthropic, Google' },
  { id: 'chinese', name: 'Chinesische Provider', icon: 'globe', description: 'Zhipu, Baidu, Alibaba, DeepSeek' },
]

const PROVIDER_CONFIGS: ProviderConfig[] = [
  // Lokale Provider
  { id: 'LOCAL_OLLAMA', name: 'Ollama (Lokal)', category: 'local', requiresApiKey: false, models: ['llama3.2', 'llama3.1:8b', 'mistral', 'qwen2.5'] },
  { id: 'LOCAL_CUSTOM', name: 'Custom API (Lokal)', category: 'local', requiresApiKey: false, models: ['Konfigurierbar'] },
  // Westliche Cloud-Provider
  { id: 'OPENAI', name: 'OpenAI', category: 'western', requiresApiKey: true, models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { id: 'ANTHROPIC', name: 'Anthropic Claude', category: 'western', requiresApiKey: true, models: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'] },
  { id: 'GEMINI', name: 'Google Gemini', category: 'western', requiresApiKey: true, models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
  // Chinesische Provider
  { id: 'ZHIPU_GLM', name: 'ChatGLM / GLM-4 (Zhipu AI)', category: 'chinese', requiresApiKey: true, models: ['glm-4', 'glm-4-flash', 'glm-4v'] },
  { id: 'BAIDU_ERNIE', name: 'ERNIE Bot (Baidu)', category: 'chinese', requiresApiKey: true, requiresSecretKey: true, models: ['ernie-4.0-8k', 'ernie-4.0-turbo', 'ernie-3.5-8k'] },
  { id: 'ALIBABA_QWEN', name: 'Qwen / Tongyi (Alibaba)', category: 'chinese', requiresApiKey: true, models: ['qwen-max', 'qwen-plus', 'qwen-turbo'] },
  { id: 'DEEPSEEK', name: 'DeepSeek', category: 'chinese', requiresApiKey: true, models: ['deepseek-chat', 'deepseek-coder'] },
]

interface Props {
  isAdmin: boolean
}

export function SettingsAIAnalysis({ isAdmin }: Props) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({})
  const [testingProvider, setTestingProvider] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { status: string; latency?: number; message?: string }>>({})
  const [savingApiKey, setSavingApiKey] = useState<string | null>(null)
  const [lastHealthCheck, setLastHealthCheck] = useState<Date | null>(null)

  const { data: providers, isLoading } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => api.getLLMProviders(),
  })

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['llm-health'],
    queryFn: () => api.getLLMHealth(),
    refetchInterval: 30000,
  })

  useEffect(() => {
    if (health) {
      setLastHealthCheck(new Date())
    }
  }, [health])

  const setDefaultMutation = useMutation({
    mutationFn: (provider: string) => api.setDefaultProvider(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    },
  })

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

  // Determine Ollama status (Active/Inactive/Offline)
  const getOllamaStatus = (): OllamaStatus => {
    // health is an array of provider health statuses
    const ollamaHealth = health?.find((p: { id: string; healthy: boolean }) => p.id === 'LOCAL_OLLAMA')
    const ollamaHealthy = ollamaHealth?.healthy
    // providers array uses 'id' field (from API response)
    const ollamaProvider = providers?.find((p: ProviderInfo & { id?: string }) =>
      p.id === 'LOCAL_OLLAMA' || p.provider === 'LOCAL_OLLAMA'
    )
    const isDefault = ollamaProvider?.is_default

    if (!ollamaHealthy) return 'offline'
    if (isDefault) return 'active'
    return 'inactive'
  }

  const ollamaStatus = getOllamaStatus()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
      </div>
    )
  }

  const defaultProvider = providers?.find((p: ProviderInfo & { id?: string }) => p.is_default)
  // Get provider ID (API uses 'id', type definition uses 'provider')
  const defaultProviderId = defaultProvider?.id || defaultProvider?.provider

  return (
    <div className="space-y-6">
      {/* KI-Status Card */}
      <div className="bg-theme-selected rounded-lg border border-accent-primary/30 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-accent-primary flex items-center gap-2">
            <Zap className="h-4 w-4" />
            KI-Konfiguration
          </h3>
          <button
            onClick={() => refetchHealth()}
            className="text-xs text-accent-primary hover:text-accent-primary-hover flex items-center gap-1"
          >
            <RefreshCw className="h-3 w-3" />
            Aktualisieren
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-theme-text-muted text-xs">Aktiver Provider</p>
            <p className="font-medium text-theme-text-primary">
              {defaultProviderId ? PROVIDER_CONFIGS.find(c => c.id === defaultProviderId)?.name : '-'}
            </p>
          </div>
          <div>
            <p className="text-theme-text-muted text-xs">Ollama Status</p>
            <p className="font-medium flex items-center gap-1.5">
              <span
                className={clsx(
                  'w-2 h-2 rounded-full',
                  ollamaStatus === 'active' && 'bg-status-success',
                  ollamaStatus === 'inactive' && 'bg-theme-text-muted',
                  ollamaStatus === 'offline' && 'bg-status-danger'
                )}
              />
              <span
                className={clsx(
                  ollamaStatus === 'active' && 'text-status-success',
                  ollamaStatus === 'inactive' && 'text-theme-text-muted',
                  ollamaStatus === 'offline' && 'text-status-danger'
                )}
              >
                {ollamaStatus === 'active' && 'Aktiv'}
                {ollamaStatus === 'inactive' && 'Inaktiv'}
                {ollamaStatus === 'offline' && 'Offline'}
              </span>
            </p>
          </div>
          <div>
            <p className="text-theme-text-muted text-xs">Aktives Profil</p>
            <p className="font-medium text-theme-text-primary">Standard-Profil</p>
          </div>
          <div>
            <p className="text-theme-text-muted text-xs">Zuletzt geprüft</p>
            <p className="font-medium text-theme-text-primary">
              {lastHealthCheck ? lastHealthCheck.toLocaleTimeString('de-DE') : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Provider Selection - Grouped by Category */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-accent-primary" />
          <h3 className="text-lg font-semibold text-theme-text-primary">
            {t('settings.llmProvider')}
          </h3>
        </div>
        <p className="text-sm text-theme-text-muted mb-6">
          {t('settings.llmProviderDescription')}
        </p>

        <div className="space-y-8">
          {PROVIDER_CATEGORIES.map((category) => {
            const categoryProviders = PROVIDER_CONFIGS.filter(p => p.category === category.id)
            const CategoryIcon = category.icon === 'server' ? Server : category.icon === 'cloud' ? Cloud : Globe

            return (
              <div key={category.id}>
                {/* Category Header */}
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-theme-border-default">
                  <CategoryIcon className={clsx(
                    'h-5 w-5',
                    category.id === 'local' && 'text-status-success',
                    category.id === 'western' && 'text-status-info',
                    category.id === 'chinese' && 'text-status-warning'
                  )} />
                  <div>
                    <h4 className="font-semibold text-theme-text-primary">{category.name}</h4>
                    <p className="text-xs text-theme-text-muted">{category.description}</p>
                  </div>
                </div>

                {/* Providers in this category */}
                <div className="space-y-3">
                  {categoryProviders.map((config) => {
                    const providerData = providers?.find((p: ProviderInfo & { id?: string }) =>
                      p.id === config.id || p.provider === config.id
                    )
                    const healthData = health?.find((h: { id: string }) => h.id === config.id)
                    const isHealthy = healthData?.healthy
                    const isDefault = providerData?.is_default
                    const testResult = testResults[config.id]
                    const isOllama = config.id === 'LOCAL_OLLAMA'

                    return (
                      <div
                        key={config.id}
                        className={clsx(
                          'p-4 rounded-lg border-2 transition-all',
                          isDefault
                            ? 'border-accent-primary bg-accent-primary/10'
                            : 'border-theme-border-default hover:border-theme-border-hover'
                        )}
                      >
                        {/* Header */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div>
                              <p className="font-medium text-theme-text-primary">{config.name}</p>
                              <p className="text-xs text-theme-text-muted">
                                {config.category === 'local' ? 'Lokal' : 'Cloud-API'}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {/* Ollama-specific status */}
                            {isOllama ? (
                              <span
                                className={clsx(
                                  'flex items-center gap-1 text-xs px-2 py-1 rounded-full',
                                  ollamaStatus === 'active' && 'bg-status-success-bg text-status-success',
                                  ollamaStatus === 'inactive' && 'bg-theme-hover text-theme-text-muted',
                                  ollamaStatus === 'offline' && 'bg-status-danger-bg text-status-danger'
                                )}
                              >
                                <span
                                  className={clsx(
                                    'w-2 h-2 rounded-full',
                                    ollamaStatus === 'active' && 'bg-status-success',
                                    ollamaStatus === 'inactive' && 'bg-theme-text-muted',
                                    ollamaStatus === 'offline' && 'bg-status-danger'
                                  )}
                                />
                                {ollamaStatus === 'active' && 'Aktiv'}
                                {ollamaStatus === 'inactive' && 'Inaktiv'}
                                {ollamaStatus === 'offline' && 'Offline'}
                              </span>
                            ) : (
                              <>
                                {isHealthy ? (
                                  <span className="flex items-center gap-1 text-xs text-status-success">
                                    <span className="w-2 h-2 bg-status-success rounded-full" />
                                    {t('common.online')}
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-xs text-theme-text-muted">
                                    <span className="w-2 h-2 bg-theme-text-muted rounded-full" />
                                    {t('common.offline')}
                                  </span>
                                )}
                              </>
                            )}
                            {isDefault && (
                              <span className="text-xs bg-accent-primary text-white px-2 py-1 rounded">
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
                              className="text-xs bg-theme-hover text-theme-text-secondary px-2 py-0.5 rounded"
                            >
                              {model}
                            </span>
                          ))}
                        </div>

                        {/* API Key Input for Cloud Providers */}
                        {config.requiresApiKey && (
                          <div className="mt-3 pt-3 border-t border-theme-border-default">
                            <div className="flex items-center gap-2 mb-2">
                              <Key className="h-4 w-4 text-theme-text-muted" />
                              <span className="text-sm font-medium text-theme-text-secondary">
                                {t('settings.apiKey')}
                                {config.requiresSecretKey && ' + Secret Key'}
                              </span>
                              {providerData && (
                                <span
                                  className={clsx(
                                    'text-xs px-2 py-0.5 rounded',
                                    isHealthy
                                      ? 'bg-status-success-bg text-status-success'
                                      : 'bg-theme-hover text-theme-text-muted'
                                  )}
                                >
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
                                className="flex-1 px-3 py-2 text-sm border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                              />
                              <button
                                onClick={() => handleSaveApiKey(config.id)}
                                disabled={!apiKeyInputs[config.id] || savingApiKey === config.id}
                                className="px-3 py-2 bg-accent-primary text-white text-sm rounded-lg hover:bg-accent-primary-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
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
                                  className="px-3 py-2 text-status-danger hover:bg-status-danger-bg rounded-lg"
                                  title={t('settings.deleteApiKey')}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="mt-3 pt-3 border-t border-theme-border-default flex items-center gap-2">
                          <button
                            onClick={() => handleTestConnection(config.id)}
                            disabled={testingProvider === config.id}
                            className="px-3 py-1.5 text-sm border border-theme-border-default rounded-lg hover:bg-theme-hover flex items-center gap-1"
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
                              className="px-3 py-1.5 text-sm bg-theme-hover text-theme-text-secondary rounded-lg hover:bg-theme-hover"
                            >
                              {t('settings.selectAsDefault')}
                            </button>
                          )}
                          {testResult && (
                            <span
                              className={clsx(
                                'ml-auto text-xs px-2 py-1 rounded',
                                testResult.status === 'ok'
                                  ? 'bg-status-success-bg text-status-success'
                                  : 'bg-status-danger-bg text-status-danger'
                              )}
                            >
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
            )
          })}
        </div>
      </div>

      {/* Profile Selection (Read-only for non-admin) */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-accent-primary" />
            <h3 className="text-lg font-semibold text-theme-text-primary">
              Aktives Profil
            </h3>
          </div>
          {!isAdmin && (
            <span className="flex items-center gap-1 text-xs text-theme-text-muted">
              <Lock className="h-3 w-3" />
              Zentral durch Admin festgelegt
            </span>
          )}
        </div>
        <p className="text-sm text-theme-text-muted mb-4">
          Profile definieren die LLM-Parameter für die Dokumentenanalyse.
        </p>

        <select
          disabled={!isAdmin}
          className={clsx(
            'w-full md:w-64 px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary',
            !isAdmin && 'opacity-60 cursor-not-allowed'
          )}
        >
          <option value="default">Standard-Profil</option>
        </select>

        {isAdmin && (
          <p className="mt-2 text-xs text-theme-text-muted">
            Profile können im Tab "Profile & Modelle" verwaltet werden.
          </p>
        )}
      </div>

      {/* RAG Settings */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <h3 className="text-lg font-semibold text-theme-text-primary mb-4">
          {t('settings.ragSettings')}
        </h3>
        <p className="text-sm text-theme-text-muted mb-4">
          {t('settings.ragDescription')}
        </p>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-theme-text-primary">{t('settings.autoLearning')}</p>
              <p className="text-sm text-theme-text-muted">
                {t('settings.autoLearningDescription')}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-theme-hover peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-theme-border-default after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary" />
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-theme-text-primary">{t('settings.fewShotExamples')}</p>
              <p className="text-sm text-theme-text-muted">
                {t('settings.fewShotDescription')}
              </p>
            </div>
            <select className="px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary">
              <option value="3">3 {t('settings.examples')}</option>
              <option value="5">5 {t('settings.examples')}</option>
              <option value="10">10 {t('settings.examples')}</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}
