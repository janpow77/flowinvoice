# FlowAudit – Technisches Sanierungs- und Erweiterungskonzept
**Version:** 1.0  
**Datum:** 15. Dezember 2025  
**Status:** Entwurf zur sofortigen Umsetzung  
**Zielgruppe:** Entwicklung & Audit

---

## 1. Management Summary
Das Projekt „FlowAudit“ liegt als funktionaler Prototyp (PoC) vor. Um den Anforderungen an den Einsatz im öffentlichen Dienst (Revisionssicherheit, Datenschutz gemäß DSGVO, Stabilität) gerecht zu werden, ist eine umfassende technische Sanierung notwendig. 

Dieses Konzept beschreibt die Transformation von einem unsicheren Prototyp zu einer mandantenfähigen Anwendung mit Rollenkonzept, Sicherheitsarchitektur und behobenen funktionalen Mängeln.

---

## 2. Ist-Analyse & Kritische Mängel
Das durchgeführte Code-Audit hat folgende Blocker identifiziert, die vor jeder Weiterentwicklung behoben werden müssen:

### 2.1. Deployment & Stabilität
* **CRITICAL:** `backend/pyproject.toml` enthält ungültige Syntax (Docstring am Dateianfang), was Build-Pipelines blockiert.
* **CRITICAL:** `backend/app/llm/ollama.py` greift auf ein nicht existierendes Konfigurationsattribut zu (`ollama_url` statt `ollama_host`), was zum Runtime-Crash führt.

### 2.2. Sicherheit (Security)
* **HIGH:** Es existiert keine Authentifizierung. API-Endpunkte sind öffentlich.
* **HIGH:** Admin-Rechte werden über einen manipulierbaren Header (`X-Role`) simuliert („Security by Obscurity“).
* **HIGH:** CORS-Einstellungen erlauben Zugriff von allen Ursprüngen (`*`).
* **MEDIUM:** Hardcoded Secrets in der Konfiguration ohne Erzwingung von Environment-Variablen.

### 2.3. Funktionalität & UX
* **LOGIC:** Der Rechnungs-Generator ignoriert komplexe Parameter (z.B. `date_format_profiles`, `per_feature_error_rates`) und nutzt stattdessen generischen Zufall.
* **UX:** GUI-Elemente (Buttons „Neues Projekt“, Feedback-Buttons) sind ohne Funktion („Dead UI“).
* **UX:** Routing erfolgt teilweise über Hard-Reloads (`<a href>`) statt Client-Side-Routing.

---

## 3. Soll-Architektur: Sicherheitsmodul & Nutzerverwaltung

### 3.1. Rollenkonzept
Das System unterscheidet streng zwischen zwei Rollen:
1.  **Admin:**
    * Kann Nutzer anlegen/sperren.
    * Sieht Systemstatistiken (z.B. aktive Nutzer).
    * Konfiguriert globale Einstellungen (Rulesets).
      *  Admins dürfen keine fachlichen Prüfentscheidungen treffen, sondern ausschließlich Systemfunktionen ausführen.


2.  **User (Auditor):**
    * Kann Projekte erstellen.
    * Kann Dokumente hochladen und prüfen.
    * Kann Ergebnisse exportieren.

### 3.2. Authentifizierungs-Flow
* **Standard:** OAuth2 mit Password Flow (Bearer Token).
* **Technologie:** JWT (JSON Web Tokens) mit HS256 Signatur.
* **Hashing:** Passwörter werden mittels `bcrypt` gehasht gespeichert.
* **Session-Management:**
    * Auto-Logout nach **10 Minuten Inaktivität** (Client-seitig erzwungen).
    * Token-Validierung bei jedem Request.

### 3.3. Performance-Strategie (Active User Tracking)
Um die Datenbank nicht durch Aktivitäts-Tracking zu überlasten, wird eine „Throttling“-Strategie implementiert: Der Zeitstempel `last_active_at` wird maximal alle 5 Minuten aktualisiert, auch wenn der Nutzer häufiger Interaktionen durchführt.

---

## 4. Implementierungsschritte (Backend)

### 4.1. Sanierung der Konfiguration

**Datei:** `backend/pyproject.toml`
*Korrektur:* Entfernen des führenden Docstrings.

```toml
[project]
name = "flowaudit-backend"
version = "0.1.0"
# ... restliche Konfiguration
````

**Datei:** `backend/app/llm/ollama.py`
*Korrektur:* Variable an `config.py` anpassen.

```python
# Zeile 33 ändern in:
self.base_url = base_url or settings.ollama_host
```

### 4.2. Datenbank-Erweiterung (User Model)

**Datei:** `backend/app/models/user.py` (Neu)

```python
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Login & Auth
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Stammdaten
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    organization = Column(String, nullable=True)
    contact_info = Column(String, nullable=True)
    
    # Einstellungen & Status
    language = Column(String, default="de")
    role = Column(String, default="user") # 'admin' oder 'user'
    is_active = Column(Boolean, default=True)
    
    # Tracking (Throttled)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=True)
