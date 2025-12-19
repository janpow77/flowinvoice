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
    if (healthy === undefined) return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    return healthy ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    )
  }

  const getMetricColor = (percent: number): string => {
    if (percent < 60) return 'bg-green-500'
    if (percent < 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
          <p className="text-sm text-amber-700 dark:text-amber-300">
            GPU- und Performance-Einstellungen erfordern einen Neustart der Container, um wirksam zu werden.
          </p>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              System-Auslastung
            </h3>
          </div>
          <button
            onClick={() => refetchMetrics()}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className={clsx('h-4 w-4', metricsLoading && 'animate-spin')} />
          </button>
        </div>

        {metricsLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : metrics ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CPU */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">CPU</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {(metrics as SystemMetrics).cpu_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).cpu_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).cpu_percent ?? 0}%` }}
                />
              </div>
            </div>

            {/* Memory */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <HardDrive className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">RAM</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {(metrics as SystemMetrics).memory_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                {((metrics as SystemMetrics).memory_used_gb ?? 0).toFixed(1)} / {((metrics as SystemMetrics).memory_total_gb ?? 0).toFixed(1)} GB
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).memory_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).memory_percent ?? 0}%` }}
                />
              </div>
            </div>

            {/* Disk */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Festplatte</span>
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {(metrics as SystemMetrics).disk_percent?.toFixed(1) ?? '0'}%
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                {((metrics as SystemMetrics).disk_used_gb ?? 0).toFixed(1)} / {((metrics as SystemMetrics).disk_total_gb ?? 0).toFixed(1)} GB
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={clsx('h-2 rounded-full transition-all', getMetricColor((metrics as SystemMetrics).disk_percent ?? 0))}
                  style={{ width: `${(metrics as SystemMetrics).disk_percent ?? 0}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4 text-gray-500">
            Keine Metriken verfügbar
          </div>
        )}
      </div>

      {/* GPU & Thermal Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            GPU & Performance
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Diese Einstellungen beeinflussen die Ollama-Leistung und den Ressourcenverbrauch.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* GPU Memory Fraction */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
              <span className="w-16 text-right text-sm font-medium text-gray-900 dark:text-white">
                {(gpuSettings.gpu_memory_fraction * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Anteil des GPU-Speichers für Ollama (höher = schneller, aber weniger Headroom)
            </p>
          </div>

          {/* Parallel Requests */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
              <span className="w-16 text-right text-sm font-medium text-gray-900 dark:text-white">
                {gpuSettings.num_parallel}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Anzahl gleichzeitiger LLM-Anfragen (höher = mehr Durchsatz, aber mehr VRAM)
            </p>
          </div>

          {/* Context Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Kontextgröße (Token)
            </label>
            <select
              value={gpuSettings.context_size}
              onChange={(e) => handleGpuChange('context_size', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            >
              <option value={2048}>2048 (minimal)</option>
              <option value={4096}>4096 (standard)</option>
              <option value={8192}>8192 (erweitert)</option>
              <option value={16384}>16384 (groß)</option>
              <option value={32768}>32768 (maximal)</option>
            </select>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Maximale Eingabelänge für das LLM (größer = mehr VRAM benötigt)
            </p>
          </div>

          {/* Thermal Throttle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <div className="flex items-center gap-2">
                <Thermometer className="h-4 w-4 text-red-500" />
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
              <span className="w-16 text-right text-sm font-medium text-gray-900 dark:text-white">
                {gpuSettings.thermal_throttle_temp}°C
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
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
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {updateGpuMutation.isPending ? 'Wird gespeichert...' : 'Einstellungen speichern'}
            </button>
          </div>
        )}

        {updateGpuMutation.isSuccess && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-300 text-sm">
              <CheckCircle className="h-4 w-4" />
              Einstellungen gespeichert. Container-Neustart erforderlich für volle Wirkung.
            </div>
          </div>
        )}
      </div>

      {/* Service Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Service-Status
            </h3>
          </div>
          <button
            onClick={() => refetchHealth()}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Aktualisieren"
          >
            <RefreshCw className={clsx('h-4 w-4', healthLoading && 'animate-spin')} />
          </button>
        </div>

        {healthLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : health ? (
          <div className="space-y-4">
            {/* Overall Status */}
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <div>
                <span className="font-medium text-gray-900 dark:text-white">Gesamtstatus</span>
                {(health as DetailedHealth).uptime_seconds && (
                  <span className="ml-2 text-sm text-gray-500">
                    (Uptime: {formatUptime((health as DetailedHealth).uptime_seconds)})
                  </span>
                )}
              </div>
              <div className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium',
                (health as DetailedHealth).status === 'healthy'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              )}>
                {(health as DetailedHealth).status === 'healthy' ? 'Gesund' : 'Probleme'}
              </div>
            </div>

            {/* Individual Services */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.database)}
                <span className="text-sm text-gray-700 dark:text-gray-300">PostgreSQL</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.redis)}
                <span className="text-sm text-gray-700 dark:text-gray-300">Redis</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.chromadb)}
                <span className="text-sm text-gray-700 dark:text-gray-300">ChromaDB</span>
              </div>
              <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                {getStatusIcon((health as DetailedHealth).services?.ollama)}
                <span className="text-sm text-gray-700 dark:text-gray-300">Ollama</span>
              </div>
            </div>

            {/* Version Info */}
            {(health as DetailedHealth).version && (
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <span className="text-sm text-gray-700 dark:text-gray-300">Version</span>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {(health as DetailedHealth).version}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-4 text-gray-500">
            Keine Health-Daten verfügbar
          </div>
        )}
      </div>

      {/* Contact & Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Info className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Über FlowAudit
          </h3>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            FlowAudit ist ein KI-gestütztes Rechnungsprüfungssystem für die automatisierte
            Analyse und Validierung von Belegen nach steuerlichen Regelwerken.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="https://github.com/janpow77/flowinvoice"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Github className="h-5 w-5 text-gray-700 dark:text-gray-300" />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">GitHub Repository</div>
                <div className="text-xs text-gray-500">Quellcode und Issues</div>
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400 ml-auto" />
            </a>

            <a
              href="mailto:support@flowinvoice.de"
              className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Mail className="h-5 w-5 text-gray-700 dark:text-gray-300" />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">Support</div>
                <div className="text-xs text-gray-500">support@flowinvoice.de</div>
              </div>
              <ExternalLink className="h-4 w-4 text-gray-400 ml-auto" />
            </a>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              © 2024 FlowInvoice/FlowAudit • Alle Rechte vorbehalten
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
