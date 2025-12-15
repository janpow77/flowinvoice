# FlowAudit – Betrieb, Performance & Sicherheit
## Operations Guide für Produktion und Seminarbetrieb
## Version: 1.0.0

---

## 0. Zweck dieses Dokuments

Dieses Dokument spezifiziert:

- Performance-Anforderungen und Grenzen
- Authentifizierung und Autorisierung
- CI/CD-Pipeline
- Monitoring und Alerting
- Backup und Disaster Recovery

Es ergänzt die funktionalen Anforderungen aus `requirements.md` um operative Aspekte.

---

## 1. Performance-Anforderungen

### 1.1 Response-Zeit-Ziele

| Operation | Ziel (p50) | Ziel (p95) | Maximum |
|-----------|------------|------------|---------|
| **PDF Upload** | < 500ms | < 2s | 10s (für große PDFs) |
| **PDF Parse** | < 2s | < 5s | 30s |
| **Precheck (Regelprüfung)** | < 500ms | < 1s | 5s |
| **Prepare Payload** | < 1s | < 2s | 10s |
| **LLM Inference (lokal)** | < 15s | < 30s | 120s |
| **LLM Inference (extern)** | < 5s | < 15s | 60s |
| **Finalize** | < 500ms | < 1s | 5s |
| **UI Page Load** | < 1s | < 2s | 5s |
| **API List Endpoints** | < 200ms | < 500ms | 2s |

### 1.2 Durchsatz-Ziele

| Metrik | Seminar-Betrieb | Demo-Betrieb |
|--------|-----------------|--------------|
| **Gleichzeitige Benutzer** | 20 | 5 |
| **Dokumente pro Stunde** | 100 | 20 |
| **Parallele LLM-Aufrufe** | 2 | 1 |
| **Uploads pro Minute** | 10 | 5 |

### 1.3 Ressourcen-Limits

#### 1.3.1 NUC-Konfiguration (64 GB RAM)

```yaml
# Docker Resource Limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M

  worker:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '4'
        reservations:
          memory: 1G

  ollama:
    deploy:
      resources:
        limits:
          memory: 32G  # Für 8B-Modell
          cpus: '8'
        reservations:
          memory: 16G

  db:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M

  chroma:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M

  redis:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1'
        reservations:
          memory: 128M

  frontend:
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
```

#### 1.3.2 Speicher-Limits

| Ressource | Soft Limit | Hard Limit | Aktion bei Überschreitung |
|-----------|------------|------------|---------------------------|
| **Upload-Ordner** | 10 GB | 20 GB | Warnung / Upload blockieren |
| **Export-Ordner** | 5 GB | 10 GB | Alte Exporte löschen |
| **Log-Ordner** | 1 GB | 5 GB | Log-Rotation |
| **ChromaDB** | 5 GB | 10 GB | Warnung an Admin |
| **PostgreSQL** | 10 GB | 20 GB | Warnung an Admin |

### 1.4 PDF-Größen-Limits

| Limit | Wert | Begründung |
|-------|------|------------|
| **Max. Dateigröße** | 50 MB | Speicher + Verarbeitungszeit |
| **Max. Seitenanzahl** | 100 | Parser-Performance |
| **Max. Text-Länge** | 500.000 Zeichen | LLM-Context-Limit |
| **Empfohlene Größe** | < 5 MB | Optimale Performance |

### 1.5 Batch-Verarbeitung

```python
BATCH_CONFIG = {
    "max_concurrent_uploads": 10,
    "max_concurrent_parses": 4,
    "max_concurrent_llm_calls": 2,  # Lokal
    "max_concurrent_llm_calls_external": 5,  # Extern (API-abhängig)
    "batch_chunk_size": 10,  # Dokumente pro Batch-Chunk
    "progress_update_interval_seconds": 2
}
```

### 1.6 Caching-Strategie

| Cache | TTL | Invalidierung |
|-------|-----|---------------|
| **Ruleset-Daten** | 1 Stunde | Bei Ruleset-Update |
| **Project-Daten** | 5 Minuten | Bei Project-Update |
| **Settings** | 10 Minuten | Bei Settings-Update |
| **Static Assets** | 1 Tag | Bei Deployment |
| **RAG Embeddings** | Persistent | Nie (immutable) |

---

## 2. Authentifizierung & Autorisierung

### 2.1 Stufen der Implementierung

| Stufe | Kontext | Implementierung |
|-------|---------|-----------------|
| **Demo** | Lokaler Entwickler-Test | Keine Auth (X-Role Header) |
| **Seminar** | Geschlossene Gruppe | Basic Auth oder Simple Token |
| **Produktion** | Offener Zugang | OAuth 2.0 / OIDC |

### 2.2 Demo-Modus (Standard)

