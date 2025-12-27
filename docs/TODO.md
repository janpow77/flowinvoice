# FlowAudit TODO Liste

Übersicht aller offenen Aufgaben mit Erfüllungskriterien.

---

## Offene Aufgaben

### 1. RAG-Einschränkungen im UI

**Status:** In Bearbeitung
**Priorität:** Niedrig
**Quelle:** improvement_plan.md #9

**Beschreibung:**
Die RAG-Einschränkungen (max. 3 Beispiele, gleicher Dokumenttyp, gleiches Ruleset) sind im Backend implementiert, aber das UI fehlt noch.

**Erfüllungskriterien:**
- [ ] Settings-UI für RAG-Parameter erstellen
- [ ] Parameter konfigurierbar: `max_examples`, `same_document_type`, `same_ruleset`
- [ ] Settings werden an Backend-API übermittelt
- [ ] Anzeige des Hinweises "Dieses Beispiel stammt aus einem früheren Vergleichsfall" in Analyse-Ergebnissen

**Dateien:**
- `frontend/src/components/settings/SettingsRAG.tsx` (existiert bereits, erweitern)
- `backend/app/api/settings.py` (RAG-Parameter-Endpoints)

---

### 2. DocumentDetail.tsx mit i18n verbinden

**Status:** Offen
**Priorität:** Mittel

**Beschreibung:**
Die DocumentDetail-Seite enthält noch hardcodierte deutsche Texte, die mit i18n übersetzt werden müssen.

**Erfüllungskriterien:**
- [ ] Import von `useTranslation` aus `react-i18next`
- [ ] Alle deutschen Hardcoded-Strings durch `t('xxx')` ersetzen
- [ ] TypeScript kompiliert ohne Fehler (`npx tsc --noEmit`)

**Dateien:**
- `frontend/src/pages/DocumentDetail.tsx`
- `frontend/src/lib/i18n/de.ts` (ggf. Übersetzungen ergänzen)
- `frontend/src/lib/i18n/en.ts` (ggf. Übersetzungen ergänzen)

---

### 3. Installer-Verbesserungen

**Status:** Offen
**Priorität:** Hoch
**Quelle:** issues.md

**Beschreibung:**
Der Installer benötigt robustere Preflight-Checks und automatische Setup-Funktionen.

**Erfüllungskriterien:**

#### 3.1 Preflight-Checks
- [ ] Port-Verfügbarkeit prüfen (3000, 8000, 8001, 11434, 9443)
- [ ] Zielverzeichnis auf leer/Git-Repo prüfen
- [ ] Docker + Compose Version prüfen
- [ ] GPU-Verfügbarkeit prüfen (`lspci | grep NVIDIA`)
- [ ] NVIDIA-Treiber-Status prüfen (`nvidia-smi`)
- [ ] Container-Toolkit prüfen (`docker run --gpus all ...`)

#### 3.2 Automatische Installation
- [ ] NVIDIA-Treiber installieren (wenn GPU vorhanden, Treiber fehlt)
- [ ] NVIDIA Container Toolkit installieren
- [ ] Docker-Service neustarten nach Toolkit-Installation
- [ ] Nouveau-Treiber deaktivieren (blacklist)

#### 3.3 Sicherheit
- [ ] Secrets automatisch generieren (starke Passwörter)
- [ ] Ports über .env konfigurierbar machen
- [ ] Ports bei Konflikt automatisch auf freie Ports ändern
- [ ] Installer-Log schreiben

#### 3.4 Ollama-Setup
- [ ] Health-Check nach Ollama-Start
- [ ] Automatischer Model-Pull (konfiguriertes Modell)
- [ ] Warmup-Prompt nach Model-Pull

**Dateien:**
- `scripts/install.sh` oder `installer/` Verzeichnis
- `docker/docker-compose.yml` (Ports via .env)
- `docker/stack.env` (Port-Variablen ergänzen)

---

### 4. Chunking-System implementieren

**Status:** Geplant
**Priorität:** Mittel
**Quelle:** Plan-Datei

