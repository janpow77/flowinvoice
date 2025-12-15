Sehr gut. 👍
Hier ist eine saubere, repo-taugliche ISSUES.md, die exakt die real aufgetretenen Probleme abbildet, technisch korrekt, nachvollziehbar und ohne Schuldzuweisung.
Du kannst sie 1:1 ins Repo übernehmen.


---

# Issues & Known Problems – FlowInvoice / FlowAudit

Diese Datei dokumentiert bekannte Probleme, typische Fehlerbilder und deren Ursachen,
die bei Installation, Deployment und Betrieb von FlowInvoice / FlowAudit auftreten können.

Ziel ist es, Fehlerquellen transparent zu machen, die Fehlersuche zu beschleunigen
und künftige Nutzer:innen vor typischen Fallstricken zu bewahren.

---

## 1. YAML-Parser-Fehler durch Python-Docstrings

### Symptom
```text
yaml.parser.ParserError: expected '<document start>', but found '<scalar>'

oder

dockerfile parse error: unknown instruction: """

Ursache

In mehreren Dateien wurden Python-Docstrings (""" ... """) verwendet in:

docker/docker-compose.yml

backend/Dockerfile

docker/ollama/Dockerfile

ggf. weiteren Dockerfiles


Diese Syntax ist nur in Python gültig, nicht jedoch in:

YAML

Dockerfiles


Lösung

Alle """ entfernen

Kommentare ausschließlich mit # schreiben

In docker-compose.yml muss services: ganz links beginnen

In Dockerfiles muss FROM ... die erste echte Anweisung sein



---

2. Installer: Klonen in nicht-leere Zielverzeichnisse

Symptom

Klonen fehlgeschlagen: Zielordner ist nicht leer

oder Repository wird nicht erkannt.

Ursache

Der Installer erlaubt die Auswahl eines existierenden, nicht-leeren Zielordners, in den anschließend ein git clone erfolgen soll. Git verhindert dies korrekt.

Verbesserungsvorschlag

Vor dem Klonen prüfen:

existiert der Ordner?

ist er leer oder enthält er ein .git-Verzeichnis?


Andernfalls klare Fehlermeldung anzeigen:

> „Zielordner muss leer sein oder ein bestehendes Git-Repository enthalten.“





---

3. Fehlende Vorab-Prüfung belegter Ports

Symptom

Bind for 0.0.0.0:8001 failed: port is already allocated

Ursache

Ports werden im docker-compose.yml fest vergeben, z. B.:

ChromaDB: 8001

Backend: 8000

Frontend: 3000

Ollama: 11434

Portainer: 9443


Der Installer prüft nicht, ob diese Ports bereits durch andere Container oder lokale Dienste belegt sind.

Lösung / Empfehlung

Vor Deployment Port-Check durchführen

Alternativ: Ports über .env konfigurierbar machen, z. B.:


CHROMADB_PORT=8001
BACKEND_PORT=8000


---

4. GPU-Nutzung: falsche Docker-Compose-Syntax

Symptom

could not select device driver "nvidia" with capabilities: [[gpu]]

Ursache

Im docker-compose.yml wird GPU-Zugriff über

deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia

konfiguriert.

Dieser Block ist Docker Swarm spezifisch und wird von docker-compose (non-Swarm) ignoriert.

Korrekte Lösung für docker-compose

device_requests:
  - driver: nvidia
    count: 1
    capabilities: [gpu]

Hinweis

deploy: sollte entfernt oder explizit als „Swarm only“ dokumentiert werden.



---

5. GPU-Voraussetzungen nicht ausreichend dokumentiert

Symptom

nvidia-smi zeigt „No devices were found“

nvidia-container-toolkit ist nicht installierbar

Docker meldet keinen GPU-Driver


Ursache

GPU-Nutzung setzt zwingend voraus:

physisch vorhandene NVIDIA-GPU

installierter NVIDIA-Treiber

aktiver Kernel-Modul-Load

NVIDIA Container Runtime


Diese Voraussetzungen waren nicht klar dokumentiert.

Empfohlene Checks

lspci | grep NVIDIA
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi


---

6. Port-Konflikte zwischen Demo- und Produktiv-Stacks

Symptom

Unklare Fehler beim Start einzelner Services, insbesondere:

ChromaDB

Backend

Demo-Stacks parallel zum Hauptsystem


Ursache

Mehrere Stacks nutzen identische Ports ohne Namensraum oder Isolation.

Empfehlung

Demo-Stacks vor Produktivstart stoppen

oder Ports konsequent trennen

oder separate Docker-Netzwerke verwenden



---

7. Fehlermeldungen teilweise nicht ursachennah

Beobachtung

Mehrere Fehler (GPU, Ports, YAML) äußern sich erst spät beim docker-compose up, obwohl sie vorab prüfbar wären.

Verbesserungspotenzial

Preflight-Checks im Installer:

Ports

GPU-Verfügbarkeit

Docker-Version


Klarere UX-Hinweise bei Abbruch



---

Status

Diese Issues wurden im Rahmen eines realen Installations- und Debugging-Prozesses identifiziert und dokumentiert.

Ein Teil der Probleme ist durch:

saubere Dokumentation

robustere Installer-Logik

geringfügige Compose-Anpassungen


dauerhaft vermeidbar.

der  Installer (und/oder ein begleitendes Setup-Skript) soll  prüfen und dann automatisiert einrichten kann:

NVIDIA-Treiber + GPU-Tools (nur wenn GPU vorhanden)

NVIDIA Container Runtime für Docker (nvidia-container-toolkit)

Docker/Compose-Prüfungen

Ollama (als Container) + automatischer Modell-Pull des ausgewählten LLM

Sicherheits- und Härtungsmaßnahmen (Ports, Least-Privilege, Secrets, Logs)


Ich schreibe das bewusst so, dass du es 1:1 als Implementations-Spezifikation für dein Repo übernehmen kannst (z. B. docs/NUC_GPU_SETUP.md + Installer-Preflight).


---

1) Sicherheitsprinzipien für einen „rundum sicheren“ Installer

1.1 Grundregeln

1. Niemals blind installieren. Immer erst prüfen:

GPU vorhanden?

Treiber aktiv?

Docker vorhanden?

Ports frei?

Internetverbindung ok?



2. Keine Root-Dauerrechte.

Installer läuft als normaler User.

Für Systemschritte (Treiber/Toolkit) gezielt sudo pro Kommando.



3. Idempotent (wiederholbar):

Wiederholtes Ausführen darf nichts zerstören, sondern nur reparieren/ergänzen.



4. Fail fast + klare Meldungen:

Wenn GPU nicht korrekt verfügbar ist, nicht „irgendwie weiter“, sondern klar: „GPU nicht aktiv – Setup erforderlich“.




1.2 Trennung von Bereichen

Systemebene: Treiber, Toolkit, Docker Service

Applikationsebene: Compose-Stack (db/redis/chroma/backend/frontend/ollama)

Modellebene: Ollama-Models (Pull, Cache, Versionierung)



---

2) Preflight-Checks: Was der Installer zwingend prüfen muss

2.1 Hardware/GPU vorhanden?

Check:

lspci | grep -Ei "nvidia|3d|vga"

Wenn keine NVIDIA-Zeile: GPU-Setup überspringen und klar informieren (kein CUDA möglich).


2.2 NVIDIA-Treiber aktiv?

Check:

command -v nvidia-smi

nvidia-smi Exit-Code == 0 und Ausgabe enthält GPU-Tabelle


Wenn nicht ok:

Installer muss Treiberinstallation anbieten/ausführen (siehe Abschnitt 3).


2.3 Docker + Compose vorhanden?

Check:

docker --version

docker compose version (Compose v2)

Optional: Fallback docker-compose --version (Compose v1 – lieber vermeiden)


Wenn nicht ok:

Docker Engine installieren (dein Repo/Guide hat das vermutlich schon; hier nur als Pflichtpunkt).


2.4 NVIDIA Container Runtime verfügbar?

Check:

dpkg -l | grep -E "nvidia-container-toolkit|libnvidia-container"

docker info | grep -i nvidia (kann leer sein, je nach Setup)

Härtetest:
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi


Wenn dieser Test fehlschlägt: Toolkit installieren und Docker neu starten.

2.5 Port-Kollisionen

Der Installer muss die Ports der Services prüfen (z. B.):

Frontend: 3000 (oder 80/443)

Backend: 8000

ChromaDB: 8001 (bei dir war das ein echter Konflikt!)

Ollama: 11434

Portainer: 9443


Check:

ss -tulpn und prüfen, ob gewünschter Port bereits LISTEN ist.


Wenn belegt:

Entweder automatisch alternative Ports vorschlagen (z. B. 8003 statt 8001),

oder Blocker identifizieren und Abbruch mit Hinweis.



---

3) Automatische Installation: NVIDIA-Treiber + Toolkit (sicher & robust)

> Wichtig: Das ist Host-/Systemebene. Der Installer muss das sauber kapseln und nur ausführen, wenn GPU vorhanden ist.



3.1 Treiberempfehlung ermitteln

ubuntu-drivers devices

Den recommended Treiber wählen (bei dir: nvidia-driver-580-open)


3.2 Nouveau (Open-Source-Treiber) deaktivieren (wenn nötig)

Sicherheits-/Stabilitätsgründe: vermeidet Konflikte.

Datei /etc/modprobe.d/blacklist-nouveau.conf setzen:

blacklist nouveau

options nouveau modeset=0


sudo update-initramfs -u

Reboot erforderlich


Der Installer sollte:

die Änderung nur setzen, wenn nouveau aktiv ist (optional Check: lsmod | grep nouveau)

und dem Nutzer klar sagen: „Neustart erforderlich“.


3.3 Treiber installieren

Beispiel (konkret für dein System):

sudo apt update

sudo apt install -y nvidia-driver-580-open

sudo reboot


Nach Reboot: nvidia-smi muss funktionieren, sonst abbrechen.

3.4 NVIDIA Container Toolkit installieren

Auf manchen Systemen ist das nicht in Standardquellen. Deshalb:

NVIDIA Repo/Key einrichten (offizieller Weg)

sudo apt update

sudo apt install -y nvidia-container-toolkit

sudo nvidia-ctk runtime configure --runtime=docker

sudo systemctl restart docker


Verifikation (Pflicht):

docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi


Wenn das nicht geht: Installer bricht ab und zeigt Diagnosepfad (Logs, Treiberstatus).


---

4) Compose-Stack GPU-sicher konfigurieren

4.1 Wichtig: deploy: ist Swarm, nicht Compose

Du hattest deploy.resources.reservations.devices im Compose – das wird bei normalem docker-compose häufig ignoriert.

Für docker-compose sollte Ollama so GPU bekommen:

ollama:
  image: ollama/ollama:latest
  container_name: flowaudit-ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  environment:
    - OLLAMA_HOST=0.0.0.0
  device_requests:
    - driver: nvidia
      count: 1
      capabilities: [gpu]
  restart: unless-stopped

4.2 Port-Konflikte vermeiden (dein 8001-Fall)

Mach Ports über .env steuerbar:

FRONTEND_PORT=3000
BACKEND_PORT=8000
CHROMADB_PORT=8001
OLLAMA_PORT=11434

Compose:

chromadb:
  ports:
    - "${CHROMADB_PORT}:8000"

Installer: wenn Port belegt → .env automatisch auf freien Port ändern.


---

5) Ollama „installieren“ und ausgewähltes LLM automatisch pullen

Du nutzt Ollama als Container – „installieren“ heißt dann:

1. Compose-Service ollama starten


2. Healthcheck abwarten


3. Modell pullen


4. Optional: „Warmup“ (ein kurzer Prompt), um Build/Cache anzustoßen



5.1 Start + Readiness

docker compose up -d ollama

Polling:

curl -fsS http://localhost:11434/api/tags bis erfolgreich



5.2 Modell-Pull (ausgewähltes LLM)

Du definierst im Installer eine Dropdown-Auswahl (z. B. llama3.1:8b, mistral, qwen2.5, …).

Dann ausführen:

docker exec -i flowaudit-ollama ollama pull <MODEL>

Beispiele:

ollama pull llama3.1:8b

ollama pull qwen2.5:14b


5.3 Modell-Versionierung & Reproduzierbarkeit

Für „rundum sicher“ solltest du im Repo/Installer speichern:

gewähltes Modell (Name + Tag)

Datum/Hash (soweit Ollama das liefert)

ggf. Mindest-VRAM-Empfehlung


In .env:

OLLAMA_MODEL=llama3.1:8b


---

6) Sicherheitshärtung für Betrieb (wichtig)

6.1 Exponierte Ports minimieren

Wenn Frontend und Backend nur lokal gebraucht werden:

nur 127.0.0.1:PORT:... binden

oder über Reverse Proxy (Traefik/Nginx) und nur 443 öffnen


Beispiel:

ports:
  - "127.0.0.1:${OLLAMA_PORT}:11434"

6.2 Secrets nicht hardcoden

.env automatisch generieren: starke Passwörter (Postgres, Admin, JWT)

keine Secrets im Git


6.3 Least Privilege

Container möglichst als non-root (wo möglich)

read-only mounts für Config

restart: unless-stopped


6.4 Logging/Audit

Installer schreibt installer.log

Compose Logs: Rotationsstrategie (json-file mit max-size/max-file) oder zentral (optional)


6.5 Integritätschecks

Installer kann die wichtigsten Dateien vor Start validieren:

docker-compose config muss fehlerfrei laufen

Verbotene Muster (z. B. """ in YAML/Dockerfile) scannen:

grep -RIn '"""' und dann Abbruch mit Hinweis





---

7) Konkretes Vorgehensmodell für deinen Installer

Phase A – Preflight

1. OS erkannt (Ubuntu Desktop)


2. Docker vorhanden?


3. GPU vorhanden?


4. Treiber aktiv?


5. Toolkit aktiv?


6. Ports frei?


7. Compose-Dateien valide? (docker compose config)



Phase B – System Setup (nur wenn nötig)

Treiber installieren → reboot

Toolkit installieren → docker restart

GPU-Testcontainer laufen lassen


Phase C – App Deploy

.env erzeugen

docker compose up -d --build


Phase D – Ollama + Model

Ollama health ok

ollama pull $MODEL

optional: kurzer Warmup


Phase E – Abschlussreport

Links:

Frontend URL

Backend URL

Ollama URL


Statusübersicht

Export „Systemreport“ (Textdatei mit Checks und Versionen)



---

8) Wo es bei dir bislang gehakt hat (als Lessons Learned)

Das sollte der Installer künftig verhindern:

1. """ in YAML/Dockerfiles → Preflight Scan + harte Fehlermeldung


2. Port 8001 belegt → Port-Check + Auto-Port-Shift


3. GPU nicht aktiv (Treiber/Toolkit fehlten) → GPU-Preflight + Auto-Install + Testcontainer


4. deploy: statt compose GPU → Compose-konforme GPU config verwenden