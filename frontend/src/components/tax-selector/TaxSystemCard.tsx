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
        'hover:shadow-lg hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        isSelected
          ? 'border-primary-500 bg-primary-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-primary-300'
      )}
    >
      {/* Ausgewählt-Indikator */}
      {isSelected && (
        <div className="absolute top-2 right-2">
          <svg
            className="w-6 h-6 text-primary-600"
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
          isSelected ? 'text-primary-700' : 'text-gray-900'
        )}
      >
        {title}
      </h3>

      {/* Untertitel */}
      <p className="text-sm text-gray-500 text-center mt-1">{subtitle}</p>

      {/* Feature-Count Badge */}
      <div
        className={clsx(
          'mt-3 px-3 py-1 rounded-full text-xs font-medium',
          isSelected
            ? 'bg-primary-100 text-primary-700'
            : 'bg-gray-100 text-gray-600'
        )}
      >
        {featureCount} Pflichtmerkmale
      </div>
    </button>
  );
}

export default TaxSystemCard;
