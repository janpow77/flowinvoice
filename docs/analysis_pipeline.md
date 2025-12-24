# FlowAudit Analyse-Pipeline

Diese Dokumentation beschreibt die Architektur und den Datenfluss der Rechnungsanalyse, einschließlich der Integration von Rechtstexten (Legal Retrieval).

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ANALYSE-PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Upload  │───▶│  Parser  │───▶│ Precheck │───▶│   RAG    │───▶│  LLM   ││
│  │   PDF    │    │          │    │          │    │ Context  │    │Analyse ││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘│
│                                                         │                    │
│                                                         ▼                    │
│                                                  ┌──────────────┐           │
│                                                  │    Legal     │           │
│                                                  │  Retrieval   │           │
│                                                  │  (optional)  │           │
│                                                  └──────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Datenmodelle (Models)

### 1.1 Dokument-Model

**Datei:** `backend/app/models/document.py`

```python
class Document(Base):
    id: str                    # UUID
    project_id: str            # Zugehöriges Projekt
    ruleset_id: str            # Angewandtes Regelwerk (z.B. "DE_USTG")
    status: DocumentStatus     # UPLOADED, PARSING, PARSED, ANALYZING, ANALYZED
    file_path: str             # Pfad zur PDF-Datei
    raw_text: str              # Extrahierter Volltext
    extracted_data: dict       # Strukturierte Felder (Betrag, Datum, etc.)
```

### 1.2 Analyse-Ergebnis-Model

**Datei:** `backend/app/models/result.py`

```python
class AnalysisResult(Base):
    id: str
    document_id: str           # Referenz zum Dokument
    provider: Provider         # LLM-Provider (OLLAMA, OPENAI, etc.)
    model: str                 # Modell-ID (llama3.1:8b, gpt-4, etc.)
    semantic_check: dict       # Semantische Prüfungsergebnisse
    economic_check: dict       # Wirtschaftlichkeitsprüfung
    beneficiary_match: dict    # Begünstigtenabgleich
    warnings: list[str]        # Warnungen
    overall_assessment: str    # Gesamtbewertung
    confidence: float          # Konfidenz (0-1)
    input_tokens: int          # Token-Verbrauch
    output_tokens: int
    latency_ms: int            # Antwortzeit
```

### 1.3 Regelwerk-Checker-Settings

**Datei:** `backend/app/models/ruleset_checker.py`

Speichert die Prüfmodul-Konfiguration pro Regelwerk:

```python
class RulesetCheckerSettings(Base):
    __tablename__ = "ruleset_checker_settings"

    id: str
    ruleset_id: str            # z.B. "DE_USTG", "EU_VAT"

    # Prüfmodul-Konfigurationen (JSONB)
    risk_checker: dict         # Betrugsrisiko-Prüfungen
    semantic_checker: dict     # Semantische Relevanzprüfung
    economic_checker: dict     # Wirtschaftlichkeitsprüfung
    legal_checker: dict        # Legal Retrieval (Rechtstexte)
```

#### Legal Checker Konfiguration

```python
legal_checker = {
    "enabled": False,              # Aktiviert/Deaktiviert
    "funding_period": "2021-2027", # EU-Förderperiode
    "max_results": 5,              # Max. Rechtstexte
    "min_relevance_score": 0.6,    # Mindest-Relevanz (0-1)
    "use_hierarchy_weighting": True,  # Normenhierarchie-Gewichtung
    "include_definitions": True,   # Legaldefinitionen einbeziehen
}
```

---

## 2. Schemas (Pydantic)

### 2.1 Analyse-Request Schema

**Datei:** `backend/app/llm/adapter.py`

```python
@dataclass
class InvoiceAnalysisRequest:
    """Request für die LLM-Rechnungsanalyse."""

    parse_result: ParseResult          # Extrahierte Rechnungsdaten
    precheck_result: PrecheckResult    # Vorprüfungsergebnisse
    ruleset_id: str                    # Regelwerk-ID
    project_context: dict | None       # Projektinformationen
    beneficiary_context: dict | None   # Begünstigten-Daten
    rag_examples: list[dict] | None    # Ähnliche Rechnungsbeispiele
    legal_context: list[dict] | None   # Relevante Rechtstexte
```

