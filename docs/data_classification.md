# Datenklassifikation (Data Classification)

Dieses Dokument beschreibt die Klassifikation und Handhabung von Daten im FlowAudit-System.

---

## 1. Übersicht der Datenklassen

| Klasse | Beschreibung | Speicherort | Aufbewahrung | Löschlogik |
|--------|--------------|-------------|--------------|------------|
| **INVOICE_DOCUMENT** | Originale Rechnungsdokumente (PDF) | `/data/uploads` | Projektlaufzeit + 6 Monate | Nach Projektende automatisch |
| **EXTRACTED_TEXT** | Extrahierter Text aus PDFs | PostgreSQL | Mit Dokument verknüpft | Mit Dokument löschen |
| **ANALYSIS_RESULT** | Prüfergebnisse und Audit-Trail | PostgreSQL | 10 Jahre (gesetzlich) | Automatisch nach 10 Jahren |
| **TRAINING_DATA** | Trainings-/Beispieldaten für RAG | ChromaDB | Unbegrenzt | Manuell durch Admin |

---

## 2. Detaillierte Klassifikation

### 2.1 INVOICE_DOCUMENT

**Inhalt:**
- Original-PDF-Dateien
- Hochgeladene Rechnungsbelege
- Gescannte Dokumente

**Speicherung:**
```
/data/uploads/
├── {project_id}/
│   ├── {document_id}.pdf
│   └── {document_id}_metadata.json
```

**Schutzstufe:** VERTRAULICH
- Nur autorisierte Benutzer haben Zugriff
- Keine Weitergabe an Dritte
- Verschlüsselung at-rest empfohlen

**Löschregeln:**
- Automatische Löschung 6 Monate nach Projektende
- Manuelle Löschung durch Admin möglich
- Bei Löschung: Auch verknüpfte Daten entfernen

### 2.2 EXTRACTED_TEXT

**Inhalt:**
- OCR-Ergebnisse
- Strukturierte Textextraktion
- Erkannte Felder und Werte

**Speicherung:**
```sql
-- PostgreSQL Tabelle: document_extractions
CREATE TABLE document_extractions (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    raw_text TEXT,
    structured_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Schutzstufe:** VERTRAULICH
- Gleiche Schutzstufe wie Originaldokument
- Kaskadierte Löschung mit Dokument

### 2.3 ANALYSIS_RESULT

**Inhalt:**
- Prüfergebnisse (FinalResult)
- Audit-Trail (alle Prüfschritte)
- Benutzer-Feedback und Korrekturen
- Konfliktdokumentation

**Speicherung:**
```sql
-- PostgreSQL Tabelle: final_results
CREATE TABLE final_results (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    analysis_status VARCHAR(50),
    metadata JSONB,  -- AnalysisMetadata
    created_at TIMESTAMP WITH TIME ZONE,
    -- Keine ON DELETE CASCADE!
);
```

**Schutzstufe:** ARCHIV (Langzeitaufbewahrung)
- 10-Jahre-Aufbewahrungspflicht für Audit-Zwecke
- Nicht mit Dokument löschen
- Anonymisierung nach Frist möglich

**Pflichtfelder für Audit-Trail:**
- `document_fingerprint` (SHA-256)
- `ruleset_id` + `ruleset_version`
- `model_id` + `prompt_version`
- `analysis_timestamp`
- `system_version`

### 2.4 TRAINING_DATA

**Inhalt:**
- Validierte Beispiel-Rechnungen für RAG
- Few-Shot-Beispiele
- Embedding-Vektoren

**Speicherung:**
```
ChromaDB Collection: flowaudit_examples
├── Embeddings (Vektoren)
├── Metadata (Ruleset, Dokumenttyp)
└── Documents (Beispieltexte)
```

**Schutzstufe:** INTERN
- Nur anonymisierte/generierte Daten
- Keine echten Kundendaten im Training
- Manuelle Verwaltung durch Administratoren

---

## 3. Datenschutz-Anforderungen

### 3.1 Personenbezogene Daten

Folgende Felder können personenbezogene Daten enthalten:

| Feld | Kategorie | Handling |
|------|-----------|----------|
| `vendor_name` | Geschäftsdaten | Standard-Schutz |
| `customer_name` | ggf. personenbezogen | Bei natürlichen Personen: DSGVO |
| `beneficiary_name` | Geschäftsdaten | Standard-Schutz |
| `vat_id` | Geschäfts-ID | Standard-Schutz |
| `bank_details` | Finanzdaten | Erhöhter Schutz |

### 3.2 Löschfristen

```
┌─────────────────────────────────────────────────────────────┐
│ LÖSCHFRIST-HIERARCHIE                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dokumente          → 6 Monate nach Projektende            │
│  Extrahierter Text  → Mit Dokument                         │
│  Analyseergebnisse  → 10 Jahre (Audit-Pflicht)             │
│  Trainingsdaten     → Manuell / nie (anonymisiert)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Auskunftsrecht

