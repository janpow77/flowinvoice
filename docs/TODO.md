# FlowAudit TODO Liste

Strukturierte Aufgabenliste mit Ausgangs-/Zielzustand und Akzeptanzkriterien.

---

## 1. RAG-Einschränkungen im UI

**Dateien:**
- `frontend/src/components/settings/SettingsRAG.tsx`
- `backend/app/api/settings.py`
- `frontend/src/lib/i18n/de.ts`
- `frontend/src/lib/i18n/en.ts`

**Ausgangszustand:**
Die RAG-Einschränkungen (max. 3 Beispiele, gleicher Dokumenttyp, gleiches Ruleset) sind im Backend implementiert. Das Frontend zeigt die RAG-Settings zwar an, aber die Einschränkungs-Parameter (`max_examples`, `same_document_type`, `same_ruleset`) sind nicht konfigurierbar. Der Hinweis "Dieses Beispiel stammt aus einem früheren Vergleichsfall" wird in Analyse-Ergebnissen nicht angezeigt.

**Zielzustand:**
Im Settings-Bereich können Benutzer die RAG-Parameter konfigurieren:
- Maximale Anzahl Beispiele (1-5)
- Toggle: Nur gleicher Dokumenttyp
- Toggle: Nur gleiches Ruleset

Die Einstellungen werden an das Backend übermittelt und bei der Analyse berücksichtigt. In den Analyse-Ergebnissen wird bei RAG-Nutzung ein Hinweis angezeigt.

**Akzeptanzkriterien:**
- [ ] Settings-UI zeigt drei neue Felder: max_examples (Slider), same_document_type (Toggle), same_ruleset (Toggle)
- [ ] Änderungen werden via API an Backend übermittelt
- [ ] Backend speichert und verwendet die Parameter
- [ ] TypeScript kompiliert ohne Fehler (`npx tsc --noEmit`)
- [ ] Keine Regressionen in bestehenden RAG-Settings

**Nach Abschluss:** Commit mit `feat: Add RAG restriction settings to UI`

---

## 2. DocumentDetail.tsx mit i18n verbinden

**Dateien:**
- `frontend/src/pages/DocumentDetail.tsx`
- `frontend/src/lib/i18n/de.ts`
- `frontend/src/lib/i18n/en.ts`

**Ausgangszustand:**
Die DocumentDetail-Seite enthält hardcodierte deutsche Texte wie "Dokument-Details", "Analyse starten", "Status", "Ergebnis", etc. Bei Sprachwechsel auf Englisch bleiben diese Texte deutsch.

**Zielzustand:**
Alle UI-Texte in DocumentDetail.tsx nutzen das i18n-System. Bei Sprachwechsel werden alle Texte korrekt übersetzt. Die Übersetzungsschlüssel folgen dem Schema `documentDetail.xxx`.

**Akzeptanzkriterien:**
- [ ] Import von `useTranslation` aus `react-i18next` vorhanden
- [ ] Alle deutschen Hardcoded-Strings durch `t('documentDetail.xxx')` ersetzt
- [ ] Übersetzungen in `de.ts` und `en.ts` vorhanden
- [ ] Sprachwechsel DE/EN funktioniert auf der Seite
- [ ] TypeScript kompiliert ohne Fehler (`npx tsc --noEmit`)
- [ ] Keine Regressionen in Dokumenten-Funktionalität

**Nach Abschluss:** Commit mit `feat: Connect DocumentDetail page with i18n`

---

## 3. Installer Preflight-Checks

**Dateien:**
- `scripts/install.sh` (erweitern)
- `scripts/preflight.sh` (neu)

**Ausgangszustand:**
Der Installer prüft vor dem Deployment nicht, ob:
- Erforderliche Ports frei sind (3000, 8000, 8001, 11434)
- Das Zielverzeichnis leer ist oder ein Git-Repo enthält
- Docker und Docker Compose installiert sind
- GPU-Treiber und NVIDIA Container Toolkit vorhanden sind

Bei Problemen schlägt `docker compose up` mit kryptischen Fehlern fehl.

