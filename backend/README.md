# FlowAudit Backend

FastAPI-basiertes Backend für transparente Rechnungsprüfung mit LLMs.

## Voraussetzungen

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- ChromaDB
- Ollama (für lokale LLM-Inferenz)

## Installation

```bash
# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder: .venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -e ".[dev]"
```

## Entwicklung

```bash
# Server starten
uvicorn app.main:app --reload --port 8000

# Tests ausführen
pytest tests/ -v

# Linting
ruff check app/
mypy app/

# Formatierung
black app/
```

## API-Dokumentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Projektstruktur

```
backend/
├── app/
│   ├── api/          # API-Router
│   ├── core/         # Kernfunktionen
│   ├── llm/          # LLM-Integration
│   ├── models/       # SQLAlchemy-Modelle
│   ├── rag/          # RAG-System
│   ├── schemas/      # Pydantic-Schemas
│   ├── services/     # Business-Logik
│   └── worker/       # Celery-Tasks
├── tests/            # Pytest-Tests
├── Dockerfile
└── pyproject.toml
```
