/**
 * Theme Context
 *
 * Provides dark/light mode switching with localStorage persistence.
 * Supports: 'light', 'dark', 'system' (follows OS preference)
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  /** Current theme setting */
  theme: Theme
  /** Resolved theme (actual light/dark based on system if theme='system') */
  resolvedTheme: 'light' | 'dark'
  /** Set the theme */
  setTheme: (theme: Theme) => void
  /** Toggle between light and dark */
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const THEME_KEY = 'app_theme'

interface ThemeProviderProps {
  children: ReactNode
  /** Default theme if nothing is stored */
  defaultTheme?: Theme
}

export function ThemeProvider({ children, defaultTheme = 'system' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return defaultTheme
    return (localStorage.getItem(THEME_KEY) as Theme) || defaultTheme
  })

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')

  // Resolve system theme
  useEffect(() => {
    const updateResolvedTheme = () => {
      if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        setResolvedTheme(prefersDark ? 'dark' : 'light')
      } else {
        setResolvedTheme(theme)
      }
    }

    updateResolvedTheme()

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (theme === 'system') {
        updateResolvedTheme()
      }
    }

    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [theme])

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement

    if (resolvedTheme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [resolvedTheme])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem(THEME_KEY, newTheme)
  }

  const toggleTheme = () => {
    if (theme === 'system') {
      setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
    } else {
      setTheme(theme === 'dark' ? 'light' : 'dark')
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

/**
 * Theme Toggle Button Component
 */
import { Moon, Sun, Monitor } from 'lucide-react'

interface ThemeToggleProps {
  /** Show all three options (light/dark/system) or just toggle */
  showSystem?: boolean
  className?: string
}

export function ThemeToggle({ showSystem = false, className = '' }: ThemeToggleProps) {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme()

  if (showSystem) {
    return (
      <div className={`flex items-center gap-1 p-1 rounded-lg bg-theme-hover ${className}`}>
        <button
          onClick={() => setTheme('light')}
          className={`p-2 rounded-md transition-colors ${
            theme === 'light' ? 'bg-theme-card text-accent-primary' : 'text-theme-text-muted hover:text-theme-text-primary'
          }`}
          title="Light mode"
        >
          <Sun className="h-4 w-4" />
        </button>
        <button
          onClick={() => setTheme('dark')}
          className={`p-2 rounded-md transition-colors ${
            theme === 'dark' ? 'bg-theme-card text-accent-primary' : 'text-theme-text-muted hover:text-theme-text-primary'
          }`}
          title="Dark mode"
        >
          <Moon className="h-4 w-4" />
        </button>
        <button
          onClick={() => setTheme('system')}
          className={`p-2 rounded-md transition-colors ${
            theme === 'system' ? 'bg-theme-card text-accent-primary' : 'text-theme-text-muted hover:text-theme-text-primary'
          }`}
          title="System preference"
        >
          <Monitor className="h-4 w-4" />
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={toggleTheme}
      className={`p-2 rounded-lg text-theme-text-muted hover:text-theme-text-primary hover:bg-theme-hover transition-colors ${className}`}
      title={resolvedTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {resolvedTheme === 'dark' ? (
        <Sun className="h-5 w-5" />
      ) : (
        <Moon className="h-5 w-5" />
      )}
    </button>
  )
}

export default ThemeContext