**Zielzustand:**
Vor dem Deployment führt der Installer automatisch Preflight-Checks durch:
- Port-Verfügbarkeit wird geprüft, bei Konflikt Warnung mit Alternative
- Zielverzeichnis wird validiert
- Docker-Installation wird verifiziert
- GPU-Status wird erkannt und gemeldet

Bei Fehlern wird eine klare Fehlermeldung mit Lösungsvorschlag angezeigt.

**Akzeptanzkriterien:**
- [ ] `preflight.sh` prüft Ports 3000, 8000, 8001, 11434 mit `ss -tulpn`
- [ ] Bei belegtem Port: Klare Meldung welcher Dienst den Port belegt
- [ ] Zielverzeichnis-Check: leer oder `.git` vorhanden
- [ ] Docker-Check: `docker --version` und `docker compose version`
- [ ] GPU-Check: `lspci | grep NVIDIA` und `nvidia-smi`
- [ ] Alle Checks liefern Exit-Code 0 bei Erfolg, 1 bei Fehler
- [ ] Installer ruft `preflight.sh` vor Deployment auf
- [ ] Keine Regressionen im bestehenden Installer-Flow

**Nach Abschluss:** Commit mit `feat: Add installer preflight checks`

---

## 4. Installer GPU-Auto-Setup

**Dateien:**
- `scripts/gpu-setup.sh` (neu)
- `scripts/install.sh`

**Ausgangszustand:**
Wenn GPU vorhanden aber Treiber/Toolkit fehlen, schlägt der Ollama-Container mit GPU-Fehlern fehl. Benutzer müssen manuell NVIDIA-Treiber und Container-Toolkit installieren.

**Zielzustand:**
Der Installer erkennt fehlende GPU-Komponenten und bietet automatische Installation an:
1. NVIDIA-Treiber installieren (empfohlene Version via `ubuntu-drivers`)
2. Nouveau-Treiber blacklisten
3. NVIDIA Container Toolkit installieren
4. Docker-Service neustarten
5. GPU-Test mit Container durchführen

**Akzeptanzkriterien:**
- [ ] Skript erkennt ob GPU vorhanden aber Treiber fehlt
- [ ] Automatische Treiberinstallation mit `ubuntu-drivers`
- [ ] Nouveau wird in `/etc/modprobe.d/blacklist-nouveau.conf` geblacklisted
- [ ] Container-Toolkit wird installiert und konfiguriert
- [ ] Test-Container `nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi` läuft erfolgreich
- [ ] Reboot-Hinweis wird angezeigt wenn nötig
- [ ] Skript ist idempotent (wiederholbar ohne Schaden)
- [ ] Keine Regressionen bei Systemen ohne GPU

**Nach Abschluss:** Commit mit `feat: Add automatic GPU driver and toolkit setup`

---

## 5. Installer Secrets-Generierung

**Dateien:**
- `scripts/install.sh`
- `docker/stack.env.template` (neu)
- `docker/stack.env`

**Ausgangszustand:**
Die `stack.env` enthält Default-Werte für Secrets (`flowaudit_secret`, `flowaudit_chroma_token`). Bei Installation werden diese unsicheren Defaults verwendet. Benutzer müssen manuell sichere Werte setzen.

**Zielzustand:**
Der Installer generiert automatisch sichere Secrets:
- `SECRET_KEY`: 64-Zeichen Hex-String
- `POSTGRES_PASSWORD`: 32-Zeichen Hex-String
- `CHROMA_TOKEN`: 32-Zeichen Hex-String
- `ADMIN_API_KEY`: 32-Zeichen Hex-String

Die generierten Werte werden in `stack.env` geschrieben.

**Akzeptanzkriterien:**
- [ ] Template-Datei `stack.env.template` mit Platzhaltern existiert
- [ ] Installer generiert Secrets mit `openssl rand -hex`
- [ ] Generierte `stack.env` enthält keine Default-Werte
- [ ] Backend startet ohne Sicherheitswarnungen
- [ ] `settings.is_production_ready` gibt `True` zurück
- [ ] Keine Regressionen bei manueller Secret-Konfiguration

**Nach Abschluss:** Commit mit `feat: Auto-generate secure secrets during installation`

---

## 6. Konfigurierbare Ports

