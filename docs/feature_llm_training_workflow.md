# LLM-Training Workflow - Feature-Spezifikation

## Übersicht

Dieses Dokument beschreibt den erweiterten Workflow für das Training des LLM-Systems durch:
1. Manuelle Prüfung und Korrektur von Analyseergebnissen
2. Import von Lösungsdateien aus dem Rechnungsgenerator
3. Kombinierte Workflows (manuell + automatisch)

---

## Aktueller Stand

### Was funktioniert

| Komponente | Status | Beschreibung |
|------------|--------|--------------|
| Backend FinalResult | ✓ | Speichert Merkmale mit `fields[]` |
| Backend Feedback-API | ✓ | Akzeptiert `FeedbackOverride` pro Merkmal |
| RAG-Lernen | ✓ | Speichert Korrekturen in ChromaDB |
| Frontend Analyse-Ansicht | ⚠️ | Zeigt nur Gesamtbewertung |
| Frontend Korrektur-Formular | ❌ | Nicht implementiert |
| Lösungsdatei-Import | ❌ | Nicht implementiert |

### Was fehlt

1. **Merkmals-Detail-Ansicht** im Frontend
2. **Korrektur-Formular** pro Merkmal
3. **Lösungsdatei-Upload** (API + UI)
4. **Merge-Logik** (manuell vs. Lösungsdatei)

---

## Gewünschter Workflow

### Workflow A: Rein manuell

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Rechnung hochladen                                          │
│     └─→ PDF wird geparst, Text extrahiert                       │
│                                                                 │
│  2. KI-Analyse starten                                          │
│     └─→ LLM prüft gegen Kriterienkatalog                        │
│                                                                 │
│  3. Ergebnis anzeigen (NEU)                                     │
│     ├─→ ✓ Eingehaltene Merkmale (grün)                          │
│     ├─→ ✗ Nicht eingehaltene Merkmale (rot)                     │
│     └─→ ? Nicht gefundene Merkmale (grau)                       │
│                                                                 │
│  4. Manuelle Korrektur (NEU)                                    │
│     └─→ Pro Merkmal: Wert ändern + Begründung                   │
│                                                                 │
│  5. Feedback absenden                                           │
│     └─→ RAG lernt aus Korrekturen                               │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow B: Mit Lösungsdatei

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Rechnungen hochladen (Bulk: 500 PDFs)                       │
│     └─→ Alle werden geparst                                     │
│                                                                 │
│  2. KI-Analyse starten (Batch)                                  │
│     └─→ Celery verarbeitet alle asynchron                       │
│                                                                 │
│  3. Lösungsdatei hochladen (NEU)                                │
│     └─→ CSV/JSON mit Ground-Truth vom Generator                 │
│                                                                 │
│  4. Automatisches Matching                                      │
│     └─→ Rechnungs-ID → Korrekte Werte                           │
│                                                                 │
│  5. Differenz-Ansicht (NEU)                                     │
│     ├─→ Was LLM erkannt hat                                     │
│     ├─→ Was korrekt wäre (aus Lösungsdatei)                     │
│     └─→ Abweichungen markiert                                   │
│                                                                 │
│  6. Bulk-Akzeptieren                                            │
│     └─→ RAG lernt aus allen Korrekturen                         │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow C: Kombiniert (manuell + Lösungsdatei)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Einzelne Rechnung analysieren                               │
│                                                                 │
│  2. Ergebnis manuell prüfen                                     │
│     └─→ Eigene Korrekturen eingeben                             │
│                                                                 │
│  3. Lösungsdatei hochladen (optional)                           │
│                                                                 │
│  4. Merge-Dialog (NEU)                                          │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ Merkmal       │ LLM    │ Manuell │ Lösung  │ Final     │ │
│     ├───────────────┼────────┼─────────┼─────────┼───────────┤ │
│     │ Rechnungsdatum│ 01.03. │ -       │ 01.03.  │ ○ LLM     │ │
│     │ Leistungsort  │ Berlin │ Hamburg │ Hamburg │ ● Manuell │ │
│     │ USt-Satz      │ 19%    │ -       │ 7%      │ ○ Lösung  │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│  5. Priorität wählen:                                           │
│     ○ Manuell überschreibt Lösungsdatei                         │
│     ○ Lösungsdatei überschreibt Manuell                         │
│     ○ Einzeln entscheiden                                       │
│                                                                 │
│  6. Absenden → RAG lernt                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lösungsdatei-Format