### 2.2 Legal Checker Config Schema

**Datei:** `backend/app/schemas/ruleset_checker.py`

```python
class LegalCheckerConfig(BaseModel):
    """Konfiguration für Legal Retrieval."""

    enabled: bool = False
    funding_period: Literal["2014-2020", "2021-2027"] = "2021-2027"
    max_results: int = Field(default=5, ge=1, le=20)
    min_relevance_score: float = Field(default=0.6, ge=0.0, le=1.0)
    use_hierarchy_weighting: bool = True
    include_definitions: bool = True
```

---

## 3. LLM Adapter

**Datei:** `backend/app/llm/adapter.py`

Der LLM Adapter ist die zentrale Schnittstelle für alle LLM-Anfragen.

### 3.1 Hauptfunktion: `analyze_invoice`

```python
async def analyze_invoice(
    self,
    analysis_request: InvoiceAnalysisRequest,
    provider_type: Provider,
    model: str | None,
    session: AsyncSession | None,
) -> InvoiceAnalysisResult:
    """
    Analysiert eine Rechnung mit dem LLM.

    1. Lädt Regelwerk-Features aus DB
    2. Baut System-Prompt mit Kontext
    3. Baut User-Prompt mit Rechnungsdaten
    4. Führt LLM-Request durch
    5. Parst Response zu strukturiertem Ergebnis
    """
```

### 3.2 Prompt-Aufbau

#### System-Prompt (`_build_system_prompt`)

Der System-Prompt enthält:

1. **Regelwerk-Features**: Pflichtangaben laut Steuerrecht
2. **Vorprüfungsergebnisse**: Bereits erkannte Fehler
3. **RAG-Beispiele**: Ähnliche Fälle (Few-Shot Learning)
4. **Rechtstexte** (wenn aktiviert): Relevante EU-Verordnungen

```python
def _build_system_prompt(
    self,
    ruleset_id: str,
    precheck_result: PrecheckResult,
    rag_examples: list[dict] | None,
    db_features: list[dict] | None,
    db_ruleset_info: dict | None,
    legal_context: list[dict] | None,  # NEU: Rechtstexte
) -> str:
```

#### Rechtstext-Integration im Prompt

```
RELEVANTE RECHTSGRUNDLAGEN:
Die folgenden Rechtstexte sind für die Prüfung relevant:

[1] Art. 53 VO (EU) 2021/1060 (EU-Verordnung):
    (1) Die Mitgliedstaaten stellen sicher, dass alle Austausche
    von Informationen zwischen den Begünstigten und den
    Programmbehörden...

[2] § 14 UStG (Nationales Recht):
    Eine Rechnung muss folgende Angaben enthalten...

Berücksichtige diese Rechtsgrundlagen bei der Analyse.
```

---

## 4. Worker Tasks

**Datei:** `backend/app/worker/tasks.py`

### 4.1 Analyse-Task: `analyze_document_task`

```python
@celery_app.task(bind=True, max_retries=3)
def analyze_document_task(
    self,
    document_id: str,
    provider: str = "LOCAL_OLLAMA",
    model: str | None = None,
) -> dict:
    """
    Celery-Task für Hintergrund-Analyse.

    Ruft die async-Funktion _analyze_document_async auf.
    """
```

### 4.2 Async-Implementierung

```python
async def _analyze_document_async(
    document_id: str,
    provider_str: str,
    model: str | None,
) -> dict:
    """
    Vollständige Analyse-Pipeline:

    1. Dokument aus DB laden
    2. PDF parsen (falls nicht bereits geparst)
    3. Projekt-Zeitraum prüfen
    4. Rule Engine Precheck
    5. RAG-Kontext holen
    6. Legal Retrieval (wenn aktiviert)  ← NEU
    7. LLM-Analyse durchführen
    8. Ergebnis speichern
    """
```

