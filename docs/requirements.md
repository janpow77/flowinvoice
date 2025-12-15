## flowaudit – Transparent Invoice Auditing with LLMs (Seminar System)
**Version:** 1.0 (Seminar-Release)
**Primary Goal:** Didaktische Transparenz (Input → Verarbeitung → Output → Feedback → Lernen)
**Target Host:** ASUS NUC (64 GB RAM), Docker, optional GPU
**Frontend Languages:** Deutsch & Englisch (UI vollständig zweisprachig)
**Rule Sets:** 🇩🇪 DE (UStG §14), 🇪🇺 EU VAT, 🇬🇧 UK VAT
**LLM Providers:** Local (Ollama + trainable local model), External (OpenAI, Gemini)

---

## 0. Nicht-Ziele / Abgrenzung (wichtig für Seminar-Transparenz)

* Kein rechtsverbindlicher Steuerbescheid / keine automatische Entscheidung.
* Kein „Prompt-Engineering UI“. Prompts bleiben serverseitig.
* Kein Speichern von Generator-Truth in DB (Truth nur als Textdatei im Exportordner).
* Kein automatisches „Lernen“ ohne menschliche Korrektur (Training nur aus bestätigtem Feedback).

---

## 1. Systemüberblick – Didaktik (was Teilnehmende verstehen sollen)

Teilnehmende müssen im System nachvollziehen können:

1. **Welche Anforderungen** gelten (Regelwerk & Merkmale).
2. **Wie PDFs maschinenlesbar werden** (Parser-Ausgabe).
3. **Was genau an die KI übergeben wird** (Input-JSON).
4. **Welche Antwort kommt zurück** (Response-JSON).
5. **Wie Menschen Feedback geben** (Accept/Correct + Kommentar).
6. **Wie Training funktioniert** (lokale LLM: Datensatz → Training → Modellversion).
7. **Wie sich Leistung und Qualität messen lassen** (Statistiken, Telemetrie, Lernkurven).
8. **Warum externe LLMs nicht „lokal trainierbar“ sind**, aber trotzdem vergleichbar (Laufzeiten/Erkennung/Fehlerquote).

---

## 2. Monorepo & Deploy (Docker)

### 2.1 Repository Layout

```
flowaudit/
├── frontend/
├── backend/
├── llm/
│   ├── runtime/                 # Ollama runtime container
│   └── trainer/                 # local training container (LoRA/QLoRA)
├── data/
│   ├── uploads/                 # hochgeladene PDFs (runtime)
│   ├── exports/                 # Generator output (PDF + truth)
│   ├── previews/                # Template previews
│   ├── training/
│   │   ├── datasets/            # exported JSONL datasets + manifests
│   │   └── runs/                # training run artifacts + metrics
│   └── logs/                    # log files & request traces
├── docker-compose.yml
└── docs/
    ├── REQUIREMENTS.md
    └── CLAUDE.md
```

### 2.2 Docker Compose Services (minimum)

* `frontend` (React/Vue)
* `backend` (FastAPI)
* `db` (PostgreSQL empfohlen; SQLite optional für Demo-only)
* `ollama` (local inference)
* `trainer` (local fine-tuning jobs)
* optional: `monitor` (simple telemetry aggregator)

### 2.3 Healthchecks

* Backend: `/health`
* DB: basic connection
* Ollama: `/api/tags` erreichbar

---

## 3. Regelwerke / Rule Sets (Flag-select)

### 3.1 Startscreen: Flaggenwahl

* 🇩🇪 → Ruleset `DE_USTG_14` (DE UI default)
* 🇪🇺 → Ruleset `EU_VAT` (EN UI default, optional DE UI)
* 🇬🇧 → Ruleset `UK_VAT` (EN UI default)

**Wichtig:** Sprachwahl (DE/EN UI) ist **unabhängig** vom Ruleset.
Beispiel: UI Deutsch, Ruleset UK VAT (für deutsche Teilnehmende) ist möglich.

### 3.2 Ruleset-Datenstruktur (versioniert, editierbar)

```json
{
  "ruleset_id": "DE_USTG_14",
  "ruleset_version": "1.0",
  "locale_default": "de",
  "display_name": {"de":"UStG §14", "en":"German VAT Act §14"},
  "legal_basis": {"de":"§ 14 Abs. 4 UStG", "en":"German VAT Act §14(4)"},
  "features": [
    {
      "id": "supplier_name_address",
      "label": {"de":"Name und Anschrift leistender Unternehmer", "en":"Supplier name and address"},
      "required": true,
      "severity": "critical",
      "explanation": {"de":"Pflichtangabe nach § 14 Abs. 4 Nr. 1 UStG", "en":"Mandatory invoice field ..."},
      "examples": {
        "positive": ["Muster GmbH, Musterstraße 1, 12345 Musterstadt"],
        "negative": ["nur 'Muster GmbH' ohne Anschrift"]
      }
    }
  ]
}
```

### 3.3 Feature-Severity (für Seminar)

* `critical` (Fehlt → hohes Risiko)
* `major`
* `minor`

Diese Severity wird für:

* Ergebnisampel
* Fehlerschwere im Generator
* Lernkurven nach Merkmal

---

## 4. Vorhaben / Project Context (für Zweck & Zeitprüfung)

### 4.1 Project Modell

```json
{
  "project_id": "PRJ_001",
  "title": "Baumaßnahme Aschaffenburg",
  "description": "Umbau und Sanierung ...",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "total_volume_eur": 1200000,
  "cost_categories": [
    {"code":"BAU", "label_de":"Bauleistungen", "label_en":"Construction works"},
    {"code":"PLAN", "label_de":"Planung", "label_en":"Planning"},
    {"code":"IT", "label_de":"IT-Infrastruktur", "label_en":"IT infrastructure"}
  ],
  "beneficiary": {
    "name": "Stadt Aschaffenburg",
    "address": "..."
  }
}
```

### 4.2 Hard Checks (ohne KI)

* `invoice_date` im Projektzeitraum? (ja/nein/unklar)
* `service_period` überschneidet Projektzeitraum? (ja/nein/unklar)