### Option 1: CSV (einfach)

```csv
invoice_id,invoice_number,invoice_date,supplier_name,supplier_address,service_description,service_location,net_amount,vat_rate,vat_amount,gross_amount,is_valid,error_codes
INV-001,RE-2025-001,2025-03-15,Mustermann GmbH,"Musterstr. 1, 12345 Berlin",Beratungsleistung,Berlin,1000.00,19,190.00,1190.00,true,
INV-002,RE-2025-002,2025-03-16,Test AG,"Testweg 5, 54321 München",Lieferung Büromaterial,München,500.00,19,95.00,595.00,false,WRONG_VAT_RATE;MISSING_SERVICE_PERIOD
```

### Option 2: JSON (strukturiert)

```json
{
  "generator_version": "1.0.0",
  "generated_at": "2025-03-20T10:00:00Z",
  "invoices": [
    {
      "invoice_id": "INV-001",
      "filename": "rechnung_001.pdf",
      "fields": {
        "invoice_number": { "value": "RE-2025-001", "valid": true },
        "invoice_date": { "value": "2025-03-15", "valid": true },
        "supplier_name": { "value": "Mustermann GmbH", "valid": true },
        "supplier_address": { "value": "Musterstr. 1, 12345 Berlin", "valid": true },
        "service_description": { "value": "Beratungsleistung", "valid": true },
        "service_location": { "value": "Berlin", "valid": true },
        "service_period_start": { "value": "2025-03-01", "valid": true },
        "service_period_end": { "value": "2025-03-15", "valid": true },
        "net_amount": { "value": 1000.00, "currency": "EUR", "valid": true },
        "vat_rate": { "value": 19, "valid": true },
        "vat_amount": { "value": 190.00, "currency": "EUR", "valid": true },
        "gross_amount": { "value": 1190.00, "currency": "EUR", "valid": true }
      },
      "validation": {
        "is_valid": true,
        "errors": [],
        "warnings": []
      }
    },
    {
      "invoice_id": "INV-002",
      "filename": "rechnung_002.pdf",
      "fields": {
        "invoice_number": { "value": "RE-2025-002", "valid": true },
        "invoice_date": { "value": "2025-03-16", "valid": true },
        "vat_rate": { "value": 7, "valid": false, "expected": 19, "error": "WRONG_VAT_RATE" }
      },
      "validation": {
        "is_valid": false,
        "errors": [
          { "code": "WRONG_VAT_RATE", "feature_id": "vat_rate", "message": "Falscher USt-Satz: 7% statt 19%" },
          { "code": "MISSING_SERVICE_PERIOD", "feature_id": "service_period", "message": "Leistungszeitraum fehlt" }
        ],
        "warnings": []
      }
    }
  ]
}
```

### Option 3: JSONL (für Streaming/große Dateien)

```jsonl
{"invoice_id":"INV-001","filename":"rechnung_001.pdf","invoice_number":"RE-2025-001","invoice_date":"2025-03-15","is_valid":true}
{"invoice_id":"INV-002","filename":"rechnung_002.pdf","invoice_number":"RE-2025-002","invoice_date":"2025-03-16","is_valid":false,"errors":["WRONG_VAT_RATE"]}
```

---

## Matching-Strategien

Wie wird eine Rechnung der Lösungsdatei zugeordnet?

### Strategie 1: Dateiname (empfohlen)

```
Hochgeladene PDF: rechnung_001.pdf
Lösungsdatei:     { "filename": "rechnung_001.pdf", ... }
→ Match!
```

### Strategie 2: Rechnungsnummer

```
Extrahiert aus PDF: RE-2025-001
Lösungsdatei:       { "invoice_number": "RE-2025-001", ... }
→ Match!
```

### Strategie 3: Hash/ID aus Generator

