/**
 * FlowAudit Login Template
 *
 * Wiederverwendbares Login-Template mit animiertem Fisch und Binary-Datenwasser.
 * Das Logo wird 1:1 aus /public/auditlogo.png verwendet.
 *
 * Features:
 * - Springender Fisch-Animation (das Original-Logo)
 * - Binary-Datenwasser mit fließenden 0 und 1
 * - Wellenanimation
 * - Frosted Glass Login-Karte
 * - Responsive Design
 */

import { ReactNode } from 'react';

// =============================================================================
// CSS Animationen
// =============================================================================

export const loginAnimations = `
  @keyframes fishJump {
    0% {
      transform: translateY(150px) translateX(-80px) rotate(-15deg) scaleX(-1);
      opacity: 0;
    }
    15% {
      opacity: 1;
    }
    50% {
      transform: translateY(-200px) translateX(0px) rotate(5deg) scaleX(-1);
    }
    85% {
      opacity: 1;
    }
    100% {
      transform: translateY(150px) translateX(80px) rotate(25deg) scaleX(-1);
      opacity: 0;
    }
  }

  .animate-fish-jump {
    animation: fishJump 7s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    filter: drop-shadow(0 0 25px rgba(96, 165, 250, 0.7));
  }

  @keyframes waveMove {
    0% { transform: translateX(0); }
    50% { transform: translateX(-25px); }
    100% { transform: translateX(0); }
  }

  .wave-animation {
    animation: waveMove 6s ease-in-out infinite;
  }

  .wave-animation-reverse {
    animation: waveMove 8s ease-in-out infinite reverse;
  }

  @keyframes dataFlow {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  .data-flow {
    animation: dataFlow 20s linear infinite;
  }

  .data-flow-fast {
    animation: dataFlow 15s linear infinite;
  }

  .data-flow-slow {
    animation: dataFlow 25s linear infinite reverse;
  }

  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.8; }
  }

  .binary-pulse {
    animation: binaryPulse 3s ease-in-out infinite;
  }
`;

// =============================================================================
// Statische Binärsequenzen (verhindert Flackern)
// =============================================================================

const BINARY_LINES = [
  '0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1',
  '1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0',
  '0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0',
  '1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1',
  '0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0',
];

// =============================================================================
// Springender Fisch - verwendet das echte Logo (PNG)
// =============================================================================

interface JumpingFishProps {
  /** Pfad zum Logo (default: /auditlogo.png) */
  logoPath?: string;
}

export function JumpingFish({ logoPath = '/auditlogo.png' }: JumpingFishProps) {
  return (
    <img
      src={logoPath}
      alt="Jumping Fish"
      className="w-full h-full object-contain"
    />
  );
}

// =============================================================================
// Binäres Datenwasser - fließende 0 und 1
// =============================================================================