Diese Flags werden:

* in der Ergebnisliste angezeigt
* in den KI-Input aufgenommen
* bei Konflikt mit KI-Aussage markiert

---

## 5. PDF Parser (Pflichtmodul, „zerlegt“ PDF)

### 5.1 Ziel

Parser erzeugt:

* Text (gesamt + je Seite)
* Zeilen (für Nachvollziehbarkeit)
* erkannte Felder (Datum, Zeitraum, Beträge wenn robust)
* Normalisierung von Datumsformaten

### 5.2 Parser Output Schema (persistiert)

```json
{
  "parser_version": "1.0",
  "file": {"name":"INV_001.pdf","sha256":"..."},
  "pages":[
    {"page":1,"text":"...","lines":["...","..."]}
  ],
  "extracted": {
    "invoice_number": {"value":"2025-001","confidence":0.62,"source":"regex"},
    "invoice_date": {"value":"2025-03-15","confidence":0.85,"source":"regex"},
    "service_period": {"from":"2025-01-01","to":"2025-12-31","confidence":0.71,"source":"nlp/regex"},
    "net_total": {"value": "1000.00", "currency":"EUR", "confidence":0.55},
    "vat_total": {"value": "190.00", "currency":"EUR", "confidence":0.55}
  }
}
```

### 5.3 Parser Tools

* Pflicht: `pdfplumber`
* optional: regex library, dateparser

### 5.4 Robustheit

* Wenn Felder nicht sicher extrahierbar sind → `confidence` niedrig + `value` null.
* Der Parser darf niemals „raten“, sondern muss Unklarheit markieren.

---

## 6. KI Input/Output – Transparenz ohne Prompt

### 6.1 KI-Input-JSON (Viewer-Reiter, exakt sichtbar)

```json
{
  "meta": {
    "run_id": "run_...",
    "ruleset_id": "DE_USTG_14",
    "ruleset_version": "1.0",
    "ui_locale": "de",
    "model_selected": "local:flowaudit-local-ft-v3"
  },
  "project": { ... },
  "requirements": { ... ruleset features ... },
  "parser_output": { ... },
  "hard_checks": {
    "invoice_date_in_project_period": "yes|no|unclear",
    "service_period_in_project_period": "yes|no|unclear"
  }
}
```

### 6.2 KI-Response-JSON (Viewer-Reiter, sichtbar)

```json
{
  "model": "flowaudit-local-ft-v3",
  "results": [
    {
      "feature_id": "vat_id_or_tax_number",
      "status": "ok|missing|unclear",
      "comment_de": "…",
      "comment_en": "…"
    }
  ],
  "overall_assessment": "ok|risk|needs_review",
  "summary_de": "…",
  "summary_en": "…"
}
```

**Hinweis:** Kommentare bilingual speichern, UI zeigt passend zur Sprache.

---

## 7. UI – Kernworkflows

### 7.1 Modus A: Teilnehmer (Standard)

* Drag&Drop Upload (PDF-only)
* Belegliste mit Status
* Analyse starten
* Live-LogView + Spinner (Logo) + Prozent
* Ergebnisliste
* Detailansicht + Feedback

### 7.2 Modus B: Trainer (versteckt)

* Generator
* Ruleset-Editor (Merkmale hinzufügen/ändern/versionieren)
* Training Dashboard (datasets, runs, model versions)
* Evaluation & A/B Comparisons

**Versteckmechanismus:** Trainer-Menü nicht prominent; z. B. in Footer-Klickfolge oder Settings-Schalter mit Passwort (nur lokal).

---

## 8. Übersichtsliste & Detailansicht (Pflicht)

### 8.1 Übersichtsliste Spalten (konfigurierbar)

* Datei
* Parser OK/Fehler
* Modell
* Overall Assessment Ampel
* Kritische Merkmale missing
* Hard-check Konflikte (Zeit)
* Laufzeit je Dokument
* Feedback-Status (offen/akzeptiert/korrigiert)

### 8.2 Detailansicht Tabs (Pflicht)

1. PDF Viewer
2. Parser JSON (syntax highlight)
3. KI Input JSON (syntax highlight + Tooltips)
4. KI Response JSON (syntax highlight + Tooltips)
5. Feedback (Accept / Correct / Comment)
6. LogView (chronologisch, filterbar)

### 8.3 JSON Viewer Anforderungen

* Syntax Highlight
* Copy Button
* Expand/Collapse (Tree view optional)
* Tooltip-Erklärungen pro Feld (z. B. „feature_id erklärt“)

---

## 9. Feedback & Versionierung (Pflicht)

### 9.1 Feedback Actions

* **Accept** (Ergebnis ok)
* **Correct** (status je Feature ändern + Kommentar)
* **Comment only**

### 9.2 Versionierung

Für jede Rechnung:

* `analysis_version` beginnt bei 1
* jede Korrektur erhöht Version

Speicherobjekt:

```json
{
  "invoice_id":"...",
  "analysis_version": 3,
  "model_used":"...",
  "human_feedback": {
    "action":"correct",
    "changes":[{"feature_id":"vat_id_or_tax_number","status":"missing"}],
    "comment":"..."
  }
}
```

### 9.3 Belegliste im „DataGrid“ erst nach Feedback

**Pflichtanforderung:**
Eine „Belegliste / extrahierte Felder-Tabelle“ (DataGrid) wird **erst angezeigt**, nachdem:

* Feedback abgegeben wurde (Accept/Correct),
  damit im Seminar sichtbar ist: *„Prüfer bestätigt erst, dann wird die strukturierte Datenlage finalisiert.“*

---

## 10. Generator (Trainer-only, versteckt)

### 10.1 Zweck

Erzeugt **realistisch aussehende** Dummy-Rechnungen (PDF), gemischt korrekt/fehlerhaft.

### 10.2 Anforderungen

