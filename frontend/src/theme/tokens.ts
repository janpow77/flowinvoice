/**
 * FlowAudit Theme Tokens
 *
 * Semantische Farb- und Design-Tokens für das zentrale Theme-System.
 * Alle UI-Komponenten verwenden ausschließlich diese Tokens.
 *
 * Prinzip: Semantik vor Farbe - die Bedeutung steht über dem Design.
 */

// =============================================================================
// Semantische Token-Typen
// =============================================================================

export interface ColorTokens {
  /** Hintergrundfarben für verschiedene Ebenen */
  background: {
    /** Haupt-App-Hintergrund (dunkelste/hellste Ebene) */
    app: string
    /** Panel/Section-Hintergrund (mittlere Ebene) */
    panel: string
    /** Card/Container-Hintergrund (hervorgehobene Ebene) */
    card: string
    /** Erhöhte Elemente (Dropdowns, Tooltips) */
    elevated: string
    /** Eingabefelder */
    input: string
    /** Deaktivierte Elemente */
    disabled: string
    /** Hover-Zustand */
    hover: string
    /** Ausgewählte Elemente */
    selected: string
  }

  /** Textfarben für verschiedene Hierarchiestufen */
  text: {
    /** Primärer Text (Überschriften, wichtige Inhalte) */
    primary: string
    /** Sekundärer Text (Absätze, normale Inhalte) */
    secondary: string
    /** Gedämpfter Text (Hilfetexte, Platzhalter) */
    muted: string
    /** Invertierter Text (auf dunklem Hintergrund in Light, auf hellem in Dark) */
    inverse: string
    /** Deaktivierter Text */
    disabled: string
    /** Link-Text */
    link: string
    /** Link-Text bei Hover */
    linkHover: string
  }

  /** Rahmenfarben */
  border: {
    /** Standard-Rahmen */
    default: string
    /** Subtiler Rahmen (weniger sichtbar) */
    subtle: string
    /** Starker Rahmen (Hervorhebung) */
    strong: string
    /** Fokus-Rahmen */
    focus: string
    /** Fehler-Rahmen */
    error: string
  }

  /** Akzentfarben für Interaktionen */
  accent: {
    /** Primäre Akzentfarbe (Hauptaktionen) */
    primary: string
    /** Primär bei Hover */
    primaryHover: string
    /** Primär bei Klick */
    primaryActive: string
    /** Sekundäre Akzentfarbe */
    secondary: string
    /** Sekundär bei Hover */
    secondaryHover: string
  }

  /** Statusfarben für semantische Bedeutung */
  status: {
    /** Erfolg (aktiv, online, bestanden) */
    success: string
    successBackground: string
    successBorder: string
    /** Warnung (Hinweis, Vorsicht) */
    warning: string
    warningBackground: string
    warningBorder: string
    /** Fehler/Gefahr (offline, Fehler) */
    danger: string
    dangerBackground: string
    dangerBorder: string
    /** Information (neutral, Hinweis) */
    info: string
    infoBackground: string
    infoBorder: string
    /** Deaktiviert/Inaktiv */
    disabled: string
    disabledBackground: string
  }

  /** Spezielle UI-Elemente */
  ui: {
    /** Scrollbar-Track */
    scrollbarTrack: string
    /** Scrollbar-Thumb */
    scrollbarThumb: string
    /** Overlay (Modal-Hintergrund) */
    overlay: string
    /** Schatten-Basis */
    shadow: string
    /** Divider/Trennlinien */
    divider: string
    /** Fokusring */
    focusRing: string
  }
}

/** Typografie-Tokens */
export interface TypographyTokens {
  /** Schriftfamilien */
  fontFamily: {
    sans: string
    mono: string
  }
  /** Schriftgrößen */
  fontSize: {
    xs: string
    sm: string
    base: string
    lg: string
    xl: string
    '2xl': string
    '3xl': string
    '4xl': string
  }
  /** Schriftgewichte */
  fontWeight: {
    normal: number
    medium: number
    semibold: number
    bold: number
  }
  /** Zeilenhöhen */
  lineHeight: {
    tight: string
    normal: string
    relaxed: string
  }
}

/** Abstands-Tokens */
export interface SpacingTokens {
  /** 4px Basis-System */
  0: string
  1: string   // 4px
  2: string   // 8px
  3: string   // 12px
  4: string   // 16px
  5: string   // 20px
  6: string   // 24px
  8: string   // 32px
  10: string  // 40px
  12: string  // 48px
  16: string  // 64px
}

/** Schatten-Tokens */
export interface ShadowTokens {
  none: string
  sm: string
  md: string
  lg: string
  xl: string
  inner: string
}

/** Border-Radius-Tokens */
export interface RadiusTokens {
  none: string
  sm: string
  md: string
  lg: string
  xl: string
  '2xl': string
  full: string
}

/** Transitions-Tokens */
export interface TransitionTokens {
  fast: string
  normal: string
  slow: string
}

/** Komplettes Theme */
export interface Theme {
  name: 'light' | 'dark'
  colors: ColorTokens
  typography: TypographyTokens
  spacing: SpacingTokens
  shadows: ShadowTokens
  radius: RadiusTokens
  transitions: TransitionTokens
}

// =============================================================================
// Gemeinsame Tokens (unabhängig von Light/Dark)
// =============================================================================

export const typography: TypographyTokens = {
  fontFamily: {
    sans: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
}

export const spacing: SpacingTokens = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
}

export const radius: RadiusTokens = {
  none: '0',
  sm: '0.25rem',    // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',
}

export const transitions: TransitionTokens = {
  fast: '150ms ease',
  normal: '200ms ease',
  slow: '300ms ease',
}