**Beschreibung:**
Text-Chunking für bessere RAG-Ergebnisse mit konfigurierbaren Parametern pro Dokumenttyp.

**Erfüllungskriterien:**

#### 4.1 Backend Chunking-Service
- [ ] `backend/app/services/chunking.py` erstellen
- [ ] Strategien: `fixed`, `paragraph`, `semantic`
- [ ] Parameter: `chunk_size`, `overlap`, `max_chunks`

#### 4.2 Dokumenttyp-Persistierung
- [ ] `backend/app/models/document_type.py` erstellen
- [ ] `backend/app/schemas/document_type.py` erstellen
- [ ] `backend/app/api/document_types.py` erstellen (CRUD-Endpoints)
- [ ] Alembic-Migration für `document_type_settings` Tabelle

#### 4.3 RAG-Integration
- [ ] `backend/app/rag/vectorstore.py` erweitern (Chunk-basiertes Speichern)
- [ ] `backend/app/rag/service.py` erweitern (Chunk-basierte Suche)

#### 4.4 Frontend-Anbindung
- [ ] `frontend/src/lib/api.ts` erweitern (DocumentType API)
- [ ] `frontend/src/components/settings/SettingsDocumentTypes.tsx` von localStorage auf API umstellen

**Dateien:**
- Siehe oben

---

### 5. Semantic-Analyse Timeout testen

**Status:** Implementiert, Test ausstehend
**Priorität:** Hoch

**Beschreibung:**
Ollama-Timeout wurde von 120s auf 300s erhöht. Muss getestet werden.

**Erfüllungskriterien:**
- [ ] Dokument parsen
- [ ] Analyse starten
- [ ] Analyse wird erfolgreich abgeschlossen (nicht "Analyse fehlgeschlagen")
- [ ] Latency < 300s
- [ ] Output-Tokens > 0 in Analyse-Ergebnis

**Test-Schritte:**
```bash
# 1. Token holen
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=admin" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r '.access_token')

# 2. Dokument parsen
curl -X POST "http://localhost:8000/api/documents/{DOC_ID}/parse" \
  -H "Authorization: Bearer $TOKEN"

# 3. Warten, dann analysieren
curl -X POST "http://localhost:8000/api/documents/{DOC_ID}/analyze" \
  -H "Authorization: Bearer $TOKEN"

# 4. Ergebnis prüfen
curl "http://localhost:8000/api/documents/{DOC_ID}" \
  -H "Authorization: Bearer $TOKEN" | jq '.analysis_result'
```

---

## Abgeschlossene Aufgaben

### Phase 1: Grundlagen (Backend) ✅
1. ✅ Fehlende Enums ergänzen (ErrorSource, Severity, AnalysisStatus)
2. ✅ Grant Purpose Schema und Checker implementieren
3. ✅ Conflict Resolution implementieren
4. ✅ Versionierungs-Metadaten hinzufügen

### Phase 2: Erweiterungen ✅
5. ✅ Risikomodul implementieren
6. ✅ UNCLEAR-Begründungspflicht (in Grant Purpose und Result Schemas)
7. ✅ Fehlerzustände definieren (AnalysisStatus Enum)

### Phase 3: QS-Werkzeuge ✅
8. ✅ Generator-Referenzszenarien (qa_scenarios.py)
9. 🔄 RAG-Einschränkungen (Backend-Logik vorhanden, UI ausstehend)
10. ✅ Datenklassifikation dokumentieren (data_classification.md)

### Phase 4: Frontend-Integration ✅
11. ✅ Übersetzungen für neue Konzepte
12. ✅ UI-Komponenten für neue Prüfungen

### Sonstige ✅
- ✅ Ollama Timeout von 120s auf 300s erhöht
- ✅ CheckersSettings.tsx mit i18n verbunden
- ✅ improvement_plan.md aktualisiert

---

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Abgeschlossen |
| 🔄 | In Bearbeitung |
| ⏳ | Geplant |
| [ ] | Teilaufgabe offen |
| [x] | Teilaufgabe erledigt |
