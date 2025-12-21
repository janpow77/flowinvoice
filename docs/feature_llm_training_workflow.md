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

## Matching-Strategie

Wie wird eine Rechnung der Lösungsdatei zugeordnet?

### Primär: Dateiname + Position (gewählt)

```
Upload-Reihenfolge:
  1. rechnung_001.pdf
  2. rechnung_002.pdf
  3. rechnung_003.pdf

Lösungsdatei (gleiche Reihenfolge):
  [
    { "position": 1, "filename": "rechnung_001.pdf", ... },
    { "position": 2, "filename": "rechnung_002.pdf", ... },
    { "position": 3, "filename": "rechnung_003.pdf", ... }
  ]

Matching:
  Position 1 + "rechnung_001.pdf" → Match mit Dokument 1
  Position 2 + "rechnung_002.pdf" → Match mit Dokument 2
  ...
```

### Warum Position + Dateiname?

1. **Position allein**: Risiko bei Fehlern in der Reihenfolge
2. **Dateiname allein**: Risiko bei Duplikaten
3. **Beides zusammen**: Doppelte Sicherheit

### Lösungsdatei-Format (empfohlen)

```json
{
  "invoices": [
    { "position": 1, "filename": "rechnung_001.pdf", "fields": {...} },
    { "position": 2, "filename": "rechnung_002.pdf", "fields": {...} }
  ]
}
```

Oder CSV:
```csv
position,filename,invoice_number,invoice_date,...
1,rechnung_001.pdf,RE-2025-001,2025-03-15,...
2,rechnung_002.pdf,RE-2025-002,2025-03-16,...
```

---

## UI-Mockups

### Ansicht 1: Belegliste (Vollbild)

Route: `/documents` oder `/projects/{id}/documents`

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  FlowAudit                                        [Projekt: Förderprojekt 2025 ▼]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  BELEGLISTE                                                    [Lösungsdatei ↑]     │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  🔍 Suchen...                      Filter: [Alle ▼]  [Status ▼]  [Sortierung ▼]     │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  #   │ Dateiname        │ Rechnungs-Nr  │ Betrag    │ Status      │ Aktion │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  1   │ rechnung_001.pdf │ RE-2025-001   │ 1.190,00€ │ ✓ OK        │  [👁]  │    │
│  │  2   │ rechnung_002.pdf │ RE-2025-002   │   595,00€ │ ⚠ Prüfung   │  [👁]  │    │
│  │  3   │ rechnung_003.pdf │ RE-2025-003   │ 2.380,00€ │ ✗ 2 Fehler  │  [👁]  │    │
│  │  4   │ rechnung_004.pdf │ RE-2025-004   │   750,00€ │ ⏳ Analyse   │  [👁]  │    │
│  │  5   │ rechnung_005.pdf │ RE-2025-005   │ 1.500,00€ │ ✓ OK        │  [👁]  │    │
│  │  6   │ rechnung_006.pdf │ -             │     -     │ 📤 Hochgel. │  [👁]  │    │
│  │ ...  │ ...              │ ...           │ ...       │ ...         │  ...   │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Seite 1 von 50  [◀ Zurück]  [1] [2] [3] ... [50]  [Weiter ▶]                       │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📊 Zusammenfassung: 500 Belege │ ✓ 320 OK │ ⚠ 45 Prüfung │ ✗ 35 Fehler │ ⏳ 100    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  [Alle analysieren]    [Lösungsdatei importieren]    [Export CSV]                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Klick auf Beleg → Ansicht 2: Split-View (Detail)

