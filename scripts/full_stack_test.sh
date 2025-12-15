#!/usr/bin/env bash
# Full-stack QA script for FlowInvoice
# Runs frontend, backend, and database checks and produces a Markdown report.

set -u
IFS=$'\n\t'

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_DIR="${ROOT_DIR}/backend"
DOCKER_DIR="${ROOT_DIR}/docker"
REPORT_DIR="${ROOT_DIR}/dev/quality/reports"
REPORT_FILE="${REPORT_DIR}/quality-report-$(date +%Y%m%d-%H%M%S).md"

mkdir -p "${REPORT_DIR}"

print_header() {
  cat >"${REPORT_FILE}" <<REPORT
# FlowInvoice Full-Stack Testbericht

- Generiert am: $(date)
- Repository-Root: ${ROOT_DIR}
- Berichtspfad: ${REPORT_FILE}

## Zusammenfassung

Die folgenden Prüfungen wurden ausgeführt. Details und Konsolenausgaben finden sich in den jeweiligen Abschnitten weiter unten.
REPORT
}

append_summary_line() {
  local icon="$1"; shift
  local title="$1"; shift
  echo "- ${icon} ${title}" >>"${REPORT_FILE}"
}

append_section() {
  local icon="$1"; shift
  local title="$1"; shift
  local workdir="$1"; shift
  local cmd="$1"; shift
  local log_file="$1"; shift
  {
    echo "\n---\n"
    echo "### ${icon} ${title}"
    echo "**Arbeitsverzeichnis:** ${workdir}"\\
    "\n""**Kommando:** ${cmd}"\\
    "\n\n**Ausgabe:**\n\n\`\`\`"
    cat "${log_file}"
    echo "\`\`\`"
  } >>"${REPORT_FILE}"
}

run_step() {
  local title="$1"; shift
  local workdir="$1"; shift
  local cmd=("$@")

  local log_file
  log_file=$(mktemp)

  echo "[RUN] ${title}"
  if (cd "${workdir}" && "${cmd[@]}") >"${log_file}" 2>&1; then
    append_summary_line "✅" "${title}"
    append_section "✅" "${title}" "${workdir}" "${cmd[*]}" "${log_file}"
  else
    append_summary_line "❌" "${title}"
    append_section "❌" "${title}" "${workdir}" "${cmd[*]}" "${log_file}"
  fi

  rm -f "${log_file}"
}

skip_step() {
  local title="$1"; shift
  local reason="$1"; shift
  local log_file
  log_file=$(mktemp)
  echo "${reason}" >"${log_file}"
  append_summary_line "⚠️" "${title} (übersprungen)"
  append_section "⚠️" "${title} (übersprungen)" "n/a" "${reason}" "${log_file}"
  rm -f "${log_file}"
}

run_checked_step() {
  local title="$1"; shift
  local workdir="$1"; shift
  local required_bin="$1"; shift
  if ! command -v "${required_bin}" >/dev/null 2>&1; then
    skip_step "${title}" "${required_bin} ist nicht installiert"
    return
  fi
  run_step "${title}" "${workdir}" "$@"
}

run_prerequisites() {
  local log_file
  log_file=$(mktemp)
  {
    echo "Node Version: $(node --version 2>/dev/null || echo 'nicht gefunden')"
    echo "NPM Version:  $(npm --version 2>/dev/null || echo 'nicht gefunden')"
    echo "Python:       $(python3 --version 2>/dev/null || echo 'nicht gefunden')"
    if command -v docker >/dev/null 2>&1; then
      docker --version || true
      if docker compose version >/dev/null 2>&1; then
        docker compose version
      elif command -v docker-compose >/dev/null 2>&1; then
        docker-compose --version
      fi
    else
      echo "Docker:       nicht gefunden"
    fi
  } >"${log_file}"
  append_summary_line "ℹ️" "Werkzeug- und Versionscheck"
  append_section "ℹ️" "Werkzeug- und Versionscheck" "${ROOT_DIR}" "node/npm/python/docker versions" "${log_file}"
  rm -f "${log_file}"
}

print_header
run_prerequisites

# Frontend: Lint, Tests, Build
if [ -d "${FRONTEND_DIR}" ]; then
  run_checked_step "Frontend Lint" "${FRONTEND_DIR}" npm npm run lint
  run_checked_step "Frontend Typprüfung" "${FRONTEND_DIR}" npm npm run typecheck --if-present
  run_checked_step "Frontend Tests (Vitest)" "${FRONTEND_DIR}" npm npm run test -- --runInBand
  run_checked_step "Frontend Build" "${FRONTEND_DIR}" npm npm run build
else
  skip_step "Frontend" "Frontend-Verzeichnis nicht gefunden: ${FRONTEND_DIR}"
fi

# Backend: Lint, Typing, Tests
if [ -d "${BACKEND_DIR}" ]; then
  run_checked_step "Backend Codeformat (Black)" "${BACKEND_DIR}" black python3 -m black --check .
  run_checked_step "Backend Lint (Ruff)" "${BACKEND_DIR}" ruff python3 -m ruff check .
  run_checked_step "Backend Typprüfung (Mypy)" "${BACKEND_DIR}" mypy python3 -m mypy .
  run_checked_step "Backend Tests (Pytest)" "${BACKEND_DIR}" python3 python3 -m pytest
else
  skip_step "Backend" "Backend-Verzeichnis nicht gefunden: ${BACKEND_DIR}"
fi

# Datenbank-Check über Docker Compose (PostgreSQL Healthcheck)
if command -v docker >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
  if ! docker compose version >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  fi

  if [ -f "${DOCKER_DIR}/docker-compose.yml" ]; then
    run_step "Datenbank Start" "${DOCKER_DIR}" ${COMPOSE_CMD} -f docker-compose.yml up -d db
    run_step "Datenbank Status" "${DOCKER_DIR}" ${COMPOSE_CMD} -f docker-compose.yml exec db pg_isready -U flowaudit -d flowaudit
    run_step "Datenbank Stop" "${DOCKER_DIR}" ${COMPOSE_CMD} -f docker-compose.yml stop db
  else
    skip_step "Datenbank" "docker-compose.yml nicht gefunden unter ${DOCKER_DIR}"
  fi
else
  skip_step "Datenbank" "Docker ist nicht installiert; Datenbanktest übersprungen"
fi

echo "Bericht gespeichert unter: ${REPORT_FILE}"