* 5 Templates (stark unterschiedliche Layouts)
* Templates als Vorschau oberhalb (Preview images)
* Checkbox-Auswahl: welche Templates aktiv
* Einstellbar:

  * Anzahl Rechnungen
  * Fehlerquote global
  * Fehlerschwere (Anzahl Fehler pro fehlerhafte Rechnung)
  * Fehlerverteilung pro Merkmal (Feature-weighting)
  * Datumsformat-Varianten (single date, range, textual)
  * Sprache: DE/EN abhängig von Ruleset
* Keine „Beispiel“-Marker in sichtbaren Inhalten (damit KI nichts triviales lernt)
* Unterschiedliche Briefköpfe, Schriftgrößen, Positionen (Adresse links/rechts), Tabellenformat variiert.

### 10.3 Generator Output

Exportverzeichnis wird im UI gewählt (nur erlaubte Aliase, kein freier Pfad):

* PDFs nach `/data/exports/<batch>/pdf/`
* Lösungen nach `/data/exports/<batch>/truth/solutions.txt`
* Zusätzlich: `manifest.json` (Templates, Settings, Hashes)

**Wichtig:** solutions.txt wird **nicht** in DB gespeichert.

---

## 11. LLM Provider & Settings UI

### 11.1 Unterstützte Provider

| Provider | ID | API-Basis | Modelle (Beispiele) |
|----------|----|-----------|--------------------|
| **Lokal (Ollama)** | `LOCAL_OLLAMA` | `http://ollama:11434` | llama3.1:8b, mistral:7b, qwen2:7b |
| **OpenAI** | `OPENAI` | `https://api.openai.com/v1` | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| **Anthropic (Claude)** | `ANTHROPIC` | `https://api.anthropic.com/v1` | claude-sonnet-4-20250514, claude-3-5-haiku-20241022 |
| **Google (Gemini)** | `GEMINI` | `https://generativelanguage.googleapis.com` | gemini-1.5-pro, gemini-1.5-flash |

### 11.2 Settings-UI Anforderungen (Pflicht)

#### 11.2.1 Provider-Auswahl

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Einstellungen / Settings                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ── LLM-Provider für Analyse ──────────────────────────────────│
│                                                                  │
│  Aktiver Provider:                                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ○ Lokal (Ollama)           ← Standard, Daten bleiben lokal ││
│  │ ○ OpenAI (ChatGPT)         ⚠️ Daten werden übertragen      ││
│  │ ○ Anthropic (Claude)       ⚠️ Daten werden übertragen      ││
│  │ ○ Google (Gemini)          ⚠️ Daten werden übertragen      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ── Lokales Modell (Ollama) ───────────────────────────────────│
│                                                                  │
│  Verfügbare Modelle:  [ llama3.1:8b-instruct-q4     ▼ ]        │
│                       ○ llama3.1:8b-instruct-q4 (geladen)      │
│                       ○ mistral:7b                             │
│                       ○ qwen2:7b                               │
│                       ○ flowaudit-ft-v1 (fine-tuned)           │
│                                                                  │
│  [ Modell laden ]   [ Neues Modell herunterladen ]             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 11.2.2 API-Key-Konfiguration (pro Provider)

```
┌─────────────────────────────────────────────────────────────────┐
│  ── API-Keys ──────────────────────────────────────────────────│
│                                                                  │
│  OpenAI:                                                        │
│  ┌─────────────────────────────────────────┐                   │
│  │ ********************************abcd    │ ✓ Gesetzt         │
│  └─────────────────────────────────────────┘                   │
│  [ Ändern ] [ Testen ] [ Löschen ]                             │
│                                                                  │
│  Anthropic (Claude):                                            │
│  ┌─────────────────────────────────────────┐                   │
│  │ sk-ant-************************1234    │ ✓ Gesetzt         │
│  └─────────────────────────────────────────┘                   │
│  [ Ändern ] [ Testen ] [ Löschen ]                             │
│                                                                  │
│  Google (Gemini):                                               │
│  ┌─────────────────────────────────────────┐                   │
│  │                                         │ ✗ Nicht gesetzt   │
│  └─────────────────────────────────────────┘                   │
│  [ API-Key eingeben ]                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 11.2.3 Modell-Auswahl (pro Provider)

```
┌─────────────────────────────────────────────────────────────────┐
│  ── Modellauswahl ─────────────────────────────────────────────│
│                                                                  │
│  OpenAI Modell:       [ gpt-4o-mini              ▼ ]           │
│                       ○ gpt-4o (teuer, beste Qualität)         │
│                       ○ gpt-4o-mini (günstig, schnell)         │
│                       ○ gpt-4-turbo                            │
│                                                                  │
│  Anthropic Modell:    [ claude-sonnet-4-20250514     ▼ ]           │
│                       ○ claude-sonnet-4-20250514 (Balance)             │
│                       ○ claude-3-5-haiku (schnell, günstig)    │
│                                                                  │
│  Gemini Modell:       [ gemini-1.5-flash         ▼ ]           │
│                       ○ gemini-1.5-pro (beste Qualität)        │
│                       ○ gemini-1.5-flash (schnell)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 11.2.4 Erweiterte Einstellungen

```
┌─────────────────────────────────────────────────────────────────┐
│  ── Erweiterte Einstellungen ──────────────────────────────────│
│                                                                  │
│  Temperature:         [ 0.2        ] (0.0 - 1.5)               │
│  Max Tokens:          [ 2000       ] (100 - 8192)              │
│  Timeout (Sekunden):  [ 120        ] (30 - 300)                │
│  Parallele Anfragen:  [ 2          ] (1 - 5)                   │
│                                                                  │
│  ☐ Verbose Logging aktivieren                                  │
│  ☑ Bei Fehler automatisch wiederholen (3x)                     │
│                                                                  │
│  [ Einstellungen speichern ]   [ Zurücksetzen ]                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3 API-Key-Sicherheit

| Anforderung | Implementierung |
|-------------|-----------------|
| **Anzeige maskiert** | Nur letzte 4 Zeichen sichtbar: `sk-ant-************************1234` |
| **Speicherung verschlüsselt** | AES-256 oder Fernet, Key aus Umgebungsvariable |
| **Keine Logs** | API-Keys werden niemals in Logs geschrieben |
| **Testfunktion** | "Testen"-Button prüft Verbindung ohne Key anzuzeigen |
| **Löschbar** | User kann API-Key jederzeit entfernen |

### 11.4 Provider Adapter (Backend)

Einheitliches Interface:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze(self, payload: PreparePayload) -> LLMResponse:
        """Führt Analyse durch und gibt strukturierte Antwort zurück."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Testet ob Provider erreichbar und API-Key gültig ist."""
        pass

    @abstractmethod
    def get_available_models(self) -> list[ModelInfo]:
        """Gibt Liste verfügbarer Modelle zurück."""
        pass
```