Route: `/documents/{id}/review`

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [← Zurück zur Liste]              rechnung_003.pdf              [◀ Prev] [Next ▶]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                    │                                                │
│  PDF-VIEWER                        │  KRITERIENKATALOG                              │
│  ══════════                        │  ═══════════════                               │
│                                    │                                                │
│  ┌──────────────────────────────┐  │  📋 DE_USTG (§14 UStG)                         │
│  │                              │  │                                                │
│  │     Mustermann GmbH          │  │  ✓ Eingehalten (12)                     [▼]   │
│  │     Musterstraße 1           │  │  ┌──────────────────────────────────────────┐ │
│  │     12345 Berlin             │  │  │ • Rechnungsnummer: RE-2025-003          │ │
│  │                              │  │  │ • Rechnungsdatum: 17.03.2025            │ │
│  │     RECHNUNG                 │  │  │ • Lieferantenname: Mustermann GmbH      │ │
│  │     Nr. RE-2025-003          │  │  │ • Lieferantenadresse: Musterstr. 1...   │ │
│  │     Datum: 17.03.2025        │  │  │ • Nettobetrag: 2.000,00 €               │ │
│  │                              │  │  │ • Bruttobetrag: 2.380,00 €              │ │
│  │     Leistung:                │  │  │ • ...                                   │ │
│  │     IT-Beratung März 2025    │  │  └──────────────────────────────────────────┘ │
│  │                              │  │                                                │
│  │     Netto:      2.000,00 €   │  │  ✗ Nicht eingehalten (2)                 [▼]   │
│  │     USt 19%:      380,00 €   │  │  ┌──────────────────────────────────────────┐ │
│  │     Brutto:     2.380,00 €   │  │  │ Leistungsort                            │ │
│  │                              │  │  │ ─────────────────────────────────────── │ │
│  └──────────────────────────────┘  │  │ Erkannt:  Berlin                        │ │
│                                    │  │ Erwartet: Hamburg (Projektstandort)     │ │
│  [◀ Seite 1/1 ▶]  [🔍 100%] [⛶]   │  │                                          │ │
│                                    │  │ Korrektur: [Hamburg_____________]       │ │
│                                    │  │ Begründung: [____________________]      │ │
│                                    │  │                        [Übernehmen]     │ │
│                                    │  └──────────────────────────────────────────┘ │
│                                    │  ┌──────────────────────────────────────────┐ │
│                                    │  │ USt-Satz                                │ │
│                                    │  │ ─────────────────────────────────────── │ │
│                                    │  │ Erkannt:  7%                            │ │
│                                    │  │ Erwartet: 19% (Standardsatz)            │ │
│                                    │  │                                          │ │
│                                    │  │ Korrektur: [19__________________]       │ │
│                                    │  │ Begründung: [Dienstleistung, kein...]   │ │
│                                    │  │                        [Übernehmen]     │ │
│                                    │  └──────────────────────────────────────────┘ │
│                                    │                                                │
│                                    │  ? Nicht gefunden (1)                    [▼]   │
│                                    │  ┌──────────────────────────────────────────┐ │
│                                    │  │ Leistungszeitraum                       │ │
│                                    │  │ ─────────────────────────────────────── │ │
│                                    │  │ Nicht erkannt                           │ │
│                                    │  │                                          │ │
│                                    │  │ Wert: [01.03.2025 - 31.03.2025]         │ │
│                                    │  │ Begründung: [Im Text erwähnt: "März"]   │ │
│                                    │  │                        [Nachtragen]     │ │
│                                    │  └──────────────────────────────────────────┘ │
│                                    │                                                │
├────────────────────────────────────┴────────────────────────────────────────────────┤
│  [Verwerfen]          [Alle Korrekturen speichern]          [Akzeptieren & Weiter]  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Navigation

```
/documents                    →  Belegliste (Vollbild)
    │
    └── Klick auf Beleg
            ↓
/documents/{id}/review        →  Split-View (PDF + Kriterienkatalog)
    │
    ├── [← Zurück zur Liste]  →  zurück zu /documents
    ├── [◀ Prev]              →  vorheriger Beleg
    └── [Next ▶]              →  nächster Beleg
```

### Belegliste Features

- **Tabellen-Layout** mit sortierbaren Spalten
- **Pagination** für große Datenmengen (500+ Belege)
- **Filter** nach Status (OK/Prüfung/Fehler/Neu)
- **Suche** nach Dateiname oder Rechnungsnummer
- **Zusammenfassung** am unteren Rand
- **Bulk-Aktionen**: Alle analysieren, Lösungsdatei importieren, Export

### Split-View Features

- **PDF links** (~50%): Zoombar, scrollbar, Seiten-Navigation
- **Kriterienkatalog rechts** (~50%): Gruppiert nach Status
- **Inline-Korrektur**: Direkt im Katalog korrigieren
- **Navigation**: Prev/Next zwischen Belegen
- **Aktionen**: Speichern, Akzeptieren & Weiter

---

### Kriterienkatalog (Detail)

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

## Batch-Workflow (Nächtliche Verarbeitung)

### Übersicht

