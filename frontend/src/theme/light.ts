/**
 * FlowAudit Light Theme
 *
 * Charakter:
 * - Sachlich, ruhig, klar
 * - Verwaltungs- und auditgeeignet
 * - Keine grellen Farben
 *
 * Zielwirkung:
 * - Sehr gute Lesbarkeit bei Tageslicht
 * - Klare visuelle Hierarchie
 * - Fokus auf Inhalte, nicht auf Effekte
 *
 * Designregeln:
 * - Hintergrund: sehr hell, nicht reinweiß
 * - Karten klar abgesetzt
 * - Dezente Borders statt starker Schatten
 * - Akzentfarben sparsam einsetzen
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
// Light Theme Farbpalette
// =============================================================================

const colors: ColorTokens = {
  background: {
    // Sehr helle, warme Grautöne - nicht reinweiß
    app: '#F8F9FA',        // Haupthintergrund
    panel: '#FFFFFF',       // Panels/Sections
    card: '#FFFFFF',        // Cards
    elevated: '#FFFFFF',    // Dropdowns, Tooltips
    input: '#FFFFFF',       // Eingabefelder
    disabled: '#F3F4F6',    // Deaktivierte Elemente
    hover: '#F3F4F6',       // Hover-Zustand
    selected: '#EEF2FF',    // Ausgewählt (leicht blau)
  },

  text: {
    // Klare Hierarchie durch Graustufen
    primary: '#111827',     // Sehr dunkel, fast schwarz
    secondary: '#374151',   // Dunkelgrau
    muted: '#6B7280',       // Mittleres Grau für Hilfetexte
    inverse: '#FFFFFF',     // Weiß auf dunklem Hintergrund
    disabled: '#9CA3AF',    // Hellgrau
    link: '#2563EB',        // Blau
    linkHover: '#1D4ED8',   // Dunkleres Blau
  },

  border: {
    // Dezente, aber sichtbare Rahmen
    default: '#E5E7EB',     // Standard-Rahmen
    subtle: '#F3F4F6',      // Sehr subtil
    strong: '#D1D5DB',      // Hervorgehoben
    focus: '#3B82F6',       // Fokus-Blau
    error: '#EF4444',       // Fehler-Rot
  },

  accent: {
    // Dezentes, professionelles Blau
    primary: '#2563EB',     // Hauptakzent
    primaryHover: '#1D4ED8', // Hover
    primaryActive: '#1E40AF', // Aktiv/Klick
    secondary: '#6B7280',   // Sekundär (Grau)
    secondaryHover: '#4B5563', // Sekundär Hover
  },

  status: {
    // Klare, aber nicht grelle Statusfarben
    success: '#059669',           // Gedämpftes Grün
    successBackground: '#ECFDF5', // Sehr heller Grün-Ton
    successBorder: '#A7F3D0',     // Helle Grün-Border

    warning: '#D97706',           // Gedämpftes Orange/Amber
    warningBackground: '#FFFBEB', // Sehr heller Amber-Ton
    warningBorder: '#FDE68A',     // Helle Amber-Border

    danger: '#DC2626',            // Gedämpftes Rot
    dangerBackground: '#FEF2F2', // Sehr heller Rot-Ton
    dangerBorder: '#FECACA',      // Helle Rot-Border

    info: '#0891B2',              // Gedämpftes Cyan
    infoBackground: '#ECFEFF',    // Sehr heller Cyan-Ton
    infoBorder: '#A5F3FC',        // Helle Cyan-Border

    disabled: '#9CA3AF',          // Grau
    disabledBackground: '#F9FAFB', // Sehr helles Grau
  },

  ui: {
    scrollbarTrack: '#F3F4F6',
    scrollbarThumb: '#D1D5DB',
    overlay: 'rgba(0, 0, 0, 0.5)',
    shadow: 'rgba(0, 0, 0, 0.1)',
    divider: '#E5E7EB',
    focusRing: 'rgba(59, 130, 246, 0.5)',
  },
}

// =============================================================================
// Light Theme Schatten
// =============================================================================

const shadows: ShadowTokens = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
}

// =============================================================================
// Export Light Theme
// =============================================================================

export const lightTheme: Theme = {
  name: 'light',
  colors,
  typography,
  spacing,
  shadows,
  radius,
  transitions,
}

export default lightTheme