```python
# Header-basierte Rollenzuweisung
# X-Role: user | admin

class DemoAuthMiddleware:
    async def __call__(self, request: Request, call_next):
        role = request.headers.get("X-Role", "user")
        request.state.user = DemoUser(role=role)
        return await call_next(request)
```

### 2.3 Seminar-Modus (Basic Auth)

```yaml
# docker-compose.override.yml für Seminar
services:
  traefik:
    labels:
      - "traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$..."
      - "traefik.http.routers.flowaudit.middlewares=auth"
```

**Benutzer-Management:**
```bash
# Benutzer hinzufügen
htpasswd -c /data/auth/.htpasswd admin
htpasswd /data/auth/.htpasswd user1
htpasswd /data/auth/.htpasswd user2
```

### 2.4 Produktions-Modus (OAuth 2.0 / OIDC)

#### 2.4.1 Unterstützte Provider

| Provider | Konfiguration |
|----------|---------------|
| **Keycloak** | Self-hosted, empfohlen für Enterprise |
| **Auth0** | SaaS, schnelle Integration |
| **Azure AD** | Microsoft-Umgebungen |
| **Google** | Einfache Google-Auth |

#### 2.4.2 Token-Schema

```python
class TokenPayload(BaseModel):
    sub: str               # User ID
    email: str
    name: str
    roles: list[str]       # ["user", "admin", "trainer"]
    exp: int               # Expiration timestamp
    iat: int               # Issued at
    iss: str               # Issuer URL

# Beispiel JWT
{
  "sub": "user_123",
  "email": "max@example.com",
  "name": "Max Mustermann",
  "roles": ["user", "trainer"],
  "exp": 1734350400,
  "iat": 1734264000,
  "iss": "https://auth.flowaudit.local"
}
```

#### 2.4.3 Rollen und Berechtigungen

| Rolle | Berechtigungen |
|-------|----------------|
| `user` | Upload, Analyse, Feedback, eigene Projekte |
| `trainer` | + Generator, Ruleset-Ansicht, Training-Daten |
| `admin` | + Settings, alle Projekte, Ruleset-Edit, System-Stats |

#### 2.4.4 Endpoint-Schutz

```python
# Beispiel-Decorator
@router.post("/api/generator/run")
@require_roles(["trainer", "admin"])
async def run_generator(config: GeneratorConfig, user: User = Depends(get_current_user)):
    ...

@router.put("/api/settings")
@require_roles(["admin"])
async def update_settings(settings: SettingsUpdate, user: User = Depends(get_current_user)):
    ...

@router.post("/api/documents/{id}/feedback")
@require_roles(["user", "trainer", "admin"])
async def submit_feedback(id: str, feedback: FeedbackCreate, user: User = Depends(get_current_user)):
    ...
```

### 2.5 API-Key-Management (für externe LLMs)

```python
class SecretStore:
    """Sichere Speicherung von API-Keys."""

    def store_api_key(self, provider: str, key: str) -> None:
        """Speichert verschlüsselten API-Key in DB."""
        encrypted = self.encrypt(key)
        # Speichern in settings-Tabelle mit provider als Key

    def get_api_key(self, provider: str) -> str | None:
        """Lädt und entschlüsselt API-Key."""
        encrypted = self.load_from_db(provider)
        return self.decrypt(encrypted) if encrypted else None

    def mask_api_key(self, key: str) -> str:
        """Maskiert Key für UI-Anzeige."""
        if len(key) < 8:
            return "****"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
```

---

## 3. CI/CD-Pipeline

### 3.1 Pipeline-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐│
│  │  Lint   │─▶│  Test   │─▶│  Build  │─▶│  Push   │─▶│ Deploy ││
│  │         │  │         │  │         │  │         │  │        ││
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────┘│
│                                                                  │
│  Trigger: Push to main, PR, Tag                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ─────────────────────────────────────────────────────────────
  # LINT
  # ─────────────────────────────────────────────────────────────
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install linters
        run: |
          pip install ruff mypy

      - name: Lint Backend
        run: |
          cd backend
          ruff check .
          mypy app --ignore-missing-imports

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Lint Frontend
        run: |
          cd frontend
          npm ci
          npm run lint
          npm run type-check

  # ─────────────────────────────────────────────────────────────
  # TEST
  # ─────────────────────────────────────────────────────────────
  test-backend:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: flowaudit_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[test]"

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/flowaudit_test
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/lcov.info

  # ─────────────────────────────────────────────────────────────
  # BUILD
  # ─────────────────────────────────────────────────────────────
  build:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push Frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ─────────────────────────────────────────────────────────────
  # DEPLOY (nur bei Release)
  # ─────────────────────────────────────────────────────────────
  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'release'
    environment: production

    steps:
      - name: Deploy to NUC
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.NUC_HOST }}
          username: ${{ secrets.NUC_USER }}
          key: ${{ secrets.NUC_SSH_KEY }}
          script: |
            cd /opt/flowaudit
            docker compose pull
            docker compose up -d --remove-orphans
            docker system prune -f
