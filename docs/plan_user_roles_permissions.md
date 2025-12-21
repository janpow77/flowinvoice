# Konzept: Nutzerverwaltung und Rollen-/Rechtekonzept

## Übersicht

Dieses Dokument beschreibt das geplante Nutzerverwaltungs- und Berechtigungssystem für FlowAudit/FlowInvoice.

### Entscheidungen (festgelegt)

- **Schüler sehen NUR ihr eigenes Projekt** (keine anderen Projekte lesbar)
- **Externe sehen vollständige Dokument-Ansicht** (nicht nur Ergebnisse)
- **Admin weist Projekte manuell zu** (Schüler wählt nicht selbst)
- **Keine Gruppen/Klassen-Struktur** (flache Hierarchie)

---

## 1. Rollenmodell

### 1.1 Rollen-Übersicht

| Rolle | Beschreibung | Zugang |
|-------|--------------|--------|
| **Admin** | Vollzugriff, Nutzerverwaltung | Lokales Netzwerk + Remote |
| **Schueler** (Student) | Projektbezogene Arbeit | Lokales Netzwerk |
| **Extern** | Eingeschränkter Gastzugang | Via Cloudflare Tunnel |

### 1.2 Detaillierte Rollenbeschreibungen

#### Admin
- **Zielgruppe:** Lehrer/Systemadministrator
- **Hauptaufgaben:**
  - Vollständige Nutzerverwaltung (CRUD für alle Nutzer)
  - Projekt-Management (alle Projekte)
  - System-Konfiguration (LLM-Provider, API-Keys)
  - Zugriff auf Statistiken und Logs
  - Regelwerk-Verwaltung (Rulesets)
- **Authentifizierung:** Username/Passwort mit JWT

#### Schueler (Student)
- **Zielgruppe:** Schüler/Auszubildende im Ausbildungsbetrieb
- **Hauptaufgaben:**
  - Arbeiten im zugewiesenen eigenen Projekt
  - Dokumente hochladen und analysieren
  - Testfälle mit dem Generator erstellen
  - Eigene Einstellungen anpassen (Sprache, Theme)
- **Einschränkungen:**
  - Kann nur eigenes Projekt sehen und bearbeiten
  - Sieht KEINE anderen Projekte
  - Keine Nutzerverwaltung
  - Keine System-Konfiguration
- **Authentifizierung:** Username/Passwort mit JWT

#### Extern (External/Guest)
- **Zielgruppe:** Externe Prüfer, Gastzugänge, Praktikanten
- **Hauptaufgaben:**
  - Lesezugriff auf freigegebenes Projekt
  - Nutzung des Testgenerators
  - Persönliche Einstellungen (Sprache, Theme)
- **Einschränkungen:**
  - Kein Upload/Ändern von Dokumenten
  - Kein Zugriff auf Statistiken
  - Kein Zugriff auf LLM-Provider-Konfiguration
  - Keine Nutzerverwaltung
- **Authentifizierung:** Link-basiert oder Username/Passwort via Cloudflare Tunnel
- **Besonderheit:** Zugang kann zeitlich begrenzt werden

---

## 2. Berechtigungsmatrix

### 2.1 Funktionsbasierte Berechtigungen

