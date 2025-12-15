#!/bin/bash
# FlowAudit - Vollständige Qualitätsprüfung
# Führt alle Linting-, Type-Checking- und Test-Prüfungen aus

set -e  # Bei Fehler abbrechen

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Ergebnis-Tracking
BACKEND_RUFF=0
BACKEND_BLACK=0
BACKEND_MYPY=0
BACKEND_PYTEST=0
FRONTEND_LINT=0
FRONTEND_TSC=0
FRONTEND_BUILD=0

# ============================================================
# BACKEND CHECKS
# ============================================================
print_header "BACKEND CHECKS"

cd "$ROOT_DIR/backend"

# 1. Ruff Linter
echo "Running Ruff linter..."
if ruff check app/ 2>/dev/null; then
    print_success "Ruff: Keine Fehler"
    BACKEND_RUFF=1
else
    print_error "Ruff: Fehler gefunden"
fi

# 2. Black Formatter Check
echo -e "\nRunning Black formatter check..."
if black --check app/ 2>/dev/null; then
    print_success "Black: Code korrekt formatiert"
    BACKEND_BLACK=1
else
    print_warning "Black: Code nicht korrekt formatiert (führe 'black app/' aus)"
fi

# 3. MyPy Type Checking
echo -e "\nRunning MyPy type checker..."
if mypy app/ --ignore-missing-imports 2>/dev/null; then
    print_success "MyPy: Keine Type-Fehler"
    BACKEND_MYPY=1
else
    print_error "MyPy: Type-Fehler gefunden"
fi

# 4. Pytest
echo -e "\nRunning Pytest..."
if pytest tests/ -v --tb=short 2>/dev/null; then
    print_success "Pytest: Alle Tests bestanden"
    BACKEND_PYTEST=1
else
    print_error "Pytest: Tests fehlgeschlagen"
fi

# ============================================================
# FRONTEND CHECKS
# ============================================================
print_header "FRONTEND CHECKS"

cd "$ROOT_DIR/frontend"

# 5. ESLint
echo "Running ESLint..."
if npm run lint 2>/dev/null; then
    print_success "ESLint: Keine Fehler"
    FRONTEND_LINT=1
else
    print_error "ESLint: Fehler gefunden"
fi

# 6. TypeScript Check
echo -e "\nRunning TypeScript compiler check..."
if npx tsc --noEmit 2>/dev/null; then
    print_success "TypeScript: Keine Type-Fehler"
    FRONTEND_TSC=1
else
    print_error "TypeScript: Type-Fehler gefunden"
fi

# 7. Build Test
echo -e "\nRunning Build..."
if npm run build 2>/dev/null; then
    print_success "Build: Erfolgreich"
    FRONTEND_BUILD=1
else
    print_error "Build: Fehlgeschlagen"
fi

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print_header "ZUSAMMENFASSUNG"

echo "Backend:"
[[ $BACKEND_RUFF -eq 1 ]] && print_success "Ruff Linter" || print_error "Ruff Linter"
[[ $BACKEND_BLACK -eq 1 ]] && print_success "Black Formatter" || print_warning "Black Formatter"
[[ $BACKEND_MYPY -eq 1 ]] && print_success "MyPy Types" || print_error "MyPy Types"
[[ $BACKEND_PYTEST -eq 1 ]] && print_success "Pytest" || print_error "Pytest"

echo -e "\nFrontend:"
[[ $FRONTEND_LINT -eq 1 ]] && print_success "ESLint" || print_error "ESLint"
[[ $FRONTEND_TSC -eq 1 ]] && print_success "TypeScript" || print_error "TypeScript"
[[ $FRONTEND_BUILD -eq 1 ]] && print_success "Build" || print_error "Build"

# Gesamtergebnis
TOTAL=$((BACKEND_RUFF + BACKEND_BLACK + BACKEND_MYPY + BACKEND_PYTEST + FRONTEND_LINT + FRONTEND_TSC + FRONTEND_BUILD))

echo -e "\n${BLUE}────────────────────────────────────────────────────────────${NC}"
if [[ $TOTAL -eq 7 ]]; then
    echo -e "${GREEN}Alle Prüfungen bestanden! (7/7)${NC}"
    exit 0
else
    echo -e "${YELLOW}$TOTAL/7 Prüfungen bestanden${NC}"
    exit 1
fi