Automatisierte Verarbeitung von generierten Test-Rechnungen über Nacht:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOB (Celery Beat)                                    Zeitplan: täglich 02:00 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  1. RECHNUNGEN ABHOLEN                                                              │
│     └─→ Aus Verzeichnis: /data/training/incoming/                                   │
│     └─→ Oder: S3 Bucket, SFTP, etc.                                                 │
│                                                                                     │
│  2. LÖSUNGSDATEI LADEN                                                              │
│     └─→ solution.json aus gleichem Verzeichnis                                      │
│     └─→ Matching: Dateiname + Position                                              │
│                                                                                     │
│  3. BULK-UPLOAD                                                                     │
│     └─→ Alle PDFs in Projekt "Training-YYYY-MM-DD" hochladen                        │
│     └─→ Position aus Dateiname oder Reihenfolge                                     │
│                                                                                     │
│  4. ANALYSE-PIPELINE                                                                │
│     ┌─────────────────────────────────────────────────────────────────────────┐     │
│     │  PDF → Parser → Rule Engine → Risk Checker → LLM → FinalResult         │     │
│     └─────────────────────────────────────────────────────────────────────────┘     │
│                                                                                     │
│  5. AUTO-FEEDBACK                                                                   │
│     └─→ Lösungsdatei mit LLM-Ergebnis vergleichen                                   │
│     └─→ Differenzen als Korrekturen speichern                                       │
│     └─→ RAG mit Korrekturen füttern                                                 │
│                                                                                     │
│  6. REPORT ERSTELLEN                                                                │
│     └─→ Zusammenfassung: X Rechnungen, Y Fehler erkannt, Z RAG-Beispiele            │
│     └─→ E-Mail an Admin oder Webhook                                                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Celery Beat Konfiguration

```python
# backend/app/worker/celery_config.py

from celery.schedules import crontab

beat_schedule = {
    'nightly-training-batch': {
        'task': 'app.worker.tasks.process_training_batch',
        'schedule': crontab(hour=2, minute=0),  # Täglich 02:00
        'args': (),
        'options': {'queue': 'training'}
    },
}
```

### Batch-Task Implementierung

```python
# backend/app/worker/tasks.py

@celery_app.task(bind=True, max_retries=3)
def process_training_batch(self):
    """
    Nächtlicher Batch-Job für Training mit generierten Rechnungen.

    1. Rechnungen aus Incoming-Verzeichnis laden
    2. Lösungsdatei parsen
    3. Projekt erstellen
    4. Alle Rechnungen hochladen + analysieren
    5. Auto-Feedback aus Lösungsdatei generieren
    6. Report erstellen
    """
    incoming_dir = Path(settings.TRAINING_INCOMING_DIR)

    # PDFs finden
    pdf_files = sorted(incoming_dir.glob("*.pdf"))
    if not pdf_files:
        return {"status": "no_files"}

    # Lösungsdatei laden
    solution_file = incoming_dir / "solution.json"
    if not solution_file.exists():
        raise ValueError("solution.json nicht gefunden")

    solutions = json.loads(solution_file.read_text())

    # Projekt erstellen
    project = create_training_project(date.today())

    # Verarbeitung
    results = []
    for idx, pdf_path in enumerate(pdf_files, start=1):
        # Upload
        doc = upload_document(project.id, pdf_path)

        # Analyse-Pipeline
        process_and_analyze_task.delay(doc.id)

        # Lösung finden
        solution = find_solution(solutions, pdf_path.name, idx)
        if solution:
            # Auto-Feedback generieren
            create_auto_feedback(doc.id, solution)

        results.append({
            "filename": pdf_path.name,
            "document_id": doc.id,
            "has_solution": solution is not None
        })

    # Dateien archivieren
    archive_dir = incoming_dir / "processed" / date.today().isoformat()
    archive_dir.mkdir(parents=True, exist_ok=True)
    for pdf_path in pdf_files:
        shutil.move(pdf_path, archive_dir / pdf_path.name)
    shutil.move(solution_file, archive_dir / "solution.json")

    # Report
    send_training_report(project.id, results)

    return {
        "status": "completed",
        "project_id": project.id,
        "documents_processed": len(results),
        "solutions_applied": sum(1 for r in results if r["has_solution"])
    }
```

### Verzeichnisstruktur

```
/data/training/
├── incoming/                    # Neue Rechnungen hier ablegen
│   ├── rechnung_001.pdf
│   ├── rechnung_002.pdf
│   ├── ...
│   └── solution.json            # Lösungsdatei (vom Generator)
│
├── processed/                   # Archiv nach Verarbeitung
│   ├── 2025-03-20/
│   │   ├── rechnung_001.pdf
│   │   ├── rechnung_002.pdf
│   │   └── solution.json
│   └── 2025-03-21/
│       └── ...
│
└── reports/                     # Batch-Reports
    ├── 2025-03-20_report.json
    └── 2025-03-21_report.json
```

