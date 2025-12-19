/**
 * SettingsGeneral - Allgemeine Einstellungen
 *
 * Sprache und Erscheinungsbild.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, Moon, Sun, CheckCircle } from 'lucide-react'
import clsx from 'clsx'
import { languages, changeLanguage, getCurrentLanguage, type LanguageCode } from '@/lib/i18n'

export function SettingsGeneral() {
  const { t } = useTranslation()
  const [currentLang, setCurrentLang] = useState<LanguageCode>(getCurrentLanguage())
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('flowaudit_theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  const handleLanguageChange = (lng: LanguageCode) => {
    changeLanguage(lng)
    setCurrentLang(lng)
  }

  const handleDarkModeToggle = () => {
    const newMode = !darkMode
    setDarkMode(newMode)
    localStorage.setItem('flowaudit_theme', newMode ? 'dark' : 'light')

    if (newMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-700 dark:text-blue-300">
          Diese Einstellungen gelten nur für die Benutzeroberfläche und werden lokal gespeichert.
        </p>
      </div>

      {/* Language Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('settings.language')}
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
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
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              )}
            >
              <span className="text-2xl">{lang.flag}</span>
              <span
                className={clsx(
                  'font-medium',
                  currentLang === lang.code
                    ? 'text-primary-700 dark:text-primary-300'
                    : 'text-gray-700 dark:text-gray-300'
                )}
              >
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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('settings.appearance')}
          </h3>
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
    </div>
  )
}
