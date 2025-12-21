/**
 * SettingsSystem - System & Performance Einstellungen
 *
 * Performance, GPU/Thermal, System-Info und Kontakt.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Server,
  Cpu,
  HardDrive,
  Thermometer,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Database,
  Zap,
  Info,
  Mail,
  Github,
  ExternalLink,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

interface GpuSettings {
  gpu_memory_fraction: number
  num_gpu_layers: number
  num_parallel: number
  context_size: number
  thermal_throttle_temp: number
}

interface SystemMetrics {
  cpu_percent: number
  memory_percent: number
  memory_used_gb: number
  memory_total_gb: number
  disk_percent: number
  disk_used_gb: number
  disk_total_gb: number
}

interface DetailedHealth {
  status: string
  services: {
    database: boolean
    redis: boolean
    chromadb: boolean
    ollama: boolean
  }
  version: string
  uptime_seconds: number
}

export function SettingsSystem() {
  useTranslation() // Hook for future i18n
  const queryClient = useQueryClient()

  // GPU Settings State
  const [gpuSettings, setGpuSettings] = useState<GpuSettings>({
    gpu_memory_fraction: 0.9,
    num_gpu_layers: -1,
    num_parallel: 2,
    context_size: 4096,
    thermal_throttle_temp: 80,
  })
  const [hasGpuChanges, setHasGpuChanges] = useState(false)

  // Queries
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: () => api.getSystemMetrics(),
    refetchInterval: 10000, // Auto-refresh every 10s
  })

  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['detailed-health'],
    queryFn: () => api.getDetailedHealth(),
    refetchInterval: 30000,
  })

  const { data: gpuData } = useQuery({
    queryKey: ['gpu-settings'],
    queryFn: () => api.getGpuSettings(),
  })

  // Initialize GPU settings from API
  useEffect(() => {
    if (gpuData) {
      setGpuSettings({
        gpu_memory_fraction: gpuData.gpu_memory_fraction ?? 0.9,
        num_gpu_layers: gpuData.num_gpu_layers ?? -1,
        num_parallel: gpuData.num_parallel ?? 2,
        context_size: gpuData.context_size ?? 4096,
        thermal_throttle_temp: gpuData.thermal_throttle_temp ?? 80,
      })
    }
  }, [gpuData])

  // Update GPU Settings Mutation
  const updateGpuMutation = useMutation({
    mutationFn: (settings: Partial<GpuSettings>) => api.updateGpuSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gpu-settings'] })
      setHasGpuChanges(false)
    },
  })

  const handleGpuChange = (key: keyof GpuSettings, value: number) => {
    setGpuSettings(prev => ({ ...prev, [key]: value }))
    setHasGpuChanges(true)
  }

  const saveGpuSettings = () => {
    updateGpuMutation.mutate(gpuSettings)
  }

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (days > 0) return `${days}d ${hours}h ${minutes}m`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const getStatusIcon = (healthy: boolean | undefined) => {
    if (healthy === undefined) return <AlertTriangle className="h-4 w-4 text-status-warning" />
    return healthy ? (
      <CheckCircle className="h-4 w-4 text-status-success" />
    ) : (
      <XCircle className="h-4 w-4 text-status-danger" />
    )
  }

  const getMetricColor = (percent: number): string => {
    if (percent < 60) return 'bg-status-success'
    if (percent < 80) return 'bg-status-warning'
    return 'bg-status-danger'
  }

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-status-warning-bg border border-status-warning-border rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertTriangle className="h-5 w-5 text-status-warning mt-0.5" />
          <p className="text-sm text-status-warning">
            GPU- und Performance-Einstellungen erfordern einen Neustart der Container, um wirksam zu werden.
          </p>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-accent-primary" />
            <h3 className="text-lg font-semibold text-theme-text-primary">
              System-Auslastung
            </h3>
          </div>
          <button
            onClick={() => refetchMetrics()}
            className="p-2 text-theme-text-muted hover:text-theme-text-secondary transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className={clsx('h-4 w-4', metricsLoading && 'animate-spin')} />
          </button>
        </div>

        {metricsLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-theme-text-muted" />
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CPU */}
            <div className="bg-theme-hover rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="h-4 w-4 text-status-info" />
                <span className="text-sm font-medium text-theme-text-secondary">CPU</span>
              </div>
              <div className="text-2xl font-bold text-theme-text-primary mb-2">
                {(metrics as SystemMetrics).cpu_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="w-full bg-theme-hover rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).cpu_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).cpu_percent ?? 0}%` }}
                />
              </div>
            </div>

            {/* Memory */}
            <div className="bg-theme-hover rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium text-theme-text-secondary">RAM</span>
              </div>
              <div className="text-2xl font-bold text-theme-text-primary mb-2">
                {(metrics as SystemMetrics).memory_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="text-xs text-theme-text-muted mb-2">
                {((metrics as SystemMetrics).memory_used_gb ?? 0).toFixed(1)} / {((metrics as SystemMetrics).memory_total_gb ?? 0).toFixed(1)} GB
              </div>
              <div className="w-full bg-theme-hover rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).memory_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).memory_percent ?? 0}%` }}
                />
              </div>
            </div>

            {/* Disk */}
            <div className="bg-theme-hover rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-4 w-4 text-status-success" />
                <span className="text-sm font-medium text-theme-text-secondary">Festplatte</span>
              </div>
              <div className="text-2xl font-bold text-theme-text-primary mb-2">
                {(metrics as SystemMetrics).disk_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="text-xs text-theme-text-muted mb-2">
                {((metrics as SystemMetrics).disk_used_gb ?? 0).toFixed(1)} / {((metrics as SystemMetrics).disk_total_gb ?? 0).toFixed(1)} GB
              </div>
              <div className="w-full bg-theme-hover rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).disk_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).disk_percent ?? 0}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4 text-theme-text-muted">
            Keine Metriken verfügbar
          </div>
        )}
      </div>

      {/* GPU & Thermal Settings */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-accent-primary" />
          <h3 className="text-lg font-semibold text-theme-text-primary">
            GPU & Performance
          </h3>
        </div>
        <p className="text-sm text-theme-text-muted mb-6">
          Diese Einstellungen beeinflussen die Ollama-Leistung und den Ressourcenverbrauch.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* GPU Memory Fraction */}
          <div>
            <label className="block text-sm font-medium text-theme-text-secondary mb-2">
              GPU-Speicher (VRAM)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={gpuSettings.gpu_memory_fraction}
                onChange={(e) => handleGpuChange('gpu_memory_fraction', parseFloat(e.target.value))}
                className="flex-1"
              />
              <span className="w-16 text-right text-sm font-medium text-theme-text-primary">
                {(gpuSettings.gpu_memory_fraction * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-1 text-xs text-theme-text-muted">
              Anteil des GPU-Speichers für Ollama (höher = schneller, aber weniger Headroom)
            </p>
          </div>

          {/* Parallel Requests */}
          <div>
            <label className="block text-sm font-medium text-theme-text-secondary mb-2">
              Parallele Anfragen
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max="8"
                step="1"
                value={gpuSettings.num_parallel}
                onChange={(e) => handleGpuChange('num_parallel', parseInt(e.target.value))}
                className="flex-1"
              />
              <span className="w-16 text-right text-sm font-medium text-theme-text-primary">
                {gpuSettings.num_parallel}
              </span>
            </div>
            <p className="mt-1 text-xs text-theme-text-muted">
              Anzahl gleichzeitiger LLM-Anfragen (höher = mehr Durchsatz, aber mehr VRAM)
            </p>
          </div>

          {/* Context Size */}
          <div>
            <label className="block text-sm font-medium text-theme-text-secondary mb-2">
              Kontextgröße (Token)
            </label>
            <select
              value={gpuSettings.context_size}
              onChange={(e) => handleGpuChange('context_size', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
            >
              <option value={2048}>2048 (minimal)</option>
              <option value={4096}>4096 (standard)</option>
              <option value={8192}>8192 (erweitert)</option>
              <option value={16384}>16384 (groß)</option>
              <option value={32768}>32768 (maximal)</option>
            </select>
            <p className="mt-1 text-xs text-theme-text-muted">
              Maximale Eingabelänge für das LLM (größer = mehr VRAM benötigt)
            </p>
          </div>

          {/* Thermal Throttle */}
          <div>
            <label className="block text-sm font-medium text-theme-text-secondary mb-2">
              <div className="flex items-center gap-2">
                <Thermometer className="h-4 w-4 text-status-danger" />
                Thermische Drosselung
              </div>
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="60"
                max="95"
                step="5"
                value={gpuSettings.thermal_throttle_temp}
                onChange={(e) => handleGpuChange('thermal_throttle_temp', parseInt(e.target.value))}
                className="flex-1"
              />
              <span className="w-16 text-right text-sm font-medium text-theme-text-primary">
                {gpuSettings.thermal_throttle_temp}°C
              </span>
            </div>
            <p className="mt-1 text-xs text-theme-text-muted">
              Ab dieser Temperatur wird die Last reduziert (GPU-Schutz)
            </p>
          </div>
        </div>

        {/* Save Button */}
        {hasGpuChanges && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={saveGpuSettings}
              disabled={updateGpuMutation.isPending}
              className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover disabled:opacity-50 transition-colors"
            >
              {updateGpuMutation.isPending ? 'Wird gespeichert...' : 'Einstellungen speichern'}
            </button>
          </div>
        )}

        {updateGpuMutation.isSuccess && (
          <div className="mt-4 p-3 bg-status-success-bg border border-status-success-border rounded-lg">
            <div className="flex items-center gap-2 text-status-success text-sm">
              <CheckCircle className="h-4 w-4" />
              Einstellungen gespeichert. Container-Neustart erforderlich für volle Wirkung.
            </div>
          </div>
        )}
      </div>

      {/* Service Status */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-accent-primary" />
            <h3 className="text-lg font-semibold text-theme-text-primary">
              Service-Status
            </h3>
          </div>
          <button
            onClick={() => refetchHealth()}
            className="p-2 text-theme-text-muted hover:text-theme-text-secondary transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className={clsx('h-4 w-4', healthLoading && 'animate-spin')} />
          </button>
        </div>

        {healthLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-theme-text-muted" />
          </div>
        ) : health ? (
          <div className="space-y-4">
            {/* Overall Status */}
            <div className="flex items-center justify-between p-3 bg-theme-hover rounded-lg">
              <div>
                <span className="font-medium text-theme-text-primary">Gesamtstatus</span>
                {(health as DetailedHealth).uptime_seconds && (
                  <span className="ml-2 text-sm text-theme-text-muted">
                    (Uptime: {formatUptime((health as DetailedHealth).uptime_seconds)})
                  </span>
                )}
              </div>
              <div className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium',
                (health as DetailedHealth).status === 'healthy'
                  ? 'bg-status-success-bg text-status-success'
                  : 'bg-status-danger-bg text-status-danger'
              )}>
                {(health as DetailedHealth).status === 'healthy' ? 'Gesund' : 'Probleme'}
              </div>
            </div>

            {/* Individual Services */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="flex items-center gap-2 p-3 bg-theme-hover rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.database)}
                <span className="text-sm text-theme-text-secondary">PostgreSQL</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-theme-hover rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.redis)}
                <span className="text-sm text-theme-text-secondary">Redis</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-theme-hover rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.chromadb)}
                <span className="text-sm text-theme-text-secondary">ChromaDB</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-theme-hover rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.ollama)}
                <span className="text-sm text-theme-text-secondary">Ollama</span>
              </div>
            </div>

            {/* Version Info */}
            {(health as DetailedHealth).version && (
              <div className="flex items-center justify-between p-3 bg-theme-hover rounded-lg">
                <span className="text-sm text-theme-text-secondary">Version</span>
                <span className="text-sm font-mono text-theme-text-primary">
                  {(health as DetailedHealth).version}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-4 text-theme-text-muted">
            Keine Health-Daten verfügbar
          </div>
        )}
      </div>

      {/* Contact & Info */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center gap-2 mb-4">
          <Info className="h-5 w-5 text-accent-primary" />
          <h3 className="text-lg font-semibold text-theme-text-primary">
            Über FlowAudit
          </h3>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-theme-text-muted">
            FlowAudit ist ein KI-gestütztes Rechnungsprüfungssystem für die automatisierte
            Analyse und Validierung von Belegen nach steuerlichen Regelwerken.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="https://github.com/janpow77/flowinvoice"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-theme-hover rounded-lg hover:bg-theme-hover transition-colors"
            >
              <Github className="h-5 w-5 text-theme-text-secondary" />
              <div>
                <div className="text-sm font-medium text-theme-text-primary">GitHub Repository</div>
                <div className="text-xs text-theme-text-muted">Quellcode und Issues</div>
              </div>
              <ExternalLink className="h-4 w-4 text-theme-text-muted ml-auto" />
            </a>

            <a
              href="mailto:support@flowinvoice.de"
              className="flex items-center gap-3 p-3 bg-theme-hover rounded-lg hover:bg-theme-hover transition-colors"
            >
              <Mail className="h-5 w-5 text-theme-text-secondary" />
              <div>
                <div className="text-sm font-medium text-theme-text-primary">Support</div>
                <div className="text-xs text-theme-text-muted">support@flowinvoice.de</div>
              </div>
              <ExternalLink className="h-4 w-4 text-theme-text-muted ml-auto" />
            </a>
          </div>

          <div className="pt-4 border-t border-theme-border-default">
            <p className="text-xs text-theme-text-muted text-center">
              © 2024 FlowInvoice/FlowAudit • Alle Rechte vorbehalten
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