**Dateien:**
- `docker/docker-compose.yml`
- `docker/docker-compose.portainer.yml`
- `docker/stack.env`
- `docs/ENV_VARIABLES.md`

**Ausgangszustand:**
Ports sind in den Compose-Dateien hardcodiert (3000, 8000, 8001, 11434). Bei Port-Konflikten muss der Benutzer manuell die Compose-Dateien editieren.

**Zielzustand:**
Alle externen Ports sind über Umgebungsvariablen konfigurierbar:
- `FRONTEND_PORT` (default: 3000)
- `BACKEND_PORT` (default: 8000)
- `CHROMADB_PORT` (default: 8001)
- `OLLAMA_PORT` (default: 11434)

Bei Port-Konflikt kann der Installer automatisch auf freie Ports wechseln.

**Akzeptanzkriterien:**
- [ ] Compose-Dateien verwenden `${FRONTEND_PORT:-3000}` Syntax
- [ ] Alle vier Ports sind konfigurierbar
- [ ] Default-Werte funktionieren ohne `.env`
- [ ] Dokumentation in `ENV_VARIABLES.md` aktualisiert
- [ ] Stack startet mit Custom-Ports korrekt
- [ ] Keine Regressionen bei Standard-Port-Konfiguration

**Nach Abschluss:** Commit mit `feat: Make service ports configurable via environment`

---

## 7. Chunking-Service Backend

**Dateien:**
- `backend/app/services/chunking.py` (neu)
- `backend/app/models/document_type.py` (neu)
- `backend/app/schemas/document_type.py` (neu)
- `backend/app/api/document_types.py` (neu)
- `backend/app/models/__init__.py`
- `backend/app/main.py`
- `alembic/versions/xxx_add_document_type_settings.py` (neu)

**Ausgangszustand:**
Das RAG-System verwendet nur die ersten 2000 Zeichen des Dokument-Textes. Es gibt kein Text-Chunking und keine Dokumenttyp-spezifischen Einstellungen. Die Frontend-Dokumenttyp-Einstellungen speichern nur in localStorage.

**Zielzustand:**
Ein Chunking-Service teilt Texte in konfigurierbare Chunks auf:
- Strategien: `fixed` (Token-basiert), `paragraph`, `semantic` (Satzgrenzen)
- Parameter pro Dokumenttyp in Datenbank gespeichert
- API-Endpoints für CRUD von Dokumenttyp-Einstellungen
- System-Dokumenttypen (Rechnung, Kontoauszug, etc.) als Defaults

**Akzeptanzkriterien:**
- [ ] `TextChunker` Klasse mit `chunk_text()` Methode
- [ ] Drei Chunking-Strategien implementiert
- [ ] SQLAlchemy Model `DocumentTypeSettings` mit Feldern: slug, name, chunk_size, overlap, max_chunks, strategy
- [ ] Pydantic Schemas für Create/Update/Response
- [ ] API: GET/POST/PUT/DELETE `/api/settings/document-types`
- [ ] Alembic-Migration erstellt und ausgeführt
- [ ] System-Dokumenttypen werden bei Migration eingefügt
- [ ] Keine Regressionen in bestehender RAG-Funktionalität

**Nach Abschluss:** Commit mit `feat: Add text chunking service with document type settings`

---

## 8. Chunking RAG-Integration

**Dateien:**
- `backend/app/rag/vectorstore.py`
- `backend/app/rag/service.py`

**Ausgangszustand:**
RAG speichert nur den vollständigen Dokument-Text als einen Eintrag in ChromaDB. Bei langen Dokumenten geht Kontext verloren oder wird abgeschnitten.

**Zielzustand:**
RAG verwendet Chunking:
- Dokument-Text wird in Chunks aufgeteilt (gemäß Dokumenttyp-Einstellungen)
- Jeder Chunk wird separat embeddet und gespeichert
- Chunk-Metadaten: Index, Total, Parent-Document-ID
- Suche findet relevante Chunks und gruppiert nach Dokument

