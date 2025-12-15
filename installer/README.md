# FlowAudit Universal GUI Installer

**Version:** 3.0 – Excellent Edition
**Zielplattform:** Ubuntu Desktop / ASUS NUC 15 (primär), Windows/macOS (best effort)

---

## 🎯 Übersicht

Der FlowAudit Installer ist eine grafische Benutzeroberfläche (GUI) zur vollautomatischen Installation und Konfiguration von FlowAudit auf lokalen Systemen. Er führt durch alle Schritte – vom Klonen des Repositories bis zum laufenden System mit Admin-Account.

```
┌─────────────────────────────────────────────────────────────────┐
│  FlowAudit Installer - Excellent Edition v3.0                   │
├─────────────────────────────────────────────────────────────────┤
│  [Logo]  FlowAudit Installer                                    │
│          Git → Konfiguration → Docker → Admin → Cloudflare      │
├─────────────┬───────────────────────────────────────────────────┤
│  Status     │  Tabs: System | Repo | Konfiguration | Deployment │
│  ────────── │  ─────────────────────────────────────────────────│
│  ● System   │  [Tab-Inhalt je nach Auswahl]                     │
│  ○ Repo     │                                                    │
│  ○ Config   │                                                    │
│  ○ Deploy   │                                                    │
├─────────────┴───────────────────────────────────────────────────┤
│  [═══════════════════════════] 45%    [Beenden] [Nächster →]    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Beschreibung |
|---------|--------------|
| **Thread-sicheres Logging** | Echtzeit-Log-Ausgabe über Queue + UI-Poller |
| **Docker Compose Abstraktion** | Erkennt automatisch `docker compose` vs `docker-compose` |
| **Robuste Readiness-Checks** | Container Status, Health-Checks, HTTP-Polling |
| **Sichere Admin-Erstellung** | JSON-Escaping verhindert Injection |
| **Logo-Integration** | Zeigt das FlowAudit-Logo in der GUI |
| **GPU-Unterstützung** | NVIDIA RTX Settings für Ollama |
| **Cloudflare Tunnel** | Optionaler sicherer Remote-Zugriff |
| **Ollama Model Pull** | Lädt lokale KI-Modelle automatisch |

---

## 📋 Voraussetzungen

### System-Anforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| RAM | 16 GB | 32+ GB |
| Storage | 50 GB SSD | 100+ GB NVMe |
| GPU | - | NVIDIA RTX (12+ GB VRAM) |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 LTS |

### Software-Abhängigkeiten

```bash
# Ubuntu/Debian - Alle Abhängigkeiten installieren
sudo apt-get update
sudo apt-get install -y python3 python3-tk python3-pip git

# Optional: PIL für Logo-Anzeige
pip3 install pillow

# Docker Engine + Compose Plugin
# (Der Installer kann Docker auch automatisch installieren)
```

### Docker ohne sudo (wichtig!)

```bash
sudo usermod -aG docker $USER
# Danach abmelden und neu anmelden ODER:
newgrp docker
```

---

## 🚀 Schnellstart

### Option A: Nur Installer downloaden (empfohlen für Neuinstallation)

```bash
# 1. Verzeichnis erstellen
mkdir ~/FlowAudit && cd ~/FlowAudit

# 2. Installer herunterladen
curl -O https://raw.githubusercontent.com/janpow77/flowinvoice/main/installer/flowaudit_installer.py

# 3. Installer starten
python3 flowaudit_installer.py

# 4. Im GUI: "Alles in einem Schritt" klicken
```

### Option B: Ganzes Repo klonen (für Entwickler)

```bash
# 1. Repo klonen
git clone https://github.com/janpow77/flowinvoice.git
cd flowinvoice/installer

# 2. Installer starten
python3 flowaudit_installer.py
```

---

## 📖 Schritt-für-Schritt Anleitung

### Schritt 1: System prüfen

Der Installer prüft automatisch:

| Prüfung | Beschreibung |
|---------|--------------|
| Python | Version ≥ 3.10 |
| Git | Installation vorhanden |
| Docker | Engine läuft |
| Compose | Plugin oder Standalone |
| GPU | NVIDIA Treiber + nvidia-smi |

**Status-Anzeige:**
- 🟢 **OK** – Komponente verfügbar
- 🟡 **WARN** – Funktioniert, aber mit Einschränkungen
- 🔴 **FEHLER** – Muss behoben werden

### Schritt 2: Repository klonen/aktualisieren

- **Neu:** Klont das Repository in das gewählte Verzeichnis
- **Bestehend:** Führt `git pull` aus, um Updates zu holen
- **Auto-Erkennung:** Erkennt, wenn bereits im Repo-Verzeichnis

### Schritt 3: Konfiguration generieren

Der Installer erstellt automatisch:

**`.env` Datei mit:**
```env
# Automatisch generierte Secrets
POSTGRES_PASSWORD=<zufällig>
JWT_SECRET_KEY=<zufällig>
CHROMA_SERVER_AUTHN_CREDENTIALS=<zufällig>

# Optional konfigurierbar
OPENAI_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
CLOUDFLARE_TUNNEL_TOKEN=...

