import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import clsx from 'clsx'
import {
  Globe,
  Cpu,
  FileText,
  Layers,
  Server,
  Shield,
  Info,
} from 'lucide-react'

// Tab Components
import { SettingsGeneral } from '@/components/settings/SettingsGeneral'
import { SettingsAIAnalysis } from '@/components/settings/SettingsAIAnalysis'
import { SettingsDocumentTypes } from '@/components/settings/SettingsDocumentTypes'
import { SettingsProfiles } from '@/components/settings/SettingsProfiles'
import { SettingsSystem } from '@/components/settings/SettingsSystem'

type SettingsTab = 'general' | 'ai-analysis' | 'document-types' | 'profiles' | 'system'

interface TabConfig {
  id: SettingsTab
  labelKey: string
  icon: React.ComponentType<{ className?: string }>
  adminOnly?: boolean
  description: string
}

const TABS: TabConfig[] = [
  {
    id: 'general',
    labelKey: 'settingsTabs.general',
    icon: Globe,
    description: 'Sprache und Erscheinungsbild',
  },
  {
    id: 'ai-analysis',
    labelKey: 'settingsTabs.aiAnalysis',
    icon: Cpu,
    description: 'Provider, Profile und RAG-Einstellungen',
  },
  {
    id: 'document-types',
    labelKey: 'settingsTabs.documentTypes',
    icon: FileText,
    adminOnly: true,
    description: 'Dokumenttypen und Chunking-Defaults',
  },
  {
    id: 'profiles',
    labelKey: 'settingsTabs.profiles',
    icon: Layers,
    adminOnly: true,
    description: 'LLM-Profile und Modellkatalog',
  },
  {
    id: 'system',
    labelKey: 'settingsTabs.system',
    icon: Server,
    description: 'Performance, GPU und Systemstatus',
  },
]

export default function Settings() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  // TODO: Replace with actual auth check
  const isAdmin = true

  const visibleTabs = TABS.filter(tab => !tab.adminOnly || isAdmin)

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return <SettingsGeneral />
      case 'ai-analysis':
        return <SettingsAIAnalysis isAdmin={isAdmin} />
      case 'document-types':
        return <SettingsDocumentTypes isAdmin={isAdmin} />
      case 'profiles':
        return <SettingsProfiles isAdmin={isAdmin} />
      case 'system':
        return <SettingsSystem />
      default:
        return null
    }
  }

  const activeTabConfig = TABS.find(t => t.id === activeTab)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {t('settings.title')}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {activeTabConfig?.description}
          </p>
        </div>
        {isAdmin && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-lg text-sm">
            <Shield className="h-4 w-4" />
            <span>Admin</span>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-4 overflow-x-auto" aria-label="Tabs">
          {visibleTabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'group inline-flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors',
                  isActive
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                )}
              >
                <Icon
                  className={clsx(
                    'h-4 w-4',
                    isActive
                      ? 'text-primary-500'
                      : 'text-gray-400 group-hover:text-gray-500 dark:text-gray-500'
                  )}
                />
                {t(tab.labelKey, tab.id)}
                {tab.adminOnly && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded">
                    Admin
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">{renderTabContent()}</div>

      {/* Footer Info */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-gray-400 mt-0.5" />
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('settings.helpTitle', 'Hilfe zu den Einstellungen')}
            </p>
            <p>
              {t(
                'settings.helpText',
                'Die Einstellungen werden automatisch gespeichert. Einige Änderungen (Performance, GPU) erfordern einen Neustart der Container.'
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
