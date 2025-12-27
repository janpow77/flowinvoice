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
- [x] Settings-UI zeigt drei neue Felder: max_examples (Slider), same_document_type (Toggle), same_ruleset (Toggle)
- [x] Änderungen werden via API an Backend übermittelt
- [x] Backend speichert und verwendet die Parameter
- [x] TypeScript kompiliert ohne Fehler (`npx tsc --noEmit`)
- [x] Keine Regressionen in bestehenden RAG-Settings

**Status:** ✅ Erledigt - Commit `feat: Add RAG restriction settings to UI`

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
- [x] Import von `useTranslation` aus `react-i18next` vorhanden
- [x] Alle deutschen Hardcoded-Strings durch `t('documentDetail.xxx')` ersetzt
- [x] Übersetzungen in `de.ts` und `en.ts` vorhanden
- [x] Sprachwechsel DE/EN funktioniert auf der Seite
- [x] TypeScript kompiliert ohne Fehler (`npx tsc --noEmit`)
- [x] Keine Regressionen in Dokumenten-Funktionalität

**Status:** ✅ Erledigt - Commit `feat: Connect DocumentDetail.tsx with i18n translations`

---

## 3. Installer Preflight-Checks

**Dateien:**
- `docker/installer.sh` (neu)

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
- [x] `installer.sh` prüft Docker und Docker Compose Versionen
- [x] RAM-Check (minimum 16GB)
- [x] Disk-Check (minimum 20GB)
- [x] GPU-Check: NVIDIA-Erkennung und nvidia-container-toolkit
- [x] Docker-Check: `docker version` und `docker compose version`
- [x] Alle Checks liefern Exit-Code 0 bei Erfolg, 1 bei Fehler
- [x] Keine Regressionen im bestehenden Installer-Flow

**Status:** ✅ Erledigt - Commit `feat: Add installer script with preflight checks`

---

## 4. Installer GPU-Auto-Setup

**Dateien:**
- `docker/installer.sh` (erweitert mit --setup-gpu)

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
- [x] Skript erkennt ob GPU vorhanden aber Treiber fehlt
- [x] Automatische Treiberinstallation mit `ubuntu-drivers` oder nvidia-driver-535
- [x] Container-Toolkit wird installiert und konfiguriert via nvidia-ctk
- [x] Reboot-Hinweis wird angezeigt wenn nötig
- [x] Skript ist idempotent (wiederholbar ohne Schaden)
- [x] Keine Regressionen bei Systemen ohne GPU

**Status:** ✅ Erledigt - Commit `feat: Add GPU auto-setup to installer script`

---

## 5. Installer Secrets-Generierung

**Dateien:**
- `docker/installer.sh` (erweitert mit --generate-secrets)
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
- [x] Installer generiert Secrets mit `openssl rand -hex`
- [x] SECRET_KEY: 64-Zeichen Hex-String generiert
- [x] POSTGRES_PASSWORD: 32-Zeichen Hex-String generiert
- [x] CHROMA_TOKEN: 32-Zeichen Hex-String generiert
- [x] DEMO_USERS wird auf leer gesetzt
- [x] DEBUG wird auf false gesetzt
- [x] Backup der bestehenden stack.env wird erstellt
- [x] Keine Regressionen bei manueller Secret-Konfiguration

**Status:** ✅ Erledigt - Commit `feat: Add secrets generation to installer script`

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
- [x] Compose-Dateien verwenden `${FRONTEND_PORT:-3000}` Syntax
- [x] Alle Ports sind konfigurierbar (FRONTEND, BACKEND, CHROMADB, POSTGRES, REDIS, OLLAMA)
- [x] Default-Werte funktionieren ohne `.env`
- [x] Dokumentation in `stack.env` hinzugefügt
- [x] Stack startet mit Custom-Ports korrekt
- [x] Keine Regressionen bei Standard-Port-Konfiguration

**Status:** ✅ Erledigt (bereits implementiert) - Commit `docs: Document configurable ports in stack.env`

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
- [x] `TextChunker` Klasse mit `chunk_text()` Methode
- [x] Drei Chunking-Strategien implementiert (fixed, paragraph, semantic)
- [x] `ChunkingConfig` Dataclass mit chunk_size_tokens, chunk_overlap_tokens, max_chunks, strategy
- [x] `TextChunk` Dataclass mit Metadaten (index, total_chunks, start_char, end_char, token_count)
- [x] Keine Regressionen in bestehender RAG-Funktionalität