| Funktion | Admin | Schueler | Extern |
|----------|-------|----------|--------|
| **Nutzerverwaltung** |
| Nutzer anlegen | ✅ | ❌ | ❌ |
| Nutzer bearbeiten | ✅ | ❌ | ❌ |
| Nutzer löschen | ✅ | ❌ | ❌ |
| Nutzer-Liste sehen | ✅ | ❌ | ❌ |
| Eigenes Profil bearbeiten | ✅ | ✅ | ✅ |
| Eigenes Passwort ändern | ✅ | ✅ | ✅ |
| **Projekte** |
| Alle Projekte sehen | ✅ | ❌ | ❌ |
| Eigenes Projekt sehen | ✅ | ✅ | ✅ (nur freigegebene) |
| Projekt erstellen | ✅ | ❌ | ❌ |
| Eigenes Projekt bearbeiten | ✅ | ✅ | ❌ |
| Fremdes Projekt bearbeiten | ✅ | ❌ | ❌ |
| Projekt löschen | ✅ | ❌ | ❌ |
| Projekt-Zuweisung ändern | ✅ | ❌ | ❌ |
| **Dokumente** |
| Dokumente hochladen (eigenes Projekt) | ✅ | ✅ | ❌ |
| Dokumente analysieren (eigenes Projekt) | ✅ | ✅ | ❌ |
| Dokumente sehen (eigenes Projekt) | ✅ | ✅ | ✅ (freigegebene) |
| Dokumente löschen | ✅ | ✅ (eigene) | ❌ |
| **Testgenerator** |
| Generator nutzen | ✅ | ✅ | ✅ |
| Generator-Einstellungen | ✅ | ❌ | ❌ |
| **Rulesets** |
| Rulesets sehen | ✅ | ✅ | ❌ |
| Rulesets erstellen/bearbeiten | ✅ | ❌ | ❌ |
| Rulesets löschen | ✅ | ❌ | ❌ |
| **Statistiken** |
| Dashboard sehen | ✅ | ✅ (eigenes Projekt) | ❌ |
| System-Statistiken | ✅ | ❌ | ❌ |
| Export-Funktionen | ✅ | ✅ (eigene Daten) | ❌ |
| **Einstellungen** |
| Sprache ändern | ✅ | ✅ | ✅ |
| Theme ändern (Hell/Dunkel) | ✅ | ✅ | ✅ |
| LLM-Provider konfigurieren | ✅ | ❌ | ❌ |
| API-Keys verwalten | ✅ | ❌ | ❌ |
| System-Einstellungen | ✅ | ❌ | ❌ |

### 2.2 API-Endpunkt-Berechtigungen

| Endpunkt | Methode | Admin | Schueler | Extern |
|----------|---------|-------|----------|--------|
| `/api/users` | GET | ✅ | ❌ | ❌ |
| `/api/users` | POST | ✅ | ❌ | ❌ |
| `/api/users/{id}` | GET | ✅ | 👤 (nur self) | 👤 (nur self) |
| `/api/users/{id}` | PUT | ✅ | 👤 (nur self) | 👤 (nur self, limited) |
| `/api/users/{id}` | DELETE | ✅ | ❌ | ❌ |
| `/api/projects` | GET | ✅ (alle) | ✅ (gefiltert) | ✅ (freigegebene) |
| `/api/projects` | POST | ✅ | ❌ | ❌ |
| `/api/projects/{id}` | GET | ✅ | ✅ (Zugriffsprüfung) | ✅ (Zugriffsprüfung) |
| `/api/projects/{id}` | PUT | ✅ | ✅ (nur eigenes) | ❌ |
| `/api/projects/{id}` | DELETE | ✅ | ❌ | ❌ |
| `/api/documents/upload` | POST | ✅ | ✅ (eigenes Projekt) | ❌ |
| `/api/documents/{id}/analyze` | POST | ✅ | ✅ (eigenes Projekt) | ❌ |
| `/api/generator/*` | * | ✅ | ✅ | ✅ |
| `/api/rulesets` | GET | ✅ | ✅ | ❌ |
| `/api/rulesets` | POST/PUT/DELETE | ✅ | ❌ | ❌ |
| `/api/stats/*` | GET | ✅ | ❌ | ❌ |
| `/api/settings` | GET | ✅ | ✅ (persönlich) | ✅ (persönlich) |
| `/api/settings` | PUT | ✅ | ✅ (persönlich) | ✅ (persönlich) |
| `/api/llm/providers` | GET/PUT | ✅ | ❌ | ❌ |

---

## 3. Datenmodell

### 3.1 Aktualisiertes User-Modell

```python
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)

    # Neue Rolle mit drei Werten
    role = Column(String(20), default="schueler", nullable=False)  # admin, schueler, extern

    # Aktivitäts-Status
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Beziehungen
    assigned_project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    assigned_project = relationship("Project", back_populates="assigned_users")

    # Persönliche Einstellungen
    language = Column(String(5), default="de")
    theme = Column(String(10), default="light")  # light, dark, system

    # Für Extern-Zugang
    access_expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional: Zeitbegrenzung
    invited_by_id = Column(String, ForeignKey("users.id"), nullable=True)
```

### 3.2 Erweitertes Project-Modell

```python
class Project(Base):
    __tablename__ = "projects"

    # ... bestehende Felder ...

    # Neue Felder für Nutzer-Zuweisung
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id])

    # Benutzer, die diesem Projekt zugewiesen sind
    assigned_users = relationship("User", back_populates="assigned_project")

    # Für Extern-Zugang: Projekt-Freigabe
    is_shared_externally = Column(Boolean, default=False)
    share_token = Column(String(64), nullable=True, unique=True)  # Für Link-basierte Freigabe
```

