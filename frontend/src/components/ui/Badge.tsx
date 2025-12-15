/**
 * Badge & Status Components
 *
 * Badges, Status-Indikatoren und Ampel-Anzeigen.
 */

import { ReactNode, HTMLAttributes } from 'react';
import clsx from 'clsx';

/* =============================================================================
   Badge
   ============================================================================= */

type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Variante */
  variant?: BadgeVariant;
  /** Größe */
  size?: BadgeSize;
  /** Mit Punkt davor */
  dot?: boolean;
  /** Kinder-Elemente */
  children: ReactNode;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'badge',
  primary: 'badge-primary',
  success: 'badge-success',
  warning: 'badge-warning',
  error: 'badge-error',
  info: 'badge-info',
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: '',
  lg: 'text-sm px-3 py-1',
};

const dotClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-500',
  primary: 'bg-primary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  error: 'bg-error-500',
  info: 'bg-info-500',
};

export function Badge({
  variant = 'default',
  size = 'md',
  dot = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={clsx(
        variantClasses[variant],
        sizeClasses[size],
        dot && 'flex items-center gap-1.5',
        className
      )}
      {...props}
    >
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full', dotClasses[variant])} />}
      {children}
    </span>
  );
}

/* =============================================================================
   StatusDot - Einfacher Status-Punkt
   ============================================================================= */

type StatusDotVariant = 'online' | 'offline' | 'busy' | 'away' | 'success' | 'warning' | 'error';

interface StatusDotProps {
  /** Status */
  status: StatusDotVariant;
  /** Mit Puls-Animation */
  pulse?: boolean;
  /** Größe in Pixel */
  size?: number;
  /** Zusätzliche Klassen */
  className?: string;
}

const statusDotClasses: Record<StatusDotVariant, string> = {
  online: 'status-dot-online',
  offline: 'status-dot-offline',
  busy: 'status-dot-busy',
  away: 'status-dot-away',
  success: 'status-dot-online',
  warning: 'status-dot-away',
  error: 'status-dot-busy',
};

export function StatusDot({ status, pulse = false, size = 8, className }: StatusDotProps) {
  return (
    <span
      className={clsx(
        statusDotClasses[status],
        pulse && 'animate-pulse',
        className
      )}
      style={{ width: size, height: size }}
    />
  );
}

/* =============================================================================
   TrafficLight - Ampel-Anzeige
   ============================================================================= */

type TrafficLightStatus = 'green' | 'yellow' | 'red' | 'off';

interface TrafficLightProps {
  /** Aktueller Status */
  status: TrafficLightStatus;
  /** Größe */
  size?: 'sm' | 'md' | 'lg';
  /** Mit Label */
  label?: string;
  /** Zusätzliche Klassen */
  className?: string;
}

const trafficLightSizes = {
  sm: 'w-3 h-3',
  md: 'w-4 h-4',
  lg: 'w-6 h-6',
};

export function TrafficLight({ status, size = 'md', label, className }: TrafficLightProps) {
  const sizeClass = trafficLightSizes[size];

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <div className="flex items-center gap-1">
        <span
          className={clsx(
            sizeClass,
            'rounded-full',
            status === 'green' ? 'traffic-light-green' : 'bg-gray-200'
          )}
        />
        <span
          className={clsx(
            sizeClass,
            'rounded-full',
            status === 'yellow' ? 'traffic-light-yellow' : 'bg-gray-200'
          )}
        />
        <span
          className={clsx(
            sizeClass,
            'rounded-full',
            status === 'red' ? 'traffic-light-red' : 'bg-gray-200'
          )}
        />
      </div>
      {label && <span className="text-sm text-gray-600">{label}</span>}
    </div>
  );
}

/* =============================================================================
   Alert - Hinweis-Box
   ============================================================================= */

type AlertVariant = 'info' | 'success' | 'warning' | 'error';

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  /** Variante */
  variant?: AlertVariant;
  /** Titel */
  title?: string;
  /** Icon links */
  icon?: ReactNode;
  /** Kann geschlossen werden */
  dismissible?: boolean;
  /** Callback beim Schließen */
  onDismiss?: () => void;
  /** Kinder-Elemente */
  children: ReactNode;
}

const alertVariantClasses: Record<AlertVariant, string> = {
  info: 'alert-info',
  success: 'alert-success',
  warning: 'alert-warning',
  error: 'alert-error',
};

const alertIcons: Record<AlertVariant, ReactNode> = {
  info: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

export function Alert({
  variant = 'info',
  title,
  icon,
  dismissible = false,
  onDismiss,
  className,
  children,
  ...props
}: AlertProps) {
  return (
    <div
      className={clsx(alertVariantClasses[variant], className)}
      role="alert"
      {...props}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          {icon || alertIcons[variant]}
        </div>
        <div className="ml-3 flex-1">
          {title && <h3 className="font-medium mb-1">{title}</h3>}
          <div className="text-sm">{children}</div>
        </div>
        {dismissible && (
          <button
            type="button"
            onClick={onDismiss}
            className="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex items-center justify-center h-8 w-8 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-offset-2"
            aria-label="Schließen"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

export default Badge;