### Batch-Job UI (optional)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOBS                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Zeitplan: Täglich 02:00 Uhr                              [Zeitplan ändern]         │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Datum       │ Status    │ Rechnungen │ Fehler erkannt │ RAG-Beispiele     │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  21.03.2025  │ ✓ Fertig  │ 500        │ 127 (25%)      │ 1.245             │    │
│  │  20.03.2025  │ ✓ Fertig  │ 500        │ 142 (28%)      │ 1.380             │    │
│  │  19.03.2025  │ ✗ Fehler  │ 312        │ -              │ -                 │    │
│  │  18.03.2025  │ ✓ Fertig  │ 500        │ 98 (20%)       │ 987               │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  [Jetzt starten]    [Logs anzeigen]    [Report herunterladen]                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Prüflogik & Kriterienkatalog

### Prüf-Pipeline

```
Invoice (PDF)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [1] PARSER                                                                         │
│      └─→ Text extrahieren, Felder erkennen                                          │
│      └─→ Ergebnis: ParseResult (raw_text, extracted_data)                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [2] RULE ENGINE (Deterministisch)                          Quelle: DE_USTG         │
│      └─→ § 14 UStG Pflichtangaben prüfen                                            │
│      └─→ Leistungsdatum im Projektzeitraum?                                         │
│      └─→ Ergebnis: PrecheckResult (errors[], warnings[])                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [3] RISK CHECKER (Heuristisch)                                                     │
│      └─→ Statistische Auffälligkeiten                                               │
│      └─→ Muster-Erkennung (Pauschalbeträge, Häufungen)                              │
│      └─→ Ergebnis: RiskFlags[]                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [4] PROJEKTABGLEICH                                                                │
│      └─→ Lieferdatum innerhalb Projektlaufzeit?                                     │
│      └─→ Empfänger = Begünstigter?                                                  │
│      └─→ Ergebnis: ProjectMatchResult                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [5] LLM ADAPTER (Semantisch)                                                       │
│      └─→ Projektbezug inhaltlich prüfen                                             │
│      └─→ Wirtschaftlichkeit (§ 7 BHO/LHO)                                           │
│      └─→ Begünstigtenabgleich                                                       │
│      └─→ Ergebnis: SemanticAnalysis                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  [6] FINAL RESULT                                                                   │
│      └─→ Alle Ergebnisse zusammenführen                                             │
│      └─→ Traffic-Light berechnen (GREEN/YELLOW/RED)                                 │
│      └─→ fields[] mit allen Merkmalen                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Fehler-Klassifizierung

```python
class ErrorSourceCategory(Enum):
    TAX_LAW = "TAX_LAW"              # § 14 UStG Pflichtangaben
    PROJECT_CONTEXT = "PROJECT_CONTEXT"  # Projektzeitraum, Begünstigter
    SEMANTIC = "SEMANTIC"             # KI-basierte Plausibilität
    ECONOMIC = "ECONOMIC"             # Wirtschaftlichkeit (§ 7 BHO)