### 11.5 Datenschutz-Hinweise in UI

Bei Auswahl eines externen Providers:

```
⚠️ HINWEIS: Bei Verwendung von [OpenAI/Claude/Gemini] werden
Rechnungsdaten an externe Server übertragen.

Übertragene Daten:
• Extrahierter Text aus PDFs
• Projektkontext (anonymisiert)
• Regelwerk-Anforderungen

Die Daten werden gemäß den Datenschutzrichtlinien des
jeweiligen Anbieters verarbeitet.

[ Verstanden, fortfahren ]   [ Abbrechen ]
```

---

## 12. Laufzeit-/Nutzungsstatistik (alle Modelle, Pflicht)

Pro Run:

* Gesamtzeit
* Zeit pro Dokument
* Anzahl Dokumente
* Anzahl Features geprüft
* Anzahl Erkennungen (ok/missing/unclear counts)
* Fehlerquote (gegen menschliches Feedback, sobald vorhanden)

UI:

* Run Summary Box (oben)
* Export als CSV/JSON

---

## 13. Local LLM Telemetrie (zusätzlich, Pflicht)

Nur bei local:

* Token Input/Output/Total
* CPU avg/peak
* RAM avg/peak
* optional GPU usage
* tokens/s (wenn verfügbar)

Erhebung:

* tokens: aus provider response oder tokenizer
* CPU/RAM: `psutil`
* GPU: `nvidia-smi` (optional)

---

## 14. Training (lokale LLM) – sichtbar & dokumentiert

### 14.1 Trainingsdaten entstehen nur aus Feedback

* Nur bestätigte Korrekturen werden Trainingsbeispiele.

### 14.2 Dataset Export (JSONL)

Endpoint:

* `POST /api/training/export`
  Output:
* `/data/training/datasets/<dataset_id>/train.jsonl`
* `/data/training/datasets/<dataset_id>/val.jsonl`
* `/data/training/datasets/<dataset_id>/manifest.json` (counts, hashes, seed)

### 14.3 Training Run Orchestrierung

Endpoint:

* `POST /api/training/runs`
  Parameter:
* dataset_id, base_model, epochs, lr, lora_rank, seed

Artifacts:

* adapter files
* metrics.json (loss, eval)
* run logs

### 14.4 Modell Registry

Endpoint:

* `POST /api/models/register`
  List:
* `GET /api/models`

UI:

* Model Versions list (v1, v2, v3)
* “trained on N examples” counter

---

## 15. Evaluation & Lernkurven (Pflicht)

### 15.1 Holdout/Eval Set

Es gibt einen festen Eval-Satz (nicht fürs Training).
Daraus werden Metriken pro Modellversion berechnet.

### 15.2 Metriken

Pro Feature:

* Precision / Recall / F1 (ok/missing/unclear classification)
* Confusion counts

Global:

* Macro-F1
* Overall assessment accuracy
* Fehlerquote über Zeit

### 15.3 UI: Learning Dashboard

* Trainingsbeispiele count (gesamt, pro ruleset, pro Sprache)
* Training runs count
* Modellversionen + “trained on …”
* Lernkurve (F1 über Versionen)
* Fehlerkurve (kritische Features separat)
* A/B Vergleich (Model A vs B vs C)

---

## 16. Vergleich externer vs lokaler Modelle (Seminarpflicht)

Auch externe Provider zeigen:

* Laufzeit
* Dokumentcount
* Featurecount
* Erkennungscounts (ok/missing/unclear)
* Fehlerquote bezogen auf Feedback (falls vorhanden)

Lokale Provider zusätzlich:

* Tokens
* CPU/RAM/GPU
* Trainingsstand

---

## 17. Logging & LogView (Pflicht)

### 17.1 Was geloggt wird

* Upload event
* Parser start/end + duration
* Input JSON created (hash + size, optional full JSON in verbose)
* Provider call start/end + status
* Response received
* Persist events
* Training run events

### 17.2 LogView UI

* Filter (parser/provider/training)
* per Dokument
* per Run
* Export

---

## 18. Datenbank (Minimum Tables)

### 18.1 Tabellen

* `rulesets`
* `ruleset_versions`
* `projects`
* `invoices`
* `parser_outputs`
* `analysis_runs`
* `analysis_results`
* `feedback`
* `training_examples`
* `training_datasets`
* `training_runs`
* `model_registry`
* `model_metrics`

**Wichtig:** Keine Generator-truth in DB.

---

## 19. Sicherheit & Datenschutz (Seminarbetrieb)

* Uploads lokal
* keine offenen Ports nötig (optional Cloudflare Tunnel)
* externe Provider: klare Kennzeichnung „Data leaves device“
* API keys verschlüsselt/secret storage (mindestens env + masked UI)

---

## 20. Error Handling & Recovery (Pflicht)

### 20.1 Fehlerklassifikation

| Fehlerklasse | Beschreibung | Auswirkung |
|--------------|--------------|------------|
| `RECOVERABLE` | Kann automatisch wiederholt werden | Retry mit Backoff |
| `USER_CORRECTABLE` | Benutzer kann beheben | Fehlermeldung mit Anleitung |
| `SYSTEM_ERROR` | Systemfehler, Admin nötig | Alert + Logging |
| `DATA_ERROR` | Fehlerhafte Eingabedaten | Dokument als ERROR markieren |

### 20.2 Fehlerszenarien und Reaktionen

