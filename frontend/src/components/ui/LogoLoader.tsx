/**
 * FlowAudit LogoLoader
 *
 * CI-konformer Ladeindikator auf Basis des FlowAudit-Logos.
 *
 * Grundprinzipien:
 * - Das Logo selbst bleibt IMMER statisch und unverändert
 * - Bewegung findet ausschließlich um das Logo herum statt
 * - Das Logo ist stets klar erkennbar und im Zentrum platziert
 *
 * Varianten:
 * - ring: Kreisförmiger Fortschrittsring (bevorzugt)
 * - ticks: 60 Minutenstriche (Uhr-Analogie)
 *
 * Der Ring schließt sich progressiv von 0% bis 100%.
 * 100% entsprechen didaktisch 60 Minuten (Uhr-Analogie).
 */

import { useMemo } from 'react'
import { useTheme } from '../../theme'

// =============================================================================
// Types
// =============================================================================

interface LogoLoaderProps {
  /** Fortschritt in Prozent (0-100). Wenn nicht gesetzt, wird indeterminate */
  progress?: number
  /** Unbestimmter Fortschritt (zyklische Animation) */
  indeterminate?: boolean
  /** Größe des Loaders */
  size?: 'small' | 'medium' | 'large'
  /** Variante der Animation */
  variant?: 'ring' | 'ticks'
  /** Optionaler Text unter dem Loader */
  text?: string
  /** Zusätzliche CSS-Klassen */
  className?: string
}

// =============================================================================
// Size Configuration
// =============================================================================

const sizeConfig = {
  small: {
    container: 80,
    logo: 40,
    strokeWidth: 3,
    ringRadius: 34,
    tickLength: 6,
    tickWidth: 1.5,
  },
  medium: {
    container: 120,
    logo: 60,
    strokeWidth: 4,
    ringRadius: 52,
    tickLength: 8,
    tickWidth: 2,
  },
  large: {
    container: 180,
    logo: 90,
    strokeWidth: 5,
    ringRadius: 78,
    tickLength: 10,
    tickWidth: 2.5,
  },
}

// =============================================================================
// Ring Variant Component
// =============================================================================

interface RingProps {
  size: typeof sizeConfig[keyof typeof sizeConfig]
  progress: number
  indeterminate: boolean
  accentColor: string
  trackColor: string
}