```
Generator erzeugt: invoice_id = "abc123"
PDF-Metadaten:     XMP:invoice_id = "abc123"
→ Match!
```

### Strategie 4: Kombination

```
Dateiname + Rechnungsnummer müssen übereinstimmen
→ Höhere Sicherheit bei Duplikaten
```

---

## UI-Mockups

### Merkmals-Übersicht (DocumentDetail)

```
┌─────────────────────────────────────────────────────────────────┐
│  📄 Rechnung: RE-2025-001.pdf                                   │
│  Hochgeladen: 20.03.2025                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  KRITERIENKATALOG                                    [Lösung ↑] │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ✓ Eingehaltene Merkmale (8)                          [▼]       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✓ Rechnungsnummer      RE-2025-001                         ││
│  │ ✓ Rechnungsdatum       15.03.2025                          ││
│  │ ✓ Lieferantenname      Mustermann GmbH                     ││
│  │ ✓ Nettobetrag          1.000,00 €                          ││
│  │ ...                                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ✗ Nicht eingehaltene Merkmale (2)                    [▼]       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✗ Leistungsort         Berlin          [Korrigieren]       ││
│  │   └─ Erwartet: Hamburg (laut Projektstandort)              ││
│  │                                                             ││
│  │ ✗ USt-Satz             7%              [Korrigieren]       ││
│  │   └─ Erwartet: 19% (Standardsatz für Dienstleistung)       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ? Nicht gefundene Merkmale (1)                       [▼]       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ? Leistungszeitraum    nicht erkannt   [Nachtragen]        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [Alle akzeptieren]  [Korrekturen speichern]  [Abbrechen]      │
└─────────────────────────────────────────────────────────────────┘
```

### Korrektur-Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│  Merkmal korrigieren: Leistungsort                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LLM-Ergebnis:    Berlin                                        │
│  Regel-Ergebnis:  -                                             │
│  Lösungsdatei:    Hamburg (falls geladen)                       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Korrigierter Wert:                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Hamburg                                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Begründung:                                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Leistung wurde am Projektstandort Hamburg erbracht,        ││
│  │ nicht am Firmensitz Berlin.                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Fehlertyp:                                                     │
│  ○ LLM-Fehler (falsch erkannt)                                  │
│  ● Kontextfehler (richtig erkannt, aber falsch interpretiert)   │
│  ○ Dokument-Fehler (Rechnung selbst ist fehlerhaft)             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                              [Abbrechen]  [Korrektur speichern] │
└─────────────────────────────────────────────────────────────────┘
```

### Lösungsdatei-Import

```
┌─────────────────────────────────────────────────────────────────┐
│  Lösungsdatei importieren                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                             ││
│  │        📁 Datei hierher ziehen                              ││
│  │           oder klicken zum Auswählen                        ││
│  │                                                             ││
│  │        Unterstützte Formate: CSV, JSON, JSONL               ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Matching-Strategie:                                            │
│  ● Dateiname                                                    │
│  ○ Rechnungsnummer                                              │
│  ○ Generator-ID                                                 │
│                                                                 │
│  Bei Konflikten mit manuellen Eingaben:                         │
│  ○ Lösungsdatei überschreibt manuelle Eingaben                  │
│  ● Manuelle Eingaben behalten (Lösungsdatei nur für Leere)      │
│  ○ Einzeln nachfragen                                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                      [Abbrechen]  [Importieren] │
└─────────────────────────────────────────────────────────────────┘
```

### Import-Ergebnis

```
┌─────────────────────────────────────────────────────────────────┐
│  Import abgeschlossen                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Zusammenfassung                                             │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Rechnungen in Datei:          500                              │
│  Erfolgreich gematcht:         487  ✓                           │
│  Nicht gefunden:               13   ⚠️                           │
│                                                                 │
│  Korrekturen erstellt:         1.245                            │
│  RAG-Beispiele generiert:      1.245                            │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ⚠️ Nicht gematchte Rechnungen:                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ rechnung_088.pdf - Datei nicht im System                   ││
│  │ rechnung_142.pdf - Datei nicht im System                   ││
│  │ ...                                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                        [OK]     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technische Implementierung

### Neue API-Endpunkte

