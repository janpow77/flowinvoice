# ASUS NUC 15 – Komplette Einrichtung von Null

**Ziel:** Leeren NUC mit Ubuntu, Docker und FlowAudit einrichten
**Dauer:** ~1 Stunde
**Schwierigkeit:** Anfänger-freundlich

---

## 📋 Übersicht

| Phase | Was | Dauer |
|-------|-----|-------|
| 1 | USB-Stick erstellen | 10 Min |
| 2 | Ubuntu installieren | 20 Min |
| 3 | Ubuntu einrichten | 5 Min |
| 4 | NVIDIA Treiber | 5 Min |
| 5 | Docker installieren | 5 Min |
| 6 | NVIDIA Container Toolkit | 3 Min |
| 7 | FlowAudit Installer | 15 Min |

---

## Phase 1: Ubuntu USB-Stick erstellen

> **Voraussetzung:** Ein funktionierender PC + USB-Stick (mind. 8 GB)

### 1.1 Ubuntu herunterladen

```
https://ubuntu.com/download/desktop
→ Ubuntu 24.04 LTS (empfohlen)
→ Datei: ubuntu-24.04-desktop-amd64.iso (~5 GB)
```

### 1.2 Bootfähigen USB-Stick erstellen

| Dein PC | Tool | Download |
|---------|------|----------|
| **Windows** | Rufus | https://rufus.ie |
| **macOS** | balenaEtcher | https://etcher.balena.io |
| **Linux** | balenaEtcher | https://etcher.balena.io |

**Mit Rufus (Windows):**
1. Rufus starten
2. USB-Stick auswählen
3. "SELECT" → Ubuntu ISO auswählen
4. "START" klicken
5. Warten (~5 Min)

**Mit balenaEtcher (macOS/Linux):**
1. "Flash from file" → Ubuntu ISO
2. "Select target" → USB-Stick
3. "Flash!" klicken

---

## Phase 2: Ubuntu auf NUC installieren

### 2.1 NUC vorbereiten

```
☐ USB-Stick einstecken
☐ Monitor anschließen (HDMI/DisplayPort)
☐ Tastatur anschließen (USB)
☐ Maus anschließen (USB)
☐ Netzwerkkabel anschließen (empfohlen) oder WLAN später
☐ NUC einschalten
```

### 2.2 Boot-Menü aufrufen

```
Beim Start sofort drücken:
  F2  → BIOS Setup
  F10 → Boot Menu (schneller)

Im BIOS (falls nötig):
  → Boot-Reihenfolge: USB zuerst
  → Secure Boot: Disabled (bei Problemen)
  → Speichern: F10 → Yes
```

### 2.3 Ubuntu installieren

```
1. "Install Ubuntu" wählen (nicht "Try Ubuntu")

2. Sprache auswählen
   → Deutsch

3. Tastaturlayout
   → German / German

4. Installationstyp
   → "Normal installation"
   ☑️ "Install third-party software for graphics..."

5. Festplatte
   → "Erase disk and install Ubuntu"
   ⚠️ ACHTUNG: Löscht alle Daten auf der NUC!

6. Zeitzone
   → Berlin (oder deine Stadt)

7. Benutzer anlegen
   Name:         Max Mustermann
   Computername: flowaudit-nuc
   Benutzername: max
   Passwort:     ********
   ☐ "Automatisch anmelden" (optional)

8. Installation läuft... (~15-30 Minuten)

9. "Restart Now" klicken
   → USB-Stick entfernen wenn aufgefordert
   → Enter drücken
```

---

## Phase 3: Ubuntu einrichten

### 3.1 Erster Start

Nach dem Neustart:
1. Mit deinem Passwort anmelden
2. Einrichtungsassistent durchklicken (oder überspringen)

### 3.2 Terminal öffnen

```
Tastenkombination: Ctrl + Alt + T
```

### 3.3 System aktualisieren

```bash
sudo apt update && sudo apt upgrade -y
```

> Bei Frage nach Passwort: Dein Benutzerpasswort eingeben (wird nicht angezeigt)

### 3.4 Grundlegende Tools installieren

```bash
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    net-tools \
    openssh-server \
    python3 \
    python3-pip \
    python3-tk
```

### 3.5 SSH aktivieren (für Remote-Zugriff)

```bash
# SSH-Server starten
sudo systemctl enable ssh
sudo systemctl start ssh

# IP-Adresse anzeigen (für SSH von anderem PC)
ip addr show | grep "inet "
```

**Danach kannst du vom anderen PC per SSH verbinden:**
```bash
ssh max@192.168.1.xxx
```

---

## Phase 4: NVIDIA-Treiber installieren

> **Nur wenn dein NUC eine NVIDIA GPU hat (z.B. RTX)**

### 4.1 Verfügbare Treiber anzeigen

```bash
ubuntu-drivers devices
```

**Beispiel-Ausgabe:**
```
vendor   : NVIDIA Corporation
model    : GeForce RTX 4060
driver   : nvidia-driver-550 - recommended
```

### 4.2 Empfohlenen Treiber installieren

```bash
sudo ubuntu-drivers autoinstall
```

### 4.3 Neustart