function Ring({ size, progress, indeterminate, accentColor, trackColor }: RingProps) {
  const circumference = 2 * Math.PI * size.ringRadius
  const offset = circumference - (progress / 100) * circumference

  return (
    <svg
      className={`absolute inset-0 ${indeterminate ? 'animate-spin-slow' : ''}`}
      style={{
        width: size.container,
        height: size.container,
        transform: 'rotate(-90deg)',
      }}
    >
      {/* Background Ring (Track) */}
      <circle
        cx={size.container / 2}
        cy={size.container / 2}
        r={size.ringRadius}
        fill="none"
        stroke={trackColor}
        strokeWidth={size.strokeWidth}
      />
      {/* Progress Ring */}
      <circle
        cx={size.container / 2}
        cy={size.container / 2}
        r={size.ringRadius}
        fill="none"
        stroke={accentColor}
        strokeWidth={size.strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={indeterminate ? circumference * 0.75 : offset}
        style={{
          transition: indeterminate ? 'none' : 'stroke-dashoffset 0.3s ease',
        }}
      />
    </svg>
  )
}

// =============================================================================
// Ticks Variant Component (60 Minute Marks)
// =============================================================================

interface TicksProps {
  size: typeof sizeConfig[keyof typeof sizeConfig]
  progress: number
  indeterminate: boolean
  accentColor: string
  trackColor: string
}

function Ticks({ size, progress, indeterminate, accentColor, trackColor }: TicksProps) {
  const center = size.container / 2
  const innerRadius = size.ringRadius - size.tickLength
  const outerRadius = size.ringRadius

  // Wie viele Ticks sollen aktiv sein (basierend auf Fortschritt)
  const activeTicks = Math.floor((progress / 100) * 60)

  // Für indeterminate: Animation durch CSS
  const ticks = useMemo(() => {
    return Array.from({ length: 60 }, (_, i) => {
      const angle = (i * 6 - 90) * (Math.PI / 180) // 6 Grad pro Tick, Start bei 12 Uhr
      const x1 = center + innerRadius * Math.cos(angle)
      const y1 = center + innerRadius * Math.sin(angle)
      const x2 = center + outerRadius * Math.cos(angle)
      const y2 = center + outerRadius * Math.sin(angle)

      const isActive = indeterminate ? false : i < activeTicks
      const isMajor = i % 5 === 0 // Jeder 5. Tick ist ein Haupttick

      return {
        key: i,
        x1,
        y1,
        x2,
        y2,
        isActive,
        isMajor,
      }
    })
  }, [center, innerRadius, outerRadius, activeTicks, indeterminate])

  return (
    <svg
      className={`absolute inset-0 ${indeterminate ? 'logo-loader-ticks-spin' : ''}`}
      style={{
        width: size.container,
        height: size.container,
      }}
    >
      {ticks.map((tick) => (
        <line
          key={tick.key}
          x1={tick.x1}
          y1={tick.y1}
          x2={tick.x2}
          y2={tick.y2}
          stroke={tick.isActive ? accentColor : trackColor}
          strokeWidth={tick.isMajor ? size.tickWidth * 1.5 : size.tickWidth}
          strokeLinecap="round"
          style={{
            opacity: tick.isActive ? 1 : 0.4,
            transition: 'stroke 0.15s ease, opacity 0.15s ease',
          }}
        />
      ))}
    </svg>
  )
}

// =============================================================================
// Main LogoLoader Component
// =============================================================================

export function LogoLoader({
  progress,
  indeterminate = false,
  size = 'medium',
  variant = 'ring',
  text,
  className = '',
}: LogoLoaderProps) {
  const { theme, isDark } = useTheme()

  const config = sizeConfig[size]

  // Wenn weder progress noch indeterminate gesetzt, dann indeterminate
  const isIndeterminate = indeterminate || progress === undefined

  // Aktueller Fortschritt
  const currentProgress = isIndeterminate ? 25 : Math.min(100, Math.max(0, progress ?? 0))

  // Farben aus Theme
  const accentColor = theme.colors.accent.primary
  const trackColor = theme.colors.border.subtle

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 ${className}`}
      role="status"
      aria-live="polite"
      aria-busy={currentProgress < 100}
    >
      {/* Loader Container */}
      <div
        className="relative flex items-center justify-center"
        style={{
          width: config.container,
          height: config.container,
        }}
      >
        {/* Animation Ring/Ticks */}
        {variant === 'ring' ? (
          <Ring
            size={config}
            progress={currentProgress}
            indeterminate={isIndeterminate}
            accentColor={accentColor}
            trackColor={trackColor}
          />
        ) : (
          <Ticks
            size={config}
            progress={currentProgress}
            indeterminate={isIndeterminate}
            accentColor={accentColor}
            trackColor={trackColor}
          />
        )}

        {/* Logo - STATISCH UND UNVERÄNDERT */}
        <div
          className="absolute flex items-center justify-center rounded-lg"
          style={{
            width: config.logo,
            height: config.logo,
            // Logo-Hintergrund für bessere Lesbarkeit in Dark Mode
            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
          }}
        >
          <img
            src="/auditlogo.png"
            alt="FlowAudit"
            style={{
              width: config.logo * 0.9,
              height: config.logo * 0.9,
              objectFit: 'contain',
            }}
            // Logo ignoriert Theme-Tokens - KEINE Farbanpassung!
          />
        </div>
      </div>

      {/* Optional: Status-Text */}
      {text && (
        <span
          className="text-sm font-medium"
          style={{ color: theme.colors.text.muted }}
        >
          {text}
        </span>
      )}

      {/* Prozentanzeige bei determiniertem Fortschritt */}
      {!isIndeterminate && progress !== undefined && (
        <span
          className="text-xs tabular-nums"
          style={{ color: theme.colors.text.muted }}
        >
          {Math.round(currentProgress)}%
        </span>
      )}

      {/* Screen Reader Text */}
      <span className="sr-only">
        {isIndeterminate
          ? 'Wird geladen...'
          : `Fortschritt: ${Math.round(currentProgress)} Prozent`}
      </span>
    </div>
  )
}

// =============================================================================
// Convenience Components
// =============================================================================

/** Vollbild-Loader für initiales Laden */
export function FullPageLoader({ text = 'Wird geladen...' }: { text?: string }) {
  const { theme } = useTheme()

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ backgroundColor: theme.colors.background.app }}
    >
      <LogoLoader size="large" text={text} />
    </div>
  )
}

/** Inline-Loader für Cards/Panels */
export function InlineLoader({ text }: { text?: string }) {
  return (
    <div className="flex items-center justify-center py-8">
      <LogoLoader size="small" text={text} />
    </div>
  )
}

/** Overlay-Loader für Modal-Aktionen */
export function OverlayLoader({ text }: { text?: string }) {
  const { theme } = useTheme()

  return (
    <div
      className="absolute inset-0 flex items-center justify-center z-10 rounded-lg"
      style={{ backgroundColor: theme.colors.ui.overlay }}
    >
      <LogoLoader size="medium" text={text} />
    </div>
  )
}

export default LogoLoader
