# FlowAudit – Systemarchitektur
## Technische Architektur, Komponentenübersicht und Datenflüsse
## Version: 1.0.0

---

## 0. Zweck dieses Dokuments

Dieses Dokument beschreibt die **vollständige technische Architektur** von FlowAudit:

- Komponentenstruktur und Abhängigkeiten
- Datenflüsse zwischen Komponenten
- Schnittstellen und Protokolle
- Deployment-Topologie
- Skalierungsoptionen

Es dient als **Referenz für die Implementierung** und ergänzt die funktionalen Anforderungen aus `requirements.md`.

---

## 1. Systemübersicht

### 1.1 Architekturprinzipien

| Prinzip | Beschreibung |
|---------|--------------|
| **Monorepo** | Alle Komponenten in einem Repository für einfache Versionierung |
| **Container-First** | Jede Komponente läuft in eigenem Docker-Container |
| **API-First** | Backend-Kommunikation ausschließlich über REST-API |
| **Stateless Backend** | Keine Session-State im Backend, alles in DB/Cache |
| **Transparency by Design** | Alle KI-Ein-/Ausgaben werden persistiert und sind einsehbar |

### 1.2 Komponentendiagramm (Textdarstellung)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER HOST (NUC)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │                │
│  │   (React)    │     │  (FastAPI)   │     │     (DB)     │                │
│  │   Port 3000  │     │   Port 8000  │     │  Port 5432   │                │
│  └──────────────┘     └──────┬───────┘     └──────────────┘                │
│                              │                                              │
│                    ┌─────────┼─────────┐                                   │
│                    │         │         │                                   │
│                    ▼         ▼         ▼                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │    Ollama    │  │   ChromaDB   │  │    Redis     │                     │
│  │  (Local LLM) │  │ (Vector DB)  │  │   (Queue)    │                     │
│  │  Port 11434  │  │  Port 8001   │  │  Port 6379   │                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
│  ┌──────────────┐  ┌──────────────────────────────────┐                    │
│  │    Worker    │  │         Shared Volumes           │                    │
│  │   (Celery)   │  │  /data/uploads, /data/exports    │                    │
│  │              │  │  /data/logs, /data/training      │                    │
│  └──────────────┘  └──────────────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Optional: External APIs
                              ▼
              ┌──────────────────────────────┐
              │   OpenAI API / Gemini API    │
              └──────────────────────────────┘
```

---

## 2. Komponenten im Detail

### 2.1 Frontend (React/TypeScript)

| Aspekt | Spezifikation |
|--------|---------------|
| **Framework** | React 18+ mit TypeScript |
| **State Management** | Zustand oder React Query |
| **UI Framework** | Tailwind CSS + shadcn/ui |
| **Routing** | React Router v6 |
| **i18n** | react-i18next (DE/EN) |
| **Build** | Vite |
| **Container** | nginx (Production) |

**Hauptverantwortlichkeiten:**
- Upload-Interface (Drag & Drop)
- Ergebnisdarstellung (Cards, DataGrid)
- PDF-Viewer mit Overlay
- JSON-Viewer (Input/Response)
- Feedback-Formulare
- Statistik-Dashboard
- Generator-UI (Admin)
- Settings-Verwaltung

### 2.2 Backend (FastAPI/Python)

| Aspekt | Spezifikation |
|--------|---------------|
| **Framework** | FastAPI 0.100+ |
| **Python** | 3.11+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Validation** | Pydantic v2 |
| **PDF Parsing** | pdfplumber + pypdf |
| **Task Queue** | Celery mit Redis |
| **Logging** | structlog |

**Module:**
```
backend/app/
├── api/              # Route-Handler
│   ├── routes_documents.py
│   ├── routes_projects.py
│   ├── routes_analysis.py
│   ├── routes_feedback.py
│   ├── routes_generator.py
│   ├── routes_settings.py
│   └── routes_stats.py
├── services/         # Business Logic
│   ├── pdf_parser.py
│   ├── rule_engine.py
│   ├── payload_builder.py
│   ├── conflict_resolver.py
│   └── stats_aggregator.py
├── llm/              # LLM-Adapter
│   ├── base.py
│   ├── ollama_provider.py
│   ├── openai_provider.py
│   └── gemini_provider.py
├── rag/              # RAG-Komponenten
│   ├── embedder.py
│   ├── retriever.py
│   └── injector.py
├── models/           # SQLAlchemy Models
├── schemas/          # Pydantic Schemas
├── worker/           # Celery Tasks
└── tests/            # Unit & Integration Tests
```

### 2.3 PostgreSQL (Datenbank)

| Aspekt | Spezifikation |
|--------|---------------|
| **Version** | PostgreSQL 16 |
| **Extensions** | pgcrypto (für UUIDs) |
| **Migrations** | Alembic |
| **Backup** | pg_dump (zeitgesteuert) |

**Haupttabellen:**
- `projects` - Vorhabendefinitionen
- `documents` - Hochgeladene PDFs
- `parse_results` - Parser-Ausgaben
- `precheck_results` - Regel-Engine-Ergebnisse
- `prepare_payloads` - KI-Input (persistiert!)
- `llm_runs` - KI-Responses
- `final_results` - Zusammengeführte Ergebnisse
- `feedback` - Menschliche Korrekturen
- `rag_examples` - Gelernte Beispiele
- `rulesets` - Regelwerk-Versionen
- `settings` - Systemkonfiguration
- `audit_log` - Audit-Trail

### 2.4 Ollama (Lokales LLM)

| Aspekt | Spezifikation |
|--------|---------------|
| **Image** | ollama/ollama:latest |
| **API** | HTTP REST (Port 11434) |
| **Modelle** | llama3.1:8b-instruct-q4 (Standard) |
| **GPU** | Optional (NVIDIA mit nvidia-container-toolkit) |
| **Speicher** | /root/.ollama (Volume) |

**Konfiguration:**
```yaml
environment:
  OLLAMA_HOST: 0.0.0.0
  OLLAMA_ORIGINS: "*"
  OLLAMA_NUM_PARALLEL: 2
  OLLAMA_MAX_LOADED_MODELS: 1
