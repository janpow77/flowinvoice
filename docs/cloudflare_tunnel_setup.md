# Cloudflare Tunnel Setup für FlowAudit

Diese Anleitung beschreibt, wie FlowAudit sicher über das Internet via Cloudflare Tunnel zugänglich gemacht wird.

## Voraussetzungen

- Cloudflare-Account (kostenlos)
- Domain (bei Cloudflare registriert oder DNS dorthin umgeleitet)
- Linux-Server mit Docker

## 1. Lokaler Netzwerkzugang (LAN)

Die Anwendung ist bereits für LAN-Zugang konfiguriert:

```typescript
// vite.config.ts
server: {
  host: '0.0.0.0',  // Lauscht auf allen Interfaces
  port: 3000,
}
```

### Zugriff im LAN

```bash
# Server-IP ermitteln
ip addr show | grep "inet " | grep -v 127.0.0.1

# Beispiel: http://192.168.1.100:3000
```

### Firewall-Regeln (Ubuntu/Debian)

```bash
# Frontend-Port öffnen
sudo ufw allow 3000/tcp comment 'FlowAudit Frontend'

# Backend-Port (optional)
sudo ufw allow 8000/tcp comment 'FlowAudit API'

# Status prüfen
sudo ufw status
```

---

## 2. Cloudflare Tunnel Installation

### 2.1 cloudflared installieren

```bash
# Debian/Ubuntu
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Arch Linux
yay -S cloudflared

# macOS
brew install cloudflared
```

### 2.2 Mit Cloudflare authentifizieren

```bash
cloudflared tunnel login
```

Dies öffnet einen Browser zur Authentifizierung. Nach erfolgreicher Anmeldung wird ein Zertifikat unter `~/.cloudflared/` gespeichert.

### 2.3 Tunnel erstellen

```bash
# Tunnel erstellen
cloudflared tunnel create flowaudit

# Ausgabe enthält Tunnel-ID (z.B. abc123-def456-...)
# Diese ID notieren!

# Tunnel-Liste anzeigen
cloudflared tunnel list
```

---

## 3. Tunnel-Konfiguration

### 3.1 Konfigurationsdatei erstellen

```bash
mkdir -p /home/user/flowinvoice/deploy/cloudflared
```

Datei `deploy/cloudflared/config.yml` erstellen:

```yaml
# Cloudflare Tunnel Konfiguration für FlowAudit
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  # Frontend (Haupt-Domain)
  - hostname: flowaudit.example.com
    service: http://localhost:3000
    originRequest:
      noTLSVerify: true

  # API (optional - für direkten API-Zugang)
  - hostname: api.flowaudit.example.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true

  # Catch-all (erforderlich)
  - service: http_status:404
```

**Wichtig:** `<TUNNEL_ID>` durch die echte Tunnel-ID ersetzen!

### 3.2 DNS-Route erstellen

```bash
# DNS-Eintrag für Frontend
cloudflared tunnel route dns flowaudit flowaudit.example.com

# DNS-Eintrag für API (optional)
cloudflared tunnel route dns flowaudit api.flowaudit.example.com
```

---

## 4. Tunnel starten

### 4.1 Manueller Start (Test)

```bash
cloudflared tunnel --config deploy/cloudflared/config.yml run flowaudit
```

### 4.2 Als systemd-Service

```bash
# Service installieren
sudo cloudflared service install

# Service starten
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Status prüfen
sudo systemctl status cloudflared
```

### 4.3 Docker Compose Integration

Füge zu `docker-compose.yml` hinzu:

```yaml
services:
  # ... bestehende Services ...

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: flowaudit-tunnel
    command: tunnel --config /etc/cloudflared/config.yml run
    volumes:
      - ./deploy/cloudflared/config.yml:/etc/cloudflared/config.yml:ro
      - ${HOME}/.cloudflared:/root/.cloudflared:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - flowaudit-network
```

---

## 5. Sicherheit mit Cloudflare Access

### 5.1 Access-Anwendung erstellen

1. Cloudflare Zero Trust Dashboard öffnen: https://one.dash.cloudflare.com/
2. Access > Applications > Add an Application
3. Self-hosted auswählen

### 5.2 Application konfigurieren

```
Application name: FlowAudit
Session Duration: 24 hours
Application domain: flowaudit.example.com
```

### 5.3 Policy erstellen

```yaml
Policy name: Allowed Users
Action: Allow

Include rules (eine oder mehrere):
  # Option A: E-Mail-Domain
  - Selector: Emails ending in
    Value: @example.com

  # Option B: Einzelne E-Mails
  - Selector: Emails
    Value: user1@example.com, user2@example.com

  # Option C: One-time PIN (für Gäste)
  - Selector: One-time PIN
```

---

## 6. Troubleshooting

### Tunnel-Status prüfen

```bash
# Lokaler Status
cloudflared tunnel info flowaudit

# Im Cloudflare Dashboard
# Zero Trust > Networks > Tunnels
```

### Logs anzeigen

```bash
# systemd
journalctl -u cloudflared -f

# Docker
docker logs -f flowaudit-tunnel
```

### Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `failed to connect to origin` | Backend/Frontend läuft nicht |
| `unable to reach the origin service` | Firewall blockiert lokalen Port |
| `certificate error` | `cloudflared tunnel login` erneut ausführen |
| `tunnel not found` | Tunnel-ID in config.yml prüfen |

---

## 7. Produktions-Checkliste

- [ ] Cloudflare Access aktiviert
- [ ] HTTPS-only im Dashboard aktiviert
- [ ] Rate Limiting konfiguriert
- [ ] WAF-Regeln aktiviert (optional)
- [ ] Backup der Credentials (`~/.cloudflared/*.json`)
- [ ] Monitoring eingerichtet

---

## 8. Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INTERNET                                    │
│                              │                                       │
│                    flowaudit.example.com                             │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │  Cloudflare Edge  │                            │
│                    │   (TLS, WAF, ...)  │                            │
│                    └─────────┬─────────┘                            │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │ Cloudflare Access │                            │
│                    │  (Authentication) │                            │
│                    └─────────┬─────────┘                            │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ Encrypted Tunnel
┌──────────────────────────────┼──────────────────────────────────────┐
│  LOCAL NETWORK               │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │    cloudflared    │                            │
│                    │   (Tunnel Agent)  │                            │
│                    └─────────┬─────────┘                            │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              │               │               │                      │
│       ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐              │
│       │   Frontend  │ │   Backend   │ │   ChromaDB  │              │
│       │  (Vite/React)│ │  (FastAPI)  │ │    (RAG)    │              │
│       │   :3000     │ │   :8000     │ │   :8001     │              │
│       └─────────────┘ └─────────────┘ └─────────────┘              │
│                                                                      │
│                         SERVER (192.168.x.x)                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Weiterführende Links

- [Cloudflare Tunnel Dokumentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Access Dokumentation](https://developers.cloudflare.com/cloudflare-one/policies/access/)
- [Zero Trust Dashboard](https://one.dash.cloudflare.com/)
