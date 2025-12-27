# FlowAudit - Claude Code Projektguide

## Projektüberblick

FlowAudit ist ein KI-gestütztes Schulungs- und Prüfungssystem für die regelbasierte Analyse von Geschäftsdokumenten (Rechnungen, Kontoauszüge, Belege). Das System prüft Dokumente gegen konfigurierbare steuerliche Regelwerke (DE_USTG, EU_VAT, UK_VAT) und ist darauf ausgelegt, weitere Regelwerke modular zu integrieren. Zielgruppe sind Finanzabteilungen, Steuerberater und Ausbildungseinrichtungen, die strukturierte Dokumentenprüfung erlernen oder automatisieren möchten.

---

## Technologie-Stack

### Backend (Python 3.11+)

| Komponente | Bibliothek | Version | Anmerkungen |
|------------|-----------|---------|-------------|
| Web Framework | FastAPI | ≥0.109 | Async-first, Pydantic v2 |
| HTTP Client | **httpx** | ≥0.26 | Nicht requests verwenden |
| ORM | SQLAlchemy | ≥2.0.25 | Async mit asyncpg |
| Migrations | Alembic | ≥1.13 | |
| Task Queue | Celery + Redis | ≥5.3.6 | |
| PDF Parsing | pdfplumber, pypdf | | |
| Validation | Pydantic | ≥2.5.3 | Strikte Schemas |
| LLM Clients | openai, anthropic, google-generativeai | | Ollama via httpx |
| Vector Store | ChromaDB | ≥0.4.22 | RAG-Funktionalität |
| Embeddings | sentence-transformers | ≥2.3.1 | |

### Frontend (Node 18+)

| Komponente | Bibliothek | Version | Anmerkungen |
|------------|-----------|---------|-------------|
| Framework | React | 18.3 | Functional Components only |
| Build | Vite | 5.4 | |
| Sprache | TypeScript | 5.6 | Strict mode, kein `any` |
| Styling | Tailwind CSS | 3.4 | Utility-first |
| HTTP Client | **axios** | 1.7 | Nicht fetch direkt |
| Server State | @tanstack/react-query | 5.60 | Caching, Refetching |
| Client State | zustand | 5.0 | Auth, UI-Preferences |
| i18n | i18next + react-i18next | | DE/EN |
| Icons | lucide-react | 0.460 | |
| Router | react-router-dom | 6.28 | |
| Charts | recharts | 2.13 | |

### Infrastruktur

| Dienst | Technologie | Port |
|--------|------------|------|
| Datenbank | PostgreSQL 16 + pgvector | 5432 |
| Cache/Queue | Redis | 6379 |
| Vector DB | ChromaDB | 8001 |
| LLM (lokal) | Ollama | 11434 |
| Backend | Uvicorn | 8000 |
| Frontend | Nginx/Vite | 3000 |

---

## Kritische Bereiche

> Diese Dateien/Module dürfen **NICHT** ohne explizite Anweisung geändert werden:

### Regelwerk-Logik (produktiv validiert)

```
backend/app/services/rule_engine.py      # Regelwerk-Auswertung
backend/app/services/validators.py       # Steuerliche Validierungen
backend/app/seeds/rulesets.py            # Seed-Daten für DE_USTG, EU_VAT, UK_VAT
docs/rulesets.md                         # Ground Truth für Regelwerke
```

### Datenbank-Schema

```
backend/app/models/*.py                  # SQLAlchemy Models
backend/alembic/versions/*.py            # Migrations - nie manuell editieren
```

### Sicherheit

```
backend/app/core/security.py             # JWT, Passwort-Hashing
backend/app/core/permissions.py          # Rollenbasierte Zugriffskontrolle
backend/app/api/auth.py                  # Auth-Endpunkte
```

### API-Contracts

```
backend/app/schemas/*.py                 # Pydantic-Schemas (API-Vertrag)
docs/api_contracts.md                    # API-Spezifikation
```

---

## Code-Konventionen

### Python (Backend)

**Import-Reihenfolge** (durch ruff/isort erzwungen):
```python
# 1. Standard Library
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports
from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse
```

**Docstring-Format** (Google-Style):
```python
def process_invoice(document_id: str, ruleset_id: str) -> AuditResult:
    """
    Prüft eine Rechnung gegen ein Regelwerk.

    Args:
        document_id: UUID des Dokuments.
        ruleset_id: ID des Regelwerks (z.B. "DE_USTG").

    Returns:
        AuditResult mit Prüfergebnissen.

    Raises:
        DocumentNotFoundError: Dokument existiert nicht.
        RulesetNotFoundError: Regelwerk nicht gefunden.
    """
```

**Namenskonventionen**:
- Klassen: `PascalCase` (z.B. `AuditService`, `DocumentResponse`)
- Funktionen/Variablen: `snake_case` (z.B. `get_document`, `ruleset_id`)
- Konstanten: `UPPER_SNAKE_CASE` (z.B. `DEFAULT_PAGE_SIZE`)
- Private: `_leading_underscore` (z.B. `_internal_helper`)

**Type Hints**: Immer verwenden, `Any` vermeiden:
```python
# Richtig
async def get_documents(limit: int = 20) -> list[Document]: ...

# Falsch
async def get_documents(limit=20): ...
```

### TypeScript (Frontend)

**Import-Reihenfolge**:
```typescript
// 1. React/externe Libs
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

// 2. Komponenten
import { Button } from '@/components/ui/Button'
import { Layout } from '@/components/Layout'

// 3. Utilities/Types
import { api } from '@/lib/api'
import type { Document } from '@/lib/types'
```