```

### 2.5 ChromaDB (Vector Store)

| Aspekt | Spezifikation |
|--------|---------------|
| **Version** | ChromaDB 0.4+ |
| **Embedding** | sentence-transformers/all-MiniLM-L6-v2 |
| **Persistenz** | /data/chroma (Volume) |
| **Collections** | `rag_examples_{ruleset_id}` |

### 2.6 Redis (Task Queue & Cache)

| Aspekt | Spezifikation |
|--------|---------------|
| **Version** | Redis 7 |
| **Verwendung** | Celery Broker + Result Backend |
| **Optional** | Response-Caching |

### 2.7 Worker (Celery)

| Aspekt | Spezifikation |
|--------|---------------|
| **Concurrency** | 2-4 (abhängig von RAM) |
| **Tasks** | parse, precheck, prepare, llm_run, finalize |
| **Retry** | 3x mit exponential backoff |
| **Timeout** | 300s pro Task |

---

## 3. Datenflüsse

### 3.1 Hauptworkflow: Dokumentanalyse

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Upload  │───▶│  Parse  │───▶│Precheck │───▶│ Prepare │───▶│LLM Run  │
│         │    │         │    │ (Rules) │    │(Payload)│    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                  │
┌─────────┐    ┌─────────┐    ┌─────────┐                        │
│ Export  │◀───│Feedback │◀───│Finalize │◀───────────────────────┘
│         │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘
```

### 3.2 Detaillierter Datenfluss

#### Schritt 1: Upload
```
Frontend                    Backend                     Storage
   │                           │                           │
   │──POST /documents/upload──▶│                           │
   │   (multipart/form-data)   │                           │
   │                           │──save PDF────────────────▶│
   │                           │──calculate SHA256─────────│
   │                           │──INSERT documents─────────│
   │◀──201 {document_id}───────│                           │
```

#### Schritt 2: Parse
```
Backend                     Worker                      Storage
   │                           │                           │
   │──task: parse_document────▶│                           │
   │                           │◀──read PDF────────────────│
   │                           │──pdfplumber extract───────│
   │                           │──regex extraction─────────│
   │                           │──INSERT parse_results─────│
   │◀──task complete───────────│                           │
```

#### Schritt 3: Precheck (Regel-Engine)
```
Backend                     Worker                         DB
   │                           │                           │
   │──task: precheck───────────▶│                           │
   │                           │◀──load parse_results──────│
   │                           │◀──load project_context────│
   │                           │──apply rule checks────────│
   │                           │  (dates, amounts, math)   │
   │                           │──INSERT precheck_results──│
   │◀──task complete───────────│                           │
```

#### Schritt 4: Prepare Payload
```
Backend                     Worker                         DB
   │                           │                           │
   │──task: prepare────────────▶│                           │
   │                           │◀──load ruleset────────────│
   │                           │◀──load parse_results──────│
   │                           │◀──load precheck_results───│
   │                           │◀──RAG: retrieve examples──│
   │                           │──build input JSON─────────│
   │                           │──INSERT prepare_payloads──│  ◀── PERSISTIERT!
   │◀──task complete───────────│                           │
```

#### Schritt 5: LLM Run
```
Backend           Worker              LLM Provider           DB
   │                 │                      │                 │
   │──task: llm_run─▶│                      │                 │
   │                 │◀──load payload───────┼─────────────────│
   │                 │──send prompt────────▶│                 │
   │                 │◀──response───────────│                 │
   │                 │──validate JSON───────│                 │
   │                 │──INSERT llm_runs─────┼─────────────────│
   │◀──task complete─│                      │                 │
```

