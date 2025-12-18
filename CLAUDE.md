# FlowInvoice/FlowAudit - Claude Code Guide

## Projektübersicht

FlowAudit ist ein KI-gestütztes Rechnungsprüfungssystem mit:
- **Backend**: FastAPI (Python 3.11+) mit Celery Worker
- **Frontend**: React 18 + TypeScript + Vite + Tailwind
- **Datenbank**: PostgreSQL 16 mit pgvector
- **LLM**: Ollama (lokal) oder OpenAI/Anthropic/Gemini (Cloud)
- **Vector DB**: ChromaDB für RAG
- **Queue**: Redis für Celery Tasks

---

## Schnellstart (Docker)

### Voraussetzungen
- Docker + Docker Compose
- Mindestens 16 GB RAM (für Ollama)
- Optional: NVIDIA GPU mit nvidia-container-toolkit

### Starten

```bash
# Für lokale Entwicklung (mit Build)
cd docker
docker compose up -d

# Für Portainer (mit pre-built Images)
# Compose path: docker/docker-compose.portainer.yml
```

### Services und Ports

| Service   | Port  | URL                          |
|-----------|-------|------------------------------|
| Frontend  | 3000  | http://localhost:3000        |
| Backend   | 8000  | http://localhost:8000        |
| API Docs  | 8000  | http://localhost:8000/docs   |
| PostgreSQL| 5432  | -                            |
| Redis     | 6379  | -                            |
| ChromaDB  | 8001  | http://localhost:8001        |
| Ollama    | 11434 | http://localhost:11434       |

---

## Häufige Probleme & Lösungen

### Backend startet nicht

```bash
# Logs prüfen
docker logs flowaudit-backend

# Typische Ursachen:
# 1. Datenbank nicht bereit → warten oder neu starten
# 2. Redis nicht erreichbar → Redis-Container prüfen
# 3. Migrations-Fehler → Datenbank-Init prüfen
```

### Frontend kann Backend nicht erreichen

```bash
# Prüfen ob Backend läuft
curl http://localhost:8000/api/health

# CORS-Probleme: Backend-Umgebungsvariable prüfen
CORS_ORIGINS=http://localhost:3000
```

### Ollama antwortet nicht

```bash
# Status prüfen
curl http://localhost:11434/api/tags

# Modell herunterladen (falls noch nicht vorhanden)
docker exec flowaudit-ollama ollama pull llama3.2

# GPU-Probleme: CPU-Fallback in docker-compose.portainer.yml nutzen
```

### Celery Worker hängt

```bash
# Worker-Logs prüfen
docker logs flowaudit-worker

# Worker neu starten
docker restart flowaudit-worker
```

---

## Entwicklung

### Backend (Python)

```bash
cd backend

# Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Dependencies
pip install -e ".[dev]"

# Lokaler Start (ohne Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React)

```bash
cd frontend

# Dependencies
npm install

# Entwicklungsserver
npm run dev

# Build
npm run build

# Type-Check
npx tsc --noEmit
```

---

## Projektstruktur

```
flowinvoice/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes
│   │   ├── models/       # SQLAlchemy Models
│   │   ├── schemas/      # Pydantic Schemas
│   │   ├── services/     # Business Logic
│   │   ├── llm/          # LLM Provider (Ollama, OpenAI, etc.)
│   │   ├── rag/          # RAG mit ChromaDB
│   │   └── worker/       # Celery Tasks
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/        # React Pages
│   │   ├── components/   # React Components
│   │   ├── lib/          # API Client, Utils
│   │   └── i18n/         # Übersetzungen (DE/EN)
│   ├── Dockerfile
│   └── package.json
├── docker/
│   ├── docker-compose.yml              # Lokale Entwicklung
│   ├── docker-compose.portainer.yml    # Portainer (ohne GPU)
│   ├── docker-compose.portainer.gpu.yml # Portainer (mit GPU)
│   └── stack.env                       # Umgebungsvariablen
└── docs/
    ├── architecture.md    # Systemarchitektur
    ├── api_contracts.md   # API Spezifikation
    ├── rulesets.md        # Steuerliche Regelwerke
    └── requirements.md    # Funktionale Anforderungen
```

---

## API Endpunkte (wichtigste)

```
GET  /api/health              # Health Check
GET  /api/health/detailed     # Detaillierter Status

# Dokumente
POST /api/documents/upload    # PDF hochladen
GET  /api/documents/{id}      # Dokument abrufen
POST /api/documents/{id}/analyze  # Analyse starten

# Projekte
GET  /api/projects            # Alle Projekte
POST /api/projects            # Neues Projekt

# LLM Provider
GET  /api/llm/providers       # Verfügbare Provider
POST /api/llm/providers/{id}/test  # Provider testen

# Einstellungen
GET  /api/settings            # Alle Einstellungen
PUT  /api/settings            # Einstellungen aktualisieren
```

---

## Umgebungsvariablen

### Backend (.env oder docker-compose)

```bash
# Datenbank
DATABASE_URL=postgresql+asyncpg://flowaudit:flowaudit_secret@db:5432/flowaudit
POSTGRES_PASSWORD=flowaudit_secret

