/**
 * FlowAudit Theme Context
 *
 * React Context für das zentrale Theme-System.
 * Ermöglicht Theme-Wechsel ohne Reload und persistiert die Einstellung.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from 'react'
import { Theme } from './tokens'
import { lightTheme } from './light'
import { darkTheme } from './dark'

// =============================================================================
// Types
// =============================================================================

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  /** Aktives Theme-Objekt */
  theme: Theme
  /** Aktueller Modus (light/dark/system) */
  mode: ThemeMode
  /** Tatsächlich angewandtes Theme (light/dark) */
  resolvedTheme: 'light' | 'dark'
  /** Theme wechseln */
  setMode: (mode: ThemeMode) => void
  /** Direkt zwischen Light/Dark toggeln */
  toggleTheme: () => void
  /** Ist Dark Mode aktiv? */
  isDark: boolean
}

// =============================================================================
// Constants
// =============================================================================

const STORAGE_KEY = 'flowaudit_theme'

// =============================================================================
// Context
// =============================================================================

const ThemeContext = createContext<ThemeContextValue | null>(null)

// =============================================================================
// Helper Functions
// =============================================================================

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getStoredMode(): ThemeMode {
  if (typeof window === 'undefined') return 'system'
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored
  }
  return 'system'
}

function applyTheme(theme: Theme) {
  const root = document.documentElement

  // CSS-Klasse für Tailwind dark mode
  if (theme.name === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }

  // CSS Custom Properties setzen
  const colors = theme.colors

  // Background colors
  root.style.setProperty('--color-bg-app', colors.background.app)
  root.style.setProperty('--color-bg-panel', colors.background.panel)
  root.style.setProperty('--color-bg-card', colors.background.card)
  root.style.setProperty('--color-bg-elevated', colors.background.elevated)
  root.style.setProperty('--color-bg-input', colors.background.input)
  root.style.setProperty('--color-bg-disabled', colors.background.disabled)
  root.style.setProperty('--color-bg-hover', colors.background.hover)
  root.style.setProperty('--color-bg-selected', colors.background.selected)

  // Text colors
  root.style.setProperty('--color-text-primary', colors.text.primary)
  root.style.setProperty('--color-text-secondary', colors.text.secondary)
  root.style.setProperty('--color-text-muted', colors.text.muted)
  root.style.setProperty('--color-text-inverse', colors.text.inverse)
  root.style.setProperty('--color-text-disabled', colors.text.disabled)
  root.style.setProperty('--color-text-link', colors.text.link)
  root.style.setProperty('--color-text-link-hover', colors.text.linkHover)

  // Border colors
  root.style.setProperty('--color-border-default', colors.border.default)
  root.style.setProperty('--color-border-subtle', colors.border.subtle)
  root.style.setProperty('--color-border-strong', colors.border.strong)
  root.style.setProperty('--color-border-focus', colors.border.focus)
  root.style.setProperty('--color-border-error', colors.border.error)

  // Accent colors
  root.style.setProperty('--color-accent-primary', colors.accent.primary)
  root.style.setProperty('--color-accent-primary-hover', colors.accent.primaryHover)
  root.style.setProperty('--color-accent-primary-active', colors.accent.primaryActive)
  root.style.setProperty('--color-accent-secondary', colors.accent.secondary)
  root.style.setProperty('--color-accent-secondary-hover', colors.accent.secondaryHover)

  // Status colors
  root.style.setProperty('--color-status-success', colors.status.success)
  root.style.setProperty('--color-status-success-bg', colors.status.successBackground)
  root.style.setProperty('--color-status-success-border', colors.status.successBorder)
  root.style.setProperty('--color-status-warning', colors.status.warning)
  root.style.setProperty('--color-status-warning-bg', colors.status.warningBackground)
  root.style.setProperty('--color-status-warning-border', colors.status.warningBorder)
  root.style.setProperty('--color-status-danger', colors.status.danger)
  root.style.setProperty('--color-status-danger-bg', colors.status.dangerBackground)
  root.style.setProperty('--color-status-danger-border', colors.status.dangerBorder)
  root.style.setProperty('--color-status-info', colors.status.info)
  root.style.setProperty('--color-status-info-bg', colors.status.infoBackground)
  root.style.setProperty('--color-status-info-border', colors.status.infoBorder)
  root.style.setProperty('--color-status-disabled', colors.status.disabled)
  root.style.setProperty('--color-status-disabled-bg', colors.status.disabledBackground)

  // UI colors
  root.style.setProperty('--color-ui-scrollbar-track', colors.ui.scrollbarTrack)
  root.style.setProperty('--color-ui-scrollbar-thumb', colors.ui.scrollbarThumb)
  root.style.setProperty('--color-ui-overlay', colors.ui.overlay)
  root.style.setProperty('--color-ui-shadow', colors.ui.shadow)
  root.style.setProperty('--color-ui-divider', colors.ui.divider)
  root.style.setProperty('--color-ui-focus-ring', colors.ui.focusRing)

  // Shadows
  root.style.setProperty('--shadow-sm', theme.shadows.sm)
  root.style.setProperty('--shadow-md', theme.shadows.md)
  root.style.setProperty('--shadow-lg', theme.shadows.lg)
  root.style.setProperty('--shadow-xl', theme.shadows.xl)
  root.style.setProperty('--shadow-inner', theme.shadows.inner)
}

// =============================================================================
// Provider Component
// =============================================================================

interface ThemeProviderProps {
  children: ReactNode
  /** Initiales Theme (überschreibt gespeicherte Einstellung) */
  defaultMode?: ThemeMode
}

export function ThemeProvider({ children, defaultMode }: ThemeProviderProps) {
  const [mode, setModeState] = useState<ThemeMode>(() => defaultMode ?? getStoredMode())
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() => {
    if (defaultMode === 'system' || (!defaultMode && getStoredMode() === 'system')) {
      return getSystemTheme()
    }
    return defaultMode ?? getStoredMode() as 'light' | 'dark'
  })

  // Theme basierend auf Modus auflösen
  const theme = resolvedTheme === 'dark' ? darkTheme : lightTheme

  // Modus setzen und persistieren
  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode)
    localStorage.setItem(STORAGE_KEY, newMode)

    const newResolved = newMode === 'system' ? getSystemTheme() : newMode
    setResolvedTheme(newResolved)
  }, [])

  // Toggle zwischen Light und Dark
  const toggleTheme = useCallback(() => {
    const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark'
    setMode(newTheme)
  }, [resolvedTheme, setMode])

  // Theme anwenden wenn sich resolvedTheme ändert
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  // System Theme Änderungen beobachten
  useEffect(() => {
    if (mode !== 'system') return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = (e: MediaQueryListEvent) => {
      setResolvedTheme(e.matches ? 'dark' : 'light')
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [mode])

  // Flicker Prevention: Theme sofort beim Mount anwenden
  useEffect(() => {
    applyTheme(theme)
  }, [])

  const value: ThemeContextValue = {
    theme,
    mode,
    resolvedTheme,
    setMode,
    toggleTheme,
    isDark: resolvedTheme === 'dark',
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

// =============================================================================
// Hook
// =============================================================================

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// =============================================================================
// Script für Flicker Prevention (im HTML <head> einfügen)
// =============================================================================

export const themeInitScript = `
(function() {
  try {
    var mode = localStorage.getItem('flowaudit_theme') || 'system';
    var dark = mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (dark) document.documentElement.classList.add('dark');
  } catch (e) {}
})();
`