#### Schritt 6: Finalize
```
Backend                     Worker                         DB
   │                           │                           │
   │──task: finalize───────────▶│                           │
   │                           │◀──load all results────────│
   │                           │──resolve conflicts────────│
   │                           │  (rule vs llm vs user)    │
   │                           │──calculate amounts────────│
   │                           │──INSERT final_results─────│
   │◀──task complete───────────│                           │
```

### 3.3 RAG-Lernzyklus

```
┌──────────────────────────────────────────────────────────────────┐
│                         RAG Learning Loop                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Feedback            Embedding           Storage      Retrieval │
│      │                    │                  │             │     │
│      ▼                    ▼                  ▼             ▼     │
│  ┌────────┐         ┌──────────┐      ┌──────────┐   ┌─────────┐│
│  │ Accept │────────▶│ Embed    │─────▶│ ChromaDB │──▶│ Similar ││
│  │Correct │  text   │ Correction│ vec  │ Store    │   │Examples ││
│  └────────┘         └──────────┘      └──────────┘   └────┬────┘│
│                                                            │     │
│                          ┌─────────────────────────────────┘     │
│                          ▼                                       │
│                    ┌───────────┐      ┌──────────┐              │
│                    │ Inject to │─────▶│ Better   │              │
│                    │ Payload   │      │ Results  │              │
│                    └───────────┘      └──────────┘              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Schnittstellen

### 4.1 Interne Schnittstellen

| Von | Nach | Protokoll | Zweck |
|-----|------|-----------|-------|
| Frontend | Backend | HTTP REST | Alle API-Aufrufe |
| Backend | PostgreSQL | TCP (psycopg) | Datenpersistenz |
| Backend | Redis | TCP | Task Queue |
| Backend | ChromaDB | HTTP | Vector-Operationen |
| Worker | Ollama | HTTP | LLM-Inferenz |
| Worker | OpenAI/Gemini | HTTPS | Externe LLM-APIs |

### 4.2 Externe Schnittstellen

| Schnittstelle | Richtung | Authentifizierung |
|---------------|----------|-------------------|
| OpenAI API | Outbound | API Key (Bearer) |
| Gemini API | Outbound | API Key |
| Cloudflare Tunnel | Inbound (optional) | Access Tokens |

### 4.3 Dateisystem-Schnittstellen

```
/data/
├── uploads/              # Hochgeladene PDFs (Backend schreibt, Worker liest)
│   └── {project_id}/
│       └── {document_id}.pdf
├── exports/              # Generierte Exporte (Worker schreibt, Frontend liest)
│   └── {export_id}/
├── generated/            # Generator-Output (Worker schreibt)
│   └── {batch_id}/
│       ├── pdf/
│       └── solutions.txt  # Niemals in DB!
├── chroma/               # ChromaDB Persistenz
├── logs/                 # Strukturierte Logs
│   └── {date}/
└── backups/              # DB-Backups
```

---

## 5. Deployment

### 5.1 Docker Compose (Entwicklung/Demo)

```yaml
version: "3.9"

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000/api

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
      - chroma
    environment:
      - DATABASE_URL=postgresql+asyncpg://flowaudit:flowaudit@db:5432/flowaudit
      - REDIS_URL=redis://redis:6379/0
      - CHROMA_URL=http://chroma:8000
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data:/data

  worker:
    build: ./backend
    command: celery -A app.worker worker -l info -c 2
    depends_on:
      - backend
      - redis
      - ollama
    environment:
      - DATABASE_URL=postgresql+asyncpg://flowaudit:flowaudit@db:5432/flowaudit
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data:/data

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=flowaudit
      - POSTGRES_PASSWORD=flowaudit
      - POSTGRES_DB=flowaudit
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  chroma:
    image: chromadb/chroma:latest
    volumes:
      - ./data/chroma:/chroma/chroma
    ports:
      - "8001:8000"

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollamadata:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  pgdata:
  redisdata:
  ollamadata:
