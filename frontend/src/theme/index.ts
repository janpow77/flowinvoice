/**
 * FlowAudit Theme System
 *
 * Zentrales Export-Modul für das Theme-System.
 *
 * Verwendung:
 *
 * 1. ThemeProvider in App.tsx einbinden:
 *    import { ThemeProvider } from './theme'
 *    <ThemeProvider><App /></ThemeProvider>
 *
 * 2. Theme in Komponenten nutzen:
 *    import { useTheme } from './theme'
 *    const { theme, isDark, toggleTheme } = useTheme()
 *
 * 3. CSS-Variablen verwenden:
 *    background-color: var(--color-bg-app);
 *    color: var(--color-text-primary);
 */

// Token-Typen
export type {
  Theme,
  ColorTokens,
  TypographyTokens,
  SpacingTokens,
  ShadowTokens,
  RadiusTokens,
  TransitionTokens,
} from './tokens'

// Gemeinsame Tokens
export {
  typography,
  spacing,
  radius,
  transitions,
} from './tokens'

// Themes
export { lightTheme } from './light'
export { darkTheme } from './dark'

// Context und Provider
export { ThemeProvider, useTheme, themeInitScript } from './ThemeContext'

// =============================================================================
// CSS Custom Property Namen (für Tailwind-Konfiguration)
// =============================================================================

export const cssVars = {
  // Background
  bgApp: 'var(--color-bg-app)',
  bgPanel: 'var(--color-bg-panel)',
  bgCard: 'var(--color-bg-card)',
  bgElevated: 'var(--color-bg-elevated)',
  bgInput: 'var(--color-bg-input)',
  bgDisabled: 'var(--color-bg-disabled)',
  bgHover: 'var(--color-bg-hover)',
  bgSelected: 'var(--color-bg-selected)',

  // Text
  textPrimary: 'var(--color-text-primary)',
  textSecondary: 'var(--color-text-secondary)',
  textMuted: 'var(--color-text-muted)',
  textInverse: 'var(--color-text-inverse)',
  textDisabled: 'var(--color-text-disabled)',
  textLink: 'var(--color-text-link)',
  textLinkHover: 'var(--color-text-link-hover)',

  // Border
  borderDefault: 'var(--color-border-default)',
  borderSubtle: 'var(--color-border-subtle)',
  borderStrong: 'var(--color-border-strong)',
  borderFocus: 'var(--color-border-focus)',
  borderError: 'var(--color-border-error)',

  // Accent
  accentPrimary: 'var(--color-accent-primary)',
  accentPrimaryHover: 'var(--color-accent-primary-hover)',
  accentPrimaryActive: 'var(--color-accent-primary-active)',
  accentSecondary: 'var(--color-accent-secondary)',
  accentSecondaryHover: 'var(--color-accent-secondary-hover)',

  // Status
  statusSuccess: 'var(--color-status-success)',
  statusSuccessBg: 'var(--color-status-success-bg)',
  statusSuccessBorder: 'var(--color-status-success-border)',
  statusWarning: 'var(--color-status-warning)',
  statusWarningBg: 'var(--color-status-warning-bg)',
  statusWarningBorder: 'var(--color-status-warning-border)',
  statusDanger: 'var(--color-status-danger)',
  statusDangerBg: 'var(--color-status-danger-bg)',
  statusDangerBorder: 'var(--color-status-danger-border)',
  statusInfo: 'var(--color-status-info)',
  statusInfoBg: 'var(--color-status-info-bg)',
  statusInfoBorder: 'var(--color-status-info-border)',
  statusDisabled: 'var(--color-status-disabled)',
  statusDisabledBg: 'var(--color-status-disabled-bg)',

  // UI
  uiScrollbarTrack: 'var(--color-ui-scrollbar-track)',
  uiScrollbarThumb: 'var(--color-ui-scrollbar-thumb)',
  uiOverlay: 'var(--color-ui-overlay)',
  uiShadow: 'var(--color-ui-shadow)',
  uiDivider: 'var(--color-ui-divider)',
  uiFocusRing: 'var(--color-ui-focus-ring)',

  // Shadows
  shadowSm: 'var(--shadow-sm)',
  shadowMd: 'var(--shadow-md)',
  shadowLg: 'var(--shadow-lg)',
  shadowXl: 'var(--shadow-xl)',
  shadowInner: 'var(--shadow-inner)',
} as const

// =============================================================================
// Tailwind Class Helpers
// =============================================================================

/**
 * Klassen für semantische Hintergründe
 */
export const bgClasses = {
  app: 'bg-theme-app',
  panel: 'bg-theme-panel',
  card: 'bg-theme-card',
  elevated: 'bg-theme-elevated',
  input: 'bg-theme-input',
  disabled: 'bg-theme-disabled',
  hover: 'hover:bg-theme-hover',
  selected: 'bg-theme-selected',
} as const

/**
 * Klassen für semantische Textfarben
 */
export const textClasses = {
  primary: 'text-theme-primary',
  secondary: 'text-theme-secondary',
  muted: 'text-theme-muted',
  inverse: 'text-theme-inverse',
  disabled: 'text-theme-disabled',
  link: 'text-theme-link hover:text-theme-link-hover',
} as const

/**
 * Klassen für semantische Rahmen
 */
export const borderClasses = {
  default: 'border-theme-default',
  subtle: 'border-theme-subtle',
  strong: 'border-theme-strong',
  focus: 'focus:border-theme-focus',
  error: 'border-theme-error',
} as const

/**
 * Klassen für Status-Indikatoren
 */
export const statusClasses = {
  success: 'text-status-success',
  successBg: 'bg-status-success-bg text-status-success border border-status-success-border',
  warning: 'text-status-warning',
  warningBg: 'bg-status-warning-bg text-status-warning border border-status-warning-border',
  danger: 'text-status-danger',
  dangerBg: 'bg-status-danger-bg text-status-danger border border-status-danger-border',
  info: 'text-status-info',
  infoBg: 'bg-status-info-bg text-status-info border border-status-info-border',
  disabled: 'text-status-disabled',
  disabledBg: 'bg-status-disabled-bg text-status-disabled',
} as const
