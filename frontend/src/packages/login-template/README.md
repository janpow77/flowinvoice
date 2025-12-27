# FlowAudit Login Template

Wiederverwendbares Login-Template mit animiertem Fisch und Binary-Datenwasser.

## Features

- **Springender Fisch**: Das Original-Logo (`auditlogo.png`) springt aus dem Datenwasser
- **Binary-Datenwasser**: Fließende 0 und 1 als Wasser-Animation
- **Wellenanimation**: Realistische Wellenoberfläche
- **Frosted Glass Design**: Moderne Login-Karte mit Blur-Effekt
- **Responsive**: Mobile-first Design
- **Tailwind CSS**: Nutzt nur Tailwind-Klassen

## Voraussetzungen

- React 18+
- Tailwind CSS
- Das Logo muss im `public`-Verzeichnis liegen: `/public/auditlogo.png`

## Verwendung

### Einfaches Beispiel

```tsx
import { LoginTemplate, LoginInput, LoginButton, LoginError } from '@/packages/login-template';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Login-Logik hier
  };

  return (
    <LoginTemplate
      logoPath="/auditlogo.png"
      title="flowaudit"
      subtitle="Automated Audit Systems"
      footer={<p className="text-xs text-blue-200/60 text-center">Demo: admin / admin</p>}
    >
      <form className="space-y-6" onSubmit={handleSubmit}>
        <LoginInput
          id="username"
          label="Kennung"
          placeholder="Benutzername"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <LoginInput
          id="password"
          type="password"
          label="Passwort"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <LoginError message={error} />}
        <LoginButton type="submit">Login</LoginButton>
      </form>
    </LoginTemplate>
  );
}
```

### Mit Google OAuth

```tsx
import {
  LoginTemplate,
  LoginInput,
  LoginButton,
  LoginDivider,
  OAuthButton,
  GoogleIcon,
} from '@/packages/login-template';

function LoginPage() {
  return (
    <LoginTemplate logoPath="/auditlogo.png" title="flowaudit">
      <form className="space-y-6" onSubmit={handleSubmit}>
        {/* Standard Login Form */}
        <LoginInput label="Kennung" />
        <LoginInput label="Passwort" type="password" />
        <LoginButton type="submit">Login</LoginButton>
      </form>

      <LoginDivider text="oder" />

      <OAuthButton icon={<GoogleIcon />} onClick={handleGoogleLogin}>
        Mit Google anmelden
      </OAuthButton>
    </LoginTemplate>
  );
}
```

## Props

### LoginTemplate

| Prop | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `logoPath` | `string` | `/auditlogo.png` | Pfad zum Logo (das Original!) |
| `title` | `string` | `flowaudit` | Haupttitel |
| `subtitle` | `string` | `Automated Audit Systems` | Untertitel |
| `children` | `ReactNode` | - | Login-Formular (required) |
| `footer` | `ReactNode` | - | Footer-Inhalt (z.B. Demo-Hint) |
| `logoHeight` | `string` | `h-24` | Tailwind-Klasse für Logo-Höhe |
| `showJumpingFish` | `boolean` | `true` | Fisch-Animation anzeigen |
| `showBinaryWater` | `boolean` | `true` | Binary-Wasser anzeigen |
| `showBubbles` | `boolean` | `true` | Deko-Blasen anzeigen |

### LoginInput

| Prop | Typ | Beschreibung |
|------|-----|--------------|
| `label` | `string` | Label über dem Input |
| `...rest` | `InputHTMLAttributes` | Alle Standard-Input-Props |

### LoginButton

| Prop | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `loading` | `boolean` | `false` | Zeigt Spinner an |
| `children` | `ReactNode` | - | Button-Text |

## Animationen

Das Template enthält folgende CSS-Animationen:

- `animate-fish-jump`: Der Fisch springt aus dem Wasser
- `data-flow`: Binärcode fließt horizontal
- `wave-animation`: Wellenoberfläche bewegt sich
- `binary-pulse`: Pulsierender Opazitätseffekt

Die Animationen werden automatisch über `<style>{loginAnimations}</style>` eingefügt.

## Anpassungen

### Eigenes Logo

```tsx
<LoginTemplate logoPath="/mein-logo.png" title="MeinProjekt">
  ...
</LoginTemplate>
```

### Ohne Animationen

```tsx
<LoginTemplate
  showJumpingFish={false}
  showBinaryWater={false}
  showBubbles={false}
>
  ...
</LoginTemplate>
```

### Eigene Farben

Die Farben können über Tailwind-Klassen im `children`-Bereich angepasst werden.
Der Hintergrund-Gradient ist fest auf Blue-Töne eingestellt.

## Struktur

```
login-template/
├── index.ts              # Package exports
├── LoginTemplate.tsx     # Hauptkomponente mit Animationen
├── LoginFormElements.tsx # Form-Komponenten
└── README.md            # Diese Dokumentation
```

## Logo-Hinweis

**WICHTIG**: Das Template verwendet das Original-Logo (`auditlogo.png`) ohne Änderungen.
Das Logo muss als Datei im `public`-Verzeichnis vorliegen. Es wird nicht modifiziert oder generiert.