### 4.3 Legal Retrieval Integration

```python
# Legal Retrieval Kontext holen (wenn aktiviert)
legal_context: list[dict] | None = None
ruleset_id = document.ruleset_id or "DE_USTG"

try:
    # Checker-Einstellungen laden
    checker_settings = await session.execute(
        select(RulesetCheckerSettings).where(
            RulesetCheckerSettings.ruleset_id == ruleset_id
        )
    )
    checker_row = checker_settings.scalar_one_or_none()

    if checker_row and checker_row.legal_checker.get("enabled", False):
        legal_config = checker_row.legal_checker

        # Suchanfrage aus Rechnungsdaten bauen
        query_parts = []
        if parse_result.extracted.get("leistung"):
            query_parts.append(parse_result.extracted["leistung"].value)
        if parse_result.extracted.get("beschreibung"):
            query_parts.append(parse_result.extracted["beschreibung"].value)

        # Legal Retrieval durchführen
        legal_service = get_legal_retrieval_service()
        legal_results = legal_service.search(
            query=" ".join(query_parts),
            funding_period=legal_config.get("funding_period", "2021-2027"),
            n_results=legal_config.get("max_results", 5),
            rerank_by_hierarchy=legal_config.get("use_hierarchy_weighting", True),
        )

        # Ergebnisse filtern und formatieren
        if legal_results:
            legal_context = [
                {
                    "norm_citation": r.norm_citation,
                    "content": r.content,
                    "hierarchy_level": r.hierarchy_level,
                    "weighted_score": r.weighted_score,
                }
                for r in legal_results
                if r.weighted_score >= legal_config.get("min_relevance_score", 0.6)
            ]
except Exception as e:
    logger.warning(f"Legal Retrieval Fehler: {e}")
```

---

## 5. Legal Retrieval Service

**Datei:** `backend/app/services/legal_retrieval.py`

### 5.1 Normenhierarchie-Gewichtung

Rechtstexte werden nach ihrer Stellung in der Normenhierarchie gewichtet:

| Level | Typ | Gewicht |
|-------|-----|---------|
| 1 | EU-Primärrecht (Verträge) | 1.5 |
| 2 | EU-Verordnung | 1.4 |
| 3 | EU-Richtlinie | 1.3 |
| 4 | Delegierte Verordnung | 1.2 |
| 5 | Nationales Recht | 1.1 |
| 6 | Verwaltungsvorschrift | 1.0 |
| 7 | Guidance/Leitlinien | 0.9 |

### 5.2 Suchmethode

```python
def search(
    self,
    query: str,
    funding_period: str | None = None,
    n_results: int = 10,
    hierarchy_filter: list[int] | None = None,
    rerank_by_hierarchy: bool = True,
) -> list[LegalSearchResult]:
    """
    Sucht relevante Rechtstexte mit Hierarchie-Reranking.

    1. Query-Embedding erstellen
    2. Vektor-Suche in ChromaDB
    3. Hierarchie-Gewichtung anwenden
    4. Nach gewichtetem Score sortieren
    """
```

### 5.3 Suchergebnis

```python
@dataclass
class LegalSearchResult:
    content: str              # Textinhalt
    norm_citation: str        # z.B. "Art. 53 VO (EU) 2021/1060"
    article: str | None       # Artikelnummer
    paragraph: str | None     # Absatznummer
    hierarchy_level: int      # 1-7
    similarity: float         # Kosinus-Ähnlichkeit (0-1)
    weighted_score: float     # similarity × hierarchy_weight
    cross_references: list    # Querverweise
    definitions_used: list    # Verwendete Legaldefinitionen
    metadata: dict            # Weitere Metadaten
```

---

## 6. Legal Chunker

**Datei:** `backend/app/services/legal_chunker.py`

Der Legal Chunker zerlegt juristische Texte in strukturierte Chunks.

### 6.1 Chunk-Struktur