```

### 3.3 Test-Strategie

#### 3.3.1 Backend-Tests

| Test-Typ | Abdeckungsziel | Framework |
|----------|----------------|-----------|
| **Unit Tests** | > 80% | pytest |
| **Integration Tests** | Kritische Pfade | pytest + testcontainers |
| **API Tests** | Alle Endpoints | pytest + httpx |
| **E2E Tests** | Happy Paths | (optional) Playwright |

```python
# Beispiel: Test-Struktur
backend/tests/
├── unit/
│   ├── test_pdf_parser.py
│   ├── test_rule_engine.py
│   ├── test_validators.py
│   └── test_payload_builder.py
├── integration/
│   ├── test_llm_providers.py
│   ├── test_rag_retrieval.py
│   └── test_workflow.py
├── api/
│   ├── test_documents.py
│   ├── test_projects.py
│   ├── test_feedback.py
│   └── test_generator.py
└── conftest.py
```

#### 3.3.2 Frontend-Tests

| Test-Typ | Abdeckungsziel | Framework |
|----------|----------------|-----------|
| **Unit Tests** | > 70% | Vitest |
| **Component Tests** | Alle UI-Komponenten | React Testing Library |
| **E2E Tests** | Kritische Flows | Playwright |

### 3.4 Deployment-Prozess

#### 3.4.1 Manuelle Deployment-Schritte (NUC)

```bash
# 1. SSH auf NUC
ssh user@nuc.local

# 2. Ins Projektverzeichnis wechseln
cd /opt/flowaudit

# 3. Neueste Version holen
git pull origin main

# 4. Container aktualisieren
docker compose pull
docker compose up -d --build

# 5. Migrationen ausführen
docker compose exec backend alembic upgrade head

# 6. Health-Check
curl http://localhost:8000/api/health

# 7. Alte Images aufräumen
docker system prune -f
```

#### 3.4.2 Rollback-Prozedur

```bash
# 1. Auf vorherige Version zurück
git checkout <previous-tag>

# 2. Container mit alten Images starten
docker compose up -d --build

# 3. Datenbank-Rollback (falls nötig)
docker compose exec backend alembic downgrade -1

# 4. Verifizieren
curl http://localhost:8000/api/health
```

---

## 4. Monitoring & Alerting

### 4.1 Metriken-Endpunkte

```python
# /api/metrics (Prometheus-Format)
# flowaudit_http_requests_total{method="POST", endpoint="/api/documents/upload", status="201"} 142
# flowaudit_http_request_duration_seconds{endpoint="/api/documents/{id}/run"} 12.5
# flowaudit_documents_processed_total{status="success"} 1234
# flowaudit_llm_calls_total{provider="ollama", model="llama3.1"} 987
# flowaudit_llm_duration_seconds{provider="ollama"} 15.2
# flowaudit_active_tasks 3
# flowaudit_queue_size 5
```

### 4.2 Health-Checks

```python
# GET /api/health
{
  "status": "healthy",  # healthy | degraded | unhealthy
  "timestamp": "2025-12-15T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "db": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "ollama": {"status": "healthy", "latency_ms": 50, "model_loaded": "llama3.1:8b"},
    "chroma": {"status": "healthy", "latency_ms": 10, "collections": 3}
  },
  "resources": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_percent": 34.5
  }
}
```

### 4.3 Alerting-Regeln

| Alert | Bedingung | Schwere | Aktion |
|-------|-----------|---------|--------|
| `ServiceDown` | Health != healthy für 2 Min | Critical | Sofort benachrichtigen |
| `HighLatency` | p95 > 30s für 5 Min | Warning | Überprüfen |
| `HighErrorRate` | Error-Rate > 5% für 5 Min | Warning | Überprüfen |
| `DiskSpaceLow` | Disk > 80% | Warning | Aufräumen |
| `DiskSpaceCritical` | Disk > 95% | Critical | Sofort handeln |
| `MemoryHigh` | Memory > 90% für 5 Min | Warning | Überprüfen |
| `OllamaUnresponsive` | Ollama-Check fails 3x | Critical | Neustart |

### 4.4 Log-Aggregation

```yaml
# docker-compose.override.yml für Logging
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Optional: Loki für zentrale Logs
  loki:
    image: grafana/loki:latest
    volumes:
      - loki-data:/loki

  # Optional: Grafana für Dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

---

## 5. Backup & Disaster Recovery

### 5.1 Backup-Strategie