```bash
sudo reboot
```

### 4.4 Treiber prüfen

```bash
nvidia-smi
```

**Erwartete Ausgabe:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 550.xx    Driver Version: 550.xx    CUDA Version: 12.x          |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA GeForce RTX ...   |                      |                      |
+-------------------------------+----------------------+----------------------+
```

---

## Phase 5: Docker installieren

### 5.1 Alte Versionen entfernen (falls vorhanden)

```bash
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null
```

### 5.2 Abhängigkeiten installieren

```bash
sudo apt install -y ca-certificates curl gnupg lsb-release
```

### 5.3 Docker GPG-Key hinzufügen

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 5.4 Docker Repository hinzufügen

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 5.5 Docker installieren

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
```

### 5.6 Docker ohne sudo ermöglichen

```bash
# Benutzer zur docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Änderung aktivieren (WICHTIG!)
newgrp docker
```

> **Alternative:** Komplett abmelden und neu anmelden

### 5.7 Docker testen

```bash
# Test-Container ausführen
docker run hello-world

# Docker Compose Version prüfen
docker compose version
```

**Erwartete Ausgabe:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

## Phase 6: NVIDIA Container Toolkit

> **Nur wenn NVIDIA GPU vorhanden**

### 6.1 Repository hinzufügen

```bash
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### 6.2 Toolkit installieren

```bash
sudo apt update
sudo apt install -y nvidia-container-toolkit
```

### 6.3 Docker für GPU konfigurieren

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 6.4 GPU in Docker testen

```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## Phase 7: FlowAudit Installer starten

### 7.1 Verzeichnis erstellen

```bash
mkdir -p ~/FlowAudit && cd ~/FlowAudit
```

### 7.2 PIL für Logo installieren

```bash
pip3 install pillow
```

### 7.3 Installer herunterladen

```bash
curl -O https://raw.githubusercontent.com/janpow77/flowinvoice/main/installer/flowaudit_installer.py
```

### 7.4 Installer starten

```bash
python3 flowaudit_installer.py
```

### 7.5 Im GUI

```
1. Tab "System" prüfen
   → Alle Checks sollten grün sein ✅

2. Button "Alles in einem Schritt" klicken
   → Klont Repository
   → Erstellt Konfiguration
   → Baut Docker Images
   → Startet Container
   → Erstellt Admin-User
   → Lädt KI-Modell (optional)

3. Warten... (~10-30 Minuten)

4. Fertig! 🎉
```

---

## 🎉 Nach der Installation

### FlowAudit öffnen

```
Browser öffnen:
→ http://localhost:3000

Login:
→ E-Mail:    admin@local
→ Passwort:  admin123

⚠️ WICHTIG: Passwort sofort ändern!
```

### API-Dokumentation

```
→ http://localhost:8000/docs
```

---

## 🔧 Nützliche Befehle

### System-Info

```bash
uname -a              # Kernel-Version
lsb_release -a        # Ubuntu-Version
free -h               # RAM-Nutzung
df -h                 # Festplattenplatz
nvidia-smi            # GPU-Status (falls vorhanden)
htop                  # Prozesse live
```

### Docker-Befehle

```bash
docker ps                   # Laufende Container
docker compose ps           # FlowAudit Container Status
docker compose logs -f      # Live-Logs aller Services
docker compose logs backend # Logs eines Services
```

### FlowAudit steuern

```bash
cd ~/FlowAudit/flowaudit_repo/docker

# Container stoppen
docker compose down

# Container starten
docker compose up -d

# Container neu starten
docker compose restart

# Alles neu bauen
docker compose build --no-cache
docker compose up -d
```

### SSH von anderem PC

```bash
# IP-Adresse auf NUC herausfinden
ip addr show | grep "inet "

# Von anderem PC verbinden
ssh benutzername@192.168.1.xxx
```

---

## 🔍 Troubleshooting

### Problem: "Permission denied" bei Docker

```bash
# Lösung 1: newgrp
newgrp docker

# Lösung 2: Komplett abmelden und neu anmelden

# Lösung 3: Prüfen ob in Gruppe
groups | grep docker
```

### Problem: NVIDIA GPU nicht erkannt

```bash
# Treiber-Status prüfen
nvidia-smi

# Falls Fehler: Treiber neu installieren
sudo apt install --reinstall nvidia-driver-550
sudo reboot
```

### Problem: Kein Internet

```bash
# Netzwerk-Status prüfen
ip addr
ping google.com

# WLAN verbinden (falls kein Kabel)
nmcli device wifi list
nmcli device wifi connect "WLAN-Name" password "geheim"
```

### Problem: Installer startet nicht

```bash
# Tkinter installiert?
sudo apt install python3-tk

# PIL installiert?
pip3 install pillow

# Python-Version
python3 --version  # Sollte 3.10+ sein
```

---

## 📞 Support

Bei Problemen:

1. **Installer-Log prüfen:** `~/FlowAudit/installer.log`
2. **Container-Logs:** `docker compose logs`
3. **GitHub Issue:** https://github.com/janpow77/flowinvoice/issues

---

**Viel Erfolg mit deinem NUC und FlowAudit! 🐟**
