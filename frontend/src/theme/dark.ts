/**
 * FlowAudit Dark Theme
 *
 * Charakter:
 * - Professionell, ruhig, augenschonend
 * - "Control Room"-Charakter, nicht "Gaming"
 *
 * Zielwirkung:
 * - Lange Nutzungsdauer ohne Ermüdung
 * - Klare Statusanzeigen (Admin, Aktiv, Warnung)
 * - Keine Blendung
 *
 * Designregeln:
 * - 3 Ebenen klar trennen:
 *   1. App-Hintergrund (sehr dunkel)
 *   2. Panels/Sections (etwas heller)
 *   3. Cards/Inputs (noch etwas heller)
 * - Text niemals hellgrau auf mittelgrau
 * - Akzentfarben entsättigen (gleicher Farbton wie Light, weniger Leuchtkraft)
 */

import {
  ColorTokens,
  ShadowTokens,
  Theme,
  typography,
  spacing,
  radius,
  transitions,
} from './tokens'

// =============================================================================
// Dark Theme Farbpalette
// =============================================================================

const colors: ColorTokens = {
  background: {
    // 3 klar getrennte Ebenen - von dunkel zu weniger dunkel
    app: '#0F1419',         // Sehr dunkler App-Hintergrund
    panel: '#1A1F26',       // Panels/Sections (eine Stufe heller)
    card: '#242B35',        // Cards (hervorgehoben)
    elevated: '#2D3541',    // Dropdowns, Tooltips (am hellsten)
    input: '#1E242C',       // Eingabefelder (zwischen Panel und Card)
    disabled: '#1A1F26',    // Deaktivierte Elemente
    hover: '#2D3541',       // Hover-Zustand
    selected: '#1E3A5F',    // Ausgewählt (gedämpftes Blau)
  },

  text: {
    // Klare Hierarchie - niemals hellgrau auf mittelgrau!
    primary: '#F3F4F6',     // Fast weiß, aber nicht blendend
    secondary: '#D1D5DB',   // Helles Grau
    muted: '#9CA3AF',       // Gedämpftes Grau für Hilfetexte
    inverse: '#111827',     // Dunkler Text auf hellen Elementen
    disabled: '#6B7280',    // Deutlich dunkler
    link: '#60A5FA',        // Helleres, entsättigtes Blau
    linkHover: '#93C5FD',   // Noch heller bei Hover
  },

  border: {
    // Subtile Rahmen für bessere Tiefenwahrnehmung
    default: '#374151',     // Standard-Rahmen
    subtle: '#2D3541',      // Sehr subtil
    strong: '#4B5563',      // Hervorgehoben
    focus: '#3B82F6',       // Fokus-Blau
    error: '#F87171',       // Helles Fehler-Rot
  },

  accent: {
    // Entsättigte Akzentfarben - weniger Leuchtkraft als Light
    primary: '#3B82F6',     // Gedämpftes Blau
    primaryHover: '#60A5FA', // Heller bei Hover (statt dunkler)
    primaryActive: '#2563EB', // Aktiv
    secondary: '#6B7280',   // Sekundär (Grau)
    secondaryHover: '#9CA3AF', // Heller bei Hover
  },

  status: {
    // Entsättigte, aber klar erkennbare Statusfarben
    success: '#34D399',           // Entsättigtes Grün (heller als Light)
    successBackground: '#064E3B', // Dunkler Grün-Hintergrund
    successBorder: '#065F46',     // Grün-Border

    warning: '#FBBF24',           // Entsättigtes Amber
    warningBackground: '#78350F', // Dunkler Amber-Hintergrund
    warningBorder: '#92400E',     // Amber-Border

    danger: '#F87171',            // Entsättigtes Rot
    dangerBackground: '#7F1D1D',  // Dunkler Rot-Hintergrund
    dangerBorder: '#991B1B',      // Rot-Border

    info: '#22D3EE',              // Entsättigtes Cyan
    infoBackground: '#164E63',    // Dunkler Cyan-Hintergrund
    infoBorder: '#155E75',        // Cyan-Border

    disabled: '#6B7280',          // Grau
    disabledBackground: '#1F2937', // Dunkles Grau
  },

  ui: {
    scrollbarTrack: '#1A1F26',
    scrollbarThumb: '#4B5563',
    overlay: 'rgba(0, 0, 0, 0.7)',
    shadow: 'rgba(0, 0, 0, 0.4)',
    divider: '#374151',
    focusRing: 'rgba(59, 130, 246, 0.6)',
  },
}

// =============================================================================
// Dark Theme Schatten (weniger prominent)
// =============================================================================

const shadows: ShadowTokens = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.4)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',
}

// =============================================================================
// Export Dark Theme
// =============================================================================

export const darkTheme: Theme = {
  name: 'dark',
  colors,
  typography,
  spacing,
  shadows,
  radius,
  transitions,
}

export default darkTheme