```

### Kriterienkatalog: DE_USTG (§ 14 UStG)

#### Kategorie 1: TAX_LAW (Steuerrecht)

| # | Merkmal | Feature-ID | Prüfung | Severity |
|---|---------|------------|---------|----------|
| 1 | Vollständiger Name des Lieferanten | `supplier_name` | Vorhanden + nicht leer | HIGH |
| 2 | Vollständige Anschrift des Lieferanten | `supplier_address` | Straße, PLZ, Ort | HIGH |
| 3 | Vollständiger Name des Empfängers | `customer_name` | Vorhanden + nicht leer | HIGH |
| 4 | Vollständige Anschrift des Empfängers | `customer_address` | Straße, PLZ, Ort | HIGH |
| 5 | Steuernummer oder USt-IdNr. | `tax_id` | Vorhanden, Format gültig | HIGH |
| 6 | Rechnungsdatum | `invoice_date` | Vorhanden, Format DD.MM.YYYY | HIGH |
| 7 | Fortlaufende Rechnungsnummer | `invoice_number` | Vorhanden, eindeutig | HIGH |
| 8 | Menge und Art der Lieferung | `service_description` | Vorhanden, aussagekräftig | HIGH |
| 9 | Zeitpunkt der Lieferung/Leistung | `supply_date_or_period` | Datum oder Zeitraum | HIGH |
| 10 | Nettobetrag | `net_amount` | Vorhanden, numerisch | HIGH |
| 11 | Steuersatz | `vat_rate` | 0%, 7%, oder 19% | HIGH |
| 12 | Steuerbetrag | `vat_amount` | Berechnung korrekt | HIGH |
| 13 | Bruttobetrag | `gross_amount` | Netto + USt = Brutto | HIGH |

#### Kategorie 2: PROJECT_CONTEXT (Projektbezug)

| # | Merkmal | Feature-ID | Prüfung | Severity |
|---|---------|------------|---------|----------|
| 14 | Leistungsdatum im Projektzeitraum | `supply_in_project_period` | supply_date zwischen project_start und project_end | HIGH |
| 15 | Empfänger = Begünstigter | `recipient_is_beneficiary` | customer_name ≈ beneficiary_name | MEDIUM |
| 16 | Leistungsort = Projektstandort | `service_location_match` | Optional, wenn definiert | LOW |

#### Kategorie 3: SEMANTIC (KI-Plausibilität)

| # | Merkmal | Feature-ID | Prüfung | Severity |
|---|---------|------------|---------|----------|
| 17 | Semantischer Projektbezug | `semantic_project_relevance` | Leistungsbeschreibung passt zum Projektziel | MEDIUM |
| 18 | Keine Red-Flags | `no_red_flags` | Keine Luxusgüter, Bewirtung, etc. | MEDIUM |

#### Kategorie 4: ECONOMIC (Wirtschaftlichkeit)

| # | Merkmal | Feature-ID | Prüfung | Severity |
|---|---------|------------|---------|----------|
| 19 | Wirtschaftlichkeit | `economic_plausibility` | § 7 BHO: Ausgabe wirtschaftlich & sparsam | LOW |
| 20 | Keine statistischen Auffälligkeiten | `no_statistical_anomalies` | Betrag nicht > Median + 2σ | LOW |

### Risk-Checker Regeln

| # | Prüfung | Schwelle | Severity |
|---|---------|----------|----------|
| 1 | Hohe Beträge | > 50.000€ oder > Median + 2σ | MEDIUM |
| 2 | Lieferantenhäufung | > 30% vom selben Lieferanten | LOW |
| 3 | Fehlender Leistungszeitraum | Kein Start-/Enddatum | MEDIUM |
| 4 | Runde Pauschalbeträge | ≥ 1.000€ + durch 100 teilbar | LOW |
| 5 | Außerhalb Projektzeitraum | Vor project_start oder nach project_end | HIGH |
| 6 | Fehlender Projektbezug | Generische Begriffe: "Diverse", "Pauschale" | MEDIUM |
| 7 | Empfänger-Abweichung | invoice_recipient ≠ beneficiary_name | MEDIUM |

### UI: Kriterienkatalog nach Kategorien

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  KRITERIENKATALOG                                           Ruleset: DE_USTG        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📜 STEUERRECHT (§ 14 UStG)                                              13 Merkmale│
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ✓ Eingehalten (11)                                                          [▼]   │
│  ├── Lieferantenname: Mustermann GmbH                                              │
│  ├── Lieferantenadresse: Musterstr. 1, 12345 Berlin                                │
│  ├── Rechnungsnummer: RE-2025-003                                                  │
│  ├── Rechnungsdatum: 17.03.2025                                                    │
│  └── ...                                                                           │
│                                                                                     │
│  ✗ Nicht eingehalten (1)                                                     [▼]   │
│  └── USt-Satz: 7% erkannt, erwartet 19%                         [Korrigieren]      │
│                                                                                     │
│  ? Nicht gefunden (1)                                                        [▼]   │
│  └── Leistungszeitraum: nicht erkannt                           [Nachtragen]       │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  📋 PROJEKTBEZUG                                                          3 Merkmale│
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ✓ Eingehalten (1)                                                           [▼]   │
│  └── Empfänger = Begünstigter: ✓ Übereinstimmung                                   │
│                                                                                     │
│  ✗ Nicht eingehalten (1)                                                     [▼]   │
│  └── Leistungsdatum im Projektzeitraum:                                            │
│      Leistung: 15.03.2025                                                          │
│      Projekt: 01.04.2025 - 31.12.2025                                              │
│      → Leistung VOR Projektbeginn!                              [Korrigieren]      │
│                                                                                     │
│  ? Nicht gefunden (1)                                                        [▼]   │
│  └── Leistungsort: nicht geprüft (kein Projektstandort definiert)                  │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  🤖 SEMANTISCHE PRÜFUNG (KI)                                              2 Merkmale│
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ✓ Eingehalten (1)                                                           [▼]   │
│  └── Semantischer Projektbezug: "IT-Beratung" passt zu "Digitalisierung"           │
│                                                                                     │
│  ⚠ Warnung (1)                                                               [▼]   │
│  └── Red-Flag erkannt: "Bewirtungskosten" in Beschreibung       [Details]          │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  💰 WIRTSCHAFTLICHKEIT (§ 7 BHO)                                          2 Merkmale│
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ✓ Eingehalten (2)                                                           [▼]   │
│  ├── Wirtschaftlichkeit: Betrag im üblichen Rahmen                                 │
│  └── Keine statistischen Auffälligkeiten                                           │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Projektdaten-Integration

### Projektmodell (vereinfacht)

```python
class Project:
    id: UUID
    title: str                    # "Förderprojekt Digitalisierung 2025"
    project_number: str           # "FKZ-2025-12345"

    # Zeitraum
    project_period: dict          # {"start": "2025-01-01", "end": "2025-12-31"}

    # Begünstigter
    beneficiary_name: str         # "Muster GmbH"
    beneficiary_address: str      # "Musterstr. 1, 12345 Berlin"

    # Optional
    project_location: str | None  # "Hamburg" (für Leistungsort-Prüfung)
    project_description: str      # Für semantische Prüfung

    # Ruleset
    ruleset_id: str               # "DE_USTG"