# Redis
REDIS_URL=redis://redis:6379/0

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_TOKEN=flowaudit_chroma_token

# Ollama
OLLAMA_HOST=http://ollama:11434

# Sicherheit
SECRET_KEY=change_in_production

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

---

## Tests

```bash
# Backend Tests
cd backend
pytest

# Frontend Tests
cd frontend
npm test
```

---

## Dokumentation

Ausführliche Dokumentation in `/docs/`:

- **architecture.md** - Systemarchitektur und Komponenten
- **api_contracts.md** - Vollständige API-Spezifikation
- **rulesets.md** - Steuerliche Regelwerke (DE/EU)
- **requirements.md** - Funktionale Anforderungen
- **rag_learning.md** - RAG und Lernmechanismus
- **operations.md** - Betrieb und Monitoring

---

---

## Frontend GUI

### Seiten-Übersicht

| Seite        | Route              | Zweck                              |
|--------------|--------------------|------------------------------------|
| Dashboard    | `/`                | Übersicht, Statistiken             |
| Projekte     | `/projects`        | Projektverwaltung                  |
| Dokumente    | `/documents`       | Dokumenten-Upload und Liste        |
| Rulesets     | `/rulesets`        | Steuerliche Regelwerke verwalten   |
| Statistik    | `/statistics`      | Auswertungen und Charts            |
| Einstellungen| `/settings`        | LLM-Provider, Sprache, Theme       |
| Login        | `/login`           | Anmeldung                          |

### Komponenten-Struktur

```
src/
├── pages/
│   ├── Dashboard.tsx       # Startseite mit Kennzahlen
│   ├── Projects.tsx        # Projektliste
│   ├── ProjectDetail.tsx   # Einzelnes Projekt
│   ├── Documents.tsx       # Dokumentenverwaltung
│   ├── DocumentDetail.tsx  # Dokument-Analyse-Ansicht
│   ├── Rulesets.tsx        # Regelwerk-Editor
│   ├── Statistics.tsx      # Statistik-Dashboard
│   ├── Settings.tsx        # Einstellungen
│   └── Login.tsx           # Authentifizierung
├── components/
│   ├── Layout.tsx          # Haupt-Layout mit Sidebar
│   ├── Sidebar.tsx         # Navigation
│   └── ui/                 # Wiederverwendbare UI-Komponenten
├── lib/
│   ├── api.ts              # API-Client (axios)
│   ├── types.ts            # TypeScript Interfaces
│   └── i18n.ts             # Internationalisierung
└── store/
    └── authStore.ts        # Zustand für Auth
```

### UI-Funktionen

- **Dark Mode**: Toggle in Settings, persistiert in localStorage
- **Sprache**: Deutsch/Englisch umschaltbar
- **LLM-Provider**: Auswahl zwischen Ollama, OpenAI, Anthropic, Gemini
- **API-Keys**: Maskierte Eingabe für Cloud-Provider
- **Live-Status**: System-Metriken (CPU, RAM, GPU) in Settings

### Styling

- **Tailwind CSS**: Utility-First CSS Framework
- **Farben**: Primary (Blau), Grau-Töne, Status-Farben (Rot/Gelb/Grün)
- **Icons**: Lucide React
- **Responsive**: Mobile-First Design

### State Management

- **React Query**: Server-State (API-Daten, Caching)
- **Zustand**: Client-State (Auth, UI-Preferences)
- **localStorage**: Theme, Sprache

---

## Portainer GUI Deployment

### Schritt-für-Schritt

1. **Portainer öffnen** → Stacks → Add Stack

2. **Build method**: Repository wählen

3. **Repository-Einstellungen**:
   - URL: `https://github.com/janpow77/flowinvoice.git`
   - Reference: `refs/heads/main`
   - Compose path: `docker/docker-compose.portainer.yml`
   - (Mit GPU: `docker/docker-compose.portainer.gpu.yml`)

4. **Environment variables**:
   - Werden aus `docker/stack.env` geladen
   - Oder manuell überschreiben

5. **Deploy the stack** klicken

### Portainer Troubleshooting

| Problem | Lösung |
|---------|--------|
| "stack.env not found" | Datei existiert jetzt im Repo |
| "Image pull failed" | GitHub Actions muss Images erst bauen |
| "GPU not available" | `docker-compose.portainer.yml` (ohne GPU) verwenden |
| "Container unhealthy" | Logs prüfen, start_period abwarten |

---

## Bekannte Einschränkungen

1. **Ollama braucht Zeit** - Erster Start lädt Modelle (mehrere GB)
2. **GPU optional** - Ohne GPU ist LLM langsamer aber funktional
3. **ChromaDB Healthcheck** - Gibt immer "healthy" zurück (by design)
4. **Frontend Build** - Strikte TypeScript-Prüfung (keine `any` ohne Annotation)
5. **GitHub Actions** - Images werden erst bei Push zu `main` gebaut