**Komponenten-Struktur**:
```typescript
// Functional Components mit expliziten Props-Interface
interface DocumentCardProps {
  document: Document
  onSelect: (id: string) => void
}

export function DocumentCard({ document, onSelect }: DocumentCardProps) {
  // Hooks zuerst
  const [isExpanded, setIsExpanded] = useState(false)

  // Event Handler
  const handleClick = () => onSelect(document.id)

  // JSX
  return (...)
}
```

**Strikte TypeScript-Regeln**:
- Kein `any` ohne explizite Annotation/Begründung
- Kein `@ts-ignore` ohne Kommentar
- Immer `interface` für Props, `type` für Unions

### Commit-Messages

Format: `<type>: <description>`

Typen:
- `feat:` Neue Funktionalität
- `fix:` Bugfix
- `refactor:` Code-Umstrukturierung ohne Funktionsänderung
- `docs:` Dokumentation
- `test:` Tests hinzufügen/ändern
- `chore:` Build, Dependencies, Konfiguration

Beispiele:
```
feat: Add UK_VAT ruleset support
fix: Correct VAT calculation for small invoices
refactor: Extract PDF parsing into dedicated service
docs: Update API documentation for batch endpoints
```

---

## Externe Abhängigkeiten

### Datenbank (PostgreSQL)

```
Host: db (Docker) / localhost (lokal)
Port: 5432
Connection: postgresql+asyncpg://flowaudit:***@db:5432/flowaudit
```

### Redis (Celery Queue)

```
Host: redis (Docker) / localhost (lokal)
Port: 6379
URL: redis://redis:6379/0
```

### ChromaDB (Vector Store)

```
Host: chromadb (Docker) / localhost (lokal)
Port: 8000 (intern) / 8001 (extern)
Auth: Token-basiert (CHROMA_TOKEN)
```

### Ollama (LLM - lokal)

```
Host: ollama (Docker) / localhost (lokal)
Port: 11434
Endpunkte:
  POST /api/generate     # Text-Generierung
  POST /api/embeddings   # Embeddings
  GET  /api/tags         # Verfügbare Modelle
```

### LLM Cloud-Provider (optional)

| Provider | Basis-URL | Auth |
|----------|-----------|------|
| OpenAI | https://api.openai.com/v1 | Bearer Token |
| Anthropic | https://api.anthropic.com/v1 | x-api-key Header |
| Google AI | https://generativelanguage.googleapis.com | API Key |

---

## Wichtige Befehle

### Backend

```bash
# Entwicklungsserver starten
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests ausführen
pytest                           # Alle Tests
pytest tests/test_rulesets.py    # Spezifische Tests
pytest --cov=app                 # Mit Coverage

# Linting & Formatting
ruff check .                     # Linting
ruff format .                    # Formatting (ersetzt black)
mypy app                         # Type-Checking

# Celery Worker
celery -A app.worker.celery_app worker --loglevel=info

# Alembic Migrations
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
alembic downgrade -1
```

### Frontend

```bash
cd frontend

# Entwicklungsserver
npm run dev

# Build
npm run build

# Type-Check (ohne Emit)
npx tsc --noEmit

# Linting
npm run lint

# Tests
npm test                         # Vitest
```

### Docker

```bash
cd docker

# Alle Services starten (lokal mit Build)
docker compose up -d

# Logs anzeigen
docker compose logs -f backend
docker compose logs -f worker

# Einzelnen Service neu starten
docker restart flowaudit-backend

# Ollama-Modell laden
docker exec flowaudit-ollama ollama pull llama3.2

# Datenbank-Shell
docker exec -it flowaudit-db psql -U flowaudit -d flowaudit
```

### Health-Checks

```bash
# Backend Health
curl http://localhost:8000/api/health

# Detaillierter Status
curl http://localhost:8000/api/health/detailed

# Ollama Status
curl http://localhost:11434/api/tags

# ChromaDB Status
curl http://localhost:8001/api/v1/heartbeat
```

---

## Projektstruktur

```
flowinvoice/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI Router (REST-Endpunkte)
│   │   ├── models/           # SQLAlchemy Models
│   │   ├── schemas/          # Pydantic Request/Response Schemas
│   │   ├── services/         # Business Logic
│   │   ├── llm/              # LLM-Provider-Adapter
│   │   ├── rag/              # RAG mit ChromaDB
│   │   ├── core/             # Security, Config
│   │   ├── worker/           # Celery Tasks
│   │   └── seeds/            # Initiale Daten (Rulesets)
│   ├── tests/
│   ├── alembic/              # DB-Migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/            # Route-Komponenten
│   │   ├── components/       # Wiederverwendbare UI
│   │   ├── lib/              # API-Client, Utils, Types
│   │   └── i18n/             # Übersetzungen (DE/EN)
│   └── package.json
├── docker/
│   ├── docker-compose.yml              # Lokale Entwicklung
│   ├── docker-compose.portainer.yml    # Produktion (CPU)
│   └── docker-compose.portainer.gpu.yml # Produktion (GPU)
└── docs/
    ├── rulesets.md           # Steuerliche Regelwerke (Ground Truth)
    ├── api_contracts.md      # API-Spezifikation
    ├── architecture.md       # Systemarchitektur
    └── requirements.md       # Funktionale Anforderungen
```

---

## Bekannte Einschränkungen

1. **Ollama Startup**: Erster Start lädt Modelle (mehrere GB), kann Minuten dauern
2. **GPU optional**: Ohne GPU funktioniert LLM, aber langsamer
3. **TypeScript strict**: Frontend-Build schlägt bei `any` ohne Annotation fehl
4. **Async-only**: Backend verwendet durchgehend async/await (kein sync SQLAlchemy)
5. **Ruleset-Immutabilität**: Rulesets sind versioniert - Änderungen erzeugen neue Versionen
