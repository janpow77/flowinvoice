# FlowAudit – Arbeitsanweisung für Claude Code
## Verbindliche Schritt-für-Schritt-Implementierungsanleitung

---

## 0. Zweck dieser Datei

Diese Datei ist **die zentrale Steuerungsanweisung für Claude Code**.  
Sie ersetzt **jede implizite Interpretation**.

Claude Code arbeitet **ausschließlich** nach dieser Datei und den referenzierten Markdown-Dokumenten im Repository.

Ziel ist:
- eine **vollständig lauffähige**
- **getestete**
- **revisionssichere**
- **didaktisch transparente**

Implementierung des Systems **FlowAudit** als **Monorepo**, ausgelegt für:
- lokale LLMs auf einem ASUS NUC (64 GB RAM)
- optional externe APIs (OpenAI, Gemini)
- Seminar- und Demo-Betrieb

---

## 1. Absolute Grundregeln (nicht verhandelbar)

### 1.1 Keine Abkürzungen
- **Kein Pseudocode**
- **Keine Platzhalter**
- **Keine „Patch“-Snippets**
- **Keine TODOs**

👉 Jede Datei ist **vollständig**, **kompilierbar** und **testbar**.

---

### 1.2 Pfadpflicht
Jede ausgegebene Datei beginnt **immer** mit:

```text
# Pfad: /relativer/pfad/zur/datei.ext
````

---

### 1.3 Keine leeren Dateien

* `__init__.py` **darf nicht leer sein**
* jede Datei enthält mindestens:

  * Docstring
  * Imports
  * expliziten Zweck

---

### 1.4 Keine Annahmen

Claude Code darf:

* **nichts hinzuerfinden**
* **nichts weglassen**
* **nichts zusammenfassen**

Wenn etwas unklar ist → **nachfragen**, nicht entscheiden.

---

## 2. Repository-Struktur (verbindlich)

Claude Code **muss exakt** folgende Struktur erzeugen:

```
flowaudit/
├── CLAUDE.md
├── docker/
│   ├── docker-compose.yml
│   ├── ollama/
│   │   └── Dockerfile
│   └── postgres/
│       └── init.sql
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   ├── llm/
│   │   ├── rag/
│   │   └── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── store/
│   │   └── i18n/
│   └── package.json
├── docs/
│   ├── requirements.md
│   ├── api_contracts.md
│   ├── rulesets.md
│   ├── architecture.md
│   └── rag_learning.md
└── data/
    ├── generated_invoices/
    ├── solutions/
    └── logs/
```

---

## 3. Arbeitsreihenfolge (zwingend)

Claude Code arbeitet **linear**, kein Springen.

### Phase 1 – Dokumente lesen

Claude **muss zuerst vollständig lesen**:

1. `/docs/requirements.md`
2. `/docs/rulesets.md`
3. `/docs/api_contracts.md`
4. `/docs/architecture.md`

👉 Danach **kurz bestätigen**, dass alle Anforderungen verstanden wurden.

---

### Phase 2 – Backend (zuerst)

1. Datenbankmodelle (SQLAlchemy)
2. Migration / init.sql
3. API-Endpunkte exakt gemäß `api_contracts.md`
4. Parser + Regel-Engine
5. PreparePayload-Erzeugung (Input-JSON)
6. LLM-Adapter (lokal + extern)
7. RAG-Komponente
8. Statistik-Engine

➡️ Jeder Schritt mit **Unit-Tests**

---

### Phase 3 – Frontend

1. Seiten:

   * Dashboard
   * ProjectPage
   * UploadPage
   * ResultsPage
   * DetailView
   * SettingsPage
   * GeneratorPage (Admin)
2. Komponenten:

   * Cards mit expandierbaren Rows
   * PDF-Viewer + Overlay
   * JSON-Viewer (read-only)
   * Fortschrittsanimation (Logo-Kreis + Prozent)
3. i18n:

   * Deutsch / Englisch vollständig

---

### Phase 4 – Generator

* PDF-Erzeugung mit:

  * 5 Templates
  * variabler Typografie
  * konfigurierbaren Fehlerquoten
* Speicherung:

  * PDFs → `/data/generated_invoices`
  * Lösungen → `/data/solutions/*.txt`
* **KI darf keinen Zugriff auf solutions haben**

---

### Phase 5 – Tests & Validierung

Claude Code **muss**:

* alle APIs testen
* Generator gegen Rulesets testen
* Konfliktfälle (Regel vs KI) testen
* RAG-Lernen nachweisen (Vorher/Nachher)

---

## 4. LLM-Integration (verbindlich)

### 4.1 Lokales LLM (Standard)

* Ollama
* Empfohlenes Modell:

  * `llama3:8b-instruct-q4`
* Parameter:

  * temperature (UI-einstellbar)
  * max_tokens
  * timeout

### 4.2 Externe APIs (optional)

* OpenAI
* Gemini
* API-Key:

  * maskiert
  * sichtbar als „gesetzt“

### 4.3 Einheitliches Interface

Claude implementiert **ein einziges Interface**:

```python
class LLMProvider:
    def analyze(payload: dict) -> dict
```

---

## 5. Transparenzpflicht

Claude Code **muss sicherstellen**:

* Input-JSON wird gespeichert (`prepare_payloads`)
* Response-JSON wird gespeichert
* Logs zeigen:

  * Modell
  * Tokens
  * Laufzeit
* UI zeigt:

  * Input-JSON
  * Response-JSON
  * Confidence Scores

---

## 6. Lernen (RAG, nicht Fine-Tuning)

⚠️ **Kein echtes Weight-Finetuning** im Livebetrieb.

Stattdessen:

* Vektor-DB (ChromaDB)
* Speicherung korrigierter Beispiele
* Retrieval bei ähnlichen Rechnungen
* Dynamic Few-Shot Injection

UI zeigt:

* Anzahl gelernter Beispiele
* Trefferquote vorher / nachher

---

## 7. Abbruchregeln

Claude Code **bricht ab**, wenn:

* Anforderungen widersprüchlich sind
* Regeln fehlen
* JSON-Schemas unklar sind

👉 Dann **gezielt nachfragen**.

---

## 8. Definition of Done (global)

FlowAudit gilt als **fertig**, wenn:

* alle Funktionen aus `requirements.md` existieren
* alle Rulesets korrekt angewendet werden
* Generator reproduzierbar ist
* kein Prompt sichtbar ist, aber Input-JSON vollständig
* Lernkurve und Statistik sichtbar sind
* alles lokal auf dem NUC läuft

---

## 9. Abschlussregel

Claude Code ist **Implementierer**, nicht Architekt.

Die Architektur ist vorgegeben.
Die Gesetze sind vorgegeben.
Die Didaktik ist vorgegeben.

**Keine Vereinfachung. Keine Interpretation.**