### 3.3 Neue Tabelle: ProjectShare (für granulare Freigaben)

```python
class ProjectShare(Base):
    __tablename__ = "project_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Kann null sein für Link-Shares

    # Freigabe-Details
    share_type = Column(String(20), nullable=False)  # "user", "link"
    share_token = Column(String(64), nullable=True, unique=True)
    permissions = Column(String(20), default="read")  # "read", "write"

    # Zeitbegrenzung
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
```

---

## 4. Implementierungsplan

### Phase 1: Backend-Grundlagen (Priorität: Hoch)

#### 1.1 Datenbankmigrationen
- [ ] User-Modell erweitern um `role` mit drei Werten
- [ ] User-Modell erweitern um `assigned_project_id`, `theme`, `access_expires_at`
- [ ] Project-Modell erweitern um `owner_id`, `is_shared_externally`, `share_token`
- [ ] ProjectShare-Tabelle erstellen
- [ ] Alembic-Migration erstellen und testen

#### 1.2 Authentifizierungs-Upgrade
- [ ] Demo-User-System durch datenbankbasierte Authentifizierung ersetzen
- [ ] Unsicheres X-Role-Header-System entfernen
- [ ] Neues Permission-Checking-System implementieren

#### 1.3 Authorization-Middleware
- [ ] `CurrentSchueler` Dependency erstellen
- [ ] `CurrentExtern` Dependency erstellen
- [ ] `RequireProjectAccess` Dependency erstellen
- [ ] Permission-Decorators implementieren

### Phase 2: API-Endpunkte (Priorität: Hoch)

#### 2.1 User-Management-API
- [ ] `POST /api/users` - Nutzer erstellen (Admin only)
- [ ] `GET /api/users` - Nutzerliste (Admin only)
- [ ] `GET /api/users/{id}` - Nutzer-Details
- [ ] `PUT /api/users/{id}` - Nutzer bearbeiten
- [ ] `DELETE /api/users/{id}` - Nutzer löschen (Admin only)
- [ ] `PUT /api/users/{id}/password` - Passwort ändern
- [ ] `PUT /api/users/{id}/role` - Rolle ändern (Admin only)

#### 2.2 Projekt-Zuweisung-API
- [ ] `POST /api/projects/{id}/assign` - Nutzer zuweisen (Admin only)
- [ ] `DELETE /api/projects/{id}/assign/{user_id}` - Zuweisung entfernen
- [ ] `GET /api/projects/{id}/users` - Zugewiesene Nutzer
- [ ] `POST /api/projects/{id}/share` - Projekt freigeben
- [ ] `DELETE /api/projects/{id}/share/{share_id}` - Freigabe entfernen

#### 2.3 Bestehende Endpunkte absichern
- [ ] Alle Project-Endpunkte mit Zugriffsprüfung versehen
- [ ] Alle Document-Endpunkte mit Projekt-Zugriffsprüfung
- [ ] Settings-Endpunkte nach Rolle filtern
- [ ] Stats-Endpunkte auf Admin beschränken

### Phase 3: Frontend (Priorität: Mittel)

#### 3.1 AuthContext erweitern
- [ ] Rolle im AuthContext speichern
- [ ] Permission-Helpers implementieren (`canEditProject`, `canManageUsers`, etc.)
- [ ] Zugewiesenes Projekt im Context

#### 3.2 Nutzerverwaltungs-UI (Admin)
- [ ] Neue Seite: `/users` - Nutzerverwaltung
- [ ] User-Liste mit Suche und Filter
- [ ] User-Formular (Erstellen/Bearbeiten)
- [ ] Rollen-Zuweisung UI
- [ ] Projekt-Zuweisung UI

#### 3.3 Rollenbasierte Navigation
- [ ] Sidebar-Einträge nach Rolle filtern
- [ ] Protected Routes nach Rolle
- [ ] Bedingte UI-Elemente (Buttons, Menüs)

#### 3.4 Externe Nutzer-Ansicht
- [ ] Minimale Navigation für Externe
- [ ] Nur freigegebenes Projekt anzeigen
- [ ] Generator-Zugang
- [ ] Eingeschränkte Einstellungsseite

### Phase 4: Cloudflare-Integration (Priorität: Niedrig)

