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

### 11.1 Settings (Pflichtfelder)

* Provider: `Local (Ollama)` / `OpenAI` / `Gemini`
* Model selection:

  * Local: `llama3:8b` oder `flowaudit-local-ft-vX`
  * External: konkrete Modellnamen
* API key input (maskiert `********`, aber Indikator „gesetzt“)
* Timeout / Retries
* Parallelism (Dokumente gleichzeitig)
* Logging level (normal/verbose)

### 11.2 Provider Adapter (Backend)

Einheitliches Interface:

* `analyze_invoice(input_json) -> response_json + stats`

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

## 20. Abnahmekriterien (Definition of Done)

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