```

### Datenfluss: Projekt → Prüfung

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PROJEKT                                                                            │
│  ════════                                                                           │
│  Title: Förderprojekt Digitalisierung 2025                                          │
│  Nummer: FKZ-2025-12345                                                             │
│  Zeitraum: 01.01.2025 - 31.12.2025                                                  │
│  Begünstigter: Muster GmbH, Musterstr. 1, 12345 Berlin                              │
│  Standort: Hamburg                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PRÜFUNG                                                                            │
│  ════════                                                                           │
│                                                                                     │
│  Rule Engine:                                                                       │
│  ├── Leistungsdatum "15.03.2025" ∈ [01.01.2025, 31.12.2025]? → ✓                    │
│  └── supply_in_project_period = VALID                                              │
│                                                                                     │
│  Risk Checker:                                                                      │
│  ├── customer_name "Muster GmbH" ≈ beneficiary_name "Muster GmbH"? → ✓              │
│  └── recipient_is_beneficiary = VALID                                              │
│                                                                                     │
│  LLM:                                                                               │
│  ├── Leistung "IT-Beratung" passt zu Projekt "Digitalisierung"? → ✓                 │
│  └── semantic_project_relevance = HIGH                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Geklärte Fragen

1. **Lösungsdatei-Format**: PDF-Dateien werden generiert, Lösungsdatei separat (CSV/JSON)
2. **Matching**: Dateiname + Position in der Upload-Liste
3. **Feedback → RAG**: Bereits implementiert! Jede Korrektur wird als RAG-Beispiel gespeichert.
4. **Ruleset**: DE_USTG (§ 14 UStG Pflichtangaben)
5. **Prüfumfang**: Steuerrecht + Förderfähigkeit + Semantik + Wirtschaftlichkeit
6. **Batch-Job**: Celery Beat, täglich 02:00 Uhr

## Offene Fragen

1. **Fehler-Codes Generator**: Welche Fehler-Codes erzeugt der Rechnungsgenerator?
2. **Merge-Default**: Sollen manuelle Eingaben standardmäßig Vorrang haben?
3. **E-Mail-Benachrichtigung**: Wer soll den Batch-Report erhalten?
4. **Projektstandort**: Ist `project_location` immer definiert?

---

## Nächste Schritte

Nach Freigabe dieser Spezifikation:

1. [ ] Lösungsdatei-Format finalisieren
2. [ ] Phase 1 implementieren (Merkmals-Ansicht)
3. [ ] Phase 2 implementieren (Korrektur-Formular)
4. [ ] Phase 3-5 implementieren (Lösungsdatei-Import)
5. [ ] End-to-End Tests mit generierten Rechnungen
