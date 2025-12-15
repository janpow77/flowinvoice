import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, Globe, Cpu, AlertTriangle, RefreshCw, Thermometer, Zap } from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import { languages, changeLanguage, getCurrentLanguage, type LanguageCode } from '@/lib/i18n'
import type { ProviderInfo } from '@/lib/types'

export default function Settings() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getCurrentLanguage())
  const [uvicornWorkers, setUvicornWorkers] = useState<number>(4)
  const [celeryWorkers, setCeleryWorkers] = useState<number>(4)
  const [showRestartHint, setShowRestartHint] = useState(false)

  // GPU Settings State
  const [gpuMemoryFraction, setGpuMemoryFraction] = useState<number>(0.8)
  const [numParallel, setNumParallel] = useState<number>(2)
  const [contextSize, setContextSize] = useState<number>(4096)
  const [thermalThrottleTemp, setThermalThrottleTemp] = useState<number>(80)

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
    onSuccess: (data: { uvicorn_workers: number; celery_concurrency: number }) => {
      setUvicornWorkers(data.uvicorn_workers)
      setCeleryWorkers(data.celery_concurrency)
    },
  })

  // GPU Settings Query
  const { data: gpuSettings } = useQuery({
    queryKey: ['gpu-settings'],
    queryFn: () => api.getGpuSettings(),
    onSuccess: (data: {
      gpu_memory_fraction: number
      num_parallel: number
      context_size: number
      thermal_throttle_temp: number
    }) => {
      setGpuMemoryFraction(data.gpu_memory_fraction)
      setNumParallel(data.num_parallel)
      setContextSize(data.context_size)
      setThermalThrottleTemp(data.thermal_throttle_temp)
    },
  })

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

      {/* LLM Provider */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.llmProvider')}</h3>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.llmProviderDescription')}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers?.map((provider: ProviderInfo) => {
            const isHealthy = health?.[provider.provider]
            const isSelected = provider.is_default

            return (
              <div
                key={provider.provider}
                className={clsx(
                  'p-4 rounded-lg border-2 cursor-pointer transition-colors',
                  isSelected
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                )}
                onClick={() => setDefaultMutation.mutate(provider.provider)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{provider.provider}</p>
                    <p className="text-sm text-gray-500">{provider.default_model}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {isHealthy ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                    {isSelected && (
                      <span className="text-xs bg-primary-500 text-white px-2 py-1 rounded">
                        {t('common.active')}
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap gap-1">
                  {provider.models?.slice(0, 3).map((model: string) => (
                    <span
                      key={model}
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Ruleset Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.defaultRuleset')}</h3>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.defaultRulesetDescription')}
        </p>

        <select className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
          <option value="DE_USTG">{t('rulesets.DE_USTG')}</option>
          <option value="EU_VAT">{t('rulesets.EU_VAT')}</option>
          <option value="UK_VAT">{t('rulesets.UK_VAT')}</option>
        </select>
      </div>

      {/* RAG Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.ragSettings')}</h3>
        <p className="text-sm text-gray-500 mb-4">
          {t('settings.ragDescription')}
        </p>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.autoLearning')}</p>
              <p className="text-sm text-gray-500">
                {t('settings.autoLearningDescription')}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{t('settings.fewShotExamples')}</p>
              <p className="text-sm text-gray-500">
                {t('settings.fewShotDescription')}
              </p>
            </div>
            <select className="px-3 py-2 border border-gray-300 rounded-lg">
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500">{t('settings.version')}</p>
            <p className="font-medium">0.1.0</p>
          </div>
          <div>
            <p className="text-gray-500">{t('settings.backend')}</p>
            <p className="font-medium text-green-600">{t('common.online')}</p>
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