#### 20.2.1 PDF-Parser-Fehler

| Fehler | Reaktion |
|--------|----------|
| PDF korrupt/unlesbar | Status `ERROR`, Meldung "PDF konnte nicht gelesen werden" |
| PDF passwortgeschützt | Status `ERROR`, Meldung "Passwortgeschützte PDFs nicht unterstützt" |
| Kein Text extrahierbar (Bild-PDF) | Status `PARSED` mit Warning, OCR-Hinweis in UI |
| Parser-Timeout (>30s) | Retry 1x, dann Status `ERROR` |
| Speicherüberlauf | Task abbrechen, Status `ERROR`, Alert an Admin |

#### 20.2.2 LLM-Provider-Fehler

| Fehler | Reaktion |
|--------|----------|
| Connection Timeout | 3 Retries mit exponential backoff (2s, 4s, 8s) |
| Rate Limit (429) | Warten + Retry nach Header-Info oder 60s |
| Invalid API Key | Status `ERROR`, Settings-Prüfung anfordern |
| Model not found | Fallback auf Standard-Modell, Warning |
| Context too long | Text kürzen, Retry |
| Invalid JSON Response | 2 Retries, dann manuelle Struktur-Extraktion |
| Provider nicht erreichbar | Fallback auf alternativen Provider (wenn konfiguriert) |

#### 20.2.3 Datenbank-Fehler

| Fehler | Reaktion |
|--------|----------|
| Connection lost | Retry mit Connection Pool |
| Constraint violation | Rollback, aussagekräftige Fehlermeldung |
| Disk full | Alert an Admin, keine neuen Uploads |
| Migration failed | Rollback, System bleibt auf alter Version |

#### 20.2.4 Dateisystem-Fehler

| Fehler | Reaktion |
|--------|----------|
| Upload-Verzeichnis nicht beschreibbar | Alert, Upload-Endpoint deaktivieren |
| PDF nicht gefunden | Status `ERROR`, Konsistenzprüfung triggern |
| Export-Fehler | Retry 1x, dann Error an User |

### 20.3 Retry-Strategien

```python
RETRY_CONFIG = {
    "pdf_parse": {
        "max_retries": 1,
        "backoff": "none",
        "timeout_seconds": 30
    },
    "llm_call": {
        "max_retries": 3,
        "backoff": "exponential",
        "base_delay_seconds": 2,
        "max_delay_seconds": 30,
        "timeout_seconds": 120
    },
    "db_operation": {
        "max_retries": 3,
        "backoff": "linear",
        "delay_seconds": 1,
        "timeout_seconds": 10
    },
    "external_api": {
        "max_retries": 3,
        "backoff": "exponential",
        "base_delay_seconds": 5,
        "max_delay_seconds": 60,
        "respect_rate_limit_headers": True
    }
}
```

### 20.4 Benutzer-Fehlermeldungen (zweisprachig)

| Fehler-Code | Meldung (DE) | Meldung (EN) |
|-------------|--------------|--------------|
| `PDF_CORRUPT` | "Die PDF-Datei ist beschädigt oder nicht lesbar." | "The PDF file is corrupted or unreadable." |
| `PDF_PASSWORD` | "Passwortgeschützte PDFs werden nicht unterstützt." | "Password-protected PDFs are not supported." |
| `PDF_NO_TEXT` | "Kein Text im PDF gefunden. Möglicherweise ein Bild-PDF." | "No text found in PDF. It may be an image-based PDF." |
| `LLM_UNAVAILABLE` | "Der KI-Dienst ist vorübergehend nicht erreichbar." | "The AI service is temporarily unavailable." |
| `LLM_TIMEOUT` | "Die Analyse hat zu lange gedauert. Bitte erneut versuchen." | "Analysis took too long. Please try again." |
| `UPLOAD_FAILED` | "Upload fehlgeschlagen. Bitte erneut versuchen." | "Upload failed. Please try again." |
| `EXPORT_FAILED` | "Export konnte nicht erstellt werden." | "Export could not be created." |

### 20.5 Logging-Anforderungen

**Jeder Fehler muss enthalten:**
```json
{
  "timestamp": "2025-12-15T12:00:00Z",
  "level": "ERROR",
  "error_code": "LLM_TIMEOUT",
  "error_class": "RECOVERABLE",
  "service": "worker",
  "task_id": "task_123",
  "document_id": "doc_456",
  "project_id": "prj_789",
  "message": "LLM call timed out after 120s",
  "details": {
    "provider": "LOCAL_OLLAMA",
    "model": "llama3.1:8b",
    "retry_count": 3,
    "last_error": "Connection timed out"
  },
  "stack_trace": "..."
}
```

### 20.6 Health-Check-Integration

```python
# Automatische Fehlererkennung über Health-Checks
HEALTH_CHECK_CONFIG = {
    "db": {
        "interval_seconds": 30,
        "timeout_seconds": 5,
        "unhealthy_threshold": 3
    },
    "ollama": {
        "interval_seconds": 60,
        "timeout_seconds": 10,
        "unhealthy_threshold": 2
    },
    "chroma": {
        "interval_seconds": 60,
        "timeout_seconds": 5,
        "unhealthy_threshold": 3
    },
    "redis": {
        "interval_seconds": 30,
        "timeout_seconds": 5,
        "unhealthy_threshold": 2
    }
}
```

### 20.7 Graceful Degradation

| Komponente ausfallend | Degradiertes Verhalten |
|-----------------------|------------------------|
| Ollama | Nur externe Provider nutzbar, UI-Hinweis |
| ChromaDB | RAG deaktiviert, Analyse ohne Few-Shot |
| Redis | Synchrone Verarbeitung statt Queue |
| PostgreSQL | System nicht nutzbar, Maintenance-Seite |

---

## 21. Abnahmekriterien (Definition of Done)

Das System ist nur „fertig“, wenn:

