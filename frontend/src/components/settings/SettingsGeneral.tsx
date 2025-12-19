/**
 * SettingsGeneral - Allgemeine Einstellungen
 *
 * Sprache und Erscheinungsbild (Theme).
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, Moon, Sun, CheckCircle, Monitor } from 'lucide-react'
import clsx from 'clsx'
import { languages, changeLanguage, getCurrentLanguage, type LanguageCode } from '@/lib/i18n'
import { useTheme } from '@/theme'

export function SettingsGeneral() {
  const { t } = useTranslation()
  const { mode, setMode, isDark } = useTheme()
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getCurrentLanguage())

  const handleLanguageChange = (lng: LanguageCode) => {
    changeLanguage(lng)
    setCurrentLang(lng)
  }

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-status-info-bg border border-status-info-border rounded-lg p-4">
        <p className="text-sm text-status-info">
          Diese Einstellungen gelten nur für die Benutzeroberfläche und werden lokal gespeichert.
        </p>
      </div>

      {/* Language Selection */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="h-5 w-5 text-accent-primary" />
          <h3 className="text-lg font-semibold text-theme-text-primary">
            {t('settings.language')}
          </h3>
        </div>
        <p className="text-sm text-theme-text-muted mb-4">
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
                  ? 'border-accent-primary bg-theme-selected'
                  : 'border-theme-border-default hover:border-theme-border-strong'
              )}
            >
              <span className="text-2xl">{lang.flag}</span>
              <span
                className={clsx(
                  'font-medium',
                  currentLang === lang.code
                    ? 'text-accent-primary'
                    : 'text-theme-text-secondary'
                )}
              >
                {lang.name}
              </span>
              {currentLang === lang.code && (
                <CheckCircle className="h-5 w-5 text-accent-primary" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Theme Selection */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
        <div className="flex items-center gap-2 mb-4">
          {isDark ? (
            <Moon className="h-5 w-5 text-accent-primary" />
          ) : (
            <Sun className="h-5 w-5 text-accent-primary" />
          )}
          <h3 className="text-lg font-semibold text-theme-text-primary">
            {t('settings.appearance')}
          </h3>
        </div>
        <p className="text-sm text-theme-text-muted mb-4">
          {t('settings.appearanceDescription')}
        </p>

        {/* Theme Mode Selection */}
        <div className="grid grid-cols-3 gap-4">
          {/* Light Mode */}
          <button
            onClick={() => setMode('light')}
            className={clsx(
              'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
              mode === 'light'
                ? 'border-accent-primary bg-theme-selected'
                : 'border-theme-border-default hover:border-theme-border-strong'
            )}
          >
            <Sun className={clsx(
              'h-8 w-8',
              mode === 'light' ? 'text-accent-primary' : 'text-theme-text-muted'
            )} />
            <span className={clsx(
              'font-medium text-sm',
              mode === 'light' ? 'text-accent-primary' : 'text-theme-text-secondary'
            )}>
              Light
            </span>
          </button>

          {/* Dark Mode */}
          <button
            onClick={() => setMode('dark')}
            className={clsx(
              'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
              mode === 'dark'
                ? 'border-accent-primary bg-theme-selected'
                : 'border-theme-border-default hover:border-theme-border-strong'
            )}
          >
            <Moon className={clsx(
              'h-8 w-8',
              mode === 'dark' ? 'text-accent-primary' : 'text-theme-text-muted'
            )} />
            <span className={clsx(
              'font-medium text-sm',
              mode === 'dark' ? 'text-accent-primary' : 'text-theme-text-secondary'
            )}>
              Dark
            </span>
          </button>

          {/* System Mode */}
          <button
            onClick={() => setMode('system')}
            className={clsx(
              'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
              mode === 'system'
                ? 'border-accent-primary bg-theme-selected'
                : 'border-theme-border-default hover:border-theme-border-strong'
            )}
          >
            <Monitor className={clsx(
              'h-8 w-8',
              mode === 'system' ? 'text-accent-primary' : 'text-theme-text-muted'
            )} />
            <span className={clsx(
              'font-medium text-sm',
              mode === 'system' ? 'text-accent-primary' : 'text-theme-text-secondary'
            )}>
              System
            </span>
          </button>
        </div>

        {/* Current Status */}
        <div className="mt-4 pt-4 border-t border-theme-border-subtle">
          <p className="text-sm text-theme-text-muted">
            Aktuell aktiv: <span className="font-medium text-theme-text-primary">
              {isDark ? 'Dark Mode' : 'Light Mode'}
            </span>
            {mode === 'system' && (
              <span className="text-theme-text-muted"> (System-Präferenz)</span>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
