# Universal GUI Installer – Implementierungsleitfaden

Diese Dokumentation beschreibt den FlowAudit Universal Installer und wie er in anderen Projekten wiederverwendet werden kann.

## Inhaltsverzeichnis

- [Überblick](#überblick)
- [Anforderungen](#anforderungen)
- [Architektur](#architektur)
- [Setup & Installation](#setup--installation)
- [Anpassung für eigene Projekte](#anpassung-für-eigene-projekte)
- [Preflight-Checks](#preflight-checks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Überblick

Der Universal GUI Installer ist ein Python-basierter Tkinter-Installer, der:
- **Multi-Plattform**: Linux (primär), Windows, macOS (best effort)
- **GPU-Ready**: NVIDIA GPU-Support mit automatischen Checks
- **Docker-basiert**: Automatisches Deployment via Docker Compose
- **Robust**: Umfangreiche Preflight-Checks (Ports, GPU, Dependencies)
- **Benutzerfreundlich**: Moderne GUI mit Stepper, Logs, Fortschrittsanzeige

### Features

✅ **Systemprüfung**: Git, Docker, Docker Compose, NVIDIA GPU, Container Toolkit
✅ **Repository-Management**: Klonen, Pull, automatische Erkennung
✅ **Port-Checks**: Verhindert Deployment bei belegten Ports
✅ **GPU-Preflight**: NVIDIA Treiber, Container Toolkit, Docker GPU Test
✅ **Konfigurationsverwaltung**: `.env`-Generierung, Secrets, API-Keys
✅ **Deployment**: Docker Compose build, up, health checks
✅ **Admin-Erstellung**: Automatische Benutzeranlage im Backend
✅ **Ollama-Integration**: LLM-Modell-Pull mit Auswahl
✅ **Live-Logging**: Thread-safe UI-Logs + Datei-Logging

---

## Anforderungen

### System-Anforderungen

**Minimum:**
- Python 3.10+
- 4 GB RAM
- 10 GB Festplattenspeicher

**Empfohlen:**
- Python 3.11+
- 16 GB RAM (64 GB für LLM-Betrieb)
- NVIDIA GPU (optional, für GPU-beschleunigtes LLM)

### Python-Abhängigkeiten

**Pflicht:**
```bash
# Keine externen Abhängigkeiten für Basis-Funktionalität
# Tkinter ist in Python standard library
```

**Optional (für Logo-Anzeige):**
```bash
pip install pillow
```

### Systemabhängigkeiten

**Linux (Ubuntu/Debian):**
```bash
# Basis
sudo apt-get install -y git python3-tk

# Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Optional: GPU-Support
sudo apt-get install -y nvidia-driver-580-open nvidia-container-toolkit

# Port-Checks
# ss (iproute2) ist meist vorinstalliert
```

**Windows:**
- Git for Windows
- Docker Desktop
- Python 3.11+ (mit Tkinter)

**macOS:**
- Homebrew
- Docker Desktop
- Python 3.11+ (mit Tkinter)

---

## Architektur

### Dateistruktur

```
projekt/
├── installer/
│   ├── flowaudit_installer.py     # Haupt-Installer
│   └── auditlogo.png               # Optional: Logo
├── docker/
│   ├── docker-compose.yml          # Hauptdatei
│   ├── .env                        # Generiert vom Installer
│   └── docker-compose.override.yml # Optional (Cloudflare)
├── backend/
│   ├── Dockerfile
│   └── app/
├── frontend/
│   ├── Dockerfile
│   └── public/
│       └── auditlogo.png           # Logo-Quelle
└── docs/
    └── INSTALLER_GUIDE.md
```

### Komponenten-Übersicht

#### 1. **UI-Layer** (Tkinter)
- **Tabs**: System, Repo, Konfiguration, Deployment, Logs
- **Stepper**: Visueller Fortschritt mit Status-Badges
- **Formulare**: Eingabefelder für Secrets, API-Keys, Admin-Daten
- **Live-Logs**: Scrollbare Log-Area mit Syntax-Highlighting

#### 2. **Logic-Layer**
- **System-Checks**: `check_system()`
- **Repo-Management**: `clone_repo()`, `detect_repo()`, `pull_repo()`
- **Config-Writing**: `write_config_files()`
- **Deployment**: `_run_deployment()`
- **Preflight-Checks**: `_check_ports()`, GPU-Tests

#### 3. **Process-Layer**
- **Thread-safe Logging**: Queue-basiert
- **Subprocess-Wrapper**: `_run_process()` mit Live-Output
- **Docker Compose Abstraction**: `_detect_compose()`, `_compose()`

---

## Setup & Installation

### 1. Installer in eigenes Projekt kopieren

```bash
# Verzeichnis erstellen
mkdir -p dein-projekt/installer

# Installer kopieren
cp flowaudit_installer.py dein-projekt/installer/

# Optional: Logo kopieren
cp auditlogo.png dein-projekt/installer/
```

### 2. Anpassung der Konfiguration

Öffne `flowaudit_installer.py` und passe folgende Konstanten an:

```python
# =============================================================================
# KONFIGURATION (Zeilen ~45-70)
# =============================================================================

# Repository URL (dein GitHub/GitLab Repo)
DEFAULT_REPO = "https://github.com/deinuser/deinprojekt.git"

# Verzeichnisstruktur
DEFAULT_CLONE_DIRNAME = "deinprojekt_repo"
DEFAULT_DOCKER_DIR = "docker"  # Wo liegt docker-compose.yml?

# Service-Namen aus docker-compose.yml
SERVICE_BACKEND = "backend"
SERVICE_FRONTEND = "frontend"
SERVICE_OLLAMA = "ollama"      # Optional
SERVICE_DB = "db"
SERVICE_REDIS = "redis"
SERVICE_CHROMADB = "chromadb"  # Optional
SERVICE_WORKER = "worker"      # Optional

# URLs für Endanwender
FRONTEND_URL_HINT = "http://localhost:3000"
BACKEND_URL_HINT = "http://localhost:8000"

# Logo (relativ zum Repo-Root)
LOGO_RELATIVE_PATH = "frontend/public/logo.png"
```

### 3. Docker Compose anpassen

Stelle sicher, dass deine `docker-compose.yml`:
- **Ports über .env konfigurierbar** sind
- **Health-Checks** für kritische Services definiert
- **Korrekte GPU-Syntax** verwendet (falls GPU-Support)

**Beispiel: Ports konfigurierbar machen**

```yaml
services:
  backend:
    ports:
      - "${BACKEND_PORT:-8000}:8000"  # ← Umgebungsvariable mit Default

  frontend:
    ports:
      - "${FRONTEND_PORT:-3000}:80"
```

**Beispiel: GPU-Support (docker-compose compatible)**

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    device_requests:              # ← Nicht "deploy:"!
      - driver: nvidia
        count: 1
        capabilities: [gpu]
    mem_limit: ${OLLAMA_CONTAINER_MEMORY:-16G}
```

### 4. Installer ausführbar machen

```bash
chmod +x installer/flowaudit_installer.py

# Starten
python3 installer/flowaudit_installer.py
```

Oder als `.pyw` (Windows, ohne Konsole):
```bash
pythonw installer/flowaudit_installer.pyw
```

---

## Anpassung für eigene Projekte

### Minimal-Anpassungen (Quick Start)

1. **Repository URL** ändern (`DEFAULT_REPO`)
2. **Service-Namen** anpassen (falls abweichend)
3. **Logo-Pfad** anpassen (optional)
4. **Port-Liste** in `_check_ports()` anpassen

### Erweiterte Anpassungen

#### A) Eigene Preflight-Checks hinzufügen

Beispiel: Redis-CLI Check

```python
def check_system(self):
    # ... bestehender Code ...

    # Custom Check: Redis CLI
    redis_cli_ok = shutil.which("redis-cli") is not None
    lines.append(f"Redis CLI: {'OK' if redis_cli_ok else 'FEHLT (optional)'}")

    if not redis_cli_ok:
        self.log("Redis CLI nicht gefunden. Installiere mit: sudo apt install redis-tools", "warning")
```

#### B) Zusätzliche .env-Variablen

```python
def write_config_files(self):
    # ... bestehender Code ...

    # Eigene Variablen
    self.custom_api_key = tk.StringVar(value="")

    env_lines = [
        # ... Standard-Variablen ...
        "",
        "# Custom API Key",
        f"CUSTOM_API_KEY={sanitize_env_value(self.custom_api_key.get())}",
    ]
```

#### C) Eigene Admin-Erstellung (Non-FastAPI)

Falls dein Backend kein FastAPI ist:

```python
def _create_admin_user(self, docker_dir: Path):
    """Custom admin creation for Django/Flask/etc."""
    user = self.admin_user.get().strip()
    email = self.admin_email.get().strip()
    pw = self.admin_pass.get()

    # Beispiel: Django
    script = f"""
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='{user}').exists():
    User.objects.create_superuser('{user}', '{email}', '{pw}')
    print('CREATED: Admin user')
else:
    print('EXISTS: Admin user')
"""

    self._run_process(
        self._compose("exec", "-T", SERVICE_BACKEND, "python", "manage.py", "shell", "-c", script),
        cwd=str(docker_dir)
    )
```

#### D) Weitere Tabs hinzufügen

```python
def _build_ui(self):
    # ... bestehende Tabs ...

    self.tab_custom = ttk.Frame(self.nb, padding=12)
    self.nb.add(self.tab_custom, text="5) Custom Setup")
    self._build_tab_custom()

def _build_tab_custom(self):
    card = ttk.LabelFrame(self.tab_custom, text="Custom Config", padding=12)
    card.pack(fill=tk.BOTH, expand=True)

    self._section(card, "Eigene Einstellungen")
    self._field(card, "Custom Key", self.custom_key)
```

---

## Preflight-Checks

### Implementierte Checks

#### 1. **System-Checks** (`check_system()`)

✅ **Git**: `shutil.which("git")`
✅ **Docker**: `shutil.which("docker")`
✅ **Docker Compose**: `docker compose version`
✅ **NVIDIA GPU**: `nvidia-smi`
✅ **NVIDIA Container Toolkit**: `dpkg -l | grep nvidia-container-toolkit`
✅ **GPU in Docker**: Test-Container mit `nvidia/cuda:12.4.1-base-ubuntu22.04`
✅ **Docker-Gruppe**: Prüft, ob User in `docker` Gruppe

#### 2. **Port-Checks** (`_check_ports()`)

Ports werden vor Deployment geprüft:

```python
required_ports = {
    3000: "Frontend",
    8000: "Backend",
    8001: "ChromaDB",
    11434: "Ollama",
    5432: "PostgreSQL",
    6379: "Redis",
    9443: "Portainer (optional)"
}
```

**Linux**: `ss -tulpn`
**Windows**: `netstat -an`

Bei belegten **kritischen Ports** → Deployment-Abbruch mit Fehlermeldung.

#### 3. **Repository-Checks** (`detect_repo()`)

✅ `.git`-Verzeichnis vorhanden?
✅ `docker/`-Verzeichnis vorhanden?
✅ `docker-compose.yml` existiert?

#### 4. **Docker Compose Config-Check**

```python
subprocess.run(["docker", "compose", "config"], cwd=docker_dir)
# Exit-Code != 0 → Syntax-Fehler in docker-compose.yml
```

### Eigene Checks hinzufügen

**Template:**

```python
def _check_custom_requirement(self) -> bool:
    """
    Prüft eigene Voraussetzung.
    Returns True wenn OK, False bei Fehler.
    """
    try:
        # Beispiel: Custom Binary prüfen
        result = subprocess.run(
            ["custom-tool", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            self.log("Custom Tool: OK", "success")
            return True
        else:
            self.log("Custom Tool: FEHLER", "error")
            return False

    except FileNotFoundError:
        self.log("Custom Tool nicht gefunden", "warning")
        return False
    except subprocess.TimeoutExpired:
        self.log("Custom Tool: Timeout", "error")
        return False

# In check_system() einbinden:
def check_system(self):
    # ... bestehende Checks ...

    custom_ok = self._check_custom_requirement()
    lines.append(f"Custom Tool: {'OK' if custom_ok else 'FEHLT'}")

    if not custom_ok:
        ok = False  # Markiert System als nicht OK
```

---

## Best Practices

### 1. **Thread-Safety bei UI-Updates**

❌ **Falsch** (direkter UI-Zugriff aus Thread):
```python
def worker():
    self.log_area.insert(tk.END, "Text")  # ⚠️ Crash!
```

✅ **Richtig** (Queue-basiert):
```python
def worker():
    self.log("Text", "info")  # ← Nutzt Queue

def log(self, msg: str, level: str):
    self._log_queue.put((msg, level))

def _drain_log_queue(self):
    while True:
        msg, level = self._log_queue.get_nowait()
        self.log_area.insert(tk.END, f"{msg}\n", level)
    self.after(120, self._drain_log_queue)
```

### 2. **Secrets niemals hardcoden**

✅ Generiere Secrets automatisch:
```python
import secrets

self.db_password = tk.StringVar(value=secrets.token_hex(12))
self.jwt_secret = tk.StringVar(value=secrets.token_hex(32))
```

✅ Escaping für `.env`:
```python
def sanitize_env_value(v: str) -> str:
    v = str(v).replace("\r", "").replace("\n", "").strip()
    if any(ch in v for ch in [' ', '"', "'", "=", "#", "$", "`"]):
        v = v.replace('"', '\\"')
        return f'"{v}"'
    return v
```

### 3. **Fehlerbehandlung bei subprocess**

```python
def _run_process(self, cmd: list[str], timeout: int | None = None):
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        start_time = time.time()
        for line in proc.stdout:
            self.log(line.rstrip(), "info")

            if timeout and (time.time() - start_time) > timeout:
                proc.terminate()
                raise ProcessError(f"Timeout nach {timeout}s")

        proc.wait()
        if proc.returncode != 0:
            raise ProcessError(f"Befehl fehlgeschlagen (Exit {proc.returncode})")

    except FileNotFoundError:
        raise ProcessError(f"Befehl nicht gefunden: {cmd[0]}")
```

### 4. **Idempotenz (Wiederholbarkeit)**

Der Installer sollte mehrfach ohne Schaden ausführbar sein:

```python
# ✅ Gut: Prüfe, ob schon vorhanden
if (target / ".git").exists():
    self.log("Repo existiert bereits. Nutze 'Pull (Update)'.", "warning")
    return

# ❌ Schlecht: Blind überschreiben
shutil.rmtree(target)  # ⚠️ Datenverlust!
```

### 5. **Health-Checks statt sleep**

❌ **Schlecht**:
```python
subprocess.run(["docker", "compose", "up", "-d"])
time.sleep(30)  # ⚠️ Unzuverlässig
```

✅ **Gut**:
```python
subprocess.run(["docker", "compose", "up", "-d"])
self._wait_for_service_ready(docker_dir, "backend", timeout_sec=180)
```

---

## Troubleshooting

### Problem: "Port XYZ bereits belegt"

**Ursache**: Anderer Prozess nutzt Port.

**Lösung 1** (Service stoppen):
```bash
# Linux: Prozess finden
sudo ss -tulpn | grep :8000
sudo kill <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Lösung 2** (Port ändern):
```bash
# In docker/.env
BACKEND_PORT=8080  # Statt 8000
```

### Problem: "GPU in Docker nicht verfügbar"

**Check 1**: NVIDIA Treiber installiert?
```bash
nvidia-smi
# Sollte GPU-Tabelle zeigen
```

**Check 2**: Container Toolkit installiert?
```bash
dpkg -l | grep nvidia-container-toolkit
# Sollte Paket anzeigen

# Falls nicht:
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**Check 3**: Test-Container
```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
# Sollte GPU-Info zeigen
```

### Problem: "docker compose nicht gefunden"

**Ursache**: Compose Plugin fehlt oder alte Version.

**Lösung**:
```bash
# Ubuntu/Debian
sudo apt install -y docker-compose-plugin

# Verify
docker compose version
# Sollte: Docker Compose version v2.x.x
```

### Problem: "Zielordner ist nicht leer"

**Ursache**: `git clone` schlägt fehl bei nicht-leerem Verzeichnis.

**Lösung**:
1. Leeren Ordner wählen
2. Oder bestehendes Repo updaten (Button "Pull (Update)")

---

## Code-Snippets für häufige Anpassungen

### Custom Service hinzufügen

```python
# In Konfiguration (Zeile ~50)
SERVICE_CUSTOM = "mein-service"

# In Deployment (nach Zeile ~1120)
def _run_deployment(self):
    # ... Standard-Deployment ...

    # Warte auf Custom Service
    if self._service_exists(docker_dir, SERVICE_CUSTOM):
        self.log("Warte auf Custom Service...", "info")
        self._wait_for_service_ready(docker_dir, SERVICE_CUSTOM, timeout_sec=120)
        self.log("Custom Service bereit.", "success")
```

### Eigenes Skript nach Deployment ausführen

```python
def _run_deployment(self):
    # ... nach Admin-Erstellung ...

    # Custom Post-Deploy Script
    self.log("Führe Post-Deploy-Skript aus...", "info")
    script_path = self.detected_repo_root / "scripts" / "post_deploy.sh"

    if script_path.exists():
        self._run_process(["bash", str(script_path)], cwd=str(self.detected_repo_root))
        self.log("Post-Deploy-Skript abgeschlossen.", "success")
    else:
        self.log("Kein Post-Deploy-Skript gefunden (optional).", "warning")
```

### Mehrsprachigkeit (i18n)

```python
# Strings in Dict
STRINGS = {
    "de": {
        "title": "FlowAudit Installer",
        "btn_install": "Installation starten",
        "msg_success": "Installation erfolgreich!",
    },
    "en": {
        "title": "FlowAudit Installer",
        "btn_install": "Start Installation",
        "msg_success": "Installation successful!",
    }
}

class FlowAuditInstaller(tk.Tk):
    def __init__(self, lang="de"):
        self.lang = lang
        self.strings = STRINGS[lang]

        # UI
        self.title(self.strings["title"])
        ttk.Button(text=self.strings["btn_install"], command=self.install).pack()
```

---

## Checkliste für eigenes Projekt

- [ ] Repository URL angepasst (`DEFAULT_REPO`)
- [ ] Service-Namen angepasst (`SERVICE_*`)
- [ ] Port-Liste angepasst (`_check_ports()`)
- [ ] Logo-Pfad angepasst (optional)
- [ ] `.env`-Template angepasst (`write_config_files()`)
- [ ] Admin-Erstellung für eigenes Backend angepasst
- [ ] Docker Compose Ports über `.env` konfigurierbar
- [ ] Health-Checks in `docker-compose.yml` definiert
- [ ] GPU-Syntax korrekt (falls GPU-Support)
- [ ] Preflight-Checks getestet
- [ ] Installation auf Zielplattform getestet (Linux/Windows/macOS)

---

## Lizenz & Credits

**Basis-Installer**: FlowAudit Universal Installer v3.0
**Framework**: Python 3.11 + Tkinter
**Design-Inspiration**: Modern Material Design (Tailwind-Farben)

**Wiederverwendung**: Dieser Installer kann frei für eigene Projekte angepasst werden.
**Credits**: Bitte verweise auf `FlowAudit Installer` als Ursprung.

---

## Support & Weiterentwicklung

**Verbesserungsvorschläge**:
- MCP-Server-Integration
- Multi-Backend-Support (nicht nur FastAPI)
- Auto-Updates
- Rollback-Funktion
- Container-Monitoring-Dashboard
- Backup/Restore-Funktion

**Contributions**: Pull Requests willkommen!

---

**Erstellt**: 2024
**Letzte Aktualisierung**: 2025-12-16
**Version**: 3.0