```python
@dataclass
class LegalChunk:
    content: str              # Chunk-Inhalt
    norm_citation: str        # Normzitat
    article: str | None       # Artikelnummer
    paragraph: str | None     # Absatznummer
    subparagraph: str | None  # Unterabsatz
    hierarchy_level: int      # Normenhierarchie-Level
    cross_references: list    # Querverweise auf andere Artikel
    definitions_used: list    # Verwendete Begriffe aus Art. 2
    chunk_index: int          # Position im Dokument
    total_chunks: int         # Gesamtanzahl Chunks
```

### 6.2 Definitionsextraktion

EU-Verordnungen enthalten in Artikel 2 typischerweise Legaldefinitionen:

```python
# Beispiel: Art. 2 VO (EU) 2021/1060
DEFINITION_PATTERNS = [
    # Matches: 1. „Begriff" bedeutet ...
    re.compile(
        r'(\d+)\.\s*[„"]([\w\-\s]+)["]\s+(.+?)(?=\n\s*\d+\.\s*[„"]|\n\n|\Z)',
        re.DOTALL,
    ),
]
```

Erkannte Definitionen werden:
1. In ChromaDB Collection `legal_definitions` gespeichert
2. Für Chunk-Anreicherung verwendet (bessere Embeddings)

---

## 7. Datenfluss

### 7.1 Normale Rechnungsanalyse

```
1. Upload PDF
   └── Document mit status=UPLOADED erstellt

2. Parsing (Celery Task)
   ├── PDF → Text (PyMuPDF)
   ├── Feldextraktion (Regex + Heuristiken)
   └── Document.status = PARSED

3. Analyse (Celery Task)
   ├── Precheck (Rule Engine)
   │   └── Pflichtfelder prüfen
   ├── RAG-Kontext
   │   └── Ähnliche Rechnungen aus ChromaDB
   ├── LLM-Analyse
   │   ├── System-Prompt mit Regelwerk
   │   ├── User-Prompt mit Rechnungsdaten
   │   └── JSON-Response parsen
   └── AnalysisResult + FinalResult speichern
```

### 7.2 Analyse mit Legal Retrieval

```
1-2. Wie oben

3. Analyse (Celery Task)
   ├── Precheck (Rule Engine)
   ├── RAG-Kontext
   ├── ★ Checker-Settings laden
   │   └── legal_checker.enabled == True?
   ├── ★ Legal Retrieval
   │   ├── Query aus Leistungsbeschreibung
   │   ├── Vektor-Suche in legal_norms
   │   ├── Hierarchie-Reranking
   │   └── Top-N Ergebnisse filtern
   ├── LLM-Analyse
   │   ├── System-Prompt mit:
   │   │   ├── Regelwerk
   │   │   ├── RAG-Beispiele
   │   │   └── ★ Relevante Rechtstexte
   │   └── JSON-Response
   └── Ergebnis speichern
```

---

## 8. Konfiguration im Frontend

**Datei:** `frontend/src/components/settings/CheckersSettings.tsx`

Das Frontend zeigt für jedes Regelwerk eine Konfigurationsseite:

```
┌─────────────────────────────────────────────────┐
│ Prüfmodul-Konfiguration                         │
├─────────────────────────────────────────────────┤
│                                                 │
│ ⚠️  Risikoprüfung                    [Aktiv ▼] │
│     Betrugserkennungen und Plausibilität        │
│                                                 │
│ 🧠 Semantische Prüfung               [Aktiv ▼] │
│     Projektrelevanz und Beschreibungsqualität   │
│                                                 │
│ 📈 Wirtschaftlichkeitsprüfung        [Aktiv ▼] │
│     Budget- und Preiskontrollen                 │
│                                                 │
│ ⚖️  Rechtliche Prüfung              [Inaktiv ▼]│
│     EU-Verordnungen und Förderbedingungen       │
│     ┌─────────────────────────────────────────┐ │
│     │ ℹ️ Legal Retrieval: Aktiviert die Suche │ │
│     │ nach relevanten EU-Verordnungen und     │ │
│     │ Rechtstexten. Ergebnisse werden nach    │ │
│     │ Normenhierarchie gewichtet.             │ │
│     └─────────────────────────────────────────┘ │
│                                                 │
│     [ ] Rechtliche Prüfung aktivieren           │
│     EU-Förderperiode: [2021-2027 ▼]            │
│     Max. Ergebnisse: [====●====] 5              │
│     Min. Relevanz:   [====●====] 60%            │
│     [✓] Normenhierarchie-Gewichtung             │
│     [✓] Legaldefinitionen einbeziehen           │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 9. API-Endpunkte

### Checker-Settings

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/rulesets/{id}/checkers` | Checker-Settings abrufen |
| PUT | `/api/rulesets/{id}/checkers` | Checker-Settings aktualisieren |
| DELETE | `/api/rulesets/{id}/checkers` | Auf Defaults zurücksetzen |