#### 4.1 Extern-Zugang über Cloudflare Tunnel
- [ ] Separate Route für externe Nutzer (`/extern/*`)
- [ ] Cloudflare Access Integration prüfen
- [ ] Token-basierte Authentifizierung für Extern
- [ ] Zeitbegrenzte Zugänge implementieren

---

## 5. Technische Details

### 5.1 Permission-System

```python
# backend/app/core/permissions.py

from enum import Enum
from typing import Set

class Permission(str, Enum):
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"

    # Projects
    PROJECT_CREATE = "project:create"
    PROJECT_READ_ALL = "project:read_all"
    PROJECT_READ_OWN = "project:read_own"
    PROJECT_UPDATE_ALL = "project:update_all"
    PROJECT_UPDATE_OWN = "project:update_own"
    PROJECT_DELETE = "project:delete"
    PROJECT_ASSIGN = "project:assign"
    PROJECT_SHARE = "project:share"

    # Documents
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_ANALYZE = "document:analyze"
    DOCUMENT_DELETE = "document:delete"

    # Generator
    GENERATOR_USE = "generator:use"
    GENERATOR_CONFIGURE = "generator:configure"

    # Rulesets
    RULESET_READ = "ruleset:read"
    RULESET_MANAGE = "ruleset:manage"

    # Statistics
    STATS_VIEW_ALL = "stats:view_all"
    STATS_VIEW_OWN = "stats:view_own"

    # Settings
    SETTINGS_PERSONAL = "settings:personal"
    SETTINGS_SYSTEM = "settings:system"
    SETTINGS_LLM = "settings:llm"


ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "admin": {
        # Alle Berechtigungen
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
        Permission.USER_DELETE, Permission.USER_MANAGE_ROLES,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ_ALL, Permission.PROJECT_READ_OWN,
        Permission.PROJECT_UPDATE_ALL, Permission.PROJECT_UPDATE_OWN, Permission.PROJECT_DELETE,
        Permission.PROJECT_ASSIGN, Permission.PROJECT_SHARE,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_ANALYZE, Permission.DOCUMENT_DELETE,
        Permission.GENERATOR_USE, Permission.GENERATOR_CONFIGURE,
        Permission.RULESET_READ, Permission.RULESET_MANAGE,
        Permission.STATS_VIEW_ALL, Permission.STATS_VIEW_OWN,
        Permission.SETTINGS_PERSONAL, Permission.SETTINGS_SYSTEM, Permission.SETTINGS_LLM,
    },
    "schueler": {
        Permission.PROJECT_READ_OWN, Permission.PROJECT_UPDATE_OWN,
        Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_ANALYZE, Permission.DOCUMENT_DELETE,
        Permission.GENERATOR_USE,
        Permission.RULESET_READ,
        Permission.STATS_VIEW_OWN,
        Permission.SETTINGS_PERSONAL,
    },
    "extern": {
        Permission.PROJECT_READ_OWN,  # Nur freigegebene
        Permission.GENERATOR_USE,
        Permission.SETTINGS_PERSONAL,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Prüft, ob eine Rolle eine bestimmte Berechtigung hat."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions(role: str) -> Set[Permission]:
    """Gibt alle Berechtigungen einer Rolle zurück."""
    return ROLE_PERMISSIONS.get(role, set())
```

### 5.2 Authorization Dependencies

```python
# backend/app/api/deps.py (erweitert)

from fastapi import Depends, HTTPException, status
from app.core.permissions import Permission, has_permission

class RequirePermission:
    """Dependency, die eine bestimmte Berechtigung erfordert."""

    def __init__(self, permission: Permission):
        self.permission = permission

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Berechtigung '{self.permission.value}' erforderlich"
            )
        return current_user


class RequireProjectAccess:
    """Dependency, die Zugriff auf ein bestimmtes Projekt erfordert."""

    def __init__(self, require_write: bool = False):
        self.require_write = require_write

    async def __call__(
        self,
        project_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        # Admin hat immer Zugriff
        if current_user.role == "admin":
            return current_user

        # Prüfen, ob Nutzer dem Projekt zugewiesen ist
        if current_user.assigned_project_id == project_id:
            return current_user

        # Prüfen, ob Projekt für Nutzer freigegeben ist (für externe)
        if current_user.role == "extern":
            share = await db.execute(
                select(ProjectShare).where(
                    ProjectShare.project_id == project_id,
                    ProjectShare.user_id == current_user.id,
                    or_(
                        ProjectShare.expires_at.is_(None),
                        ProjectShare.expires_at > func.now()
                    )
                )
            )
            if share.scalar_one_or_none():
                if self.require_write and share.permissions != "write":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Schreibzugriff nicht erlaubt"
                    )
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kein Zugriff auf dieses Projekt"
        )
```