```

### 4.3. Security Core (Hashing & Token)

**Datei:** `backend/app/core/security.py` (Neu)

```python
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 Stunden (Frontend kickt früher)

def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```


4.3a Session-Timeout: Server-seitige Ergänzung (optional)

Client-seitig ist gut.
Besser wäre zusätzlich:

exp im JWT auf z. B. 30–60 Minuten

Refresh nur bei Aktivität

### 4.4. Auth-Dependency mit Throttling

**Datei:** `backend/app/api/deps.py` (Neu)

```python
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_session
from app.core.security import ALGORITHM
from app.config import get_settings
from app.models.user import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Performance: Update max. alle 5 Minuten
ACTIVITY_UPDATE_INTERVAL = timedelta(minutes=5)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")

    # --- Active User Tracking (Throttled) ---
    now = datetime.utcnow()
    should_update = False
    if user.last_active_at is None:
        should_update = True
    elif (now - user.last_active_at) > ACTIVITY_UPDATE_INTERVAL:
        should_update = True
        
    if should_update:
        user.last_active_at = now
        session.add(user)
        await session.commit()
    # ----------------------------------------

    return user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
```

### 4.5. API Endpoints (Login & User Management)

**Datei:** `backend/app/api/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_session
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.user import Token # Schema muss definiert sein

router = APIRouter()

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}
```

**Datei:** `backend/app/api/stats.py` (Erweiterung für Admin)

```python
@router.get("/stats/users/active", response_model=dict)
async def get_active_user_count(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    # Zählt Nutzer, die im 10-Minuten-Fenster aktiv waren
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    query = select(func.count(User.id)).where(User.last_active_at >= cutoff)
    count = await session.scalar(query) or 0
    return {"active_users": count, "timestamp": datetime.utcnow().isoformat()}
```

-----

## 5\. Implementierungsschritte (Frontend)

### 5.1. Authentication Context & Inaktivitäts-Timer

**Datei:** `frontend/src/context/AuthContext.tsx`
*Logik:* Setzt Timer bei jeder Mausbewegung zurück. Logout nach 10 Minuten.

```tsx
import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';

const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 Minuten

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  
  const login = (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    window.location.href = '/';
  };

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    window.location.href = '/login';
  }, []);

  useEffect(() => {
    if (!token) return;
    let timeoutId: NodeJS.Timeout;
    
    const resetTimer = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(logout, INACTIVITY_TIMEOUT);
    };
    
    const events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];
    events.forEach(e => document.addEventListener(e, resetTimer));
    resetTimer();
    
    return () => events.forEach(e => document.removeEventListener(e, resetTimer));
  }, [token, logout]);

  // Provider Return Code...
}
```

### 5.2. Login UI (Spezifikation)

**Datei:** `frontend/src/pages/Login.tsx`
*Design:* Zentriertes Layout mit Logo und spezifischem Schriftzug.

```tsx
// Auszug aus der Render-Methode
<div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
  <img src="/auditlogo.svg" alt="Logo" className="mx-auto h-20 w-auto" />
  <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
    FlowAudit <span className="text-primary-600">- invoice -</span>
  </h2>
  {/* Formular-Komponente... */}
</div>
```

### 5.3. API Client Interceptors

**Datei:** `frontend/src/lib/api.ts`
*Funktion:* Inijiziert JWT in jeden Request.

```typescript
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

-----

## 6\. Maßnahmenplan zur Qualitätssicherung

1.  **Linter-Installation:** Einrichtung von `pre-commit` Hooks (Ruff, Black), um Syntaxfehler wie in der `pyproject.toml` künftig automatisiert zu verhindern.
2.  **Fix Dead UI:** \* In `Projects.tsx`: Wrapping der Buttons mit `<Link to="/projects/new">`.
      * In `DocumentDetail.tsx`: Implementierung der `handleFeedback`-Funktion für Daumen-Buttons.
3.  **Generator-Logik:** Überarbeitung von `tasks.py`, um `per_feature_error_rates` tatsächlich in der Fehlerauswahl-Logik zu berücksichtigen, statt `random.sample` zu nutzen.
4.  **OCR-Integration:** Hinzufügen von `pytesseract` als Fallback in `parser.py`, falls `extract_text()` leer ist.

## 7\. Rechtliche Betrachtung (DSGVO & Compliance)

Durch die Umsetzung dieses Konzepts werden folgende Compliance-Anforderungen erfüllt:

  * **Zugangskontrolle (Art. 32 DSGVO):** Nur authentifizierte Nutzer haben Zugriff auf personenbezogene Daten (Rechnungen).
  * **Weitergabekontrolle:** Durch TLS (HTTPS) und gesicherte Endpoints ist unbefugtes Mitlesen verhindert.
  * **Eingabekontrolle (Audit Trail):** Durch die neue `User`-Tabelle und die Verknüpfung in Logs ist nachvollziehbar, wer (User-ID) wann (Timestamp) aktiv war.
  * **Availability:** Die Beseitigung der Crash-Bugs (Ollama, TOML) stellt die Verfügbarkeit des Systems sicher.

