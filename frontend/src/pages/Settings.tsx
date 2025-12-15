import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, Globe, Cpu, AlertTriangle, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import { languages, changeLanguage, getCurrentLanguage, type LanguageCode } from '@/lib/i18n'

export default function Settings() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getCurrentLanguage())
  const [uvicornWorkers, setUvicornWorkers] = useState<number>(4)
  const [celeryWorkers, setCeleryWorkers] = useState<number>(4)
  const [showRestartHint, setShowRestartHint] = useState(false)

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
          {providers?.map((provider: any) => {
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
