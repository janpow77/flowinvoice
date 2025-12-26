# FlowAudit Environment Variables

Diese Dokumentation beschreibt alle Umgebungsvariablen für FlowAudit.

## Sicherheitshinweis

> **WICHTIG**: Vor dem Produktionseinsatz MÜSSEN alle mit `🔴 REQUIRED` markierten Variablen auf sichere Werte gesetzt werden!

---

## Kritische Sicherheitsvariablen

| Variable | Default | Produktion | Beschreibung |
|----------|---------|------------|--------------|
| 🔴 `SECRET_KEY` | `flowaudit_dev_secret_key...` | **ÄNDERN!** | JWT-Signierung, mind. 32 Zeichen |
| 🔴 `POSTGRES_PASSWORD` | `flowaudit_secret` | **ÄNDERN!** | Datenbank-Passwort |
| 🔴 `CHROMA_TOKEN` | `flowaudit_chroma_token` | **ÄNDERN!** | ChromaDB Auth-Token |
| 🔴 `DEMO_USERS` | `admin:admin,user:user` | `""` (leer) | Demo-Benutzer deaktivieren! |
| 🟡 `DEBUG` | `false` | `false` | Debug-Modus (niemals `true` in Prod) |
| 🟡 `ADMIN_API_KEY` | `null` | Setzen | API-Key für Admin-Endpoints |

### Sichere Werte generieren

```bash
# SECRET_KEY generieren (Linux/Mac)
openssl rand -hex 32

# Oder mit Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Alle Umgebungsvariablen

### Application

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `APP_NAME` | `FlowAudit` | Anwendungsname |
| `APP_VERSION` | `0.1.0` | Version |
| `DEBUG` | `false` | Debug-Modus aktivieren |
| `LOG_LEVEL` | `INFO` | Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `SECRET_KEY` | Dev-Default | JWT-Secret für Token-Signierung |

### Datenbank (PostgreSQL)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `DATABASE_URL` | `postgresql+asyncpg://flowaudit:flowaudit_secret@db:5432/flowaudit` | Vollständige DB-URL |
| `POSTGRES_USER` | `flowaudit` | DB-Benutzer |
| `POSTGRES_PASSWORD` | `flowaudit_secret` | DB-Passwort |
| `POSTGRES_DB` | `flowaudit` | Datenbankname |
| `DATABASE_POOL_SIZE` | `5` | Connection Pool Größe |
| `DATABASE_MAX_OVERFLOW` | `10` | Max. zusätzliche Connections |

### Redis

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis-Verbindungs-URL |

### ChromaDB (Vector Store)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `CHROMA_HOST` | `chromadb` | ChromaDB Hostname |
| `CHROMA_PORT` | `8000` | ChromaDB Port (intern) |
| `CHROMADB_PORT` | `8001` | ChromaDB Port (extern) |
| `CHROMA_TOKEN` | `flowaudit_chroma_token` | Auth-Token |
| `CHROMA_COLLECTION_NAME` | `flowaudit_corrections` | Collection-Name |

### Ollama (Lokales LLM)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama API URL |
| `OLLAMA_DEFAULT_MODEL` | `llama3.1:8b` | Standard-Modell |
| `OLLAMA_TIMEOUT_SEC` | `120` | Request-Timeout |
| `OLLAMA_GPU_MEMORY_FRACTION` | `0.8` | GPU-Speicher Anteil (0-1) |
| `OLLAMA_NUM_GPU` | `999` | GPU-Layers (-1=alle, 0=CPU) |
| `OLLAMA_NUM_PARALLEL` | `2` | Parallele Requests |
| `OLLAMA_NUM_CTX` | `4096` | Context Window |

### Externe LLM-Provider (Optional)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `OPENAI_API_KEY` | `null` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | `null` | Anthropic API Key |
| `GEMINI_API_KEY` | `null` | Google Gemini API Key |

### LLM-Inference

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `DEFAULT_TEMPERATURE` | `0.2` | Sampling Temperature |
| `DEFAULT_MAX_TOKENS` | `2000` | Max. Output-Tokens |
| `DEFAULT_TIMEOUT_SEC` | `120` | Timeout für LLM-Calls |

