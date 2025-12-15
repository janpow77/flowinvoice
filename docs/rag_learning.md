# FlowAudit – RAG & Lernmechanismus
## Retrieval-Augmented Generation für kontinuierliche Verbesserung
## Version: 1.0.0

---

## 0. Zweck dieses Dokuments

Dieses Dokument beschreibt den **Lernmechanismus** von FlowAudit:

- Wie das System aus menschlichem Feedback lernt
- Technische Umsetzung mit ChromaDB
- Embedding-Strategie und Retrieval-Logik
- Few-Shot-Injection in LLM-Prompts
- Metriken zur Erfolgsmessung

**Wichtig:** FlowAudit verwendet **kein Weight-Fine-Tuning** im Livebetrieb, sondern **Retrieval-Augmented Generation (RAG)** mit dynamischem Few-Shot-Learning.

---

## 1. Konzept: Warum RAG statt Fine-Tuning?

### 1.1 Vergleich der Ansätze

| Aspekt | Fine-Tuning | RAG (FlowAudit) |
|--------|-------------|-----------------|
| **Trainingsaufwand** | Hoch (GPU, Stunden) | Gering (CPU, Sekunden) |
| **Datenbedarf** | Hunderte Beispiele | Ab 1 Beispiel wirksam |
| **Aktualisierung** | Neues Modell nötig | Sofort nach Feedback |
| **Nachvollziehbarkeit** | Blackbox | Transparent (welche Beispiele?) |
| **Didaktischer Wert** | Gering | Hoch (zeigt Lernprozess) |

### 1.2 Grundprinzip

```
┌──────────────────────────────────────────────────────────────────┐
│                     RAG Learning Pipeline                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. FEEDBACK                    2. EMBEDDING                     │
│  ┌──────────────┐              ┌──────────────┐                  │
│  │ User accepts │              │ Sentence     │                  │
│  │ or corrects  │─────────────▶│ Transformer  │                  │
│  │ LLM result   │   text       │ encodes text │                  │
│  └──────────────┘              └──────┬───────┘                  │
│                                       │ vector                    │
│                                       ▼                           │
│  3. STORAGE                    4. RETRIEVAL                      │
│  ┌──────────────┐              ┌──────────────┐                  │
│  │ ChromaDB     │              │ Similarity   │                  │
│  │ stores       │◀────────────▶│ Search       │                  │
│  │ vector + meta│              │ (cosine)     │                  │
│  └──────────────┘              └──────┬───────┘                  │
│                                       │ top-k                     │
│                                       ▼                           │
│  5. INJECTION                  6. IMPROVED OUTPUT                │
│  ┌──────────────┐              ┌──────────────┐                  │
│  │ Add examples │              │ LLM produces │                  │
│  │ to prompt    │─────────────▶│ better       │                  │
│  │ (few-shot)   │              │ predictions  │                  │
│  └──────────────┘              └──────────────┘                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Technische Komponenten

### 2.1 ChromaDB (Vector Store)

**Konfiguration:**
```python
CHROMA_CONFIG = {
    "host": "chroma",
    "port": 8000,
    "persist_directory": "/data/chroma",
    "anonymized_telemetry": False
}
```

**Collection-Struktur:**
```python
# Eine Collection pro Ruleset für bessere Isolation
COLLECTION_NAME_PATTERN = "rag_examples_{ruleset_id}"

