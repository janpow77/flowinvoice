# FlowAudit Universal GUI Installer

**Version:** 3.0
**Ziel:** Stabiler, thread-sicherer, plattformtauglicher Installer für FlowAudit
**Primär:** Ubuntu Desktop / ASUS NUC 15

## Features

- Thread-sicheres Logging (Queue + UI-Poller)
- Docker Compose Abstraktion (`docker compose` vs `docker-compose`)
- Robuste Readiness-Checks (Container Status/Health/Polling)
- Sichere Admin-Erstellung (JSON-Escaping)
- Schönes UI mit Logo, Stepper, Status-Karten, Progressbar
- GPU-Einstellungen für NVIDIA RTX
- Cloudflare Tunnel Integration (optional)
- Ollama Model Pull (optional)

## Voraussetzungen

### Ubuntu/Debian

```bash
# Python + Tkinter
sudo apt-get update
sudo apt-get install -y python3 python3-tk python3-pip

# Optional: PIL für Logo-Anzeige
pip3 install pillow

# Git
sudo apt-get install -y git

# Docker Engine + Compose Plugin
# (Installer kann Docker auch installieren)
```

### Docker ohne sudo

```bash
sudo usermod -aG docker $USER
# Danach abmelden/neu anmelden oder reboot
```

## Schnellstart

```bash
# In das Installer-Verzeichnis wechseln
cd /pfad/zu/flowinvoice/installer

# Installer starten
python3 gui_installer.py
```

## Verwendung

1. **System prüfen** - Überprüft Python, Git, Docker, Compose, GPU
2. **Repo klonen/aktualisieren** - Klont das Repository oder aktualisiert es
3. **Konfiguration generieren** - Erstellt `.env` mit Secrets
4. **Deployment starten** - Baut und startet alle Container, erstellt Admin-User

### Quick Actions

- **Alles in einem Schritt** - Führt alle Schritte automatisch aus
- **Container Status** - Zeigt den Status aller Container

## Konfigurationsoptionen

### Sicherheit & Datenbank
- DB Passwort (automatisch generiert)
- JWT Secret (automatisch generiert)
- Chroma Token (automatisch generiert)

### Cloudflare Tunnel (optional)
- Sicherer Zugriff von außen ohne Portfreigabe
- Token aus dem Cloudflare Dashboard

### KI API Keys (optional)
- OpenAI
- Google Gemini
- Anthropic Claude

### GPU Einstellungen (NVIDIA RTX)
- GPU Memory Fraction (Standard: 0.8)
- GPU Layers (Standard: 999 = alle)
- Container Memory Limit (Standard: 16G)

### Lokales KI-Modell (Ollama)
- Qwen 2.5 32B (Empfohlen für NUC)
- Qwen 2.5 14B (Schneller)
- Llama 3.1 70B (High-End)
- Mistral Small 22B
- Keines (nur Cloud APIs)

## Docker Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| frontend | 3000 | React Frontend |
| backend | 8000 | FastAPI Backend |
| db | 5432 | PostgreSQL |
| redis | 6379 | Task Queue & Cache |
| chromadb | 8001 | Vector Store |
| ollama | 11434 | Local LLM |
| worker | - | Celery Worker |

## Dateien

```
installer/
├── gui_installer.py    # Hauptinstaller
├── auditlogo.png       # Logo für UI
└── README.md           # Diese Datei
```

## Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### NVIDIA GPU nicht erkannt
```bash
# NVIDIA Container Toolkit installieren
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Modell-Download langsam
Große Modelle wie Qwen 32B oder Llama 70B können mehrere GB groß sein. Der Download kann je nach Internetverbindung lange dauern.

## Sicherheitshinweise

- `.env` enthält Secrets → **nicht committen**
- Admin-Passwort nach Erststart ändern
- Bei Cloudflare Tunnel: Token wie Passwort behandeln

## Support

Bei Problemen:
1. Log-Datei prüfen: `installer.log`
2. Container-Logs prüfen: Docker Logs Button im Installer
3. Issue im Repository erstellen
