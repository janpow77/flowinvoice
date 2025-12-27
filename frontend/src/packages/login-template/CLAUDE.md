# Login Template Package - Claude Code Guide

## Übersicht

Dieses Package enthält ein wiederverwendbares Login-Template mit animiertem Fisch und Binary-Datenwasser. Es extrahiert die Login-Seite von FlowAudit in ein eigenständiges, konfigurierbares Template.

## Wichtige Hinweise für Claude Code

### Logo-Verwendung

**KRITISCH**: Das Logo (`auditlogo.png`) wird IMMER als externe Datei referenziert und NIEMALS generiert oder modifiziert. Das Logo muss im `public`-Verzeichnis der Anwendung liegen.

```tsx
// RICHTIG: Logo als Pfad referenzieren
<LoginTemplate logoPath="/auditlogo.png" />

// FALSCH: Kein SVG generieren oder Logo verändern!
```

### Dateistruktur

```
login-template/
├── index.ts              # Alle Exports - hier importieren!
├── LoginTemplate.tsx     # Hauptkomponente mit Animationen
├── LoginFormElements.tsx # Styled Form-Komponenten
├── README.md            # Benutzer-Dokumentation
└── CLAUDE.md            # Diese Datei (für Claude Code)
```

### Exports

```typescript
// Aus index.ts verfügbar:

// Hauptkomponente
LoginTemplate        // Container mit Background, Animationen, Logo
loginAnimations      // CSS-String mit allen Keyframe-Animationen

// Einzelne Animationskomponenten
JumpingFish          // Springender Fisch (verwendet logoPath)
BinaryDataWater      // Fließende 0 und 1
DecorativeBubbles    // Kleine schwebende Blasen

// Form-Elemente (vorgefertigt für Login)
LoginInput           // Styled Input mit Label
LoginButton          // Blauer Submit-Button mit Loading-State
LoginError           // Rote Fehlermeldung
LoginDivider         // Trennlinie mit Text ("oder")
OAuthButton          // Button für OAuth-Provider
GoogleIcon           // Google SVG-Icon
DemoHint             // Kleiner Hinweistext
```

### Typische Aufgaben

#### Neues Login erstellen

```tsx
import {
  LoginTemplate,
  LoginInput,
  LoginButton,
  LoginError
} from '@/packages/login-template';

function MyLogin() {
  return (
    <LoginTemplate
      logoPath="/mein-logo.png"
      title="MeinProjekt"
      subtitle="Untertitel hier"
    >
      <form className="space-y-6" onSubmit={handleSubmit}>
        <LoginInput
          id="email"
          label="E-Mail"
          type="email"
          required
        />
        <LoginInput
          id="password"
          label="Passwort"
          type="password"
          required
        />
        {error && <LoginError message={error} />}
        <LoginButton type="submit" loading={isLoading}>
          Anmelden
        </LoginButton>
      </form>
    </LoginTemplate>
  );
}
```

#### Animationen deaktivieren

```tsx
<LoginTemplate
  showJumpingFish={false}
  showBinaryWater={false}
  showBubbles={false}
>
  {/* Nur die Login-Karte ohne Animationen */}
</LoginTemplate>
```

#### OAuth hinzufügen

```tsx
import { LoginDivider, OAuthButton, GoogleIcon } from '@/packages/login-template';

// Nach dem Formular:
<LoginDivider text="oder" />
<OAuthButton
  icon={<GoogleIcon />}
  onClick={handleGoogleAuth}
  loading={googleLoading}
>
  Mit Google anmelden
</OAuthButton>
```

### Abhängigkeiten

- **React 18+**: Verwendet Hooks (useState, useEffect)
- **Tailwind CSS**: Alle Styles sind Tailwind-Klassen
- **Keine externen Bibliotheken**: Kein clsx, keine Icons-Lib

### CSS-Animationen

Die Animationen sind als CSS-String in `loginAnimations` exportiert. Sie werden automatisch über `<style>` in `LoginTemplate` eingefügt:

- `fishJump`: 7s Sprung-Animation für den Fisch
- `waveMove`: 6-8s Wellenbewegung
- `dataFlow`: 15-25s horizontales Fließen der Binärzahlen
- `binaryPulse`: 3s Pulsieren der Opazität

### Styling-Konventionen

- **Hintergrund**: Blau-Gradient (`from-blue-900 via-blue-700 to-blue-500`)
- **Karte**: Frosted Glass (`bg-white/10 backdrop-blur-lg`)
- **Text**: Weiß/Blau-Töne für Kontrast
- **Inputs**: Transparenter Hintergrund mit weißer Schrift
- **Button**: Solid Blue (`bg-blue-600`)

### Bekannte Einschränkungen

1. **Fester Hintergrund**: Der blaue Gradient ist nicht konfigurierbar
2. **Tailwind erforderlich**: Funktioniert nicht ohne Tailwind CSS
3. **Logo extern**: Muss als Datei vorliegen, nicht inline

### Bei Änderungen beachten

- Keine Änderungen am Logo-Rendering
- CSS-Animationen in `loginAnimations` sind als String - bei Änderungen Template-Literale beachten
- Form-Elemente haben feste Styles - für Anpassungen eigene Komponenten erstellen