1. Parser funktioniert robust für 5 Generator-Templates
2. UI zeigt: PDF + Parser JSON + Input JSON + Response JSON
3. Prompt ist nirgendwo sichtbar
4. Generator erzeugt PDFs + solutions.txt im gewählten Exportordner
5. solutions.txt wird NICHT in DB gespeichert
6. Feedback erzeugt Versionen
7. Belegliste/DataGrid erscheint erst nach Feedback
8. Statistiken für externe & lokale Modelle vorhanden
9. Lokale Telemetrie (tokens/cpu/ram) sichtbar
10. Training läuft lokal, neue Modellversion registrierbar
11. Lern-Dashboard zeigt Kurven + Zähler + Fehlerquoten
12. A/B Vergleich funktioniert

---

## 21. Minimaler MVP-Plan (für Claude Code Umsetzung)

**MVP 1:** Parser + Viewer + External Provider + Stats
**MVP 2:** Generator + Template Previews + Hidden Trainer Menu
**MVP 3:** Local Ollama + Telemetry + Settings
**MVP 4:** Feedback Versionierung + DataGrid-after-feedback
**MVP 5:** Training pipeline + Model registry + Evaluation + Learning dashboard


# flowaudit – Beleganalyse (UStG + Zuwendungszweck) mit lokaler KI
**Konzept- & Setup-Guide (GitHub-Repo-Startpunkt)**  
Stand: 12.12.2025

Dieses Repository beschreibt ein System, mit dem Nutzer **ohne Prompt-Eingabe** PDF‑Belege hochladen (oder aus einem Schulungsset auswählen) und eine **Ergebnisliste** erhalten. Die KI läuft **unsichtbar im Backend** (lokal über Ollama oder alternativ über Cloud‑API).

Das System unterstützt zwei Modi:
- **Training (Anlernen):** Belege hochladen/auswählen, Goldstandard pro Modul erfassen (Labels + Begründung).
- **Prüfen (Module 1–3):** Vorhabenprofil erfassen/auswählen, Belege hochladen, Analyse starten, Ergebnisse ansehen, Feedback speichern.

---

## 1. Ziele und Grundprinzipien

### 1.1 Nutzerinteraktion (keine Prompts)
- Frontend bietet **nur**:
  - Datei‑Upload (PDF; optional Batch)
  - Auswahl aus Schulungsbelegen
  - Start‑Button „Analyse“
  - Ergebnisliste + Detailansicht + Feedback
- **Kein** Freitext‑Promptfeld. Prompts sind **fest im Backend versioniert**.

### 1.2 Fachliche Module
- **Modul 1 – UStG‑Rechnungspflichtangaben**  
  Fokus auf formale Anforderungen (Vorsteuer‑Relevanz als Prüfhilfe). Typische Pflichtangaben ergeben sich aus **§ 14 Abs. 4 UStG**, Sonderfälle aus **§ 14a UStG**, Vorsteuerabzug aus **§ 15 Abs. 1 UStG**.
- **Modul 2 – Vorhabenzusammenhang / Zuwendungszweck**  
  Prüfung, ob der Beleg sachlich/zeitlich/organisatorisch plausibel zum Vorhaben passt (Zweckbindung).
- **Modul 3 – Risiko / Vergabe / weitere Prüfregeln (optional erweiterbar)**  
  Z. B. vergaberechtliche Indikatoren, Plausibilitäten, typische Fehlerbilder, Checklistenlogik.

### 1.3 „Wiedererkennung“ der 50 Schulungsbelege
Ein LLM „merkt“ Belege nicht wie ein Speicher. Für **sofortige Wiedererkennung** nutzen wir im Backend:
- **Fingerprint (SHA‑256)** über PDF‑Bytes oder normalisierten Extrakt‑Text
- Lookup in DB → wenn bekannt: Ergebnis **aus DB** statt Inferenz

---

## 2. Architektur

### 2.1 Komponenten (Docker‑Stack)
- **frontend** (React oder Vue) – Upload, Training‑Formulare, Ergebnisliste, Detail, Feedback
- **api** (FastAPI) – Upload‑Endpoints, Projektprofile, Job‑Start, Ergebnis‑API
- **worker** (Celery/RQ/Arq) – Batch‑Analyse, Parallelisierung, robuste Jobs
- **db** (PostgreSQL) – Belege, Projekte, Ergebnisse, Trainingsdaten, Feedback, Prompt‑Versionen
- **ollama** (lokales LLM) – Inferenz über HTTP (z. B. Llama/Qwen/Mistral)
- **traefik** (optional) – Reverse Proxy, HTTPS (oder Cloudflare Tunnel)
- **minio** (optional) – Objekt‑Storage für PDFs (statt Dateisystem)
- **pgadmin** (optional) – DB‑UI

### 2.2 Datenfluss (Prüfmodus)
1. Upload PDF(s) → `api` speichert Datei + extrahiert Text
2. Fingerprint berechnen → bekannte Belege?  
   - Ja → Ergebnis aus DB laden  
   - Nein → Job an `worker` geben
3. Worker:
   - Prompt‑Version laden (fest versioniert)
   - Modul 1–3 ausführen (lokales LLM oder Cloud)
   - JSON validieren → DB schreiben
4. Frontend pollt Status → Ergebnisliste → Detailansicht → Feedback speichern

### 2.3 Datenfluss (Trainingsmodus)
1. Upload/Select Beleg → extrahierter Text sichtbar (optional)
2. Goldstandard pro Modul erfassen (ok/missing/unclear etc.)
3. Speicherung als **Training Example** (Goldstandard)  
4. Optional: „KI‑Vorschlag holen“ → dann manuell korrigieren → als Goldstandard speichern

---

## 3. Repo‑Struktur (Vorschlag)