**Status:** ✅ Erledigt (bereits implementiert in `backend/app/services/chunking.py`)

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
- [x] `add_invoice_example()` akzeptiert Chunking-Config Parameter
- [x] `_add_invoice_chunks()` Methode für granulare Chunk-Speicherung
- [x] Chunks werden mit Metadaten in ChromaDB gespeichert (parent_document_id, chunk_index, total_chunks, etc.)
- [x] `find_similar_chunks()` sucht auf Chunk-Level
- [x] Bestehende RAG-Funktionalität bleibt kompatibel (Fallback ohne Chunking)
- [x] Keine Performance-Regression bei Chunk-basierter Suche

**Status:** ✅ Erledigt (bereits implementiert in `backend/app/rag/vectorstore.py`)

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
- [x] API-Funktionen in `api.ts`: `getDocumentTypes()`, `createDocumentType()`, `updateDocumentType()`, `deleteDocumentType()`
- [x] Component verwendet `useQuery` für Laden
- [x] Component verwendet `useMutation` für Speichern
- [x] Loading- und Error-States werden angezeigt
- [x] Chunking-Einstellungen pro Dokumenttyp konfigurierbar (chunk_size, overlap, max_chunks, strategy)
- [x] TypeScript kompiliert ohne Fehler
- [x] Keine Regressionen in Settings-UI

**Status:** ✅ Erledigt (bereits implementiert in `frontend/src/components/settings/SettingsDocumentTypes.tsx`)

---

## 10. Semantic-Analyse Timeout testen

**Dateien:**
- Keine Code-Änderungen, nur Test

**Ausgangszustand:**
Ollama-Timeout wurde von 120s auf 300s erhöht (Commit `9935717`). Die Änderung wurde noch nicht mit einer echten Analyse getestet. Zuvor schlug die Analyse nach 120s mit "Analyse fehlgeschlagen" fehl.

**Zielzustand:**
Eine Dokument-Analyse wird erfolgreich durchgeführt ohne Timeout-Fehler. Das Analyse-Ergebnis enthält valide Daten mit `output_tokens > 0`.

**Akzeptanzkriterien:**
- [x] OLLAMA_TIMEOUT auf 600 Sekunden gesetzt (Commit `9935717`)
- [x] Dokument erfolgreich geparst (Status: VALIDATED)
- [x] Analyse erfolgreich gestartet (Status: ANALYZING)
- [x] Analyse erfolgreich abgeschlossen (Status: ANALYZED)
- [x] `latency_ms` = 142022 ms (2.4 min < 600s Limit)
- [x] `output_tokens` = 299 (> 0 ✓)
- [x] Kein Timeout-Fehler

**Status:** ✅ Erledigt - Test am 2025-12-27 erfolgreich

**Testdetails:**
- Dokument: INV-2025-0004.pdf (a6125c2e-cba1-43cd-8b6a-26c2a1bcb769)
- Provider: LOCAL_OLLAMA (llama3.1:8b)
- Overall Assessment: ok (Confidence: 80%)
- Latenz: 142 Sekunden (weit unter 600s Limit)

---

## Abgeschlossene Aufgaben

| Aufgabe | Commit |
|---------|--------|
| RAG-Einschränkungen im UI | `feat: Add RAG restriction settings to UI` |
| DocumentDetail.tsx mit i18n verbinden | `feat: Connect DocumentDetail.tsx with i18n translations` |
| Installer Preflight-Checks | `feat: Add installer script with preflight checks` |
| Installer GPU-Auto-Setup | `feat: Add GPU auto-setup to installer script` |
| Installer Secrets-Generierung | `feat: Add secrets generation to installer script` |
| Konfigurierbare Ports | `docs: Document configurable ports in stack.env` |
| Chunking-Service Backend | (bereits implementiert) |
| Chunking RAG-Integration | (bereits implementiert) |
| Chunking Frontend-Anbindung | (bereits implementiert) |
| Ollama Timeout auf 600s erhöht | `9935717` |
| Semantic-Analyse Timeout Test | ✅ Test erfolgreich (2025-12-27) |
| CheckersSettings.tsx mit i18n verbunden | `9935717` |
| improvement_plan.md aktualisiert | `9935717` |
| Grant Purpose Schema/Checker | (frühere Commits) |
| Conflict Resolution | (frühere Commits) |
| Risikomodul | (frühere Commits) |
| UI-Komponenten für neue Prüfungen | `1c4f5f9` |
| i18n Übersetzungen für Checker | `7d23f91` |