**Akzeptanzkriterien:**
- [ ] `add_invoice_example()` akzeptiert Chunking-Config Parameter
- [ ] Chunks werden mit Metadaten in ChromaDB gespeichert
- [ ] `get_context_for_analysis()` sucht auf Chunk-Level
- [ ] Gefundene Chunks werden nach Parent-Dokument gruppiert
- [ ] Bestehende RAG-Funktionalität bleibt kompatibel (Fallback ohne Chunking)
- [ ] Keine Performance-Regression bei Chunk-basierter Suche

**Nach Abschluss:** Commit mit `feat: Integrate chunking into RAG vectorstore`

---

## 9. Chunking Frontend-Anbindung

**Dateien:**
- `frontend/src/lib/api.ts`
- `frontend/src/components/settings/SettingsDocumentTypes.tsx`

**Ausgangszustand:**
Die Dokumenttyp-Einstellungen im Frontend speichern nur in localStorage. Änderungen gehen bei Browser-Clear verloren und sind nicht projekt-übergreifend.

**Zielzustand:**
Frontend kommuniziert mit Backend-API:
- Dokumenttypen werden via API geladen
- Änderungen werden an API übermittelt
- React Query für Caching und Invalidierung
- localStorage wird nicht mehr verwendet

**Akzeptanzkriterien:**
- [ ] API-Funktionen in `api.ts`: `getDocumentTypes()`, `createDocumentType()`, `updateDocumentType()`, `deleteDocumentType()`
- [ ] Component verwendet `useQuery` für Laden
- [ ] Component verwendet `useMutation` für Speichern
- [ ] localStorage-Code entfernt
- [ ] Loading- und Error-States werden angezeigt
- [ ] TypeScript kompiliert ohne Fehler
- [ ] Keine Regressionen in Settings-UI

**Nach Abschluss:** Commit mit `feat: Connect document type settings to backend API`

---

## 10. Semantic-Analyse Timeout testen

**Dateien:**
- Keine Code-Änderungen, nur Test

**Ausgangszustand:**
Ollama-Timeout wurde von 120s auf 300s erhöht (Commit `9935717`). Die Änderung wurde noch nicht mit einer echten Analyse getestet. Zuvor schlug die Analyse nach 120s mit "Analyse fehlgeschlagen" fehl.

**Zielzustand:**
Eine Dokument-Analyse wird erfolgreich durchgeführt ohne Timeout-Fehler. Das Analyse-Ergebnis enthält valide Daten mit `output_tokens > 0`.

**Akzeptanzkriterien:**
- [ ] Dokument erfolgreich geparst (Status: PARSED)
- [ ] Analyse erfolgreich gestartet (Status: ANALYZING)
- [ ] Analyse erfolgreich abgeschlossen (Status: ANALYZED)
- [ ] `latency_ms` < 300000 (5 Minuten)
- [ ] `output_tokens` > 0 im Analyse-Ergebnis
- [ ] Kein "Analyse fehlgeschlagen" oder Timeout-Fehler
- [ ] Keine Regressionen bei kurzen Analysen

**Test-Befehle:**
```bash
# Token holen
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=admin" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r '.access_token')

# Dokument parsen
DOC_ID="7739f8a3-cbd3-46dd-95b3-80a3ae646605"
curl -X POST "http://localhost:8000/api/documents/$DOC_ID/parse" \
  -H "Authorization: Bearer $TOKEN"

# Warten bis PARSED, dann analysieren
curl -X POST "http://localhost:8000/api/documents/$DOC_ID/analyze" \
  -H "Authorization: Bearer $TOKEN"

# Ergebnis prüfen
curl "http://localhost:8000/api/documents/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{status, analysis_result: .analysis_result | {latency_ms, output_tokens}}'
```

**Nach Abschluss:** Commit mit `test: Verify semantic analysis with increased timeout`

---

## Abgeschlossene Aufgaben

| Aufgabe | Commit |
|---------|--------|
| Ollama Timeout auf 300s erhöht | `9935717` |
| CheckersSettings.tsx mit i18n verbunden | `9935717` |
| improvement_plan.md aktualisiert | `9935717` |
| Grant Purpose Schema/Checker | (frühere Commits) |
| Conflict Resolution | (frühere Commits) |
| Risikomodul | (frühere Commits) |
| UI-Komponenten für neue Prüfungen | `1c4f5f9` |
| i18n Übersetzungen für Checker | `7d23f91` |
