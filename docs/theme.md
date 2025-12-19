# FlowAudit Theme System

Zentrales Design-System für konsistente Light- und Dark-Mode-Unterstützung.

---

## Übersicht

Das Theme-System basiert auf **semantischen Tokens** - Farben werden nicht direkt, sondern über ihre Bedeutung definiert. Dies ermöglicht:

- Konsistente Darstellung in beiden Themes
- Einfache Wartbarkeit
- Klare Trennung von Design und Implementierung

---

## Designprinzipien

### 1. Semantik vor Farbe

Komponenten verwenden **keine hartcodierten Farben**, sondern semantische Tokens:

```tsx
// ❌ Falsch
<div className="bg-gray-100 text-gray-900">

// ✅ Richtig
<div className="bg-theme-card text-theme-text-primary">
```

### 2. Light & Dark als gleichwertige Themes

Beide Themes sind vollständig definiert - Dark ist kein Graufilter:

- Light: Sachlich, klar, auditgeeignet
- Dark: Professionell, augenschonend, "Control Room"

### 3. Drei-Ebenen-Hierarchie (Dark Mode)

```
App-Hintergrund (dunkelste Ebene)
└── Panel/Section (mittlere Ebene)
    └── Card/Input (hellste Ebene)
```

---

## Token-Übersicht

### Hintergrundfarben (`bg-theme-*`)

| Token | Light | Dark | Verwendung |
|-------|-------|------|------------|
| `app` | `#F8F9FA` | `#0F1419` | Haupthintergrund |
| `panel` | `#FFFFFF` | `#1A1F26` | Sidebar, Header |
| `card` | `#FFFFFF` | `#242B35` | Karten, Container |
| `elevated` | `#FFFFFF` | `#2D3541` | Dropdowns, Tooltips |
| `input` | `#FFFFFF` | `#1E242C` | Eingabefelder |
| `hover` | `#F3F4F6` | `#2D3541` | Hover-Zustände |
| `selected` | `#EEF2FF` | `#1E3A5F` | Ausgewählte Elemente |

### Textfarben (`text-theme-text-*`)

| Token | Light | Dark | Verwendung |
|-------|-------|------|------------|
| `primary` | `#111827` | `#F3F4F6` | Überschriften, wichtig |
| `secondary` | `#374151` | `#D1D5DB` | Normaler Text |
| `muted` | `#6B7280` | `#9CA3AF` | Hilfetexte, Platzhalter |
| `disabled` | `#9CA3AF` | `#6B7280` | Deaktivierte Elemente |
| `link` | `#2563EB` | `#60A5FA` | Links |

### Rahmenfarben (`border-theme-border-*`)

| Token | Light | Dark | Verwendung |
|-------|-------|------|------------|
| `default` | `#E5E7EB` | `#374151` | Standard-Rahmen |
| `subtle` | `#F3F4F6` | `#2D3541` | Sehr dezent |
| `strong` | `#D1D5DB` | `#4B5563` | Hervorgehoben |
| `focus` | `#3B82F6` | `#3B82F6` | Fokus-Zustand |

### Statusfarben (`text-status-*`, `bg-status-*-bg`)

| Status | Light Text | Dark Text |
|--------|------------|-----------|
| Success | `#059669` | `#34D399` |
| Warning | `#D97706` | `#FBBF24` |
| Danger | `#DC2626` | `#F87171` |
| Info | `#0891B2` | `#22D3EE` |

### Akzentfarben (`text-accent-*`, `bg-accent-*`)

| Token | Light | Dark |
|-------|-------|------|
| `primary` | `#2563EB` | `#3B82F6` |
| `primary-hover` | `#1D4ED8` | `#60A5FA` |

---

## Verwendung

### Im React-Code

```tsx
import { useTheme } from '@/theme'

function MyComponent() {
  const { theme, isDark, toggleTheme, setMode } = useTheme()

  return (
    <div style={{ backgroundColor: theme.colors.background.card }}>
      <p style={{ color: theme.colors.text.primary }}>
        {isDark ? 'Dark Mode aktiv' : 'Light Mode aktiv'}
      </p>
      <button onClick={toggleTheme}>Theme wechseln</button>
      <button onClick={() => setMode('system')}>System-Präferenz</button>
    </div>
  )
}
```

### Mit Tailwind-Klassen