### Legal API

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| POST | `/api/legal/regulations/json` | EU-Verordnung hinzufügen |
| POST | `/api/legal/national-laws/json` | Nationales Recht hinzufügen |
| GET | `/api/legal/search` | Rechtstexte suchen |
| GET | `/api/legal/stats` | Statistiken |
| GET | `/api/legal/definitions` | Legaldefinitionen abrufen |

---

## 10. Beispiel: Vollständiger Analyseprozess

```python
# 1. Dokument hochladen
document = Document(
    project_id="proj-123",
    ruleset_id="EU_VAT",
    file_path="/data/uploads/invoice.pdf",
)

# 2. Parser extrahiert Daten
parse_result = ParseResult(
    raw_text="Rechnung Nr. 2024-001...",
    extracted={
        "rechnungsnummer": ExtractedValue(value="2024-001"),
        "betrag": ExtractedValue(value="5.000,00 EUR"),
        "leistung": ExtractedValue(value="IT-Beratung Förderprojekt"),
    }
)

# 3. Legal Retrieval findet relevante Texte
legal_results = [
    LegalSearchResult(
        norm_citation="Art. 53 VO (EU) 2021/1060",
        content="Die Mitgliedstaaten stellen sicher...",
        hierarchy_level=2,  # EU-Verordnung
        weighted_score=0.84,
    ),
    LegalSearchResult(
        norm_citation="§ 14 UStG",
        content="Eine Rechnung muss folgende Angaben...",
        hierarchy_level=5,  # Nationales Recht
        weighted_score=0.71,
    ),
]

# 4. LLM erhält erweiterten Kontext
system_prompt = """
Du bist ein Experte für steuerliche Rechnungsprüfung.
...

RELEVANTE RECHTSGRUNDLAGEN:
[1] Art. 53 VO (EU) 2021/1060 (EU-Verordnung):
    Die Mitgliedstaaten stellen sicher...

[2] § 14 UStG (Nationales Recht):
    Eine Rechnung muss folgende Angaben...

Berücksichtige diese Rechtsgrundlagen bei der Analyse.
"""

# 5. LLM-Analyse liefert strukturiertes Ergebnis
analysis_result = InvoiceAnalysisResult(
    semantic_check={"relevant": True, "confidence": 0.9},
    economic_check={"reasonable": True},
    warnings=[],
    overall_assessment="APPROVED",
    confidence=0.92,
)
```

---

## Zusammenfassung

| Komponente | Datei | Funktion |
|------------|-------|----------|
| **Model** | `models/ruleset_checker.py` | Speichert Checker-Konfiguration (JSONB) |
| **Schema** | `schemas/ruleset_checker.py` | Pydantic-Validierung für API |
| **LLM Adapter** | `llm/adapter.py` | Baut Prompts, führt LLM-Requests durch |
| **Worker** | `worker/tasks.py` | Celery-Tasks für Hintergrundverarbeitung |
| **Legal Retrieval** | `services/legal_retrieval.py` | Vektor-Suche mit Hierarchie-Gewichtung |
| **Legal Chunker** | `services/legal_chunker.py` | Strukturierte Zerlegung von Rechtstexten |