# Beispiel: rag_examples_DE_USTG, rag_examples_EU_VAT, rag_examples_UK_VAT
```

### 2.2 Embedding-Modell

| Aspekt | Spezifikation |
|--------|---------------|
| **Modell** | sentence-transformers/all-MiniLM-L6-v2 |
| **Dimensionen** | 384 |
| **Sprachen** | Mehrsprachig (DE/EN) |
| **Lizenz** | Apache 2.0 |
| **RAM-Bedarf** | ~500 MB |

**Alternativen (optional konfigurierbar):**
- `paraphrase-multilingual-MiniLM-L12-v2` - Besser für DE
- `all-mpnet-base-v2` - Höhere Qualität, mehr RAM

**Code:**
```python
from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """Erzeugt 384-dimensionalen Embedding-Vektor."""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch-Embedding für bessere Performance."""
        return self.model.encode(texts, normalize_embeddings=True).tolist()
```

### 2.3 Was wird eingebettet?

Das Embedding basiert auf einem **kombinierten Text**, der die relevanten Kontextinformationen enthält:

```python
def build_embedding_text(
    parsed_text: str,
    feature_corrections: list[dict],
    project_description: str | None = None
) -> str:
    """
    Baut den Text für das Embedding.

    Struktur:
    - Gekürzte Rechnungsinhalte (Supplier, Beschreibung, Beträge)
    - Korrigierte Features mit Begründung
    - Optional: Projektkontext
    """
    parts = []

    # 1. Extrahierte Schlüsselfelder (max. 500 Zeichen)
    key_text = extract_key_fields(parsed_text)
    parts.append(f"INVOICE: {key_text[:500]}")

    # 2. Korrekturen
    for correction in feature_corrections:
        parts.append(
            f"CORRECTION {correction['feature_id']}: "
            f"{correction['llm_value']} -> {correction['user_value']} "
            f"({correction.get('note', 'no note')})"
        )

    # 3. Projektkontext (optional, gekürzt)
    if project_description:
        parts.append(f"PROJECT: {project_description[:200]}")

    return "\n".join(parts)
```

---

## 3. Datenmodell

### 3.1 RAG Example Schema

```python
class RAGExample(BaseModel):
    """Ein gelerntes Beispiel in ChromaDB."""

    # Identifikation
    rag_example_id: str          # UUID
    document_id: str             # Referenz zum Originaldokument
    feedback_id: str             # Referenz zum Feedback

    # Kontext
    ruleset_id: str              # DE_USTG, EU_VAT, UK_VAT
    ruleset_version: str         # Version zum Zeitpunkt des Feedbacks

    # Embedding-Quelle
    embedding_text: str          # Der Text, der eingebettet wurde
    embedding_model: str         # Modellname für Reproduzierbarkeit

    # Korrekturinformationen
    corrections: list[FeatureCorrection]
    original_llm_response: dict  # Zur Nachvollziehbarkeit

    # Metadaten
    created_at: datetime
    created_by: str              # User-ID oder "system"

    # Qualitätsindikatoren
    confidence_score: float      # 0-1, wie sicher war die Korrektur?
    retrieval_count: int         # Wie oft wurde dieses Beispiel abgerufen?
    positive_feedback_count: int # Wie oft hat es geholfen?


class FeatureCorrection(BaseModel):
    """Eine einzelne Feature-Korrektur."""

    feature_id: str
    llm_status: str              # PRESENT, MISSING, UNCLEAR
    llm_value: str | None
    user_status: str
    user_value: str | None
    note: str | None             # Begründung des Users
```

### 3.2 ChromaDB Metadaten

```python
# Beim Speichern in ChromaDB
collection.add(
    ids=[rag_example_id],
    embeddings=[embedding_vector],
    metadatas=[{
        "document_id": document_id,
        "feedback_id": feedback_id,
        "ruleset_id": ruleset_id,
        "created_at": created_at.isoformat(),
        "correction_features": json.dumps([c.feature_id for c in corrections]),
        "confidence_score": confidence_score
    }],
    documents=[embedding_text]  # Für Debug/Anzeige
)
```

---

## 4. Retrieval-Logik

### 4.1 Retrieval-Prozess

```python
class RAGRetriever:
    def __init__(
        self,
        chroma_client: ChromaClient,
        embedder: Embedder,
        config: RAGConfig
    ):
        self.chroma = chroma_client
        self.embedder = embedder
        self.config = config

    async def retrieve(
        self,
        query_text: str,
        ruleset_id: str,
        top_k: int = 3,
        min_similarity: float = 0.25
    ) -> list[RAGMatch]:
        """
        Findet ähnliche Beispiele für den aktuellen Rechnungstext.

        Args:
            query_text: Kombinierter Text aus Rechnung + Projekt
            ruleset_id: Nur Beispiele aus diesem Ruleset
            top_k: Maximale Anzahl Ergebnisse
            min_similarity: Mindest-Ähnlichkeit (Cosine, 0-1)

        Returns:
            Liste von RAGMatch-Objekten, sortiert nach Ähnlichkeit
        """
        # 1. Query embedden
        query_vector = self.embedder.embed(query_text)

        # 2. Collection abrufen
        collection = self.chroma.get_collection(
            f"rag_examples_{ruleset_id}"
        )

        # 3. Similarity Search
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k * 2,  # Mehr holen, dann filtern
            include=["documents", "metadatas", "distances"]
        )

        # 4. In Matches konvertieren und filtern
        matches = []
        for i, distance in enumerate(results["distances"][0]):
            similarity = 1 - distance  # Cosine distance -> similarity

            if similarity >= min_similarity:
                matches.append(RAGMatch(
                    rag_example_id=results["ids"][0][i],
                    similarity=similarity,
                    embedding_text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i]
                ))

        # 5. Sortieren und limitieren
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:top_k]
```

### 4.2 Retrieval-Konfiguration

```python
class RAGConfig(BaseModel):
    """Konfiguration für RAG-System."""

    enabled: bool = True

    # Retrieval
    top_k: int = 3                    # Max. Anzahl Beispiele
    similarity_threshold: float = 0.25 # Mindest-Ähnlichkeit

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    max_embedding_text_length: int = 1000

    # Injection
    max_examples_in_prompt: int = 3
    example_format: str = "structured"  # structured | narrative

    # Qualitätskontrolle
    min_confidence_score: float = 0.5  # Nur hochwertige Beispiele
    prefer_recent: bool = True         # Neuere Beispiele bevorzugen
```

---

## 5. Few-Shot-Injection

### 5.1 Injektionspunkt im PreparePayload

```python
class PayloadBuilder:
    async def build(
        self,
        document: Document,
        project: Project,
        ruleset: Ruleset,
        rag_retriever: RAGRetriever
    ) -> PreparePayload:
        # ... andere Payload-Teile ...

        # RAG-Kontext hinzufügen
        if self.config.rag_enabled:
            query_text = self.build_rag_query(document, project)
            rag_matches = await rag_retriever.retrieve(
                query_text=query_text,
                ruleset_id=ruleset.ruleset_id,
                top_k=self.config.rag_top_k
            )

            payload.rag_context = RAGContext(
                enabled=True,
                examples=self.format_examples(rag_matches),
                retrieval_info={
                    "query_text_hash": hash(query_text),
                    "matches_count": len(rag_matches),
                    "avg_similarity": sum(m.similarity for m in rag_matches) / len(rag_matches) if rag_matches else 0
                }
            )
        else:
            payload.rag_context = RAGContext(enabled=False, examples=[])

        return payload
```

### 5.2 Beispiel-Format im Prompt

**Strukturiertes Format (Standard):**

```json
{
  "rag_context": {
    "enabled": true,
    "examples": [
      {
        "similarity": 0.87,
        "situation": "Invoice from construction company, missing tax ID",
        "correction": {
          "feature_id": "supplier_tax_or_vat_id",
          "was_detected_as": "PRESENT",
          "correct_status": "MISSING",
          "explanation": "The number '12345' is a customer number, not a tax ID. German tax IDs follow pattern XX/XXX/XXXXX."
        }
      },
      {
        "similarity": 0.72,
        "situation": "Service period stated as 'Q3 2025'",
        "correction": {
          "feature_id": "supply_date_or_period",
          "was_detected_as": "UNCLEAR",
          "correct_status": "PRESENT",
          "explanation": "'Q3 2025' clearly means July-September 2025, which is a valid period specification."
        }
      }
    ]
  }
}
```

**Narratives Format (Alternative):**

```
## Ähnliche Fälle aus früheren Prüfungen:

1. (Ähnlichkeit: 87%) Bei einer Handwerkerrechnung wurde eine Kundennummer
   fälschlicherweise als Steuernummer erkannt. Richtig: MISSING, weil deutsche
   Steuernummern dem Muster XX/XXX/XXXXX folgen.

2. (Ähnlichkeit: 72%) Der Leistungszeitraum "Q3 2025" wurde als UNCLEAR
   klassifiziert. Richtig: PRESENT, weil Q3 eindeutig Juli-September bedeutet.

Bitte berücksichtige diese Erfahrungen bei der aktuellen Prüfung.
```

---

## 6. Feedback-Integration

### 6.1 Wann wird ein RAG-Beispiel erstellt?

```python
class FeedbackProcessor:
    async def process_feedback(
        self,
        feedback: FeedbackCreate,
        final_result: FinalResult
    ) -> Feedback:
        # 1. Feedback speichern
        saved_feedback = await self.repo.save(feedback)

        # 2. Prüfen, ob RAG-Beispiel erstellt werden soll
        should_create_rag = self.should_create_rag_example(feedback)

        if should_create_rag:
            rag_example = await self.create_rag_example(
                feedback=feedback,
                final_result=final_result
            )
            saved_feedback.rag_example_id = rag_example.rag_example_id

        return saved_feedback

    def should_create_rag_example(self, feedback: FeedbackCreate) -> bool:
        """
        Entscheidet, ob ein RAG-Beispiel erstellt werden soll.

        Regeln:
        - CORRECT mit mindestens einer Korrektur: JA
        - PARTIAL mit Korrekturen: JA
        - CORRECT ohne Korrekturen (pure acceptance): NEIN
        - WRONG ohne Details: NEIN
        """
        if feedback.rating == "WRONG" and not feedback.overrides:
            return False

        if feedback.rating == "CORRECT" and not feedback.overrides:
            return False

        return len(feedback.overrides) > 0
```

### 6.2 Qualitätssicherung

```python
def calculate_confidence_score(
    feedback: Feedback,
    corrections: list[FeatureCorrection]
) -> float:
    """
    Berechnet Konfidenz-Score für RAG-Beispiel.

    Faktoren:
    - Anzahl der Korrekturen (mehr = weniger sicher)
    - Vorhandensein von Begründungen
    - User-Expertise (falls verfügbar)
    """
    score = 1.0

    # Viele Korrekturen = komplexer Fall = weniger sicher
    if len(corrections) > 3:
        score -= 0.2

    # Begründungen erhöhen Konfidenz
    noted_corrections = sum(1 for c in corrections if c.note)
    if noted_corrections == len(corrections):
        score += 0.1
    elif noted_corrections == 0 and len(corrections) > 1:
        score -= 0.1

    return max(0.0, min(1.0, score))
```

---

## 7. UI-Integration

### 7.1 Anzeige des Lernfortschritts

**Dashboard-Metriken:**
```json
{
  "rag_stats": {
    "total_examples": 84,
    "examples_by_ruleset": {
      "DE_USTG": 62,
      "EU_VAT": 15,
      "UK_VAT": 7
    },
    "examples_last_7_days": 12,
    "most_corrected_features": [
      {"feature_id": "supplier_tax_or_vat_id", "count": 18},
      {"feature_id": "supply_date_or_period", "count": 14},
      {"feature_id": "supply_description", "count": 9}
    ],
    "avg_retrieval_similarity": 0.68,
    "examples_used_in_last_100_runs": 234
  }
}
```

### 7.2 Transparenz im Detail-View

Nach einer Analyse zeigt die UI:

```
┌─────────────────────────────────────────────────────────────────┐
│ 📚 RAG-Kontext (3 ähnliche Fälle berücksichtigt)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 1. Ähnlichkeit: 87%                                             │
│    └─ Korrektur bei: supplier_tax_or_vat_id                     │
│    └─ Grund: "Kundennummer statt Steuernummer"                  │
│                                                                  │
│ 2. Ähnlichkeit: 72%                                             │
│    └─ Korrektur bei: supply_date_or_period                      │
│    └─ Grund: "Q3 ist ein gültiger Zeitraum"                     │
│                                                                  │
│ 3. Ähnlichkeit: 65%                                             │
│    └─ Korrektur bei: net_amount                                 │
│    └─ Grund: "Dezimaltrennzeichen falsch erkannt"               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Lernkurven-Visualisierung

**API-Endpunkt:**
```
GET /api/stats/learning-curve?ruleset_id=DE_USTG&feature_id=supplier_tax_or_vat_id
```

**Response:**
```json
{
  "feature_id": "supplier_tax_or_vat_id",
  "data_points": [
    {"date": "2025-12-01", "error_rate": 0.32, "rag_examples_count": 5},
    {"date": "2025-12-08", "error_rate": 0.21, "rag_examples_count": 12},
    {"date": "2025-12-15", "error_rate": 0.14, "rag_examples_count": 18}
  ],
  "trend": "improving",
  "improvement_percent": 56.25
}
```

---

## 8. Wartung & Administration

### 8.1 RAG-Beispiele verwalten

**Admin-Endpunkte:**
```
GET    /api/admin/rag/examples          # Liste aller Beispiele
GET    /api/admin/rag/examples/{id}     # Einzelnes Beispiel
DELETE /api/admin/rag/examples/{id}     # Beispiel löschen
POST   /api/admin/rag/rebuild           # Collection neu aufbauen
GET    /api/admin/rag/stats             # Detaillierte Statistiken
```

### 8.2 Collection Maintenance

```python
async def maintenance_job():
    """Regelmäßige Wartung der RAG-Collections."""

    # 1. Verwaiste Einträge entfernen (Dokument gelöscht)
    orphaned = await find_orphaned_examples()
    for example in orphaned:
        await delete_example(example.id)

    # 2. Niedrigqualitative Beispiele markieren
    low_quality = await find_low_quality_examples(
        min_confidence=0.3,
        max_retrievals_without_positive=10
    )
    for example in low_quality:
        await flag_for_review(example.id)

    # 3. Statistiken aktualisieren
    await update_retrieval_stats()
```

### 8.3 Backup & Export

```python
async def export_rag_examples(
    ruleset_id: str,
    format: str = "jsonl"
) -> str:
    """Exportiert RAG-Beispiele für Backup oder Transfer."""

    collection = chroma.get_collection(f"rag_examples_{ruleset_id}")
    all_data = collection.get(include=["documents", "metadatas", "embeddings"])

    output_path = f"/data/backups/rag_{ruleset_id}_{date.today()}.jsonl"

    with open(output_path, "w") as f:
        for i in range(len(all_data["ids"])):
            record = {
                "id": all_data["ids"][i],
                "document": all_data["documents"][i],
                "metadata": all_data["metadatas"][i],
                "embedding": all_data["embeddings"][i]
            }
            f.write(json.dumps(record) + "\n")

    return output_path
```

---

## 9. Erfolgsmessung

### 9.1 Metriken

| Metrik | Beschreibung | Zielwert |
|--------|--------------|----------|
| **Error Rate Reduction** | Fehlerrate vor/nach RAG | > 30% Reduktion |
| **Retrieval Precision** | Relevante Beispiele / Alle Beispiele | > 70% |
| **User Correction Rate** | Korrekturen mit RAG / ohne RAG | < 50% (mit RAG weniger) |
| **Avg. Similarity Score** | Durchschnittliche Ähnlichkeit der Top-K | > 0.5 |

### 9.2 A/B-Testing

```python
async def run_ab_comparison(
    document_ids: list[str],
    with_rag: bool = True
) -> ABComparisonResult:
    """
    Vergleicht Ergebnisse mit und ohne RAG.

    Für Seminar-Demonstrationen.
    """
    results = {
        "with_rag": [],
        "without_rag": []
    }

    for doc_id in document_ids:
        # Mit RAG
        result_with = await analyze(doc_id, rag_enabled=True)
        results["with_rag"].append(result_with)

        # Ohne RAG
        result_without = await analyze(doc_id, rag_enabled=False)
        results["without_rag"].append(result_without)

    return ABComparisonResult(
        document_count=len(document_ids),
        with_rag=aggregate_results(results["with_rag"]),
        without_rag=aggregate_results(results["without_rag"]),
        improvement=calculate_improvement(results)
    )
```

---

## 10. Didaktische Aspekte

### 10.1 Was Teilnehmende lernen

1. **Wie maschinelles Lernen funktioniert** - ohne die Blackbox des Fine-Tunings
2. **Warum Feedback wichtig ist** - direkte Auswirkung sichtbar
3. **Transfer Learning in Aktion** - ähnliche Fälle helfen bei neuen
4. **Grenzen des Systems** - was passiert ohne Beispiele?

### 10.2 Demonstrationsszenarien

**Szenario 1: Erste Rechnung ohne Beispiele**
- System macht Fehler
- User korrigiert
- Beispiel wird gespeichert

**Szenario 2: Ähnliche Rechnung danach**
- System findet das Beispiel
- Macht den gleichen Fehler nicht mehr
- User sieht die Verbesserung

**Szenario 3: Lernkurve über Zeit**
- Dashboard zeigt sinkende Fehlerrate
- Pro Feature einzeln nachvollziehbar
- Anzahl Beispiele vs. Qualität

---

## 11. Grenzen & Einschränkungen

### 11.1 Bekannte Limitierungen

| Limitation | Beschreibung | Workaround |
|------------|--------------|------------|
| **Cold Start** | Ohne Beispiele keine Verbesserung | Generator-Belege mit manuellem Seed |
| **Embedding-Qualität** | Semantische Ähnlichkeit nicht perfekt | Threshold anpassen |
| **Skalierung** | Bei >10.000 Beispielen langsamer | Collection-Sharding |
| **Sprachenmix** | DE/EN in einer Collection | Separate Collections pro Sprache |

### 11.2 Nicht-Ziele

- Kein Ersatz für echtes Fine-Tuning bei Production-Scale
- Keine automatische Qualitätsbewertung der Beispiele
- Kein Cross-Ruleset-Learning (DE → EU nicht automatisch)