```
POST /api/projects/{project_id}/solutions/upload
     Body: multipart/form-data mit Lösungsdatei
     Response: { matched: 487, not_found: 13, corrections_created: 1245 }

GET  /api/projects/{project_id}/solutions/preview
     Query: ?solution_file_id=xxx
     Response: Vorschau der Matches ohne Speicherung

POST /api/projects/{project_id}/solutions/apply
     Body: { solution_file_id, merge_strategy, override_manual }
     Response: { applied: true, rag_examples_created: 1245 }

GET  /api/documents/{id}/comparison
     Query: ?solution_file_id=xxx
     Response: { llm_values, solution_values, differences }
```

### Neue Frontend-Komponenten

```
src/
├── components/
│   ├── DocumentFeatureList.tsx      # Merkmals-Übersicht
│   ├── FeatureCorrectionDialog.tsx  # Korrektur-Modal
│   ├── SolutionFileUpload.tsx       # Upload-Komponente
│   ├── SolutionComparisonView.tsx   # Vergleichsansicht
│   └── MergeStrategySelector.tsx    # Merge-Optionen
└── pages/
    └── DocumentDetail.tsx           # Erweitert mit Features
```

### Datenbank-Erweiterungen

```sql
-- Neue Tabelle für Lösungsdateien
CREATE TABLE solution_files (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    filename VARCHAR(255) NOT NULL,
    format VARCHAR(10) NOT NULL,  -- 'csv', 'json', 'jsonl'
    content JSONB NOT NULL,       -- Geparster Inhalt
    record_count INTEGER,
    matched_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Neue Tabelle für Solution-Matches
CREATE TABLE solution_matches (
    id UUID PRIMARY KEY,
    solution_file_id UUID REFERENCES solution_files(id),
    document_id UUID REFERENCES documents(id),
    match_strategy VARCHAR(50),   -- 'filename', 'invoice_number', etc.
    match_confidence FLOAT,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Implementierungs-Reihenfolge

### Phase 1: Merkmals-Ansicht (Frontend)
1. `DocumentFeatureList` Komponente erstellen
2. `DocumentDetail.tsx` erweitern
3. Farbcodierung (grün/rot/grau) implementieren
4. Collapsible Sections für Kategorien

### Phase 2: Korrektur-Formular (Frontend + Backend)
1. `FeatureCorrectionDialog` Modal erstellen
2. Feedback-API mit Overrides verbinden
3. Inline-Edit für einfache Korrekturen
4. Begründungs-Feld mit Vorschlägen

### Phase 3: Lösungsdatei-Import (Backend)
1. Upload-Endpunkt implementieren
2. Parser für CSV/JSON/JSONL
3. Matching-Logik implementieren
4. Preview-Endpunkt

### Phase 4: Lösungsdatei-Import (Frontend)
1. `SolutionFileUpload` Komponente
2. Drag & Drop Support
3. Format-Erkennung
4. Matching-Strategie Auswahl

### Phase 5: Merge & Apply
1. `SolutionComparisonView` für Differenzen
2. Merge-Strategie Implementierung
3. Bulk-Apply mit Progress-Anzeige
4. RAG-Learning Integration

---

## Offene Fragen

1. **Lösungsdatei-Format**: Welches Format verwendet der Rechnungsgenerator aktuell?
2. **Matching**: Haben die generierten Rechnungen eine eindeutige ID?
3. **Fehler-Codes**: Gibt es eine definierte Liste von Fehler-Codes im Generator?
4. **Merge-Default**: Sollen manuelle Eingaben standardmäßig Vorrang haben?
5. **Bulk-Limit**: Wie viele Rechnungen sollen maximal gleichzeitig verarbeitet werden?

---

## Nächste Schritte

Nach Freigabe dieser Spezifikation:

1. [ ] Lösungsdatei-Format finalisieren
2. [ ] Phase 1 implementieren (Merkmals-Ansicht)
3. [ ] Phase 2 implementieren (Korrektur-Formular)
4. [ ] Phase 3-5 implementieren (Lösungsdatei-Import)
5. [ ] End-to-End Tests mit generierten Rechnungen