```

### 5.2 Produktions-Deployment (NUC)

**Zusätzliche Maßnahmen:**
- Traefik als Reverse Proxy mit HTTPS
- Cloudflare Tunnel für externen Zugang
- Watchtower für Auto-Updates
- Prometheus + Grafana für Monitoring (optional)

### 5.3 Ressourcen-Anforderungen

| Komponente | RAM (min) | RAM (empf.) | CPU | Disk |
|------------|-----------|-------------|-----|------|
| Backend | 512 MB | 1 GB | 1 | - |
| Worker | 1 GB | 2 GB | 2 | - |
| PostgreSQL | 256 MB | 512 MB | 1 | 10 GB |
| Redis | 128 MB | 256 MB | 0.5 | 1 GB |
| ChromaDB | 512 MB | 1 GB | 1 | 5 GB |
| Ollama (CPU) | 8 GB | 16 GB | 4 | 20 GB |
| Ollama (GPU) | 4 GB | 8 GB | 2 | 20 GB |
| **Gesamt** | **~11 GB** | **~21 GB** | 11.5 | 56 GB |

---

## 6. Sicherheitsarchitektur

### 6.1 Netzwerk-Isolation

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐                                        │
│  │    Frontend     │◀───── Port 3000 (exposed)              │
│  └────────┬────────┘                                        │
│           │ internal                                         │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │     Backend     │◀───── Port 8000 (exposed for dev)      │
│  └────────┬────────┘                                        │
│           │ internal only                                    │
│           ▼                                                  │
│  ┌─────┐ ┌─────┐ ┌──────┐ ┌────────┐                       │
│  │ DB  │ │Redis│ │Chroma│ │ Ollama │ ◀── no external ports │
│  └─────┘ └─────┘ └──────┘ └────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Secrets Management

| Secret | Speicherort | Zugriff |
|--------|-------------|---------|
| DB Password | Environment Variable | Backend, Worker |
| API Keys (OpenAI, Gemini) | DB (verschlüsselt) | Backend |
| JWT Secret (zukünftig) | Environment Variable | Backend |

### 6.3 Datenschutz

- PDFs werden nur lokal gespeichert
- Externe API-Aufrufe werden im UI gekennzeichnet ("Data leaves device")
- Keine personenbezogenen Daten in Logs
- Generator-Lösungen niemals in DB

---

## 7. Erweiterbarkeit

### 7.1 Neue LLM-Provider

```python
# Implementierung eines neuen Providers
class NewProvider(BaseLLMProvider):
    async def analyze(self, payload: PreparePayload) -> LLMResponse:
        # 1. Payload zu Provider-Format konvertieren
        # 2. API-Aufruf
        # 3. Response parsen und validieren
        # 4. Einheitliches LLMResponse-Objekt zurückgeben
        pass
```

### 7.2 Neue Rulesets

1. Neues Ruleset in `/data/rulesets/{ruleset_id}.json` anlegen
2. Datenbank-Migration für neue Features
3. Generator-Templates anpassen
4. UI-Übersetzungen ergänzen

### 7.3 Neue Prüfregeln

```python
# Neue Regel in rule_engine.py
@register_rule("CUSTOM_CHECK")
def check_custom(doc: ParsedDocument, project: Project) -> RuleCheckResult:
    # Prüflogik
    return RuleCheckResult(
        check_id="CUSTOM_CHECK",
        status=RuleCheckStatus.OK,
        observed={...},
        comment="..."
    )
```

---

## 8. Monitoring & Observability

### 8.1 Health Checks

| Endpoint | Prüft | Intervall |
|----------|-------|-----------|
| `/api/health` | DB, Redis, Ollama, Chroma | 30s |
| `/api/health/db` | Nur Datenbank | 10s |
| `/api/health/llm` | Nur LLM-Provider | 60s |

### 8.2 Metriken (optional Prometheus)

- `flowaudit_documents_total` - Anzahl verarbeiteter Dokumente
- `flowaudit_llm_latency_seconds` - LLM-Antwortzeiten
- `flowaudit_parse_duration_seconds` - Parser-Laufzeiten
- `flowaudit_errors_total` - Fehler nach Typ

### 8.3 Logging

```json
{
  "timestamp": "2025-12-15T12:00:00Z",
  "level": "INFO",
  "service": "worker",
  "task_id": "abc123",
  "document_id": "doc_456",
  "event": "llm_response_received",
  "duration_ms": 12800,
  "tokens_in": 2100,
  "tokens_out": 650
}
```

---

## 9. Disaster Recovery

### 9.1 Backup-Strategie

| Komponente | Methode | Frequenz | Retention |
|------------|---------|----------|-----------|
| PostgreSQL | pg_dump | Täglich | 30 Tage |
| ChromaDB | Verzeichnis-Backup | Täglich | 14 Tage |
| Uploads | rsync zu NAS | Stündlich | Unbegrenzt |
| Konfiguration | Git | Bei Änderung | Unbegrenzt |

### 9.2 Recovery-Prozedur

1. Docker-Stack stoppen
2. Volumes aus Backup wiederherstellen
3. Datenbank-Dump einspielen
4. Docker-Stack starten
5. Health-Checks verifizieren

---

## 10. Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **PreparePayload** | Vollständiges Input-JSON für KI (persistiert) |
| **Precheck** | Regelbasierte Vorprüfung ohne KI |
| **Finalize** | Zusammenführung aller Ergebnisse |
| **RAG** | Retrieval-Augmented Generation |
| **Ruleset** | Steuerliches Regelwerk (DE/EU/UK) |
