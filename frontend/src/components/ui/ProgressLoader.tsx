/**
 * ProgressLoader Component
 *
 * Zeigt Fortschritt bei Dokumentenverarbeitung mit dem Logo-Spinner.
 */

import { LogoSpinner } from './LogoSpinner';

interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface ProgressLoaderProps {
  /** Titel */
  title?: string;
  /** Aktuelle Nachricht */
  message?: string;
  /** Fortschritt 0-100 */
  progress?: number;
  /** Einzelne Schritte */
  steps?: ProgressStep[];
  /** Spinner-Größe */
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 80,
  md: 120,
  lg: 160,
};

export function ProgressLoader({
  title,
  message,
  progress,
  steps,
  size = 'md',
}: ProgressLoaderProps) {
  const spinnerSize = sizeMap[size];

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <LogoSpinner size={spinnerSize} progress={progress} />

      {title && (
        <h3 className="mt-6 text-lg font-semibold text-theme-text-primary">
          {title}
        </h3>
      )}

      {message && (
        <p className="mt-2 text-sm text-theme-text-muted">
          {message}
        </p>
      )}

      {/* Schritte anzeigen */}
      {steps && steps.length > 0 && (
        <div className="mt-6 w-full max-w-xs space-y-2">
          {steps.map((step) => (
            <div
              key={step.id}
              className="flex items-center text-sm"
            >
              <div className="mr-3">
                {step.status === 'completed' && (
                  <svg className="w-5 h-5 text-status-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {step.status === 'running' && (
                  <div className="w-5 h-5 border-2 border-status-info border-t-transparent rounded-full animate-spin" />
                )}
                {step.status === 'pending' && (
                  <div className="w-5 h-5 border-2 border-theme-border-default rounded-full" />
                )}
                {step.status === 'error' && (
                  <svg className="w-5 h-5 text-status-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>
              <span
                className={`${
                  step.status === 'completed'
                    ? 'text-status-success'
                    : step.status === 'running'
                    ? 'text-status-info font-medium'
                    : step.status === 'error'
                    ? 'text-status-danger'
                    : 'text-theme-text-muted'
                }`}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Dokument-Verarbeitungs-Overlay
 */
interface DocumentProcessingOverlayProps {
  isVisible: boolean;
  documentName?: string;
  currentStep?: string;
  progress?: number;
}

export function DocumentProcessingOverlay({
  isVisible,
  documentName,
  currentStep,
  progress,
}: DocumentProcessingOverlayProps) {
  if (!isVisible) return null;

  const steps: ProgressStep[] = [
    { id: 'upload', label: 'Datei hochladen', status: progress && progress > 0 ? 'completed' : 'running' },
    { id: 'parse', label: 'PDF analysieren', status: progress && progress > 20 ? 'completed' : progress && progress > 0 ? 'running' : 'pending' },
    { id: 'precheck', label: 'Vorprüfung', status: progress && progress > 40 ? 'completed' : progress && progress > 20 ? 'running' : 'pending' },
    { id: 'llm', label: 'KI-Analyse', status: progress && progress > 70 ? 'completed' : progress && progress > 40 ? 'running' : 'pending' },
    { id: 'result', label: 'Ergebnis erstellen', status: progress && progress >= 100 ? 'completed' : progress && progress > 70 ? 'running' : 'pending' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-theme-card rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        <ProgressLoader
          title={documentName ? `Verarbeite: ${documentName}` : 'Dokument wird verarbeitet'}
          message={currentStep}
          progress={progress}
          steps={steps}
          size="lg"
        />
      </div>
    </div>
  );
}

export default ProgressLoader;