### Storage

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `STORAGE_PATH` | `/data` | Basis-Pfad für Dateien |
| `UPLOADS_DIR` | `uploads` | Upload-Verzeichnis |
| `EXPORTS_DIR` | `exports` | Export-Verzeichnis |
| `PREVIEWS_DIR` | `previews` | Preview-Verzeichnis |
| `LOGS_DIR` | `logs` | Log-Verzeichnis |

### RAG (Retrieval Augmented Generation)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `RAG_ENABLED` | `true` | RAG aktivieren |
| `RAG_TOP_K` | `3` | Anzahl ähnlicher Beispiele |
| `RAG_SIMILARITY_THRESHOLD` | `0.25` | Mindest-Ähnlichkeit (0-1) |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Embedding-Modell |

### Parser

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `PARSER_TIMEOUT_SEC` | `30` | PDF-Parser Timeout |
| `PARSER_MAX_PAGES` | `50` | Max. Seiten pro PDF |

### Generator

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `GENERATOR_ENABLED` | `true` | Generator aktivieren |
| `GENERATOR_MAX_COUNT` | `100` | Max. Rechnungen pro Batch |

### Authentifizierung

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `JWT_ALGORITHM` | `HS256` | JWT-Algorithmus |
| `JWT_EXPIRE_HOURS` | `24` | Token-Gültigkeit in Stunden |
| `DEMO_USERS` | `admin:admin,user:user` | Demo-Benutzer (username:password) |
| `ADMIN_API_KEY` | `null` | API-Key für Admin-Endpoints |

### Google OAuth (Optional)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `GOOGLE_CLIENT_ID` | `null` | OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | `null` | OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:3000/auth/google/callback` | Callback-URL |

### CORS

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Erlaubte Origins (kommasepariert) |

### Performance

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `UVICORN_WORKERS` | `4` | API-Worker (1-8) |
| `CELERY_CONCURRENCY` | `4` | Celery-Worker (1-8) |

---

## Produktions-Checkliste

```bash
# 1. Sichere Secrets generieren
export SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export CHROMA_TOKEN=$(openssl rand -hex 16)
export ADMIN_API_KEY=$(openssl rand -hex 16)

# 2. Demo-Benutzer deaktivieren
export DEMO_USERS=""

# 3. Debug deaktivieren
export DEBUG=false

# 4. CORS auf Produktions-Domain setzen
export CORS_ORIGINS="https://your-domain.com"

# 5. Prüfen ob Konfiguration sicher ist
# Backend startet mit Warnungen wenn unsichere Defaults verwendet werden
```

---

## Beispiel: `.env.production`

```bash
# ============================================
# FlowAudit Production Configuration
# ============================================

# Security - CHANGE THESE!
SECRET_KEY=your-secure-secret-key-min-32-chars
POSTGRES_PASSWORD=your-secure-db-password
CHROMA_TOKEN=your-secure-chroma-token
ADMIN_API_KEY=your-secure-admin-key

# Disable demo users
DEMO_USERS=

# Disable debug
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://flowaudit:${POSTGRES_PASSWORD}@db:5432/flowaudit

# CORS - Set to your domain
CORS_ORIGINS=https://flowaudit.example.com

# Optional: External LLM providers
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=...

# Optional: Google OAuth
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
# GOOGLE_REDIRECT_URI=https://flowaudit.example.com/auth/google/callback
```

---

## Health-Check Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `HEALTH_DB_INTERVAL_SEC` | `30` | DB-Check Intervall |
| `HEALTH_DB_TIMEOUT_SEC` | `5` | DB-Check Timeout |
| `HEALTH_OLLAMA_INTERVAL_SEC` | `60` | Ollama-Check Intervall |
| `HEALTH_CHROMA_INTERVAL_SEC` | `60` | ChromaDB-Check Intervall |
| `HEALTH_REDIS_INTERVAL_SEC` | `30` | Redis-Check Intervall |

---

## Retry-Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `RETRY_LLM_MAX_RETRIES` | `3` | Max. LLM-Retries |
| `RETRY_LLM_BASE_DELAY_SEC` | `2` | Basis-Wartezeit |
| `RETRY_LLM_MAX_DELAY_SEC` | `30` | Max. Wartezeit |
| `RETRY_DB_MAX_RETRIES` | `3` | Max. DB-Retries |