Bei Auskunftsersuchen (Art. 15 DSGVO):

1. Suche nach `customer_name` in allen Dokumenten
2. Export der verknüpften Daten
3. Pseudonymisierte Analyseergebnisse bereitstellen

---

## 4. Technische Umsetzung

### 4.1 Enum-Definition

```python
class DataClassification(str, Enum):
    """Datenklassifikation für Speicherung und Löschung."""

    INVOICE_DOCUMENT = "INVOICE_DOCUMENT"
    EXTRACTED_TEXT = "EXTRACTED_TEXT"
    ANALYSIS_RESULT = "ANALYSIS_RESULT"
    TRAINING_DATA = "TRAINING_DATA"
```

### 4.2 Lösch-Service (Pseudocode)

```python
async def delete_project_data(
    project_id: str,
    classification: DataClassification,
    force: bool = False
) -> DeleteResult:
    """
    Löscht Daten einer bestimmten Klassifikation.

    Args:
        project_id: Projekt-ID
        classification: Zu löschende Datenklasse
        force: Auch bei Aufbewahrungspflicht löschen

    Returns:
        Löschergebnis mit Statistiken
    """
    if classification == DataClassification.ANALYSIS_RESULT and not force:
        # Prüfe 10-Jahres-Frist
        if not retention_period_expired(project_id):
            raise RetentionPeriodActiveError()

    # Löschung durchführen
    ...
```

### 4.3 Anonymisierungs-Service

```python
def anonymize_for_training(document_data: dict) -> dict:
    """
    Anonymisiert Dokumentdaten für Trainingszwecke.

    Ersetzt:
    - Namen → Generische Bezeichnungen
    - Adressen → Fiktive Adressen
    - IDs → Generierte IDs
    """
    anonymized = document_data.copy()

    # Personenbezogene Felder ersetzen
    anonymized["vendor_name"] = generate_fake_company()
    anonymized["customer_name"] = generate_fake_company()
    anonymized["address"] = generate_fake_address()

    # IDs neu generieren
    anonymized["vat_id"] = generate_valid_vat_id_format()

    return anonymized
```

---

## 5. Backup und Recovery

### 5.1 Backup-Strategie

| Datenklasse | Backup-Intervall | Aufbewahrung | Verschlüsselung |
|-------------|------------------|--------------|-----------------|
| INVOICE_DOCUMENT | Täglich | 30 Tage | AES-256 |
| EXTRACTED_TEXT | Mit PostgreSQL | 30 Tage | AES-256 |
| ANALYSIS_RESULT | Mit PostgreSQL | 90 Tage | AES-256 |
| TRAINING_DATA | Wöchentlich | 30 Tage | Optional |

### 5.2 Recovery-Priorität

1. **Kritisch:** ANALYSIS_RESULT (Audit-Trail)
2. **Hoch:** INVOICE_DOCUMENT (Originale)
3. **Mittel:** EXTRACTED_TEXT (regenerierbar)
4. **Niedrig:** TRAINING_DATA (rekonstruierbar)

---

## 6. Checkliste für Entwickler

### Bei neuen Datenfeldern:

- [ ] Datenklassifikation festlegen
- [ ] Aufbewahrungsfrist definieren
- [ ] Löschlogik implementieren
- [ ] Backup-Strategie prüfen
- [ ] DSGVO-Relevanz dokumentieren

### Bei Datenlöschung:

- [ ] Aufbewahrungsfristen prüfen
- [ ] Kaskadierte Abhängigkeiten beachten
- [ ] Audit-Trail nicht löschen (10 Jahre)
- [ ] Löschung protokollieren

---

## Anhang: Rechtliche Grundlagen

| Regelung | Relevanz | Auswirkung |
|----------|----------|------------|
| DSGVO Art. 17 | Recht auf Löschung | Löschfristen beachten |
| DSGVO Art. 15 | Auskunftsrecht | Export-Funktion |
| GoBD | Aufbewahrungspflicht | 10 Jahre für Belege |
| AO §147 | Steuerliche Aufbewahrung | 10 Jahre für Rechnungen |
