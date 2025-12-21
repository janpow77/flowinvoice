import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Shield,
  Brain,
  TrendingUp,
  Save,
  RotateCcw,
  Info,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

interface CheckerConfig {
  enabled: boolean
  severity_threshold: string
  custom_rules?: Record<string, unknown>
}

interface CheckersSettingsState {
  risk_checker: CheckerConfig & {
    check_self_invoice: boolean
    check_duplicate_invoice: boolean
    check_round_amounts: boolean
    check_weekend_dates: boolean
    round_amount_threshold: number
  }
  semantic_checker: CheckerConfig & {
    check_project_relevance: boolean
    check_description_quality: boolean
    min_relevance_score: number
    use_rag_context: boolean
  }
  economic_checker: CheckerConfig & {
    check_budget_limits: boolean
    check_unit_prices: boolean
    check_funding_rate: boolean
    max_deviation_percent: number
  }
}

const defaultSettings: CheckersSettingsState = {
  risk_checker: {
    enabled: true,
    severity_threshold: 'MEDIUM',
    check_self_invoice: true,
    check_duplicate_invoice: true,
    check_round_amounts: true,
    check_weekend_dates: true,
    round_amount_threshold: 1000,
  },
  semantic_checker: {
    enabled: true,
    severity_threshold: 'MEDIUM',
    check_project_relevance: true,
    check_description_quality: true,
    min_relevance_score: 0.6,
    use_rag_context: true,
  },
  economic_checker: {
    enabled: true,
    severity_threshold: 'LOW',
    check_budget_limits: true,
    check_unit_prices: true,
    check_funding_rate: true,
    max_deviation_percent: 20,
  },
}

