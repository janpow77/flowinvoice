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
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  const defaultProvider = providers?.find((p: ProviderInfo & { id?: string }) => p.is_default)
  // Get provider ID (API uses 'id', type definition uses 'provider')
  const defaultProviderId = defaultProvider?.id || defaultProvider?.provider

  return (
    <div className="space-y-6">
      {/* KI-Status Card */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg border border-primary-200 dark:border-primary-800 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-primary-900 dark:text-primary-100 flex items-center gap-2">
            <Zap className="h-4 w-4" />
            KI-Konfiguration
          </h3>
          <button
            onClick={() => refetchHealth()}
            className="text-xs text-primary-600 hover:text-primary-800 flex items-center gap-1"
          >
            <RefreshCw className="h-3 w-3" />
            Aktualisieren
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-xs">Aktiver Provider</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {defaultProviderId ? PROVIDER_CONFIGS.find(c => c.id === defaultProviderId)?.name : '-'}
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-xs">Ollama Status</p>
            <p className="font-medium flex items-center gap-1.5">
              <span
                className={clsx(
                  'w-2 h-2 rounded-full',
                  ollamaStatus === 'active' && 'bg-green-500',
                  ollamaStatus === 'inactive' && 'bg-gray-400',
                  ollamaStatus === 'offline' && 'bg-red-500'
                )}
              />
              <span
                className={clsx(
                  ollamaStatus === 'active' && 'text-green-700 dark:text-green-400',
                  ollamaStatus === 'inactive' && 'text-gray-600 dark:text-gray-400',
                  ollamaStatus === 'offline' && 'text-red-700 dark:text-red-400'
                )}
              >
                {ollamaStatus === 'active' && 'Aktiv'}
                {ollamaStatus === 'inactive' && 'Inaktiv'}
                {ollamaStatus === 'offline' && 'Offline'}
              </span>
            </p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-xs">Aktives Profil</p>
            <p className="font-medium text-gray-900 dark:text-white">Standard-Profil</p>
          </div>
          <div>
            <p className="text-gray-500 dark:text-gray-400 text-xs">Zuletzt geprüft</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {lastHealthCheck ? lastHealthCheck.toLocaleTimeString('de-DE') : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Provider Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('settings.llmProvider')}
          </h3>
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
            const isOllama = config.id === 'LOCAL_OLLAMA'

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
                    {/* Ollama-specific status */}
                    {isOllama ? (
                      <span
                        className={clsx(
                          'flex items-center gap-1 text-xs px-2 py-1 rounded-full',
                          ollamaStatus === 'active' && 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
                          ollamaStatus === 'inactive' && 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
                          ollamaStatus === 'offline' && 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                        )}
                      >
                        <span
                          className={clsx(
                            'w-2 h-2 rounded-full',
                            ollamaStatus === 'active' && 'bg-green-500',
                            ollamaStatus === 'inactive' && 'bg-gray-400',
                            ollamaStatus === 'offline' && 'bg-red-500'
                          )}
                        />
                        {ollamaStatus === 'active' && 'Aktiv'}
                        {ollamaStatus === 'inactive' && 'Inaktiv'}
                        {ollamaStatus === 'offline' && 'Offline'}
                      </span>
                    ) : (
                      <>
                        {isHealthy ? (
                          <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                            <span className="w-2 h-2 bg-green-500 rounded-full" />
                            {t('common.online')}
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-gray-400">
                            <span className="w-2 h-2 bg-gray-400 rounded-full" />
                            {t('common.offline')}
                          </span>
                        )}
                      </>
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
                        <span
                          className={clsx(
                            'text-xs px-2 py-0.5 rounded',
                            isHealthy
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
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
                    <span
                      className={clsx(
                        'ml-auto text-xs px-2 py-1 rounded',
                        testResult.status === 'ok'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
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

      {/* Profile Selection (Read-only for non-admin) */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Aktives Profil
            </h3>
          </div>
          {!isAdmin && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <Lock className="h-3 w-3" />
              Zentral durch Admin festgelegt
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Profile definieren die LLM-Parameter für die Dokumentenanalyse.
        </p>

        <select
          disabled={!isAdmin}
          className={clsx(
            'w-full md:w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500',
            !isAdmin && 'opacity-60 cursor-not-allowed'
          )}
        >
          <option value="default">Standard-Profil</option>
        </select>

        {isAdmin && (
          <p className="mt-2 text-xs text-gray-400">
            Profile können im Tab "Profile & Modelle" verwaltet werden.
          </p>
        )}
      </div>

      {/* RAG Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('settings.ragSettings')}
        </h3>
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
              <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600" />
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
    </div>
  )
}