export function BinaryDataWater() {
  const binaryLines = BINARY_LINES;

  return (
    <div className="absolute bottom-0 left-0 right-0 h-48 overflow-hidden pointer-events-none">
      {/* Wellenförmiger Clip-Path über dem Binärcode */}
      <svg className="absolute bottom-0 left-0 right-0 h-full w-full" preserveAspectRatio="none">
        <defs>
          <clipPath id="waveClip">
            <path d="M0,60 Q180,20 360,50 T720,40 T1080,55 T1440,45 L1440,200 L0,200 Z" />
          </clipPath>
        </defs>
      </svg>

      {/* Hintere Datenschicht (dunkler, langsamer) */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-blue-950/90 via-blue-900/70 to-transparent">
        <div className="data-flow-slow whitespace-nowrap font-mono text-xs leading-relaxed pt-8">
          <span className="text-blue-400/40">{binaryLines[0]} {binaryLines[0]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-xs leading-relaxed">
          <span className="text-cyan-400/30">{binaryLines[1]} {binaryLines[1]}</span>
        </div>
      </div>

      {/* Mittlere Datenschicht */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-800/80 via-blue-700/50 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-sm leading-relaxed pt-4">
          <span className="text-blue-300/50">{binaryLines[2]} {binaryLines[2]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-sm leading-relaxed">
          <span className="text-cyan-300/40">{binaryLines[3]} {binaryLines[3]}</span>
        </div>
      </div>

      {/* Vordere Datenschicht (heller, schneller) */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-blue-600/90 via-blue-500/60 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-base leading-relaxed pt-2 binary-pulse">
          <span className="text-blue-200/70">{binaryLines[4]} {binaryLines[4]}</span>
        </div>
      </div>

      {/* Wellenförmige Oberfläche */}
      <div className="absolute bottom-16 left-0 right-0 wave-animation">
        <svg className="w-full h-12" viewBox="0 0 1440 48" preserveAspectRatio="none">
          <path
            fill="rgba(96, 165, 250, 0.3)"
            d="M0,24 Q180,8 360,20 T720,16 T1080,22 T1440,18 L1440,48 L0,48 Z"
          />
        </svg>
      </div>
      <div className="absolute bottom-12 left-0 right-0 wave-animation-reverse">
        <svg className="w-full h-10" viewBox="0 0 1440 40" preserveAspectRatio="none">
          <path
            fill="rgba(59, 130, 246, 0.4)"
            d="M0,20 Q180,4 360,16 T720,12 T1080,18 T1440,14 L1440,40 L0,40 Z"
          />
        </svg>
      </div>
    </div>
  );
}

// =============================================================================
// Dekorative Blasen
// =============================================================================

export function DecorativeBubbles() {
  return (
    <>
      <div
        className="absolute bottom-40 left-1/4 w-3 h-3 bg-blue-300/30 rounded-full animate-bounce"
        style={{ animationDelay: '0s', animationDuration: '3s' }}
      />
      <div
        className="absolute bottom-52 left-1/3 w-2 h-2 bg-blue-200/20 rounded-full animate-bounce"
        style={{ animationDelay: '1s', animationDuration: '4s' }}
      />
      <div
        className="absolute bottom-36 right-1/4 w-4 h-4 bg-blue-300/25 rounded-full animate-bounce"
        style={{ animationDelay: '0.5s', animationDuration: '3.5s' }}
      />
      <div
        className="absolute bottom-60 right-1/3 w-2 h-2 bg-blue-200/30 rounded-full animate-bounce"
        style={{ animationDelay: '1.5s', animationDuration: '4.5s' }}
      />
    </>
  );
}

// =============================================================================
// Main LoginTemplate Component
// =============================================================================

export interface LoginTemplateProps {
  /** Pfad zum Logo (default: /auditlogo.png) */
  logoPath?: string;
  /** Titel unter dem Logo */
  title?: string;
  /** Untertitel unter dem Titel */
  subtitle?: string;
  /** Inhalt der Login-Karte (Formular) */
  children: ReactNode;
  /** Footer-Inhalt unter dem Formular */
  footer?: ReactNode;
  /** Logo-Höhe in Tailwind-Klassen (default: h-24) */
  logoHeight?: string;
  /** Zeige springenden Fisch-Animation */
  showJumpingFish?: boolean;
  /** Zeige Binary-Datenwasser */
  showBinaryWater?: boolean;
  /** Zeige dekorative Blasen */
  showBubbles?: boolean;
}

export function LoginTemplate({
  logoPath = '/auditlogo.png',
  title = 'flowaudit',
  subtitle = 'Automated Audit Systems',
  children,
  footer,
  logoHeight = 'h-24',
  showJumpingFish = true,
  showBinaryWater = true,
  showBubbles = true,
}: LoginTemplateProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 relative overflow-hidden flex flex-col justify-center items-center py-12 sm:px-6 lg:px-8">
      <style>{loginAnimations}</style>

      {/* Binary-Datenwasser */}
      {showBinaryWater && <BinaryDataWater />}

      {/* Springender Fisch */}
      {showJumpingFish && (
        <div className="absolute bottom-20 left-1/2 -ml-16 z-20 w-32 h-20 animate-fish-jump pointer-events-none">
          <JumpingFish logoPath={logoPath} />
        </div>
      )}

      {/* Login-Bereich */}
      <div className="relative z-30 sm:mx-auto sm:w-full sm:max-w-md px-4">
        {/* Logo und Überschrift */}
        <div className="text-center mb-8">
          <img
            src={logoPath}
            alt={`${title} Logo`}
            className={`${logoHeight} w-auto mx-auto mb-4 drop-shadow-lg`}
          />
          <h1 className="text-5xl sm:text-6xl font-extrabold text-white drop-shadow-lg tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-2 text-blue-200 text-sm uppercase tracking-widest font-medium">
              {subtitle}
            </p>
          )}
        </div>

        {/* Login-Karte (Frosted Glass) */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          {children}

          {/* Footer */}
          {footer && (
            <div className="mt-6 pt-4 border-t border-white/10">
              {footer}
            </div>
          )}
        </div>
      </div>

      {/* Dekorative Blasen */}
      {showBubbles && <DecorativeBubbles />}
    </div>
  );
}

export default LoginTemplate;
