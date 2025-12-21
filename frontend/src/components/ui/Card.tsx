/**
 * Card Component
 *
 * Karten-Container für Inhalte mit optionalem Header und Footer.
 */

import { ReactNode, HTMLAttributes } from 'react';
import clsx from 'clsx';

/* =============================================================================
   Card
   ============================================================================= */

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Hover-Effekt aktivieren */
  hover?: boolean;
  /** Padding entfernen */
  noPadding?: boolean;
  /** Kinder-Elemente */
  children: ReactNode;
}

export function Card({ hover = false, noPadding = false, className, children, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'card',
        hover && 'card-hover',
        noPadding && '[&>.card-body]:p-0',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/* =============================================================================
   CardHeader
   ============================================================================= */

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  /** Titel */
  title?: string;
  /** Untertitel */
  subtitle?: string;
  /** Action-Bereich rechts */
  action?: ReactNode;
  /** Kinder-Elemente (überschreibt title/subtitle) */
  children?: ReactNode;
}

export function CardHeader({ title, subtitle, action, className, children, ...props }: CardHeaderProps) {
  return (
    <div className={clsx('card-header', className)} {...props}>
      {children ? (
        children
      ) : (
        <div className="flex items-center justify-between">
          <div>
            {title && <h3 className="text-lg font-semibold text-theme-text-primary">{title}</h3>}
            {subtitle && <p className="text-sm text-theme-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
    </div>
  );
}

/* =============================================================================
   CardBody
   ============================================================================= */

interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function CardBody({ className, children, ...props }: CardBodyProps) {
  return (
    <div className={clsx('card-body', className)} {...props}>
      {children}
    </div>
  );
}

/* =============================================================================
   CardFooter
   ============================================================================= */

interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function CardFooter({ className, children, ...props }: CardFooterProps) {
  return (
    <div className={clsx('card-footer', className)} {...props}>
      {children}
    </div>
  );
}

/* =============================================================================
   StatCard - Spezielle Karte für Statistiken
   ============================================================================= */

interface StatCardProps {
  /** Titel/Label */
  label: string;
  /** Hauptwert */
  value: string | number;
  /** Icon */
  icon?: ReactNode;
  /** Änderung (z.B. "+12%") */
  change?: string;
  /** Änderung ist positiv */
  changePositive?: boolean;
  /** Zusätzliche Klassen */
  className?: string;
}

export function StatCard({
  label,
  value,
  icon,
  change,
  changePositive,
  className,
}: StatCardProps) {
  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-theme-text-muted">{label}</p>
            <p className="text-2xl font-bold text-theme-text-primary mt-1">{value}</p>
            {change && (
              <p
                className={clsx(
                  'text-sm mt-1 flex items-center',
                  changePositive ? 'text-success-600' : 'text-error-600'
                )}
              >
                {changePositive ? (
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                )}
                {change}
              </p>
            )}
          </div>
          {icon && (
            <div className="p-3 bg-accent-primary/10 rounded-xl text-accent-primary">
              {icon}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}

export default Card;
