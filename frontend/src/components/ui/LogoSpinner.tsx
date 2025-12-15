/**
 * LogoSpinner Component
 *
 * Zeigt das AuditLogo mit einer Uhr-Animation.
 * Die Minutenmarkierungen leuchten progressiv auf (0-100%).
 */

import { useEffect, useState } from 'react';

interface LogoSpinnerProps {
  /** Fortschritt 0-100, undefined für indeterminate */
  progress?: number;
  /** Größe in Pixel */
  size?: number;
  /** Nur Logo ohne Animation */
  static?: boolean;
  /** Zusätzliche CSS-Klassen */
  className?: string;
}

export function LogoSpinner({
  progress,
  size = 120,
  static: isStatic = false,
  className = ''
}: LogoSpinnerProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const isIndeterminate = progress === undefined && !isStatic;

  // Anzahl der Minutenmarkierungen (wie bei einer Uhr)
  const tickCount = 60;
  const radius = (size / 2) - 8;
  const center = size / 2;
  const logoSize = size * 0.6;

  // Animation für indeterminate Modus
  useEffect(() => {
    if (isIndeterminate) {
      const interval = setInterval(() => {
        setAnimatedProgress(prev => (prev + 1) % 101);
      }, 50);
      return () => clearInterval(interval);
    } else if (progress !== undefined) {
      setAnimatedProgress(progress);
    }
  }, [isIndeterminate, progress]);

  // Berechne welche Markierungen aktiv sind
  const activeTickCount = Math.floor((animatedProgress / 100) * tickCount);

  // Generiere Minutenmarkierungen
  const ticks = Array.from({ length: tickCount }, (_, i) => {
    const angle = (i * 360 / tickCount) - 90; // Start bei 12 Uhr (-90°)
    const radian = (angle * Math.PI) / 180;

    // Position der Markierung
    const x1 = center + (radius - 6) * Math.cos(radian);
    const y1 = center + (radius - 6) * Math.sin(radian);
    const x2 = center + radius * Math.cos(radian);
    const y2 = center + radius * Math.sin(radian);

    // Ist diese Markierung aktiv?
    let isActive = false;
    if (isIndeterminate) {
      // Bei indeterminate: Welleneffekt
      const waveStart = animatedProgress % tickCount;
      const waveLength = 15;
      const tickPosition = i;
      const distance = (tickPosition - waveStart + tickCount) % tickCount;
      isActive = distance < waveLength;
    } else {
      isActive = i < activeTickCount;
    }

    // Jede 5. Markierung ist länger (wie bei einer Uhr)
    const isHourMark = i % 5 === 0;
    const tickLength = isHourMark ? 8 : 4;
    const innerX = center + (radius - tickLength) * Math.cos(radian);
    const innerY = center + (radius - tickLength) * Math.sin(radian);

    return {
      key: i,
      x1: innerX,
      y1: innerY,
      x2,
      y2,
      isActive,
      isHourMark,
    };
  });

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-0"
      >
        {/* Hintergrund-Ring */}
        <circle
          cx={center}
          cy={center}
          r={radius - 4}
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          className="text-gray-200 dark:text-gray-700"
        />

        {/* Minutenmarkierungen */}
        {ticks.map(tick => (
          <line
            key={tick.key}
            x1={tick.x1}
            y1={tick.y1}
            x2={tick.x2}
            y2={tick.y2}
            strokeWidth={tick.isHourMark ? 3 : 2}
            strokeLinecap="round"
            className={`transition-all duration-150 ${
              tick.isActive
                ? 'stroke-blue-600 dark:stroke-blue-400'
                : 'stroke-gray-300 dark:stroke-gray-600'
            }`}
            style={{
              opacity: tick.isActive ? 1 : 0.4,
            }}
          />
        ))}

        {/* Fortschritts-Bogen (optional) */}
        {!isStatic && progress !== undefined && (
          <circle
            cx={center}
            cy={center}
            r={radius - 12}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * (radius - 12)}`}
            strokeDashoffset={`${2 * Math.PI * (radius - 12) * (1 - progress / 100)}`}
            className="text-blue-600 dark:text-blue-400 transition-all duration-300"
            transform={`rotate(-90 ${center} ${center})`}
          />
        )}
      </svg>

      {/* Logo im Zentrum */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        style={{ padding: (size - logoSize) / 2 }}
      >
        <img
          src="/auditlogo.png"
          alt="FlowAudit Logo"
          className={`w-full h-full object-contain ${
            isIndeterminate ? 'animate-pulse' : ''
          }`}
          onError={(e) => {
            // Fallback wenn Logo nicht geladen werden kann
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
          }}
        />
      </div>

      {/* Prozent-Anzeige (optional) */}
      {progress !== undefined && !isStatic && (
        <div
          className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-2
                     text-xs font-medium text-gray-600 dark:text-gray-400"
        >
          {Math.round(progress)}%
        </div>
      )}
    </div>
  );
}

/**
 * Vollbild-Ladebildschirm mit Logo
 */
interface LoadingScreenProps {
  /** Ladetext */
  message?: string;
  /** Fortschritt 0-100 */
  progress?: number;
}

export function LoadingScreen({ message = 'Wird geladen...', progress }: LoadingScreenProps) {
  return (
    <div className="fixed inset-0 bg-white dark:bg-gray-900 flex flex-col items-center justify-center z-50">
      <LogoSpinner size={160} progress={progress} />
      <p className="mt-6 text-lg text-gray-600 dark:text-gray-400 animate-pulse">
        {message}
      </p>
    </div>
  );
}

/**
 * Inline-Spinner für Buttons etc.
 */
export function InlineSpinner({ size = 24 }: { size?: number }) {
  return <LogoSpinner size={size} className="inline-block" />;
}

export default LogoSpinner;
