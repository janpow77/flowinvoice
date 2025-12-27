# Login Template - Claude Code Guide

## Übersicht

Dieses Template enthält eine vollständige Login-Lösung mit animiertem Fisch und Binary-Datenwasser, bereit zur Integration in andere Projekte.

## Wichtige Hinweise für Claude Code

### Logo-Verwendung

**Das Logo ist im Template enthalten** unter `frontend/public/auditlogo.png` und `frontend/public/auditlogo.svg`.

```tsx
// Das Logo liegt in frontend/public/ und wird per URL referenziert:
<img src="/auditlogo.png" alt="Logo" />

// FALSCH: Kein SVG generieren oder Logo programmatisch erstellen!
```

### Dateistruktur

```
login-template/
├── frontend/
│   ├── public/
│   │   ├── auditlogo.png         # FlowAudit Logo (PNG)
│   │   └── auditlogo.svg         # FlowAudit Logo (SVG)
│   ├── components/ui/
│   │   ├── Button.tsx            # Styled Button
│   │   └── Input.tsx             # Styled Input
│   ├── pages/
│   │   ├── Login.tsx             # Hauptseite mit Animationen
│   │   └── GoogleCallback.tsx    # OAuth Callback Handler
│   ├── context/
│   │   └── AuthContext.tsx       # Auth State + Protected Routes
│   └── styles/
│       └── login-animations.css  # CSS Keyframe-Animationen
├── backend/
│   ├── auth.py                   # FastAPI Auth-Endpoints
│   └── config_additions.py       # Config-Erweiterungen
├── README.md                     # Benutzer-Dokumentation
└── CLAUDE.md                     # Diese Datei
```

### Komponenten

| Datei | Beschreibung |
|-------|--------------|
| `Login.tsx` | Hauptseite mit Animationen (Fisch, Binary-Wasser, Glassmorphism) |
| `GoogleCallback.tsx` | Verarbeitet OAuth-Redirect von Google |
| `AuthContext.tsx` | Auth-State, Login/Logout, Token-Refresh, Protected Routes |
| `Button.tsx` | Styled Button mit Loading-State |
| `Input.tsx` | Styled Input mit Label und Error |
| `auth.py` | FastAPI Endpoints für Login, OAuth, Token-Refresh |

### Typische Aufgaben

#### Template in neues Projekt integrieren

```bash
# Frontend-Dateien kopieren
cp -r frontend/components/* your-project/src/components/
cp -r frontend/pages/* your-project/src/pages/
cp -r frontend/context/* your-project/src/context/
cp frontend/styles/login-animations.css your-project/src/styles/
cp frontend/public/* your-project/public/

# Backend-Dateien kopieren (FastAPI)
cp backend/auth.py your-project/app/api/
```

#### Routes hinzufügen

```tsx
import Login from './pages/Login'
import GoogleCallback from './pages/GoogleCallback'

<Route path="/login" element={<Login />} />
<Route path="/auth/google/callback" element={<GoogleCallback />} />
```

#### Protected Routes verwenden

```tsx
import { AuthProvider, ProtectedRoute } from './context/AuthContext'

<AuthProvider>
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/*" element={
      <ProtectedRoute>
        {/* Geschützte Inhalte */}
      </ProtectedRoute>
    } />
  </Routes>
</AuthProvider>
```

### Abhängigkeiten

**Frontend:**
- React 18+
- react-router-dom
- axios
- Tailwind CSS

**Backend:**
- FastAPI
- python-jose (JWT)
- httpx (für Google OAuth)
- bcrypt (Passwort-Hashing)

### Animationen

Die CSS-Animationen sind in `frontend/styles/login-animations.css` definiert:

- `fishJump`: 7s Sprung-Animation für den Fisch
- `waveMove`: 6-8s Wellenbewegung
- `dataFlow`: 15-25s horizontales Fließen der Binärzahlen
- `binaryPulse`: 3s Pulsieren der Opazität

Die Animationen werden auch inline in `Login.tsx` als CSS-String eingefügt (funktioniert ohne separate CSS-Datei).

### Styling-Konventionen

- **Hintergrund**: Blau-Gradient (`from-blue-900 via-blue-700 to-blue-500`)
- **Karte**: Glassmorphism (`bg-white/10 backdrop-blur-lg`)
- **Text**: Weiß/Blau-Töne für Kontrast
- **Inputs**: Transparenter Hintergrund mit weißer Schrift
- **Button**: Solid Blue (`bg-blue-600`)

### Anpassungen

#### Logo ändern
```tsx
// In Login.tsx:
<img src="/your-logo.png" alt="Logo" className="h-24 w-auto mx-auto" />
```

#### Titel ändern
```tsx
// In Login.tsx:
<h1 className="text-5xl font-extrabold text-white">
  Your Brand
</h1>
<p className="text-blue-200 text-sm">
  Your Tagline
</p>
```

#### Farben ändern
Tailwind-Klassen in Login.tsx anpassen:
- `from-blue-900 via-blue-700 to-blue-500` → eigene Farben
- `bg-blue-600` → eigene Button-Farbe

### Sicherheit

- CSRF-Schutz via State-Token bei OAuth
- JWT-Tokens mit konfigurierbarer Ablaufzeit (default: 24h)
- Inaktivitäts-Timeout (10 Minuten)
- Passwörter werden mit bcrypt gehasht
- Google OAuth-Tokens werden nie clientseitig gespeichert

### Bei Änderungen beachten

- Logo-Dateien nicht verändern, nur ersetzen
- CSS-Animationen sind sowohl in separater Datei als auch inline in Login.tsx
- AuthContext enthält Token-Refresh-Logik - vorsichtig ändern
- Backend auth.py ist für FastAPI optimiert