```text
flowaudit-invoice-ai/
├─ README.md
├─ docs/
│  ├─ 01_architektur.md
│  ├─ 02_datenmodell.md
│  ├─ 03_prompts.md
│  ├─ 04_security.md
│  ├─ 05_training_workflow.md
│  └─ 06_codex_workflow.md
├─ deploy/
│  ├─ docker-compose.yml
│  ├─ docker-compose.override.example.yml
│  ├─ traefik/
│  │  ├─ traefik.yml
│  │  └─ dynamic.yml
│  └─ cloudflared/
│     └─ config.yml
├─ backend/
│  ├─ Dockerfile
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ api/
│  │  │  ├─ routes_invoices.py
│  │  │  ├─ routes_projects.py
│  │  │  ├─ routes_training.py
│  │  │  └─ routes_results.py
│  │  ├─ services/
│  │  │  ├─ pdf_extract.py
│  │  │  ├─ fingerprint.py
│  │  │  ├─ llm_client_ollama.py
│  │  │  ├─ llm_prompts.py
│  │  │  ├─ validators.py
│  │  │  └─ scoring.py
│  │  ├─ db/
│  │  │  ├─ session.py
│  │  │  ├─ models.py
│  │  │  └─ migrations/
│  │  └─ worker/
│  │     ├─ tasks.py
│  │     └─ queue.py
│  └─ tests/
├─ frontend/
│  ├─ Dockerfile
│  ├─ package.json
│  └─ src/
│     ├─ pages/
│     │  ├─ Training.tsx
│     │  ├─ Check.tsx
│     │  └─ Projects.tsx
│     ├─ components/
│     │  ├─ UploadDropzone.tsx
│     │  ├─ ResultsTable.tsx
│     │  ├─ InvoiceDetail.tsx
│     │  └─ ModuleTabs.tsx
│     └─ lib/api.ts
└─ data/
   ├─ training_invoices/   (nur für Demo/Schulung; optional .gitignore)
   └─ seed/
      ├─ projects.json
      └─ invoices_manifest.json
```

---

## 4. Datenmodell (Minimal‑Variante)

### 4.1 Tabellen
**invoices**
- `id` (PK)
- `fingerprint` (unique, SHA‑256)
- `file_name`
- `storage_path` (oder minio key)
- `text_extracted`
- `created_at`

**projects**
- `id` (PK)
- `code` (unique)
- `title`
- `description`
- `funding_purpose`
- `period_start`, `period_end`
- `beneficiary_name`
- `eligible_cost_categories` (JSON)
- `ineligible_cost_examples` (JSON)
- `created_at`

**prompt_versions**
- `id` (PK)
- `module` (1/2/3)
- `version` (z. B. `m1_v1.2`)
- `prompt_template` (Text)
- `schema_json` (JSON‑Schema)
- `created_at`

**ai_results**
- `id` (PK)
- `invoice_id` (FK)
- `project_id` (FK, nullable)
- `module` (1/2/3)
- `model_name`
- `prompt_version_id` (FK)
- `result_json`
- `status` (queued/running/done/failed)
- `created_at`

**training_examples**
- `id` (PK)
- `invoice_id` (FK)
- `project_id` (FK, nullable)
- `module` (1/2/3)
- `label_json` (Goldstandard)
- `source` (manual/corrected_from_ai)
- `created_at`

**feedback**
- `id` (PK)
- `ai_result_id` (FK)
- `module`
- `rating` (correct/partial/wrong)
- `correction_json`
- `comment`
- `created_at`

---

## 5. Ergebnis‑Schemas (Beispiel)

### 5.1 Modul 1 – UStG (Beispiel‑JSON)
```json
{
  "invoice_number": "2025-001",
  "issue_date": "2025-10-15",
  "supplier_name": "Muster GmbH",
  "customer_name": "Begünstigter e.V.",
  "net_amount_total": "1000.00",
  "vat_amount_total": "190.00",
  "checks": [
    {
      "field": "supplier_name_and_address",
      "required_by": "§ 14 Abs. 4 Nr. 1 UStG",
      "status": "ok",
      "comment": "Name und Anschrift des leistenden Unternehmers sind angegeben."
    }
  ],
  "overall_assessment": "likely_valid",
  "overall_comment": "Formale Pflichtangaben überwiegend vorhanden; keine offensichtlichen Ausschlussgründe erkennbar."
}
```

### 5.2 Modul 2 – Vorhabenzusammenhang (Beispiel‑JSON)
```json
{
  "project_relation": {
    "relation_level": "yes",
    "score": 0.86,
    "mapped_cost_category": "Baukosten",
    "time_plausible": true,
    "beneficiary_plausible": true,
    "reasons": [
      "Leistungsbeschreibung bezieht sich auf Umbau/Installation im Projektstandort.",
      "Rechnungsdatum liegt innerhalb des Förderzeitraums.",
      "Kostenart ist im Projektprofil als förderfähig vorgesehen."
    ]
  }
}
```

### 5.3 Modul 3 – Risikoindikatoren (Beispiel‑JSON)
```json
{
  "risk": {
    "risk_level": "medium",
    "signals": [
      "Leistungszeitpunkt nicht eindeutig angegeben",
      "Positionen sehr allgemein beschrieben"
    ],
    "recommendations": [
      "Leistungsnachweis/Abnahmeprotokoll anfordern",
      "Projektzuordnung über Kostenträger prüfen"
    ]
  }
}
```

---

## 6. Setup auf dem NUC (Ubuntu Server)

### 6.1 Basis‑Installation
Empfohlen: Ubuntu Server LTS, SSH aktiviert.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg git ufw
```

### 6.2 Docker installieren
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 6.3 NVIDIA (optional, für GPU‑LLM)
Wenn GPU‑Inferenz genutzt wird: NVIDIA Treiber + Container Toolkit.
(Die konkrete Version hängt vom System ab; anschließend Test mit `nvidia-smi`.)

```bash
# (Beispiel) Toolkit installieren, dann:
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### 6.4 Repo clonen und starten
```bash
git clone https://github.com/<dein-user>/flowaudit-invoice-ai.git
cd flowaudit-invoice-ai/deploy
cp .env.example .env
docker compose up -d --build
```

---

## 7. Docker Compose (Minimal‑Beispiel)

