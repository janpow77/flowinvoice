import { CheckCircle, XCircle, AlertTriangle, HelpCircle, Clock, Edit2 } from 'lucide-react'
import clsx from 'clsx'
import type { FeatureStatus } from '@/lib/types'

interface FeatureStatusBadgeProps {
  status: FeatureStatus
  label?: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const statusConfig: Record<FeatureStatus, {
  icon: typeof CheckCircle
  color: string
  bgColor: string
  label: string
}> = {
  VALID: {
    icon: CheckCircle,
    color: 'text-status-success',
    bgColor: 'bg-status-success-bg',
    label: 'Korrekt',
  },
  INVALID: {
    icon: XCircle,
    color: 'text-status-danger',
    bgColor: 'bg-status-danger-bg',
    label: 'Fehler',
  },
  WARNING: {
    icon: AlertTriangle,
    color: 'text-status-warning',
    bgColor: 'bg-status-warning-bg',
    label: 'Warnung',
  },
  MISSING: {
    icon: HelpCircle,
    color: 'text-theme-text-muted',
    bgColor: 'bg-theme-surface',
    label: 'Fehlt',
  },
  PENDING: {
    icon: Clock,
    color: 'text-status-info',
    bgColor: 'bg-status-info-bg',
    label: 'Ausstehend',
  },
  CORRECTED: {
    icon: Edit2,
    color: 'text-theme-primary',
    bgColor: 'bg-theme-primary/10',
    label: 'Korrigiert',
  },
}

const sizeConfig = {
  sm: { icon: 'w-3 h-3', text: 'text-xs', padding: 'px-1.5 py-0.5' },
  md: { icon: 'w-4 h-4', text: 'text-sm', padding: 'px-2 py-1' },
  lg: { icon: 'w-5 h-5', text: 'text-base', padding: 'px-2.5 py-1.5' },
}

export default function FeatureStatusBadge({
  status,
  label,
  size = 'sm',
  showLabel = true,
}: FeatureStatusBadgeProps) {
  const config = statusConfig[status]
  const sizes = sizeConfig[size]
  const Icon = config.icon

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full font-medium',
        config.bgColor,
        config.color,
        sizes.padding,
        sizes.text
      )}
      title={label || config.label}
    >
      <Icon className={sizes.icon} />
      {showLabel && <span>{label || config.label}</span>}
    </span>
  )
}