### 5.3 Frontend Permission Helpers

```typescript
// frontend/src/lib/permissions.ts

export type Role = 'admin' | 'schueler' | 'extern';

export enum Permission {
  USER_CREATE = 'user:create',
  USER_READ = 'user:read',
  USER_UPDATE = 'user:update',
  USER_DELETE = 'user:delete',
  PROJECT_CREATE = 'project:create',
  PROJECT_READ_ALL = 'project:read_all',
  PROJECT_UPDATE_OWN = 'project:update_own',
  DOCUMENT_UPLOAD = 'document:upload',
  GENERATOR_USE = 'generator:use',
  RULESET_READ = 'ruleset:read',
  RULESET_MANAGE = 'ruleset:manage',
  STATS_VIEW_ALL = 'stats:view_all',
  SETTINGS_SYSTEM = 'settings:system',
  SETTINGS_LLM = 'settings:llm',
}

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  admin: Object.values(Permission),
  schueler: [
    Permission.PROJECT_UPDATE_OWN,
    Permission.DOCUMENT_UPLOAD,
    Permission.GENERATOR_USE,
    Permission.RULESET_READ,
  ],
  extern: [
    Permission.GENERATOR_USE,
  ],
};

export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

export function usePermission(permission: Permission): boolean {
  const { user } = useAuth();
  return user ? hasPermission(user.role as Role, permission) : false;
}
```

---

## 6. UI-Mockups

### 6.1 Nutzerverwaltung (Admin-Ansicht)