# GPU-Einstellungen
GPU_MEMORY_FRACTION=0.8
OLLAMA_NUM_GPU=999
```

**`docker-compose.override.yml` für:**
- GPU-Reservierung für Ollama
- Memory-Limits
- Cloudflare Tunnel Service

### Schritt 4: Deployment starten

Der Installer führt aus:

1. `docker compose build` – Images bauen
2. `docker compose up -d` – Container starten
3. Warten auf Container-Readiness
4. Admin-User erstellen via Backend-CLI
5. Optional: Ollama-Modell pullen

---

## ⚙️ Konfigurationsoptionen

### Sicherheit & Datenbank

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| DB Passwort | PostgreSQL Passwort | Auto-generiert (24 Hex) |
| JWT Secret | Token-Signierung | Auto-generiert (64 Hex) |
| Chroma Token | Vector-DB Auth | Auto-generiert (24 Hex) |

### KI API Keys (optional)

| Provider | Für | Empfehlung |
|----------|-----|------------|
| OpenAI | GPT-4, GPT-3.5 | Production |
| Gemini | Google AI | Alternative |
| Anthropic | Claude | Premium |

> **Hinweis:** Ohne API-Keys läuft FlowAudit mit lokalem Ollama-Modell.

### GPU Einstellungen (NVIDIA)

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| GPU Memory Fraction | Anteil VRAM für Ollama | 0.8 (80%) |
| GPU Layers | Anzahl Layers auf GPU | 999 (alle) |
| Container Memory | Max RAM für Ollama | 16G |

### Lokales KI-Modell (Ollama)

| Modell | Parameter | VRAM | Empfehlung |
|--------|-----------|------|------------|
| **Qwen 2.5 32B** | 32B | 20+ GB | ⭐ NUC 15 mit RTX |
| Qwen 2.5 14B | 14B | 10+ GB | Schneller |
| Llama 3.1 70B | 70B | 40+ GB | High-End |
| Mistral Small 22B | 22B | 14+ GB | Gut balanciert |
| Keines | - | - | Nur Cloud APIs |

### Cloudflare Tunnel (optional)

Ermöglicht sicheren Zugriff von außen ohne Portfreigabe:

1. Cloudflare Dashboard → Zero Trust → Tunnels
2. Neuen Tunnel erstellen
3. Token kopieren
4. Im Installer einfügen

---

## 🐳 Docker Services

| Service | Port | Beschreibung | Health-Check |
|---------|------|--------------|--------------|
| **frontend** | 3000 | React Web-UI | HTTP / |
| **backend** | 8000 | FastAPI REST API | HTTP /health |
| **db** | 5432 | PostgreSQL 16 | pg_isready |
| **redis** | 6379 | Task Queue & Cache | redis-cli ping |
| **chromadb** | 8001 | Vector Store (RAG) | HTTP /api/v1/heartbeat |
| **ollama** | 11434 | Local LLM Server | HTTP /api/tags |
| **worker** | - | Celery Background Jobs | - |

---

## 🔧 Quick Actions

| Button | Funktion |
|--------|----------|
| **Alles in einem Schritt** | Führt Schritte 1-4 automatisch aus |
| **Container Status** | Zeigt `docker compose ps` |
| **Docker Logs** | Öffnet Log-Viewer für alle Services |
| **Nächster Schritt →** | Geht zum nächsten Tab |
| **Log öffnen** | Öffnet `installer.log` |

---

## 📁 Dateistruktur

```
installer/
├── flowaudit_installer.py   # Hauptinstaller (Python/Tkinter)
├── README.md                # Diese Dokumentation
└── installer.log            # Log-Datei (nach Start)

docker/
├── docker-compose.yml       # Haupt-Compose-Datei
├── .env                     # Generierte Konfiguration
└── docker-compose.override.yml  # GPU/Cloudflare Overrides
```

---

## 🔍 Troubleshooting

### Docker Permission Denied

```bash
sudo usermod -aG docker $USER
newgrp docker
# ODER: Komplett abmelden und neu anmelden
```

### NVIDIA GPU nicht erkannt

```bash
# 1. NVIDIA Treiber prüfen
nvidia-smi

# 2. Container Toolkit installieren
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Container startet nicht

```bash
# Logs prüfen
docker compose -f docker/docker-compose.yml logs <service>

# Container neu starten
docker compose -f docker/docker-compose.yml restart <service>

# Alles neu bauen
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml build --no-cache
docker compose -f docker/docker-compose.yml up -d
```

### Modell-Download langsam

Große Modelle können mehrere GB groß sein:

| Modell | Größe |
|--------|-------|
| Qwen 2.5 32B Q4 | ~18 GB |
| Llama 3.1 70B Q4 | ~40 GB |

**Tipp:** Download läuft im Hintergrund weiter, auch wenn der Installer geschlossen wird.

### Backend nicht erreichbar

```bash
# Health-Check
curl http://localhost:8000/health

# Logs prüfen
docker compose -f docker/docker-compose.yml logs backend
```

---

## 🔒 Sicherheitshinweise

| ⚠️ Wichtig |
|-----------|
| `.env` enthält Secrets → **Niemals committen!** |
| Admin-Passwort nach Erststart ändern |
| Cloudflare Token wie Passwort behandeln |
| Bei Produktiveinsatz: HTTPS aktivieren |

---

## 📞 Support

Bei Problemen:

1. **Log-Datei prüfen:** `installer.log` im Installer-Verzeichnis
2. **Container-Logs:** "Docker Logs" Button im Installer
3. **Issue erstellen:** [GitHub Issues](https://github.com/janpow77/flowinvoice/issues)

---

## 🎉 Nach der Installation

Nach erfolgreicher Installation:

1. **Frontend öffnen:** http://localhost:3000
2. **Mit Admin einloggen:** admin@local / admin123
3. **Passwort ändern!**
4. **API testen:** http://localhost:8000/docs

**Viel Erfolg mit FlowAudit! 🐟**
