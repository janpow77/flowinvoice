# Pfad: /backend/Dockerfile
# FlowAudit Backend Docker Image
# Python 3.11 mit FastAPI und allen Abhängigkeiten

FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 flowaudit \
    && useradd --uid 1000 --gid flowaudit --shell /bin/bash --create-home flowaudit

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install ".[dev]"

# Copy application code
COPY --chown=flowaudit:flowaudit app/ ./app/

# Create data directories
RUN mkdir -p /data/uploads /data/exports /data/logs && \
    chown -R flowaudit:flowaudit /data

# Switch to non-root user
USER flowaudit

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default workers (can be overridden by UVICORN_WORKERS env variable)
ENV UVICORN_WORKERS=4

# Run application with configurable workers
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}