```
┌─────────────────────────────────────────────────────────────────┐
│  Nutzerverwaltung                           [+ Neuer Nutzer]    │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Suche...                    Rolle: [Alle ▼]                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 👤 Max Mustermann          │ Admin    │ Aktiv  │ [✏️][🗑️] │  │
│  │    max@schule.de           │          │        │          │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ 👤 Lisa Schülerin          │ Schüler  │ Aktiv  │ [✏️][🗑️] │  │
│  │    lisa@schule.de          │ → Projekt: Übung 2024        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ 👤 Ext. Prüfer Müller      │ Extern   │ Aktiv  │ [✏️][🗑️] │  │
│  │    mueller@extern.de       │ → Freigabe: Projekt X        │  │
│  │                            │   Läuft ab: 31.12.2024       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Nutzer-Bearbeitungs-Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│  Nutzer bearbeiten                                      [X]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Benutzername *     [lisa_schuelerin          ]                 │
│  E-Mail *           [lisa@schule.de           ]                 │
│  Vollständiger Name [Lisa Schülerin           ]                 │
│                                                                 │
│  Rolle *            [Schüler              ▼]                    │
│                     ○ Admin - Vollzugriff                       │
│                     ● Schüler - Eigenes Projekt                 │
│                     ○ Extern - Eingeschränkt                    │
│                                                                 │
│  Zugewiesenes Projekt                                           │
│                     [Übung 2024           ▼]                    │
│                                                                 │
│  ☑ Aktiv                                                        │
│  ☐ Zugang läuft ab am [____________] (nur für Externe)          │
│                                                                 │
│                           [Abbrechen]  [Speichern]              │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Sidebar nach Rolle

**Admin:**
```
┌──────────────────┐
│ 📊 Dashboard     │
│ 📁 Projekte      │
│ 📄 Dokumente     │
│ 🧪 Generator     │
│ 📋 Regelwerke    │
│ 📈 Statistiken   │
│ 👥 Nutzer        │  ← Nur Admin
│ ⚙️ Einstellungen │
└──────────────────┘
```

**Schüler:**
```
┌──────────────────┐
│ 📊 Dashboard     │
│ 📁 Mein Projekt  │  ← Nur eigenes
│ 📄 Dokumente     │
│ 🧪 Generator     │
│ 📋 Regelwerke    │  ← Nur lesen
│ ⚙️ Einstellungen │  ← Nur persönlich
└──────────────────┘
```

**Extern:**
```
┌──────────────────┐
│ 📁 Projekt       │  ← Nur freigegebenes
│ 🧪 Generator     │
│ ⚙️ Einstellungen │  ← Nur Sprache/Theme
└──────────────────┘
```

---

## 7. Migration bestehender Daten

### 7.1 Migrationsstrategie

1. **Neue Spalten mit Defaults hinzufügen**
   - `role` Default: "admin" (für bestehenden Demo-Admin)
   - `assigned_project_id` Default: NULL

2. **Bestehende Demo-Nutzer migrieren**
   - `admin:admin` → role: "admin"
   - `user:user` → role: "schueler"

3. **Projekte ohne Owner**
   - Alle bestehenden Projekte dem Admin zuweisen
   - Oder: `owner_id` optional lassen

### 7.2 Alembic-Migration (Beispiel)

```python
def upgrade() -> None:
    # User-Tabelle erweitern
    op.add_column('users', sa.Column('assigned_project_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('theme', sa.String(10), server_default='light'))
    op.add_column('users', sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('invited_by_id', sa.String(), nullable=True))

    # Role-Feld aktualisieren (von user/admin zu schueler/admin/extern)
    op.execute("UPDATE users SET role = 'schueler' WHERE role = 'user'")

    # Project-Tabelle erweitern
    op.add_column('projects', sa.Column('owner_id', sa.String(), nullable=True))
    op.add_column('projects', sa.Column('is_shared_externally', sa.Boolean(), server_default='false'))
    op.add_column('projects', sa.Column('share_token', sa.String(64), nullable=True))

    # ProjectShare-Tabelle erstellen
    op.create_table(
        'project_shares',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('share_type', sa.String(20), nullable=False),
        sa.Column('share_token', sa.String(64), nullable=True),
        sa.Column('permissions', sa.String(20), server_default='read'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
    )
```

---

## 8. Sicherheitsüberlegungen

### 8.1 Bekannte Schwachstellen beheben

1. **X-Role Header entfernen** - Sofort
2. **Demo-User-System deaktivierbar machen** - Für Produktion
3. **Alle Endpunkte mit Auth schützen** - Keine offenen APIs

### 8.2 Neue Sicherheitsmaßnahmen

1. **Rate Limiting** für Login-Versuche
2. **Passwort-Komplexität** erzwingen
3. **Session-Invalidierung** bei Rollenänderung
4. **Audit-Log** für Admin-Aktionen
5. **Externe Token** mit automatischem Ablauf

### 8.3 Cloudflare-Tunnel-Sicherheit

1. Extern-Zugang **nur** über Cloudflare Tunnel
2. Separate Subdomain für Externe (z.B. `extern.flowaudit.local`)
3. Zeitbegrenzte Access-Tokens
4. IP-Whitelisting optional

---

## 9. Testplan

### 9.1 Unit Tests
- [ ] Permission-System testen
- [ ] Role-Checking testen
- [ ] ProjectAccess-Dependency testen

### 9.2 Integration Tests
- [ ] Login mit allen drei Rollen
- [ ] API-Zugriff pro Rolle testen
- [ ] Projekt-Zuweisung testen
- [ ] Extern-Freigabe testen

### 9.3 E2E Tests
- [ ] Admin kann Nutzer verwalten
- [ ] Schüler sieht nur eigenes Projekt
- [ ] Externer hat eingeschränkten Zugang

---

## 10. Entschiedene Fragen

1. **Sollen Schüler andere Projekte lesen können?**
   - ✅ **Entscheidung: Option A** - Nur eigenes Projekt sichtbar

2. **Sollen Externe direkt Dokumente sehen oder nur Ergebnisse?**
   - ✅ **Entscheidung: Option A** - Vollständige Dokument-Ansicht

3. **Wie soll die Projekt-Zuweisung erfolgen?**
   - ✅ **Entscheidung: Option A** - Admin weist manuell zu

4. **Brauchen wir Gruppen/Klassen?**
   - ✅ **Entscheidung: Nein** - Keine Gruppen/Klassen nötig

---

## Zusammenfassung

Dieses Konzept bietet ein flexibles, aber überschaubares Rollen- und Berechtigungssystem mit drei Hauptrollen:

| Rolle | Fokus | Hauptzugang |
|-------|-------|-------------|
| **Admin** | Verwaltung | Alles |
| **Schüler** | Lernen/Üben | Eigenes Projekt + Generator |
| **Extern** | Prüfen/Gastnutzung | Freigegebenes Projekt + Generator |

Die Implementierung erfolgt schrittweise, beginnend mit den Backend-Grundlagen und der Absicherung bestehender Endpunkte.
