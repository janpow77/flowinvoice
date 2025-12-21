/**
 * TaxSystemCard Component
 *
 * Einzelne Karte für Steuersystem-Auswahl mit Flagge.
 */

import clsx from 'clsx';

interface TaxSystemCardProps {
  flag: string;
  title: string;
  subtitle: string;
  featureCount: number;
  isSelected?: boolean;
  onClick: () => void;
}

export function TaxSystemCard({
  flag,
  title,
  subtitle,
  featureCount,
  isSelected = false,
  onClick,
}: TaxSystemCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'relative flex flex-col items-center p-6 rounded-xl border-2 transition-all duration-200',
        'hover:shadow-lg hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2',
        isSelected
          ? 'border-accent-primary bg-accent-primary/10 shadow-md'
          : 'border-theme-border-default bg-theme-card hover:border-accent-primary/30'
      )}
    >
      {/* Ausgewählt-Indikator */}
      {isSelected && (
        <div className="absolute top-2 right-2">
          <svg
            className="w-6 h-6 text-accent-primary"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}

      {/* Flagge */}
      <span className="text-5xl mb-3" role="img" aria-label={title}>
        {flag}
      </span>

      {/* Titel */}
      <h3
        className={clsx(
          'text-lg font-semibold text-center',
          isSelected ? 'text-accent-primary' : 'text-theme-text-primary'
        )}
      >
        {title}
      </h3>

      {/* Untertitel */}
      <p className="text-sm text-theme-text-muted text-center mt-1">{subtitle}</p>

      {/* Feature-Count Badge */}
      <div
        className={clsx(
          'mt-3 px-3 py-1 rounded-full text-xs font-medium',
          isSelected
            ? 'bg-accent-primary/10 text-accent-primary'
            : 'bg-theme-hover text-theme-text-muted'
        )}
      >
        {featureCount} Pflichtmerkmale
      </div>
    </button>
  );
}

export default TaxSystemCard;