```tsx
// Hintergründe
<div className="bg-theme-app">        {/* App-Hintergrund */}
<div className="bg-theme-panel">      {/* Panel-Hintergrund */}
<div className="bg-theme-card">       {/* Card-Hintergrund */}

// Text
<p className="text-theme-text-primary">    {/* Primärer Text */}
<p className="text-theme-text-secondary">  {/* Sekundärer Text */}
<p className="text-theme-text-muted">      {/* Gedämpfter Text */}

// Rahmen
<div className="border border-theme-border-default">
<div className="border border-theme-border-subtle">

// Status
<span className="text-status-success">Aktiv</span>
<span className="text-status-danger">Fehler</span>
<div className="bg-status-warning-bg text-status-warning">Warnung</div>

// Akzent
<button className="bg-accent-primary text-white">Primär</button>
```

### Mit CSS Custom Properties

```css
.my-component {
  background-color: var(--color-bg-card);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
}
```

---

## Logo-Schutz

Das FlowAudit-Logo ist **CI-geschützt** und wird in beiden Themes identisch gerendert:

- Keine Farbänderung
- Keine Filter
- Keine Theme-Anpassung

```tsx
// Logo-Komponente ignoriert Theme-Tokens
<img
  src="/auditlogo.png"
  alt="FlowAudit Logo"
  className="h-10 w-10 object-contain"
  // Keine theme-abhängigen Klassen!
/>
```

---

## LogoLoader

CI-konformer Ladeindikator mit dem FlowAudit-Logo im Zentrum:

```tsx
import { LogoLoader, FullPageLoader, InlineLoader } from '@/components/ui'

// Standard-Loader (Ring-Variante)
<LogoLoader progress={45} />

// Indeterminate (Animation)
<LogoLoader indeterminate />

// Mit Text
<LogoLoader text="Analyse läuft..." />

// Ticks-Variante (60 Minutenstriche)
<LogoLoader variant="ticks" progress={30} />

// Größen: small, medium, large
<LogoLoader size="large" />

// Convenience-Komponenten
<FullPageLoader text="Seite wird geladen..." />
<InlineLoader text="Daten werden abgerufen..." />
```

**Wichtig**: Das Logo selbst bleibt immer statisch - nur der Ring/die Ticks animieren.

---

## Migration bestehender Komponenten

### Schritt 1: Import

```tsx
import { useTheme } from '@/theme'
```

### Schritt 2: Hardcodierte Farben ersetzen

```tsx
// Vorher
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">

// Nachher
<div className="bg-theme-card text-theme-text-primary">
```

### Schritt 3: Status-Farben migrieren

```tsx
// Vorher
<span className="text-green-600 dark:text-green-400">

// Nachher
<span className="text-status-success">
```

---

## Theme-Konfiguration

### Modi

| Modus | Beschreibung |
|-------|--------------|
| `light` | Fester Light Mode |
| `dark` | Fester Dark Mode |
| `system` | Folgt System-Präferenz |

### Storage

Theme-Einstellung wird in `localStorage` unter `flowaudit_theme` gespeichert.

### Flicker Prevention

Das Theme wird sofort beim Laden angewandt (vor React-Hydration):

```html
<head>
  <script>
    (function() {
      var mode = localStorage.getItem('flowaudit_theme') || 'system';
      var dark = mode === 'dark' ||
        (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (dark) document.documentElement.classList.add('dark');
    })();
  </script>
</head>
```

---

## Dateien

| Datei | Zweck |
|-------|-------|
| `src/theme/tokens.ts` | Token-Definitionen & Typen |
| `src/theme/light.ts` | Light Theme |
| `src/theme/dark.ts` | Dark Theme |
| `src/theme/ThemeContext.tsx` | React Context & Provider |
| `src/theme/index.ts` | Exports |
| `src/index.css` | CSS Custom Properties |
| `tailwind.config.js` | Tailwind-Integration |

---

## Akzeptanzkriterien

- [x] Dark Mode ist echtes Theme, kein Graufilter
- [x] Gute Lesbarkeit in beiden Modi
- [x] Einheitliche Optik über alle Komponenten
- [x] Status-Anzeigen visuell klar
- [x] Keine hartcodierten Farben in neuen Komponenten
- [x] Logo bleibt unverändert
- [x] LogoLoader mit Fortschrittsring implementiert