> Datei: `deploy/docker-compose.yml` (Platzhalter – im Repo ausformulieren)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: flowaudit
      POSTGRES_PASSWORD: flowaudit
      POSTGRES_DB: flowaudit
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  api:
    build: ../backend
    environment:
      DATABASE_URL: postgresql+psycopg://flowaudit:flowaudit@db:5432/flowaudit
      OLLAMA_HOST: http://ollama:11434
      STORAGE_PATH: /data/invoices
    volumes:
      - ../data:/data
    ports:
      - "9100:8000"
    depends_on:
      - db
      - ollama

  worker:
    build: ../backend
    command: ["python", "-m", "app.worker.queue"]
    environment:
      DATABASE_URL: postgresql+psycopg://flowaudit:flowaudit@db:5432/flowaudit
      OLLAMA_HOST: http://ollama:11434
      STORAGE_PATH: /data/invoices
    volumes:
      - ../data:/data
    depends_on:
      - db
      - ollama

  frontend:
    build: ../frontend
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  pgdata:
  ollama_data:
```

---

## 8. Sicherheitskonzept (Kurz)

### 8.1 Zugriff
- Idealfall: **Cloudflare Tunnel + Access** (kein Port‑Forwarding)
- Alternativ: Reverse Proxy (Traefik) + HTTPS + Basic Auth/SSO
- Keine öffentlichen DB‑Ports im Internet

### 8.2 Daten
- PDFs und Extrakt‑Texte enthalten ggf. personenbezogene Daten
- Speicherung:
  - Dateisystem in Volume **oder** S3‑kompatibel (MinIO)
  - DB enthält Referenz + Ergebnisse + Hash
- Logging: keine Volltexte in Logs

### 8.3 Rollen
- Admin: Projekte/Prompts/Seeds
- Trainer: Trainingslabels pflegen
- Nutzer: Upload/Prüfen/Feedback

---

## 9. Schulungsmodus (die 50 Belege)

### 9.1 Seed‑Belege vorbereiten
- Lege Schulungs‑PDFs ab: `data/training_invoices/`
- Erstelle Manifest: `data/seed/invoices_manifest.json` (Dateiname, Code, Beschreibung)

### 9.2 Seed‑Projekte vorbereiten
- `data/seed/projects.json` enthält 1–3 Projektprofile (Titel, Zweck, Zeitraum, Kostenarten)

### 9.3 Erstbefüllung
Ein Script `backend/app/db/seed.py`:
- liest Projekte/Manifest
- importiert PDFs (Fingerprint + Text)
- legt Trainingsbeispiele an (optional leer)
- optional: erzeugt KI‑Vorschläge und speichert sie als „draft“

---

## 10. Implementierungs‑Schritte (Roadmap)

### Schritt 1 – Skeleton
- Docker Compose lauffähig (db, api, frontend, ollama)
- Health‑Endpoints + Versioning

### Schritt 2 – Upload + Extraktion
- `POST /api/invoices/upload`
- PDF speichern
- Text extrahieren (`pdfplumber` / `pypdf`)
- Fingerprint bilden

### Schritt 3 – Datenmodell + Migration
- SQLAlchemy Models
- Alembic Migration

### Schritt 4 – Analyse‑Jobs
- `POST /api/run/analyze` startet Jobs (Batch)
- Worker führt Module 1–3 aus
- Status‑Polling + Ergebnis‑API

### Schritt 5 – Trainingsseite
- Goldstandard‑Formulare + Speicherung
- optional: KI‑Vorbefüllung

### Schritt 6 – Feedback‑Loop
- Detailansicht + Feedback speichern
- Export: `training_examples` + `feedback` → JSONL

### Schritt 7 – Retrieval / Few‑Shot (optional)
- Ähnliche Trainingsbelege suchen (Embedding oder simpler TF‑IDF)
- 1–3 Beispiele in Prompt einbetten, um Konsistenz zu erhöhen

### Schritt 8 – Fine‑Tuning (optional)
- Export JSONL
- Modell fein‑tunen (lokal via LoRA oder extern)
- Modell in Ollama als neues Modell registrieren
- Konfiguration umstellen (`MODEL_NAME=jan-ustg-v1`)

---

## 11. Codex‑Workflow (damit du das Repo „programmieren lässt“)

### 11.1 Arbeitsweise
- Erzeuge pro Feature ein **Issue** im Repo
- Lass Codex jeweils **nur** einen klaren Scope umsetzen
- Verlange:
  - keine Änderungen außerhalb des Scope
  - Tests/Run‑Commands
  - kurze Begründung der Architekturentscheidung

### 11.2 Beispiel‑Prompts an Codex (Copy/Paste)

**Issue 1: Datenmodell + Alembic**
> Implementiere SQLAlchemy‑Modelle und Alembic‑Migrationen gemäß docs/02_datenmodell.md.  
> Erzeuge Tabellen: invoices, projects, prompt_versions, ai_results, training_examples, feedback.  
> Nutze klare Constraints (unique fingerprint, FK‑Beziehungen).  
> Schreibe außerdem ein Seed‑Script für projects.json.

**Issue 2: Upload‑Endpoint**
> Implementiere `POST /api/invoices/upload` (multipart PDF).  
> Speichere Datei in STORAGE_PATH, extrahiere Text, berechne SHA‑256 Fingerprint.  
> Lege invoice‑Datensatz an oder reuse bei bekanntem Fingerprint.  
> Gib JSON mit invoice_id und fingerprint zurück.

**Issue 3: Modul‑Runner**
> Implementiere Worker‑Task `analyze_invoice(invoice_id, project_id)` mit Modulen 1–3.  
> Prompts aus prompt_versions laden (Versioning).  
> LLM via Ollama‑HTTP aufrufen; Output als JSON validieren; Ergebnis in ai_results schreiben.

---

## 12. Betrieb, Updates, Backups

### 12.1 Updates
```bash
git pull
docker compose up -d --build
```

### 12.2 DB‑Backup (Beispiel)
```bash
docker exec -t deploy-db-1 pg_dump -U flowaudit flowaudit > backup_flowaudit.sql
```

### 12.3 Daten‑Backup zu QNAP (Beispiel rsync)
```bash
rsync -avz ./data/ user@qnap:/Backups/flowaudit/data/
```