| Komponente | Methode | Frequenz | Retention | Speicherort |
|------------|---------|----------|-----------|-------------|
| **PostgreSQL** | pg_dump | Täglich 2:00 | 30 Tage | /data/backups/db/ + NAS |
| **Uploads (PDFs)** | rsync | Stündlich | Unbegrenzt | NAS |
| **ChromaDB** | Verzeichnis-Copy | Täglich 3:00 | 14 Tage | /data/backups/chroma/ |
| **Konfiguration** | Git | Bei Änderung | Unbegrenzt | Remote Repo |
| **Exports** | (keine Backups) | - | 7 Tage lokal | - |

### 5.2 Backup-Skripte

```bash
#!/bin/bash
# /opt/flowaudit/scripts/backup.sh

set -e

BACKUP_DIR="/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
NAS_PATH="user@nas.local:/backups/flowaudit"

# PostgreSQL Backup
echo "Backing up PostgreSQL..."
docker exec flowaudit-db-1 pg_dump -U flowaudit flowaudit | gzip > "$BACKUP_DIR/db/flowaudit_$DATE.sql.gz"

# Alte DB-Backups löschen (> 30 Tage)
find "$BACKUP_DIR/db" -name "*.sql.gz" -mtime +30 -delete

# ChromaDB Backup
echo "Backing up ChromaDB..."
tar -czf "$BACKUP_DIR/chroma/chroma_$DATE.tar.gz" -C /data/chroma .

# Alte Chroma-Backups löschen (> 14 Tage)
find "$BACKUP_DIR/chroma" -name "*.tar.gz" -mtime +14 -delete

# Sync zu NAS
echo "Syncing to NAS..."
rsync -avz --delete "$BACKUP_DIR/" "$NAS_PATH/backups/"
rsync -avz --delete "/data/uploads/" "$NAS_PATH/uploads/"

echo "Backup completed: $DATE"
```

### 5.3 Recovery-Prozeduren

#### 5.3.1 Datenbank-Recovery

```bash
# 1. Service stoppen
docker compose stop backend worker

# 2. Altes Volume löschen (Vorsicht!)
docker volume rm flowaudit_pgdata

# 3. Neues Volume erstellen und DB starten
docker compose up -d db
sleep 10

# 4. Backup einspielen
gunzip -c /data/backups/db/flowaudit_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i flowaudit-db-1 psql -U flowaudit flowaudit

# 5. Services starten
docker compose up -d
```

#### 5.3.2 Vollständige System-Recovery

```bash
# 1. Docker und Docker Compose installieren
curl -fsSL https://get.docker.com | sh

# 2. Repository klonen
git clone https://github.com/org/flowaudit.git /opt/flowaudit
cd /opt/flowaudit

# 3. Daten vom NAS wiederherstellen
rsync -avz user@nas.local:/backups/flowaudit/uploads/ /data/uploads/
rsync -avz user@nas.local:/backups/flowaudit/backups/ /data/backups/

# 4. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env bearbeiten

# 5. System starten
docker compose up -d

# 6. Datenbank wiederherstellen
# (siehe 5.3.1)

# 7. ChromaDB wiederherstellen
tar -xzf /data/backups/chroma/chroma_LATEST.tar.gz -C /data/chroma

# 8. Ollama-Modell herunterladen
docker exec flowaudit-ollama-1 ollama pull llama3.1:8b-instruct-q4

# 9. Verifizieren
curl http://localhost:8000/api/health
```

### 5.4 RTO und RPO

| Metrik | Ziel | Beschreibung |
|--------|------|--------------|
| **RTO** (Recovery Time Objective) | < 4 Stunden | Zeit bis System wieder läuft |
| **RPO** (Recovery Point Objective) | < 1 Stunde | Max. Datenverlust |

---

## 6. Sicherheits-Checkliste

### 6.1 Vor dem Go-Live

- [ ] Alle Standard-Passwörter geändert
- [ ] API-Keys sicher gespeichert (nicht in Git)
- [ ] HTTPS aktiviert (Traefik/Cloudflare)
- [ ] Firewall konfiguriert (nur nötige Ports)
- [ ] Backup-System getestet
- [ ] Health-Checks funktionieren
- [ ] Monitoring aktiv
- [ ] Recovery-Prozedur dokumentiert und getestet

### 6.2 Regelmäßige Überprüfungen

| Aufgabe | Frequenz |
|---------|----------|
| Backup-Integrität prüfen | Wöchentlich |
| Security-Updates installieren | Wöchentlich |
| Logs auf Anomalien prüfen | Täglich |
| Disk-Space prüfen | Täglich |
| SSL-Zertifikate erneuern | Vor Ablauf |
| API-Keys rotieren | Quartalsweise |