export default function CheckersSettings() {
  const queryClient = useQueryClient()
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    risk: true,
    semantic: false,
    economic: false,
  })
  const [settings, setSettings] = useState<CheckersSettingsState>(defaultSettings)
  const [hasChanges, setHasChanges] = useState(false)

  // Load settings from backend
  const { isLoading } = useQuery({
    queryKey: ['checkerSettings'],
    queryFn: async () => {
      try {
        const response = await api.getSettings()
        if (response?.checkers) {
          setSettings(prev => ({
            ...prev,
            ...response.checkers,
          }))
        }
        return response?.checkers || defaultSettings
      } catch {
        return defaultSettings
      }
    },
  })

  // Save settings mutation
  const saveMutation = useMutation({
    mutationFn: async (newSettings: CheckersSettingsState) => {
      return api.updateSettings({ checkers: newSettings })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checkerSettings'] })
      setHasChanges(false)
    },
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const updateSetting = <T extends keyof CheckersSettingsState>(
    checker: T,
    key: keyof CheckersSettingsState[T],
    value: unknown
  ) => {
    setSettings(prev => ({
      ...prev,
      [checker]: {
        ...prev[checker],
        [key]: value,
      },
    }))
    setHasChanges(true)
  }

  const resetToDefaults = () => {
    setSettings(defaultSettings)
    setHasChanges(true)
  }

  const handleSave = () => {
    saveMutation.mutate(settings)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-theme-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-theme-text-primary">
            Prüfmodul-Konfiguration
          </h3>
          <p className="text-sm text-theme-text-muted mt-1">
            Konfigurieren Sie die automatischen Prüfungen für Rechnungsdokumente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={resetToDefaults}
            className="flex items-center gap-2 px-3 py-2 text-sm text-theme-text-muted hover:text-theme-text border border-theme-border rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Zurücksetzen
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges || saveMutation.isPending}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              hasChanges
                ? 'bg-theme-primary text-white hover:bg-theme-primary-hover'
                : 'bg-theme-surface text-theme-text-muted cursor-not-allowed'
            )}
          >
            {saveMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Speichern
          </button>
        </div>
      </div>

      {/* Risk Checker Section */}
      <div className="bg-theme-card rounded-lg border border-theme-border overflow-hidden">
        <button
          onClick={() => toggleSection('risk')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-theme-hover transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-status-danger-bg rounded-lg">
              <Shield className="w-5 h-5 text-status-danger" />
            </div>
            <div className="text-left">
              <h4 className="font-medium text-theme-text-primary">Risikoprüfung</h4>
              <p className="text-sm text-theme-text-muted">
                Betrugserkennungen und Plausibilitätsprüfungen
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={clsx(
                'px-2 py-1 text-xs rounded-full',
                settings.risk_checker.enabled
                  ? 'bg-status-success-bg text-status-success'
                  : 'bg-theme-surface text-theme-text-muted'
              )}
            >
              {settings.risk_checker.enabled ? 'Aktiv' : 'Inaktiv'}
            </span>
            {expandedSections.risk ? (
              <ChevronDown className="w-5 h-5 text-theme-text-muted" />
            ) : (
              <ChevronRight className="w-5 h-5 text-theme-text-muted" />
            )}
          </div>
        </button>

        {expandedSections.risk && (
          <div className="px-4 pb-4 border-t border-theme-border">
            <div className="mt-4 space-y-4">
              {/* Enable/Disable */}
              <div className="flex items-center justify-between">
                <label className="text-sm text-theme-text">Risikoprüfung aktivieren</label>
                <input
                  type="checkbox"
                  checked={settings.risk_checker.enabled}
                  onChange={e => updateSetting('risk_checker', 'enabled', e.target.checked)}
                  className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                />
              </div>

              {/* Severity Threshold */}
              <div>
                <label className="block text-sm text-theme-text mb-1">Schwellenwert</label>
                <select
                  value={settings.risk_checker.severity_threshold}
                  onChange={e => updateSetting('risk_checker', 'severity_threshold', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-theme-border rounded-lg bg-theme-surface text-theme-text"
                >
                  <option value="LOW">Niedrig (alle Warnungen)</option>
                  <option value="MEDIUM">Mittel (ab Warnung)</option>
                  <option value="HIGH">Hoch (nur kritische)</option>
                </select>
              </div>

              <div className="border-t border-theme-border pt-4">
                <p className="text-sm font-medium text-theme-text mb-3">Aktive Prüfungen</p>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.risk_checker.check_self_invoice}
                      onChange={e => updateSetting('risk_checker', 'check_self_invoice', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Selbstrechnungsprüfung</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.risk_checker.check_duplicate_invoice}
                      onChange={e => updateSetting('risk_checker', 'check_duplicate_invoice', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Duplikatsprüfung</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.risk_checker.check_round_amounts}
                      onChange={e => updateSetting('risk_checker', 'check_round_amounts', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Runde Beträge erkennen</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.risk_checker.check_weekend_dates}
                      onChange={e => updateSetting('risk_checker', 'check_weekend_dates', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Wochenend-Rechnungsdatum</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm text-theme-text mb-1">
                  Schwelle für runde Beträge (EUR)
                </label>
                <input
                  type="number"
                  min="100"
                  max="100000"
                  step="100"
                  value={settings.risk_checker.round_amount_threshold}
                  onChange={e => updateSetting('risk_checker', 'round_amount_threshold', parseInt(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-theme-border rounded-lg bg-theme-surface text-theme-text"
                />
                <p className="text-xs text-theme-text-muted mt-1">
                  Beträge ab diesem Wert werden bei runden Summen markiert
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Semantic Checker Section */}
      <div className="bg-theme-card rounded-lg border border-theme-border overflow-hidden">
        <button
          onClick={() => toggleSection('semantic')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-theme-hover transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-status-info-bg rounded-lg">
              <Brain className="w-5 h-5 text-status-info" />
            </div>
            <div className="text-left">
              <h4 className="font-medium text-theme-text-primary">Semantische Prüfung</h4>
              <p className="text-sm text-theme-text-muted">
                Projektrelevanz und Beschreibungsqualität
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={clsx(
                'px-2 py-1 text-xs rounded-full',
                settings.semantic_checker.enabled
                  ? 'bg-status-success-bg text-status-success'
                  : 'bg-theme-surface text-theme-text-muted'
              )}
            >
              {settings.semantic_checker.enabled ? 'Aktiv' : 'Inaktiv'}
            </span>
            {expandedSections.semantic ? (
              <ChevronDown className="w-5 h-5 text-theme-text-muted" />
            ) : (
              <ChevronRight className="w-5 h-5 text-theme-text-muted" />
            )}
          </div>
        </button>

        {expandedSections.semantic && (
          <div className="px-4 pb-4 border-t border-theme-border">
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm text-theme-text">Semantische Prüfung aktivieren</label>
                <input
                  type="checkbox"
                  checked={settings.semantic_checker.enabled}
                  onChange={e => updateSetting('semantic_checker', 'enabled', e.target.checked)}
                  className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                />
              </div>

              <div className="border-t border-theme-border pt-4">
                <p className="text-sm font-medium text-theme-text mb-3">Aktive Prüfungen</p>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.semantic_checker.check_project_relevance}
                      onChange={e => updateSetting('semantic_checker', 'check_project_relevance', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Projektrelevanz prüfen</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.semantic_checker.check_description_quality}
                      onChange={e => updateSetting('semantic_checker', 'check_description_quality', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Beschreibungsqualität</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.semantic_checker.use_rag_context}
                      onChange={e => updateSetting('semantic_checker', 'use_rag_context', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">RAG-Kontext verwenden</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm text-theme-text mb-1">
                  Minimale Relevanz-Score: {(settings.semantic_checker.min_relevance_score * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={settings.semantic_checker.min_relevance_score}
                  onChange={e => updateSetting('semantic_checker', 'min_relevance_score', parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Economic Checker Section */}
      <div className="bg-theme-card rounded-lg border border-theme-border overflow-hidden">
        <button
          onClick={() => toggleSection('economic')}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-theme-hover transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-status-warning-bg rounded-lg">
              <TrendingUp className="w-5 h-5 text-status-warning" />
            </div>
            <div className="text-left">
              <h4 className="font-medium text-theme-text-primary">Wirtschaftlichkeitsprüfung</h4>
              <p className="text-sm text-theme-text-muted">
                Budget- und Preiskontrollen
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span
              className={clsx(
                'px-2 py-1 text-xs rounded-full',
                settings.economic_checker.enabled
                  ? 'bg-status-success-bg text-status-success'
                  : 'bg-theme-surface text-theme-text-muted'
              )}
            >
              {settings.economic_checker.enabled ? 'Aktiv' : 'Inaktiv'}
            </span>
            {expandedSections.economic ? (
              <ChevronDown className="w-5 h-5 text-theme-text-muted" />
            ) : (
              <ChevronRight className="w-5 h-5 text-theme-text-muted" />
            )}
          </div>
        </button>

        {expandedSections.economic && (
          <div className="px-4 pb-4 border-t border-theme-border">
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm text-theme-text">Wirtschaftlichkeitsprüfung aktivieren</label>
                <input
                  type="checkbox"
                  checked={settings.economic_checker.enabled}
                  onChange={e => updateSetting('economic_checker', 'enabled', e.target.checked)}
                  className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                />
              </div>

              <div className="border-t border-theme-border pt-4">
                <p className="text-sm font-medium text-theme-text mb-3">Aktive Prüfungen</p>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.economic_checker.check_budget_limits}
                      onChange={e => updateSetting('economic_checker', 'check_budget_limits', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Budgetgrenzen prüfen</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.economic_checker.check_unit_prices}
                      onChange={e => updateSetting('economic_checker', 'check_unit_prices', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Stückpreise prüfen</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.economic_checker.check_funding_rate}
                      onChange={e => updateSetting('economic_checker', 'check_funding_rate', e.target.checked)}
                      className="rounded border-theme-border text-theme-primary focus:ring-theme-primary"
                    />
                    <span className="text-sm text-theme-text">Fördersatz prüfen</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm text-theme-text mb-1">
                  Max. Abweichung: {settings.economic_checker.max_deviation_percent}%
                </label>
                <input
                  type="range"
                  min="5"
                  max="50"
                  step="5"
                  value={settings.economic_checker.max_deviation_percent}
                  onChange={e => updateSetting('economic_checker', 'max_deviation_percent', parseInt(e.target.value))}
                  className="w-full"
                />
                <p className="text-xs text-theme-text-muted mt-1">
                  Erlaubte Preisabweichung vom Durchschnitt
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-status-info-bg border border-status-info-border rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-status-info mt-0.5" />
          <div>
            <p className="font-medium text-status-info">Hinweis</p>
            <p className="text-sm text-status-info mt-1">
              Änderungen an den Prüfmodulen wirken sich nur auf neue Analysen aus.
              Bereits analysierte Dokumente müssen erneut verarbeitet werden.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
