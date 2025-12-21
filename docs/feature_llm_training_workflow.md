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
| Risk Checker GUI | ❌ | Keine Konfigurationsoberfläche |
| Semantic Check GUI | ❌ | Keine Konfigurationsoberfläche |
| Economic Check GUI | ❌ | Keine Konfigurationsoberfläche |
| Schulungs-Ansicht (Prüfdetails) | ❌ | Transparente Anzeige aller Prüflogik |
| Benutzerdefinierte Kriterien | ❌ | Eigene Prüfregeln erstellen |
| Generator-GUI | ❌ | Rechnungen generieren + Batch-Zugriff |

### Was fehlt

1. **Merkmals-Detail-Ansicht** im Frontend
2. **Korrektur-Formular** pro Merkmal
3. **Lösungsdatei-Upload** (API + UI)
4. **Merge-Logik** (manuell vs. Lösungsdatei)
5. **Risk Checker GUI** - Konfiguration der Risiko-Prüfungsregeln
6. **Semantic Check GUI** - Konfiguration der semantischen Prüfung (LLM)
7. **Economic Check GUI** - Konfiguration der Wirtschaftlichkeitsprüfung
8. **Schulungs-Ansicht** - Alle Prüfdetails transparent anzeigen (nur lesen)
9. **Benutzerdefinierte Kriterien** - Eigene Prüfregeln erstellen
10. **Generator-GUI** - Rechnungen generieren und Batch-Jobs verwalten

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

## Schulungs-Ansicht: Kriterien-Details (Nur Lesen)

> **Wichtig**: Da FlowAudit auch als **Schulungstool** dient, müssen alle Prüfkriterien transparent und nachvollziehbar angezeigt werden.

### Erweiterter Kriterienkatalog mit Prüfdetails

Im Review-Modus sollen alle Kriterien inklusive ihrer **Prüflogik** angezeigt werden:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  KRITERIENKATALOG (Schulungsansicht)                    [Nur Lesen] [📖 Legende]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ⚠️ RISK CHECKER                                                          7 Regeln  │
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Hohe Beträge                                                  [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Schwellenwert:    > 50.000 € ODER > Median + 2σ                            │    │
│  │ Aktueller Median: 2.340,00 € (aus 127 Rechnungen im Projekt)               │    │
│  │ Standardabw.:     1.250,00 €                                               │    │
│  │ Grenze:           4.840,00 € (Median + 2σ)                                 │    │
│  │                                                                             │    │
│  │ Diese Rechnung:   2.380,00 €                                               │    │
│  │ Ergebnis:         ✓ OK (unter Schwelle)                                    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Lieferantenhäufung                                            [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Schwellenwert:    > 30% vom selben Lieferanten                             │    │
│  │ Lieferant:        Mustermann GmbH                                          │    │
│  │ Rechnungen:       12 von 127 (9,4%)                                        │    │
│  │ Ergebnis:         ✓ OK (unter Schwelle)                                    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Runde Pauschalbeträge                                         [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Schwellenwert:    ≥ 1.000 € UND durch 100 teilbar                          │    │
│  │ Diese Rechnung:   2.380,00 €                                               │    │
│  │ Prüfung:          2380 % 100 = 80 (nicht durch 100 teilbar)                │    │
│  │ Ergebnis:         ✓ OK                                                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Selbstrechnung (FRAUD_SELF_INVOICE)                           [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Prüflogik:        supplier_vat_id ≠ beneficiary_vat_id                     │    │
│  │ Lieferant-UST-ID: DE123456789                                              │    │
│  │ Projekt-UST-ID:   DE987654321                                              │    │
│  │ Ergebnis:         ✓ OK (verschiedene UST-IDs)                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  🤖 SEMANTISCHE PRÜFUNG                                                   3 Regeln  │
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Projektrelevanz                                               [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ LLM-Provider:     Ollama (llama3.2)                                        │    │
│  │ Schwellenwert:    ≥ 70%                                                    │    │
│  │                                                                             │    │
│  │ Projektbeschreibung:                                                        │    │
│  │ "Digitalisierung der Geschäftsprozesse durch ERP-Einführung..."            │    │
│  │                                                                             │    │
│  │ Leistungsbeschreibung (Rechnung):                                           │    │
│  │ "IT-Beratung März 2025 - ERP-Systemanalyse"                                │    │
│  │                                                                             │    │
│  │ LLM-Analyse:      "Hohe Übereinstimmung: ERP-Beratung entspricht           │    │
│  │                    Projektziel Digitalisierung/ERP-Einführung"              │    │
│  │ Konfidenz:        92%                                                       │    │
│  │ Ergebnis:         ✓ OK                                                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Red-Flag Keywords                                             [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Geprüfte Keywords (Warnung):                                                │    │
│  │   Bewirtung, Luxus, Privatfahrzeug, Alkohol, Geschenk                      │    │
│  │ Geprüfte Keywords (Ablehnung):                                              │    │
│  │   Glücksspiel, Parteispende, Waffen                                        │    │
│  │                                                                             │    │
│  │ Gefundene Matches: 0                                                        │    │
│  │ Ergebnis:          ✓ OK                                                    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  💰 WIRTSCHAFTLICHKEIT                                                    2 Regeln  │
│  ══════════════════════════════════════════════════════════════════════════════════ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Statistische Ausreißer                                        [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Methode:          Median + 2 Standardabweichungen                          │    │
│  │ Vergleichsgruppe: IT-Beratung (48 Rechnungen)                              │    │
│  │ Median:           150,00 €/Stunde                                          │    │
│  │ Grenze:           220,00 €/Stunde                                          │    │
│  │                                                                             │    │
│  │ Diese Rechnung:   175,00 €/Stunde (geschätzt aus 2.000€/~11h)              │    │
│  │ Ergebnis:         ✓ OK (im üblichen Rahmen)                                │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Regel: Preis-Benchmark                                               [ℹ️]   │    │
│  │ ─────────────────────────────────────────────────────────────────────────── │    │
│  │ Leistungsart:     IT-Beratung                                              │    │
│  │ Benchmark:        max. 180,00 €/Stunde (Marktüblich)                       │    │
│  │                                                                             │    │
│  │ Diese Rechnung:   175,00 €/Stunde                                          │    │
│  │ Ergebnis:         ✓ OK                                                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### JSON-Export der Prüfdetails

Alle Prüfdetails können als JSON exportiert werden (für Schulungszwecke):

```json
{
  "document_id": "abc-123",
  "ruleset": "DE_USTG",
  "check_results": {
    "risk_checker": {
      "enabled": true,
      "rules": [
        {
          "rule_id": "high_amount",
          "name": "Hohe Beträge",
          "threshold": {"type": "or", "conditions": [
            {"field": "gross_amount", "operator": ">", "value": 50000},
            {"field": "gross_amount", "operator": ">", "value": "median_plus_2sigma"}
          ]},
          "computed": {
            "median": 2340.00,
            "sigma": 1250.00,
            "threshold_dynamic": 4840.00
          },
          "invoice_value": 2380.00,
          "result": "PASS",
          "message": "Betrag unter Schwellenwert"
        },
        {
          "rule_id": "self_invoice",
          "name": "Selbstrechnung",
          "threshold": {"field": "supplier_vat_id", "operator": "!=", "value": "beneficiary_vat_id"},
          "invoice_value": "DE123456789",
          "project_value": "DE987654321",
          "result": "PASS",
          "message": "Verschiedene UST-IDs"
        }
      ]
    },
    "semantic_check": {
      "enabled": true,
      "provider": "ollama",
      "model": "llama3.2",
      "rules": [
        {
          "rule_id": "project_relevance",
          "name": "Projektrelevanz",
          "threshold": {"field": "relevance_score", "operator": ">=", "value": 0.7},
          "invoice_description": "IT-Beratung März 2025 - ERP-Systemanalyse",
          "project_description": "Digitalisierung der Geschäftsprozesse...",
          "llm_response": "Hohe Übereinstimmung: ERP-Beratung entspricht...",
          "score": 0.92,
          "result": "PASS"
        }
      ]
    },
    "economic_check": {
      "enabled": true,
      "rules": [
        {
          "rule_id": "statistical_outlier",
          "name": "Statistische Ausreißer",
          "threshold": {"type": "median_plus_sigma", "sigma_count": 2},
          "comparison_group": "IT-Beratung",
          "comparison_count": 48,
          "median_hourly": 150.00,
          "threshold_hourly": 220.00,
          "invoice_hourly_estimate": 175.00,
          "result": "PASS"
        }
      ]
    }
  }
}
```

---

## Benutzerdefinierte Kriterien

### Übersicht

Neben den vordefinierten Kriterien können **eigene Kriterien** definiert werden:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BENUTZERDEFINIERTE KRITERIEN                                    [+ Neues Kriterium]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Kriterium                     │ Kategorie  │ Typ       │ Aktiv │ Aktionen  │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  Max. Tagessatz                │ ECONOMIC   │ Schwelle  │  [✓]  │ [✏️] [🗑️] │    │
│  │  Pflicht-Projektnummer         │ PROJECT    │ Regex     │  [✓]  │ [✏️] [🗑️] │    │
│  │  Verbotene Lieferanten         │ FRAUD      │ Blacklist │  [✓]  │ [✏️] [🗑️] │    │
│  │  Mindestbetrag                 │ TAX        │ Schwelle  │  [ ]  │ [✏️] [🗑️] │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Kriterium-Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  NEUES KRITERIUM ERSTELLEN                                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Name:                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Max. Tagessatz für IT-Beratung                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Fehler-Code:                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ CUSTOM_MAX_DAILY_RATE                                                      │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Kategorie:  [ECONOMIC ▼]    Severity:  [MEDIUM ▼]                                  │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  Prüflogik:  [Schwellenwert ▼]                                                      │
│                                                                                     │
│  ┌─ Schwellenwert-Konfiguration ──────────────────────────────────────────────┐     │
│  │                                                                             │    │
│  │  Feld:       [daily_rate ▼] (berechnet aus: gross_amount / working_days)   │    │
│  │  Operator:   [> ▼]                                                          │    │
│  │  Wert:       [1.200] €                                                      │    │
│  │                                                                             │    │
│  │  Fehlermeldung:                                                             │    │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Tagessatz {value} € überschreitet Maximum von 1.200 €              │    │    │
│  │  └─────────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  [✓] Für Generator aktivieren (in Lösungsdatei prüfen)                              │
│  [✓] Für Batch-Job aktivieren                                                       │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                            [Abbrechen]  [Testen]  [Speichern]       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Prüflogik-Typen

| Typ | Beschreibung | Beispiel |
|-----|--------------|----------|
| **Schwellenwert** | Numerischer Vergleich | `gross_amount > 10000` |
| **Regex** | Musterprüfung | `invoice_number matches /^FKZ-\d{4}-\d+$/` |
| **Blacklist** | Verbotene Werte | `supplier_name NOT IN [...]` |
| **Whitelist** | Erlaubte Werte | `vat_rate IN [0, 7, 19]` |
| **Datumsbereich** | Zeitraumprüfung | `supply_date BETWEEN project_start AND project_end` |
| **Vergleich** | Feldvergleich | `supplier_vat_id != beneficiary_vat_id` |
| **LLM-Prompt** | Semantische Prüfung | Custom Prompt für LLM |

### Editor-Mockups pro Logik-Typ

#### 1. Schwellenwert (bereits vorhanden)

```
┌─ Schwellenwert-Konfiguration ─────────────────────────────────────────────────┐
│                                                                               │
│  Feld:       [gross_amount ▼]                                                 │
│              ○ Direkt aus Rechnung                                            │
│              ● Berechnet: [daily_rate ▼] = gross_amount / working_days        │
│                                                                               │
│  Operator:   [> ▼]   (Optionen: =, !=, <, <=, >, >=)                          │
│                                                                               │
│  Wert:       [1.200,00] €                                                     │
│              [ ] Dynamisch: Median + [2] Standardabweichungen                 │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Tagessatz {value} € überschreitet Maximum von {threshold} €          │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 2. Regex (Musterprüfung)

```
┌─ Regex-Konfiguration ─────────────────────────────────────────────────────────┐
│                                                                               │
│  Feld:       [invoice_number ▼]                                               │
│                                                                               │
│  Modus:      ● Muss matchen (Fehler wenn KEIN Match)                          │
│              ○ Darf nicht matchen (Fehler wenn Match)                         │
│                                                                               │
│  Pattern:                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ ^(RE|RG|INV)-\d{4}-\d{3,6}$                                           │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Optionen:   [✓] Case-insensitive (i)                                         │
│              [ ] Multiline (m)                                                │
│              [ ] Unicode (u)                                                  │
│                                                                               │
│  ─────────────────────────────────────────────────────────────────────────    │
│                                                                               │
│  🧪 Live-Test:                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ RE-2025-001                                                           │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│  Ergebnis: ✓ Match! Gruppen: ["RE", "2025", "001"]                            │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Rechnungsnummer "{value}" entspricht nicht dem erwarteten Format     │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 3. Blacklist (Verbotene Werte)

```
┌─ Blacklist-Konfiguration ─────────────────────────────────────────────────────┐
│                                                                               │
│  Feld:       [supplier_name ▼]                                                │
│                                                                               │
│  Matching:   ● Exakt (Groß-/Kleinschreibung ignoriert)                        │
│              ○ Enthält (Teilstring-Suche)                                     │
│              ○ Regex                                                          │
│                                                                               │
│  Verbotene Werte:                                                [Import CSV] │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │  Wert                                    │ Grund              │ Aktion│    │
│  ├───────────────────────────────────────────────────────────────────────┤    │
│  │  Scheinfirma GmbH                        │ Bekannter Betrug   │ [🗑️]  │    │
│  │  ABC Consulting Ltd.                     │ Sanktionsliste     │ [🗑️]  │    │
│  │  XYZ Holdings                            │ Insolvent          │ [🗑️]  │    │
│  │  ────────────────────────────────────────────────────────────────────│    │
│  │  [+ Neuer Eintrag...]                                                │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Einträge: 3                                               [Alle löschen]     │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Lieferant "{value}" steht auf der Sperrliste: {reason}               │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 4. Whitelist (Erlaubte Werte)

```
┌─ Whitelist-Konfiguration ─────────────────────────────────────────────────────┐
│                                                                               │
│  Feld:       [vat_rate ▼]                                                     │
│                                                                               │
│  Modus:      ● Nur diese Werte erlaubt                                        │
│              ○ Diese Werte + NULL/leer erlaubt                                │
│                                                                               │
│  Erlaubte Werte:                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │  [0]     Steuerbefreit (§4 UStG)                              [🗑️]   │    │
│  │  [7]     Ermäßigter Satz                                      [🗑️]   │    │
│  │  [19]    Regelsatz                                            [🗑️]   │    │
│  │  ────────────────────────────────────────────────────────────────────│    │
│  │  [+ Neuer Wert...]                                                   │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ USt-Satz {value}% ist nicht zulässig. Erlaubt: {allowed_values}      │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 5. Datumsbereich (Zeitraumprüfung)

```
┌─ Datumsbereich-Konfiguration ─────────────────────────────────────────────────┐
│                                                                               │
│  Zu prüfendes Feld:   [supply_date ▼]                                         │
│                                                                               │
│  Bereich:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  Von:  ● Projektfeld: [execution_period.start ▼]                       │  │
│  │        ○ Festes Datum: [____________]                                  │  │
│  │        ○ Relativ: Heute minus [__] Tage                                │  │
│  │                                                                         │  │
│  │  Bis:  ● Projektfeld: [execution_period.end ▼]                         │  │
│  │        ○ Festes Datum: [____________]                                  │  │
│  │        ○ Relativ: Heute plus [__] Tage                                 │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Optionen:  [✓] Randwerte einschließen (>=, <=)                               │
│             [ ] NULL-Werte als Fehler behandeln                               │
│                                                                               │
│  ─────────────────────────────────────────────────────────────────────────    │
│                                                                               │
│  Vorschau (aktuelles Projekt):                                                │
│  Gültiger Bereich: 01.04.2025 bis 30.11.2025                                  │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Leistungsdatum {value} liegt außerhalb des Durchführungszeitraums    │    │
│  │ ({start} bis {end})                                                   │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 6. Vergleich (Feldvergleich)

```
┌─ Vergleich-Konfiguration ─────────────────────────────────────────────────────┐
│                                                                               │
│  Feld A:     [supplier_vat_id ▼]        (aus Rechnung)                        │
│                                                                               │
│  Operator:   [!= ▼]   (Optionen: =, !=, <, <=, >, >=, enthält, beginnt mit)   │
│                                                                               │
│  Feld B:     ● Projektfeld: [beneficiary_vat_id ▼]                            │
│              ○ Anderes Rechnungsfeld: [________________ ▼]                    │
│              ○ Fester Wert: [________________________]                        │
│                                                                               │
│  Optionen:   [✓] Normalisieren vor Vergleich (Leerzeichen, Bindestriche)      │
│              [✓] Case-insensitive                                             │
│              [ ] NULL = NULL ist KEIN Match                                   │
│                                                                               │
│  ─────────────────────────────────────────────────────────────────────────    │
│                                                                               │
│  Logik-Vorschau:                                                              │
│  normalize(supplier_vat_id) != normalize(beneficiary_vat_id)                  │
│  → Fehler wenn gleich (= Selbstrechnung)                                      │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Selbstrechnung erkannt: Lieferant-UST-ID ({value_a}) entspricht      │    │
│  │ der Begünstigten-UST-ID ({value_b})                                   │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### 7. LLM-Prompt (Semantische Prüfung)

```
┌─ LLM-Prompt-Konfiguration ────────────────────────────────────────────────────┐
│                                                                               │
│  Provider:   [Ollama (llama3.2) ▼]                     [Verbindung testen]    │
│                                                                               │
│  Eingabefelder (werden in Prompt eingefügt):                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ [✓] {description}     → service_description                          │    │
│  │ [✓] {project}         → project_description                          │    │
│  │ [✓] {amount}          → gross_amount                                  │    │
│  │ [ ] {supplier}        → supplier_name                                 │    │
│  │ [+ Feld hinzufügen...]                                                │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  System-Prompt:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Du bist ein Prüfer für Fördermittelabrechnungen. Antworte immer      │    │
│  │ mit einem JSON-Objekt: {"result": "OK"|"FEHLER", "reason": "..."}    │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  User-Prompt:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ Prüfe ob folgende Leistungsbeschreibung auf Luxusgüter, private      │    │
│  │ Nutzung oder nicht-projektbezogene Ausgaben hindeutet:               │    │
│  │                                                                       │    │
│  │ Leistung: {description}                                               │    │
│  │ Betrag: {amount} €                                                    │    │
│  │ Projektbeschreibung: {project}                                        │    │
│  │                                                                       │    │
│  │ Antworte mit OK wenn die Leistung plausibel ist, sonst FEHLER.       │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Erwartete Antwort für FEHLER:                                                │
│  JSON-Pfad: [result ▼]  Wert: [FEHLER____]                                    │
│                                                                               │
│  ─────────────────────────────────────────────────────────────────────────    │
│                                                                               │
│  🧪 Test mit Beispieldaten:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ description: Catering für Firmenevent mit 50 Personen                │    │
│  │ amount: 5000                                                          │    │
│  │ project: IT-Digitalisierung                                           │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│  [Testen]                                                                     │
│                                                                               │
│  LLM-Antwort:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ {"result": "FEHLER", "reason": "Catering/Bewirtung ist keine         │    │
│  │  förderfähige Ausgabe für IT-Projekte"}                               │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│  → Würde als FEHLER gewertet (result = "FEHLER")                              │
│                                                                               │
│  Fehlermeldung:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐    │
│  │ KI-Prüfung fehlgeschlagen: {llm_reason}                               │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Datenmodell: Custom Criteria

```python
class CustomCriterion(Base):
    __tablename__ = "custom_criteria"

    id: Mapped[str] = mapped_column(UUID, primary_key=True)
    ruleset_id: Mapped[str] = mapped_column(ForeignKey("rulesets.id"))

    # Identifikation
    name: Mapped[str]                    # "Max. Tagessatz"
    error_code: Mapped[str]              # "CUSTOM_MAX_DAILY_RATE"
    category: Mapped[str]                # TAX, PROJECT, FRAUD, SEMANTIC, ECONOMIC
    severity: Mapped[str]                # LOW, MEDIUM, HIGH, CRITICAL

    # Prüflogik
    logic_type: Mapped[str]              # threshold, regex, blacklist, etc.
    logic_config: Mapped[dict]           # {"field": "daily_rate", "operator": ">", "value": 1200}
    error_message_template: Mapped[str]  # "Tagessatz {value} € überschreitet..."

    # Aktivierung
    enabled: Mapped[bool] = True
    use_in_generator: Mapped[bool] = True   # In Lösungsdatei prüfen
    use_in_batch: Mapped[bool] = True       # Im Batch-Job prüfen

    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### Auto-Sync mit Batch-Konfiguration

Wenn ein neues Kriterium erstellt wird mit `use_in_batch=True`:

```python
@celery_app.task
def sync_batch_config_on_criteria_change(ruleset_id: str):
    """
    Wird automatisch getriggert, wenn Kriterien geändert werden.
    Aktualisiert die Batch-Job-Konfiguration.
    """
    # Alle aktiven Kriterien laden
    criteria = get_active_criteria(ruleset_id, use_in_batch=True)

    # Batch-Config aktualisieren
    batch_config = get_or_create_batch_config(ruleset_id)
    batch_config.criteria_ids = [c.id for c in criteria]
    batch_config.updated_at = datetime.utcnow()

    # Nächsten Batch-Run aktualisieren
    schedule_next_batch_run(ruleset_id)

    return {"synced_criteria": len(criteria)}
```

---

## Generator-GUI mit Batch-Integration

### Übersicht

Die Generator-GUI ermöglicht:
1. Rechnungen generieren (mit Fehlern für Training)
2. Lösungsdatei erstellen
3. Batch-Job starten/überwachen
4. Ergebnisse analysieren

---

### PDF-Generierung

#### Technologie

Für die einheitliche PDF-Generierung wird **WeasyPrint** verwendet:

| Aspekt | Entscheidung |
|--------|--------------|
| **Library** | WeasyPrint (HTML/CSS → PDF) |
| **Vorlagen** | Jinja2 HTML-Templates |
| **Styling** | CSS mit Print-Media-Queries |
| **Fonts** | Google Fonts (Open Sans, Roboto) |
| **Logos** | SVG oder PNG (300 DPI) |

**Warum WeasyPrint?**
- Einheitliches Rendering
- Volle CSS-Unterstützung (Flexbox, Grid)
- Einfache Template-Erstellung mit HTML
- Gute Performance für Batch-Generierung

#### Speicherverzeichnis-Konfiguration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SPEICHERORT                                                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Basis-Verzeichnis:                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ /data/generator/output                                              [📁]     │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  Unterverzeichnis pro Batch-Lauf:                                                   │
│  [✓] Automatisch erstellen: {datum}_{zeit}_{projekt}/                               │
│      Beispiel: 2025-03-21_143022_training-2025/                                     │
│                                                                                     │
│  Inhalt pro Batch-Verzeichnis:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  📁 2025-03-21_143022_training-2025/                                          │  │
│  │  ├── 📄 rechnung_001.pdf                                                      │  │
│  │  ├── 📄 rechnung_002.pdf                                                      │  │
│  │  ├── 📄 ...                                                                   │  │
│  │  ├── 📄 rechnung_500.pdf                                                      │  │
│  │  ├── 📋 solution.json          (Lösungsdatei)                                 │  │
│  │  ├── 📋 manifest.json          (Metadaten zum Batch)                          │  │
│  │  └── 📋 protocol.log           (Fehlerprotokoll)                              │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  Aufbewahrung:                                                                      │
│  [ ] Automatisch löschen nach [30] Tagen                                            │
│  [✓] Bei Speicherplatz < [10] GB warnen                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### Fehlerprotokoll (protocol.log)

Bei Fehlern während der Generierung wird ein Protokoll geschrieben:

```
2025-03-21 14:30:22 [INFO]  Batch gestartet: 500 Rechnungen
2025-03-21 14:30:22 [INFO]  Vorlage: corporate_standard
2025-03-21 14:30:22 [INFO]  Projekt: training-2025
2025-03-21 14:30:23 [OK]    rechnung_001.pdf generiert (234 KB)
2025-03-21 14:30:24 [OK]    rechnung_002.pdf generiert (228 KB)
2025-03-21 14:30:25 [ERROR] rechnung_003.pdf FEHLGESCHLAGEN: Logo-Datei nicht gefunden
2025-03-21 14:30:25 [WARN]  Fallback auf Standard-Logo
2025-03-21 14:30:26 [OK]    rechnung_003.pdf generiert (mit Fallback, 215 KB)
...
2025-03-21 14:45:12 [INFO]  Batch abgeschlossen: 500/500 erfolgreich
2025-03-21 14:45:12 [INFO]  Lösungsdatei: solution.json (127 Fehler definiert)
2025-03-21 14:45:12 [INFO]  Gesamtgröße: 112 MB
```

#### Manifest-Datei (manifest.json)

```json
{
  "batch_id": "batch_20250321_143022",
  "created_at": "2025-03-21T14:30:22Z",
  "completed_at": "2025-03-21T14:45:12Z",
  "project": {
    "id": "proj-123",
    "name": "training-2025",
    "ruleset": "DE_USTG"
  },
  "template": "corporate_standard",
  "statistics": {
    "total": 500,
    "successful": 500,
    "failed": 0,
    "with_errors": 127,
    "valid": 373
  },
  "files": {
    "invoices": 500,
    "solution": "solution.json",
    "protocol": "protocol.log",
    "total_size_mb": 112
  },
  "error_distribution": {
    "TAX": 52,
    "PROJECT": 32,
    "FRAUD": 18,
    "SEMANTIC": 15,
    "ECONOMIC": 10
  }
}
```

---

### Rechnungsvorlagen

#### Übersicht

Der Generator enthält **eingebaute Vorlagen** und unterstützt **benutzerdefinierte Vorlagen**:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  RECHNUNGSVORLAGEN                                              [+ Neue Vorlage]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📦 EINGEBAUTE VORLAGEN                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │    │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │        │    │
│  │  │ │ LOGO    │ │  │ │▓▓▓▓▓▓▓▓▓│ │  │ │ modern  │ │  │ │  klein  │ │        │    │
│  │  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────┤ │        │    │
│  │  │ │ Adresse │ │  │ │ Minimal │ │  │ │ Design  │ │  │ │ Simple  │ │        │    │
│  │  │ │ ─────── │ │  │ │ ─────── │ │  │ │ ─────── │ │  │ │ ─────── │ │        │    │
│  │  │ │ Positio │ │  │ │ Positio │ │  │ │ Positio │ │  │ │ 1 Seite │ │        │    │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │        │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │    │
│  │   Corporate       Minimalist       Modern Color     Compact                │    │
│  │   Standard        (kein Logo)      (Akzentfarbe)    (1 Seite)              │    │
│  │   ● Ausgewählt    ○                ○                ○                      │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  📁 BENUTZERDEFINIERTE VORLAGEN                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │    │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │             │                         │    │
│  │  │ │ACME Logo│ │  │ │TechCorp │ │  │      +      │                         │    │
│  │  │ ├─────────┤ │  │ ├─────────┤ │  │             │                         │    │
│  │  │ │ Custom  │ │  │ │ Custom  │ │  │   Upload    │                         │    │
│  │  │ └─────────┘ │  │ └─────────┘ │  │             │                         │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                         │    │
│  │   ACME GmbH       TechCorp AG      Neue Vorlage                            │    │
│  │   ○ [✏️] [🗑️]     ○ [✏️] [🗑️]      hochladen                               │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### Eingebaute Vorlagen (Details)

| Vorlage | Beschreibung | Besonderheiten |
|---------|--------------|----------------|
| **Corporate Standard** | Professioneller Briefkopf mit Logo, vollständige Adressfelder, Fußzeile mit Bankverbindung | Für realistische Schulungsszenarien |
| **Minimalist** | Kein Logo, reduziertes Design | Fokus auf Inhalt, schnelle Generierung |
| **Modern Color** | Akzentfarbe (blau/grün), modernes Layout | Visuelle Abwechslung im Training |
| **Compact** | Alles auf einer Seite, kleine Schrift | Für viele Positionen |

#### Vorlage: Corporate Standard (Beispiel)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌────────────┐                      Mustermann GmbH            │
│  │            │                      Musterstraße 123           │
│  │   LOGO     │                      12345 Berlin               │
│  │            │                      Tel: 030 12345678          │
│  └────────────┘                      mail@mustermann.de         │
│                                      www.mustermann.de          │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  An:                                                            │
│  ┌─────────────────────────────────────┐                        │
│  │ Förderprojekt GmbH                  │       RECHNUNG         │
│  │ Projektstraße 45                    │                        │
│  │ 54321 Hamburg                       │       Nr. RE-2025-001  │
│  └─────────────────────────────────────┘       Datum: 15.03.2025│
│                                                                 │
│  ═══════════════════════════════════════════════════════════    │
│                                                                 │
│  Pos │ Beschreibung                      │ Menge │ Preis │ Ges. │
│  ────┼───────────────────────────────────┼───────┼───────┼──────│
│  1   │ IT-Beratung März 2025             │ 20 h  │ 100€  │2.000€│
│  2   │ Dokumentation                     │ pauschal│ 380€│  380€│
│  ────┼───────────────────────────────────┼───────┼───────┼──────│
│      │                          Netto:                  │2.380€│
│      │                          USt 19%:                │  452€│
│      │                          ═════════════════════════════  │
│      │                          GESAMT:                 │2.832€│
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Leistungszeitraum: 01.03.2025 - 31.03.2025                     │
│  Zahlungsziel: 14 Tage                                          │
│                                                                 │
│  ═══════════════════════════════════════════════════════════    │
│  Bankverbindung: Sparkasse Berlin │ IBAN: DE89 1234 5678 9012   │
│  USt-IdNr: DE123456789            │ Geschäftsführer: Max Muster │
│  Amtsgericht Berlin HRB 12345     │ Steuernummer: 27/123/45678  │
│  ═══════════════════════════════════════════════════════════    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Vorlagen-Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  VORLAGE BEARBEITEN: ACME GmbH                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │                                 │  │ FIRMENDETAILS                           │   │
│  │        LIVE-VORSCHAU            │  │ ─────────────────────────────────────── │   │
│  │                                 │  │                                         │   │
│  │  ┌───────────────────────────┐  │  │ Firmenname:                             │   │
│  │  │ ┌─────┐   ACME GmbH       │  │  │ ┌─────────────────────────────────────┐ │   │
│  │  │ │LOGO │   Industriestr. 5 │  │  │ │ ACME GmbH                           │ │   │
│  │  │ └─────┘   99999 Teststadt │  │  │ └─────────────────────────────────────┘ │   │
│  │  │                           │  │  │                                         │   │
│  │  │   RECHNUNG                │  │  │ Adresse:                                │   │
│  │  │   ...                     │  │  │ ┌─────────────────────────────────────┐ │   │
│  │  └───────────────────────────┘  │  │ │ Industriestraße 5                   │ │   │
│  │                                 │  │ │ 99999 Teststadt                     │ │   │
│  │  [◀ Seite 1/1 ▶]               │  │ └─────────────────────────────────────┘ │   │
│  │                                 │  │                                         │   │
│  └─────────────────────────────────┘  │ Logo:                                   │   │
│                                       │ ┌─────────────────────────────────────┐ │   │
│                                       │ │ acme_logo.svg              [🗑️] [↑]│ │   │
│                                       │ └─────────────────────────────────────┘ │   │
│                                       │ Größe: [150] x [50] px                  │   │
│                                       │                                         │   │
│                                       │ ───────────────────────────────────────│   │
│                                       │                                         │   │
│                                       │ FARBEN                                  │   │
│                                       │ Akzentfarbe: [#2563EB] 🎨               │   │
│                                       │ Textfarbe:   [#1F2937] 🎨               │   │
│                                       │                                         │   │
│                                       │ ───────────────────────────────────────│   │
│                                       │                                         │   │
│                                       │ BANKVERBINDUNG                          │   │
│                                       │ Bank: [Sparkasse____________]           │   │
│                                       │ IBAN: [DE89 1234 5678 9012__]           │   │
│                                       │ BIC:  [SPKDE1234___________]            │   │
│                                       │                                         │   │
│                                       │ ───────────────────────────────────────│   │
│                                       │                                         │   │
│                                       │ STEUERDATEN                             │   │
│                                       │ USt-IdNr:     [DE123456789_____]        │   │
│                                       │ Steuernummer: [27/123/45678____]        │   │
│                                       │ Handelsreg.:  [HRB 12345 Berlin]        │   │
│                                       │                                         │   │
│                                       └─────────────────────────────────────────┘   │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Basis-Vorlage: [Corporate Standard ▼]                                              │
│                                                                                     │
│                                      [Abbrechen]  [Vorschau PDF]  [Speichern]       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### Vorlagen-Datenmodell

```python
class InvoiceTemplate(Base):
    __tablename__ = "invoice_templates"

    id: Mapped[str] = mapped_column(UUID, primary_key=True)

    # Identifikation
    name: Mapped[str]                    # "ACME GmbH"
    is_builtin: Mapped[bool] = False     # True für eingebaute Vorlagen
    base_template: Mapped[str | None]    # "corporate_standard" (für Custom)

    # Firmendetails
    company_name: Mapped[str]
    company_address: Mapped[str]
    company_city: Mapped[str]
    company_phone: Mapped[str | None]
    company_email: Mapped[str | None]
    company_website: Mapped[str | None]

    # Logo
    logo_path: Mapped[str | None]        # Pfad zur Logo-Datei
    logo_width: Mapped[int] = 150
    logo_height: Mapped[int] = 50

    # Farben
    accent_color: Mapped[str] = "#2563EB"
    text_color: Mapped[str] = "#1F2937"

    # Bankverbindung
    bank_name: Mapped[str | None]
    bank_iban: Mapped[str | None]
    bank_bic: Mapped[str | None]

    # Steuerdaten
    vat_id: Mapped[str | None]           # USt-IdNr.
    tax_number: Mapped[str | None]       # Steuernummer
    trade_register: Mapped[str | None]   # Handelsregister

    # Metadaten
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

#### Verzeichnisstruktur für Vorlagen

```
/data/generator/
├── templates/
│   ├── builtin/                     # Eingebaute Vorlagen (read-only)
│   │   ├── corporate_standard/
│   │   │   ├── template.html
│   │   │   ├── style.css
│   │   │   └── default_logo.svg
│   │   ├── minimalist/
│   │   ├── modern_color/
│   │   └── compact/
│   │
│   └── custom/                      # Benutzerdefinierte Vorlagen
│       ├── acme_gmbh/
│       │   ├── template.html        # Kopie von Basis + Anpassungen
│       │   ├── style.css
│       │   └── acme_logo.svg
│       └── techcorp_ag/
│           └── ...
│
├── output/                          # Generierte Dateien
│   ├── 2025-03-21_143022_training-2025/
│   │   ├── rechnung_001.pdf
│   │   ├── ...
│   │   ├── solution.json
│   │   ├── manifest.json
│   │   └── protocol.log
│   └── ...
│
└── logos/                           # Hochgeladene Logos
    ├── acme_logo.svg
    └── techcorp_logo.png
```

---

### Tab: Lösungsdatei

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  RECHNUNGSGENERATOR                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📄 Generie- │ │ 📋 Lösungs- │ │ ⏰ Batch-   │ │ 📊 Ergeb-   │                    │
│  │    ren      │ │    datei    │ │    Jobs     │ │    nisse    │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│                        ▲                                                            │
│                        │ (aktiv)                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  LÖSUNGSDATEI VERWALTEN                                                             │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  Aktuelle Lösungsdatei:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  📋 solution.json                                                           │    │
│  │  ─────────────────────────────────────────────────────────────────────────  │    │
│  │  Erstellt:      21.03.2025 14:45:12                                         │    │
│  │  Rechnungen:    500                                                         │    │
│  │  Davon fehlerhaft: 127 (25,4%)                                              │    │
│  │  Dateigröße:    2,3 MB                                                      │    │
│  │                                                                             │    │
│  │  Verknüpft mit Batch: 2025-03-21_143022_training-2025                       │    │
│  │                                                                             │    │
│  │  [📥 Download]  [👁️ Vorschau]  [✏️ Bearbeiten]  [🗑️ Löschen]                │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  VORSCHAU (erste 10 Einträge)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  #  │ Dateiname         │ Gültig │ Fehler                         │ Details│    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  1  │ rechnung_001.pdf  │ ✓      │ -                              │  [👁️]  │    │
│  │  2  │ rechnung_002.pdf  │ ✗      │ TAX_VAT_RATE_WRONG             │  [👁️]  │    │
│  │  3  │ rechnung_003.pdf  │ ✗      │ PROJECT_PERIOD_BEFORE_START    │  [👁️]  │    │
│  │  4  │ rechnung_004.pdf  │ ✗      │ FRAUD_SELF_INVOICE             │  [👁️]  │    │
│  │  5  │ rechnung_005.pdf  │ ✓      │ -                              │  [👁️]  │    │
│  │  6  │ rechnung_006.pdf  │ ✗      │ TAX_SUPPLY_DATE_MISSING        │  [👁️]  │    │
│  │  7  │ rechnung_007.pdf  │ ✓      │ -                              │  [👁️]  │    │
│  │  8  │ rechnung_008.pdf  │ ✗      │ SEMANTIC_RED_FLAG_LUXURY       │  [👁️]  │    │
│  │  9  │ rechnung_009.pdf  │ ✓      │ -                              │  [👁️]  │    │
│  │ 10  │ rechnung_010.pdf  │ ✗      │ ECONOMIC_HIGH_AMOUNT (2)       │  [👁️]  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│  Zeige [10 ▼] von 500 Einträgen           [◀ Zurück]  Seite 1 von 50  [Weiter ▶]    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  FEHLER-STATISTIK                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  Kategorie      │ Anzahl │ Häufigste Fehler                                │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  TAX            │ 52     │ TAX_VAT_RATE_WRONG (18), TAX_SUPPLY_DATE (12)   │    │
│  │  PROJECT        │ 32     │ PROJECT_PERIOD_BEFORE_START (15)                │    │
│  │  FRAUD          │ 18     │ FRAUD_SELF_INVOICE (12), FRAUD_DUPLICATE (6)    │    │
│  │  SEMANTIC       │ 15     │ SEMANTIC_RED_FLAG_LUXURY (8)                    │    │
│  │  ECONOMIC       │ 10     │ ECONOMIC_HIGH_AMOUNT (7)                        │    │
│  │  ─────────────────────────────────────────────────────────────────────────  │    │
│  │  GESAMT         │ 127    │                                                 │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  AKTIONEN                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  [📤 In FlowAudit importieren]     → Lädt alle PDFs + Lösungsdatei hoch     │    │
│  │                                                                             │    │
│  │  [⏰ Batch-Job erstellen]          → Erstellt geplanten Job mit dieser      │    │
│  │                                      Lösungsdatei                           │    │
│  │                                                                             │    │
│  │  [📊 Vergleich mit vorherigem]     → Zeigt Änderungen zur letzten           │    │
│  │                                      Lösungsdatei                           │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Detail-Ansicht eines Eintrags (Modal)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LÖSUNGSDATEI-EINTRAG: rechnung_002.pdf                                    [✕]      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Position:     2                                                                    │
│  Dateiname:    rechnung_002.pdf                                                     │
│  Status:       ✗ Fehlerhaft                                                         │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  EXTRAHIERTE FELDER                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Feld                    │ Wert                                             │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  invoice_number          │ RE-2025-002                                      │    │
│  │  invoice_date            │ 2025-03-16                                       │    │
│  │  supplier_name           │ Test AG                                          │    │
│  │  supplier_vat_id         │ DE111222333                                      │    │
│  │  customer_name           │ Förderprojekt GmbH                               │    │
│  │  customer_vat_id         │ DE987654321                                      │    │
│  │  net_amount              │ 500.00 €                                         │    │
│  │  vat_rate                │ 7%  ← FALSCH                                     │    │
│  │  vat_amount              │ 35.00 €                                          │    │
│  │  gross_amount            │ 535.00 €                                         │    │
│  │  service_description     │ Beratung                                         │    │
│  │  supply_date             │ 2025-03-15                                       │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  DEFINIERTE FEHLER (1)                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  ✗ TAX_VAT_RATE_WRONG                                          Severity: HIGH   │
│  │  ─────────────────────────────────────────────────────────────────────────  │    │
│  │  Feature:     vat_rate                                                      │    │
│  │  Erwartet:    19                                                            │    │
│  │  Tatsächlich: 7                                                             │    │
│  │  Nachricht:   Falscher Steuersatz: 7% statt 19% für Dienstleistung          │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  RAW JSON                                                          [📋 Kopieren]    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ {                                                                           │    │
│  │   "position": 2,                                                            │    │
│  │   "filename": "rechnung_002.pdf",                                           │    │
│  │   "is_valid": false,                                                        │    │
│  │   "errors": [                                                               │    │
│  │     {                                                                       │    │
│  │       "code": "TAX_VAT_RATE_WRONG",                                         │    │
│  │       "feature_id": "vat_rate",                                             │    │
│  │       "severity": "HIGH",                                                   │    │
│  │       "expected": 19,                                                       │    │
│  │       "actual": 7,                                                          │    │
│  │       "message": "Falscher Steuersatz: 7% statt 19%..."                     │    │
│  │     }                                                                       │    │
│  │   ],                                                                        │    │
│  │   "fields": { ... }                                                         │    │
│  │ }                                                                           │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                            [◀ Vorheriger]  [Nächster ▶]  [Schließen]│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Route: `/generator`

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  RECHNUNGSGENERATOR                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📄 Generie- │ │ 📋 Lösungs- │ │ ⏰ Batch-   │ │ 📊 Ergeb-   │                    │
│  │    ren      │ │    datei    │ │    Jobs     │ │    nisse    │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│        ▲                                                                            │
│        │ (aktiv)                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  RECHNUNGEN GENERIEREN                                                              │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  Projekt:     [Förderprojekt Digitalisierung 2025 ▼]                                │
│  Ruleset:     [DE_USTG ▼]                                                           │
│                                                                                     │
│  Anzahl Rechnungen:  [500]                                                          │
│                                                                                     │
│  Fehlerquote:        [═══════●═══════════] 25%                                      │
│                                                                                     │
│  Fehlerverteilung:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Kategorie          │ Anteil │ Fehlertypen                                  │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  TAX (Steuerrecht)  │ [40]%  │ [✓] Alle  [ ] Auswählen...                   │    │
│  │  PROJECT            │ [25]%  │ [✓] Alle  [ ] Auswählen...                   │    │
│  │  FRAUD              │ [15]%  │ [✓] Alle  [ ] Auswählen...                   │    │
│  │  SEMANTIC           │ [10]%  │ [✓] Alle  [ ] Auswählen...                   │    │
│  │  ECONOMIC           │ [10]%  │ [✓] Alle  [ ] Auswählen...                   │    │
│  │  CUSTOM             │ [--]%  │ (3 benutzerdefinierte Kriterien)             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Ausgabe:                                                                           │
│  [✓] PDF-Dateien generieren                                                         │
│  [✓] Lösungsdatei (JSON) erstellen                                                  │
│  [ ] Direkt in FlowAudit hochladen                                                  │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Vorschau (5 Beispiele):                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ 1. rechnung_001.pdf │ ✓ Gültig                                             │    │
│  │ 2. rechnung_002.pdf │ ✗ TAX_VAT_RATE_WRONG (7% statt 19%)                  │    │
│  │ 3. rechnung_003.pdf │ ✗ PROJECT_PERIOD_BEFORE_START                        │    │
│  │ 4. rechnung_004.pdf │ ✗ FRAUD_SELF_INVOICE                                 │    │
│  │ 5. rechnung_005.pdf │ ✓ Gültig                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  [Generieren & Download]    [Generieren & Batch starten]                            │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Tab: Batch-Jobs

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOBS                                                        [+ Neuer Job]    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Geplante Jobs:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Name                    │ Zeitplan      │ Projekt        │ Status   │ Aktion│    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │ Nightly Training        │ Täglich 02:00 │ Training-2025  │ ✓ Aktiv  │ [⏸️]  │    │
│  │ Weekly Full Batch       │ So 03:00      │ Alle Projekte  │ ✓ Aktiv  │ [⏸️]  │    │
│  │ Manual Test Run         │ Manuell       │ Test-Projekt   │ ⏸️ Pause │ [▶️]  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  Letzte Ausführungen:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Datum       │ Job                │ Dauer  │ Dokumente │ Fehler  │ Status   │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │ 21.03. 02:00│ Nightly Training   │ 1h 23m │ 500       │ 127     │ ✓ Fertig │    │
│  │ 20.03. 02:00│ Nightly Training   │ 1h 18m │ 500       │ 142     │ ✓ Fertig │    │
│  │ 19.03. 02:00│ Nightly Training   │ 0h 45m │ 312       │ -       │ ✗ Fehler │    │
│  │ 18.03. 02:00│ Nightly Training   │ 1h 05m │ 500       │ 98      │ ✓ Fertig │    │
│  │ 16.03. 03:00│ Weekly Full Batch  │ 4h 12m │ 2.340     │ 456     │ ✓ Fertig │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  [Details] [Report herunterladen] [Erneut ausführen]                                │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Aktuell laufend:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  ⏳ Manual Test Run                                                          │    │
│  │  ─────────────────────────────────────────────────────────────────────────── │    │
│  │  Gestartet: 21.03.2025 14:32:15                                              │    │
│  │  Fortschritt: [███████████░░░░░░░░░] 127/500 Dokumente (25%)                 │    │
│  │  Geschätzte Restzeit: ~18 Minuten                                            │    │
│  │                                                                               │    │
│  │  Aktuelle Datei: rechnung_128.pdf                                            │    │
│  │  Status: Semantische Analyse...                                              │    │
│  │                                                                               │    │
│  │  [Abbrechen]                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Batch-Job Konfiguration (erweitert)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOB KONFIGURATION                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📋 Basis    │ │ 📜 Regel-   │ │ ⚙️ Worker   │ │ 📧 Nach     │                    │
│  │             │ │    werk     │ │             │ │   Abschluss │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│        ▲                                                                            │
│        │ (aktiv)                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  BASIS-EINSTELLUNGEN                                                                │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  Name:           [Nightly Training_____________]                                    │
│                                                                                     │
│  Zeitplan:                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  [✓] Geplanter Lauf                                                        │    │
│  │      Häufigkeit: [Täglich ▼]  um  [02:00 ▼]                                │    │
│  │                                                                             │    │
│  │  [ ] Manueller Lauf (nur auf Knopfdruck)                                   │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Projekt:        [Training-2025 ▼]                                                  │
│                                                                                     │
│  Quelle:                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  ● Verzeichnis:  [/data/training/incoming/______]   [📁 Durchsuchen]       │    │
│  │  ○ S3 Bucket:    [___________________________________]                     │    │
│  │  ○ Generator:    (Rechnungen bei Batch-Start generieren)                   │    │
│  │                                                                             │    │
│  │  Erwartete Dateien:  ~500 (basierend auf letztem Lauf)                     │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Lösungsdatei:   [solution.json_____] (im gleichen Verzeichnis)                     │
│                  [✓] Fehler wenn nicht vorhanden                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Tab: Regelwerk-Auswahl

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOB KONFIGURATION                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📋 Basis    │ │ 📜 Regel-   │ │ ⚙️ Worker   │ │ 📧 Nach     │                    │
│  │             │ │    werk     │ │             │ │   Abschluss │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│                        ▲                                                            │
│                        │ (aktiv)                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  REGELWERK AUSWÄHLEN                                                                │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  Aktives Regelwerk:  [DE_USTG (§ 14 UStG) ▼]                                        │
│                                                                                     │
│  Verfügbare Regelwerke:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  ● DE_USTG         │ § 14 UStG Pflichtangaben (Deutschland)        │ 30 Regeln    │
│  │  ○ DE_ESTG         │ § 4 EStG Betriebsausgaben                     │ 18 Regeln    │
│  │  ○ EU_VAT          │ EU-Richtlinie 2006/112/EG                     │ 25 Regeln    │
│  │  ○ CUSTOM_PROJECT  │ Projektspezifisch (Training-2025)             │ 12 Regeln    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  PRÜFKATEGORIEN AKTIVIEREN                               [Alle ▼] [Keine] [Invert] │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  [✓] 📜 TAX (Steuerrecht)                                       13 Regeln  │    │
│  │      └── [▼ Details anzeigen]                                              │    │
│  │          ┌───────────────────────────────────────────────────────────────┐ │    │
│  │          │ [✓] supplier_name        Lieferantenname              HIGH   │ │    │
│  │          │ [✓] supplier_address     Lieferantenadresse           HIGH   │ │    │
│  │          │ [✓] supplier_vat_id      USt-IdNr./Steuernr.          HIGH   │ │    │
│  │          │ [✓] customer_name        Empfängername                HIGH   │ │    │
│  │          │ [✓] invoice_number       Rechnungsnummer              HIGH   │ │    │
│  │          │ [✓] invoice_date         Rechnungsdatum               HIGH   │ │    │
│  │          │ [✓] service_description  Leistungsbeschreibung        HIGH   │ │    │
│  │          │ [✓] supply_date          Leistungsdatum/-zeitraum     HIGH   │ │    │
│  │          │ [✓] net_amount           Nettobetrag                  HIGH   │ │    │
│  │          │ [✓] vat_rate             Steuersatz                   HIGH   │ │    │
│  │          │ [✓] vat_amount           Steuerbetrag                 HIGH   │ │    │
│  │          │ [✓] gross_amount         Bruttobetrag                 HIGH   │ │    │
│  │          │ [ ] payment_terms        Zahlungsbedingungen          LOW    │ │    │
│  │          └───────────────────────────────────────────────────────────────┘ │    │
│  │                                                                             │    │
│  │  [✓] 📋 PROJECT (Projektbezug)                                   7 Regeln  │    │
│  │      └── [▶ Details anzeigen]                                              │    │
│  │                                                                             │    │
│  │  [✓] ⚠️ FRAUD (Betrugsindikatoren)                               5 Regeln  │    │
│  │      └── [▶ Details anzeigen]                                              │    │
│  │                                                                             │    │
│  │  [✓] 🤖 SEMANTIC (KI-Prüfung)                                    3 Regeln  │    │
│  │      └── [▶ Details anzeigen]                                              │    │
│  │          ┌───────────────────────────────────────────────────────────────┐ │    │
│  │          │ [✓] project_relevance    Projektrelevanz (LLM)       MEDIUM  │ │    │
│  │          │ [✓] red_flag_keywords    Red-Flag Keywords           MEDIUM  │ │    │
│  │          │ [✓] plausibility_check   Plausibilitätsprüfung       LOW     │ │    │
│  │          │                                                               │ │    │
│  │          │ LLM-Provider für diesen Batch:  [Ollama (llama3.2) ▼]         │ │    │
│  │          └───────────────────────────────────────────────────────────────┘ │    │
│  │                                                                             │    │
│  │  [✓] 💰 ECONOMIC (Wirtschaftlichkeit)                            2 Regeln  │    │
│  │      └── [▶ Details anzeigen]                                              │    │
│  │                                                                             │    │
│  │  [✓] 🔧 CUSTOM (Benutzerdefiniert)                               3 Regeln  │    │
│  │      └── [▶ Details anzeigen]                                              │    │
│  │          ┌───────────────────────────────────────────────────────────────┐ │    │
│  │          │ [✓] max_daily_rate       Max. Tagessatz 1.200€       MEDIUM  │ │    │
│  │          │ [✓] project_number_format Projektnr.-Format          LOW     │ │    │
│  │          │ [✓] blocked_suppliers    Gesperrte Lieferanten       HIGH    │ │    │
│  │          │                                                               │ │    │
│  │          │ [+ Neues Kriterium hinzufügen]                                │ │    │
│  │          └───────────────────────────────────────────────────────────────┘ │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Ausgewählt: 33 von 33 Regeln                            [Als Preset speichern]     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Tab: Worker-Konfiguration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOB KONFIGURATION                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📋 Basis    │ │ 📜 Regel-   │ │ ⚙️ Worker   │ │ 📧 Nach     │                    │
│  │             │ │    werk     │ │             │ │   Abschluss │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│                                       ▲                                             │
│                                       │ (aktiv)                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  WORKER & PERFORMANCE                                                               │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  ⚙️ CELERY WORKER STATUS                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  Worker              │ Status    │ CPU    │ RAM    │ Aktuelle Aufgabe       │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  worker-1            │ 🟢 Bereit │ 12%    │ 2.1 GB │ -                      │    │
│  │  worker-2            │ 🟢 Bereit │ 8%     │ 1.8 GB │ -                      │    │
│  │  worker-3            │ 🟡 Belegt │ 45%    │ 3.2 GB │ Weekly Backup (23%)    │    │
│  │  worker-4            │ 🟢 Bereit │ 5%     │ 1.5 GB │ -                      │    │
│  │  ─────────────────────────────────────────────────────────────────────────  │    │
│  │  Gesamt: 4 Worker    │ 3 verfügbar │ Ø 17% │ 8.6 GB │                       │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Worker für diesen Job:  [2 ▼] von 3 verfügbaren                                    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  📊 GESCHÄTZTE DAUER                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  Erwartete Rechnungen:  ~500                                                │    │
│  │                                                                             │    │
│  │  Schritt                    │ Pro Rechnung │ Gesamt (500) │ Mit 2 Workern  │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  PDF einlesen & OCR         │ ~0.5 Sek     │ ~4 Min       │ ~2 Min         │    │
│  │  Feldextraktion (LLM)       │ ~2.0 Sek     │ ~17 Min      │ ~8 Min         │    │
│  │  TAX-Prüfung                │ ~0.1 Sek     │ ~1 Min       │ ~30 Sek        │    │
│  │  PROJECT-Prüfung            │ ~0.1 Sek     │ ~1 Min       │ ~30 Sek        │    │
│  │  FRAUD-Prüfung              │ ~0.2 Sek     │ ~2 Min       │ ~1 Min         │    │
│  │  SEMANTIC-Prüfung (LLM)     │ ~3.0 Sek     │ ~25 Min      │ ~12 Min        │    │
│  │  ECONOMIC-Prüfung           │ ~0.5 Sek     │ ~4 Min       │ ~2 Min         │    │
│  │  RAG-Speicherung            │ ~0.2 Sek     │ ~2 Min       │ ~1 Min         │    │
│  │  ─────────────────────────────────────────────────────────────────────────  │    │
│  │  GESAMT                     │ ~6.6 Sek     │ ~55 Min      │ ~27 Min        │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  💡 Empfehlung:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Mit 2 Workern: ~27 Min (empfohlen für Nacht-Batch)                        │    │
│  │  Mit 3 Workern: ~18 Min (schneller, höhere Systemlast)                     │    │
│  │                                                                             │    │
│  │  ⚠️ Die SEMANTIC-Prüfung (LLM) ist der Flaschenhals.                        │    │
│  │     GPU-Beschleunigung kann die Dauer um 50-70% reduzieren.                │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  🎯 PRIORITÄT                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Priorität:  [Normal ▼]  (Hoch / Normal / Niedrig)                         │    │
│  │                                                                             │    │
│  │  [ ] Andere Jobs pausieren während Ausführung                              │    │
│  │  [ ] Bei Fehler: Job abbrechen (statt fortsetzen)                          │    │
│  │  [✓] Timeout pro Rechnung: [60] Sekunden                                   │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Tab: Nach Abschluss

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-JOB KONFIGURATION                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│  │ 📋 Basis    │ │ 📜 Regel-   │ │ ⚙️ Worker   │ │ 📧 Nach     │                    │
│  │             │ │    werk     │ │             │ │   Abschluss │                    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                    │
│                                                        ▲                            │
│                                                        │ (aktiv)                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  NACH ABSCHLUSS                                                                     │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  📧 BENACHRICHTIGUNG                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  [✓] Report per E-Mail senden                                              │    │
│  │      An: [jan.riener@vwvg.de__________] [+ Empfänger]                       │    │
│  │                                                                             │    │
│  │      Report enthält:                                                        │    │
│  │      [✓] Zusammenfassung (Anzahl, Fehler, Dauer)                           │    │
│  │      [✓] Fehlerverteilung nach Kategorien                                  │    │
│  │      [✓] Top 10 häufigste Fehler                                           │    │
│  │      [ ] Detailliste aller Fehler (kann groß sein)                         │    │
│  │      [✓] Link zum Dashboard                                                │    │
│  │                                                                             │    │
│  │  [✓] Bei Fehlern sofort benachrichtigen (nicht auf Abschluss warten)       │    │
│  │      Schwelle: Bei mehr als [10] % Fehlerrate                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  🔗 WEBHOOK                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  [ ] Webhook aufrufen                                                       │    │
│  │      URL: [https://api.example.com/batch-complete]                          │    │
│  │      Method: [POST ▼]                                                       │    │
│  │      Headers: [Authorization: Bearer xxx]                                   │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  📁 DATEIVERWALTUNG                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Nach erfolgreicher Verarbeitung:                                           │    │
│  │  ● Dateien im Quellverzeichnis belassen                                    │    │
│  │  ○ In Archiv verschieben: [/data/archive/{batch_id}/]                      │    │
│  │  ○ Löschen (Vorsicht!)                                                     │    │
│  │                                                                             │    │
│  │  [✓] Fehlerhafte Dateien separat speichern: [/data/failed/]                │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  📊 RAG-TRAINING                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  [✓] Automatisches RAG-Learning aktivieren                                  │    │
│  │      Quelle: Lösungsdatei (wenn vorhanden)                                 │    │
│  │                                                                             │    │
│  │  [✓] Nur bei korrekter Erkennung (LLM = Lösungsdatei) trainieren           │    │
│  │  [ ] Auch bei Abweichung trainieren (mit Lösungsdatei-Wert)                │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Zusammenfassung:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Job:        Nightly Training                                               │    │
│  │  Zeitplan:   Täglich um 02:00                                               │    │
│  │  Regelwerk:  DE_USTG (33 Regeln aktiv)                                      │    │
│  │  Worker:     2 von 4                                                        │    │
│  │  Geschätzt:  ~27 Min für ~500 Rechnungen                                    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│                                   [Abbrechen]  [Testlauf (10 Rechnungen)]  [Speichern]│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Performance-Richtwerte

| Rechnungen | Worker | Geschätzte Dauer | Empfehlung |
|------------|--------|------------------|------------|
| 100 | 1 | ~11 Min | Schnelltest |
| 100 | 2 | ~6 Min | Validierung |
| 500 | 2 | ~27 Min | Täglicher Batch |
| 500 | 4 | ~14 Min | Wenn schnell benötigt |
| 1000 | 2 | ~55 Min | Nacht-Batch |
| 1000 | 4 | ~27 Min | Mit Priorität |
| 5000 | 4 | ~2h 20m | Wochenend-Batch |

**Faktoren die Dauer beeinflussen:**
- **LLM-Provider**: Ollama (lokal) vs. OpenAI (Cloud, schneller aber teurer)
- **GPU**: Mit NVIDIA GPU ~50-70% schneller für LLM
- **Komplexität**: Rechnungen mit vielen Positionen dauern länger
- **Netzwerk**: Bei Cloud-LLM ist Latenz relevant

---

### Tab: Ergebnisse

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH-ERGEBNISSE                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Job: Nightly Training (21.03.2025)                                                 │
│                                                                                     │
│  ┌───────────────────────────┐  ┌───────────────────────────┐                       │
│  │      500                  │  │       127                 │                       │
│  │   Dokumente               │  │   Fehler erkannt          │                       │
│  │      verarbeitet          │  │      (25,4%)              │                       │
│  └───────────────────────────┘  └───────────────────────────┘                       │
│                                                                                     │
│  ┌───────────────────────────┐  ┌───────────────────────────┐                       │
│  │      1.245                │  │       98,2%               │                       │
│  │   RAG-Beispiele           │  │   Erkennungsrate          │                       │
│  │      generiert            │  │      (vs. Lösungsdatei)   │                       │
│  └───────────────────────────┘  └───────────────────────────┘                       │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  Fehlerverteilung:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                                                                             │    │
│  │  TAX          ████████████████████████████░░░░░░░  52 (41%)                │    │
│  │  PROJECT      ████████████████░░░░░░░░░░░░░░░░░░░  32 (25%)                │    │
│  │  FRAUD        ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  18 (14%)                │    │
│  │  SEMANTIC     █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12 (9%)                 │    │
│  │  ECONOMIC     ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8 (6%)                 │    │
│  │  CUSTOM       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5 (4%)                 │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                     │
│  Erkennungs-Analyse (LLM vs. Lösungsdatei):                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Fehlertyp                    │ Erwartet │ Erkannt │ Rate    │ Trend       │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  TAX_VAT_RATE_WRONG           │ 24       │ 24      │ 100%    │ ━           │    │
│  │  TAX_SUPPLY_DATE_MISSING      │ 18       │ 17      │ 94%     │ ↗ +2%       │    │
│  │  PROJECT_PERIOD_BEFORE_START  │ 15       │ 15      │ 100%    │ ━           │    │
│  │  FRAUD_SELF_INVOICE           │ 12       │ 12      │ 100%    │ ━           │    │
│  │  SEMANTIC_LOW_PROJECT_REL     │ 8        │ 6       │ 75%     │ ↘ -5%       │    │
│  │  CUSTOM_MAX_DAILY_RATE        │ 5        │ 5       │ 100%    │ NEU         │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  [Fehler im Detail] [RAG-Beispiele ansehen] [Report exportieren]                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Fehler-Codes (Schnittstelle Generator ↔ System)

### Übersicht

Die Fehler-Codes werden sowohl vom **Rechnungsgenerator** (in der Lösungsdatei) als auch vom **Prüfsystem** verwendet. Dies ermöglicht:
- Automatisches Training mit generierten Rechnungen
- Konsistente Fehler-Klassifizierung
- Vergleich: "Was sollte erkannt werden?" vs. "Was wurde erkannt?"

### Fehler-Code Struktur

```
ERROR_CODE = {KATEGORIE}_{MERKMAL}_{TYP}

Beispiele:
- TAX_SUPPLIER_NAME_MISSING     → Lieferantenname fehlt
- TAX_VAT_RATE_WRONG            → Falscher Steuersatz
- PROJECT_PERIOD_OUTSIDE        → Leistung außerhalb Projektzeitraum
- FRAUD_SELF_INVOICE            → Selbstrechnung (gleiche UST-ID)
```

### Kategorie: TAX (Steuerrecht §14 UStG)

| Code | Feature-ID | Beschreibung | Severity |
|------|------------|--------------|----------|
| `TAX_SUPPLIER_NAME_MISSING` | `supplier_name` | Lieferantenname fehlt | HIGH |
| `TAX_SUPPLIER_NAME_INCOMPLETE` | `supplier_name` | Lieferantenname unvollständig | MEDIUM |
| `TAX_SUPPLIER_ADDRESS_MISSING` | `supplier_address` | Lieferantenadresse fehlt | HIGH |
| `TAX_SUPPLIER_ADDRESS_INCOMPLETE` | `supplier_address` | Adresse unvollständig (PLZ/Ort fehlt) | MEDIUM |
| `TAX_CUSTOMER_NAME_MISSING` | `customer_name` | Empfängername fehlt | HIGH |
| `TAX_CUSTOMER_ADDRESS_MISSING` | `customer_address` | Empfängeradresse fehlt | HIGH |
| `TAX_ID_MISSING` | `tax_id` | Steuernummer/UST-ID fehlt | HIGH |
| `TAX_ID_INVALID_FORMAT` | `tax_id` | Ungültiges Format der Steuernummer | MEDIUM |
| `TAX_INVOICE_DATE_MISSING` | `invoice_date` | Rechnungsdatum fehlt | HIGH |
| `TAX_INVOICE_DATE_INVALID` | `invoice_date` | Ungültiges Datumsformat | MEDIUM |
| `TAX_INVOICE_DATE_FUTURE` | `invoice_date` | Rechnungsdatum in der Zukunft | HIGH |
| `TAX_INVOICE_NUMBER_MISSING` | `invoice_number` | Rechnungsnummer fehlt | HIGH |
| `TAX_INVOICE_NUMBER_DUPLICATE` | `invoice_number` | Rechnungsnummer bereits verwendet | HIGH |
| `TAX_SERVICE_DESCRIPTION_MISSING` | `service_description` | Leistungsbeschreibung fehlt | HIGH |
| `TAX_SERVICE_DESCRIPTION_VAGUE` | `service_description` | Leistungsbeschreibung zu ungenau | MEDIUM |
| `TAX_SUPPLY_DATE_MISSING` | `supply_date_or_period` | Leistungsdatum/-zeitraum fehlt | HIGH |
| `TAX_NET_AMOUNT_MISSING` | `net_amount` | Nettobetrag fehlt | HIGH |
| `TAX_NET_AMOUNT_INVALID` | `net_amount` | Ungültiger Nettobetrag | MEDIUM |
| `TAX_VAT_RATE_MISSING` | `vat_rate` | Steuersatz fehlt | HIGH |
| `TAX_VAT_RATE_WRONG` | `vat_rate` | Falscher Steuersatz (z.B. 7% statt 19%) | HIGH |
| `TAX_VAT_RATE_INVALID` | `vat_rate` | Ungültiger Steuersatz (nicht 0/7/19%) | HIGH |
| `TAX_VAT_AMOUNT_MISSING` | `vat_amount` | Steuerbetrag fehlt | HIGH |
| `TAX_VAT_AMOUNT_WRONG` | `vat_amount` | Steuerbetrag falsch berechnet | HIGH |
| `TAX_GROSS_AMOUNT_MISSING` | `gross_amount` | Bruttobetrag fehlt | HIGH |
| `TAX_GROSS_AMOUNT_WRONG` | `gross_amount` | Bruttobetrag stimmt nicht (Netto+USt) | HIGH |

### Kategorie: PROJECT (Projektbezug)

| Code | Feature-ID | Beschreibung | Severity |
|------|------------|--------------|----------|
| `PROJECT_PERIOD_BEFORE_START` | `supply_in_project_period` | Leistung vor Projektbeginn | HIGH |
| `PROJECT_PERIOD_AFTER_END` | `supply_in_project_period` | Leistung nach Projektende | HIGH |
| `PROJECT_PERIOD_OUTSIDE` | `supply_in_project_period` | Leistung außerhalb Durchführungszeitraum | HIGH |
| `PROJECT_RECIPIENT_MISMATCH` | `recipient_is_beneficiary` | Empfänger ≠ Begünstigter | MEDIUM |
| `PROJECT_LOCATION_MISMATCH` | `service_location_match` | Leistungsort ≠ Projektstandort | LOW |
| `PROJECT_REFERENCE_MISSING` | `project_reference` | Kein Projektbezug erkennbar | MEDIUM |
| `PROJECT_REFERENCE_VAGUE` | `project_reference` | Projektbezug unklar | LOW |

### Kategorie: FRAUD (Betrugsindikatoren)

| Code | Feature-ID | Beschreibung | Severity |
|------|------------|--------------|----------|
| `FRAUD_SELF_INVOICE` | `self_invoice_check` | **Selbstrechnung: Lieferant-UST-ID = Empfänger-UST-ID** | CRITICAL |
| `FRAUD_CIRCULAR_INVOICE` | `circular_invoice_check` | Zirkelrechnung vermutet | CRITICAL |
| `FRAUD_DUPLICATE_INVOICE` | `duplicate_check` | Rechnung bereits eingereicht | CRITICAL |
| `FRAUD_ROUND_AMOUNT_PATTERN` | `round_amount_check` | Verdächtige runde Beträge | MEDIUM |
| `FRAUD_VENDOR_CLUSTERING` | `vendor_clustering` | Ungewöhnliche Lieferantenhäufung | MEDIUM |

### Kategorie: SEMANTIC (KI-Prüfung)

| Code | Feature-ID | Beschreibung | Severity |
|------|------------|--------------|----------|
| `SEMANTIC_NO_PROJECT_RELEVANCE` | `semantic_project_relevance` | Leistung passt nicht zum Projekt | MEDIUM |
| `SEMANTIC_LOW_PROJECT_RELEVANCE` | `semantic_project_relevance` | Projektbezug fraglich | LOW |
| `SEMANTIC_RED_FLAG_LUXURY` | `no_red_flags` | Luxusgüter erkannt | HIGH |
| `SEMANTIC_RED_FLAG_ENTERTAINMENT` | `no_red_flags` | Bewirtung/Unterhaltung erkannt | MEDIUM |
| `SEMANTIC_RED_FLAG_PRIVATE` | `no_red_flags` | Privatnutzung vermutet | HIGH |

### Kategorie: ECONOMIC (Wirtschaftlichkeit)

| Code | Feature-ID | Beschreibung | Severity |
|------|------------|--------------|----------|
| `ECONOMIC_HIGH_AMOUNT` | `economic_plausibility` | Ungewöhnlich hoher Betrag | MEDIUM |
| `ECONOMIC_ABOVE_MARKET` | `economic_plausibility` | Preis über Marktüblichkeit | MEDIUM |
| `ECONOMIC_STATISTICAL_OUTLIER` | `no_statistical_anomalies` | Statistischer Ausreißer | LOW |

### Lösungsdatei mit Fehler-Codes

```json
{
  "generator_version": "1.0.0",
  "generated_at": "2025-03-20T10:00:00Z",
  "invoices": [
    {
      "position": 1,
      "filename": "rechnung_001.pdf",
      "is_valid": true,
      "errors": [],
      "fields": {
        "invoice_number": "RE-2025-001",
        "invoice_date": "2025-03-15",
        "supplier_name": "Mustermann GmbH",
        "supplier_vat_id": "DE123456789",
        "customer_name": "Förderprojekt GmbH",
        "customer_vat_id": "DE987654321",
        "net_amount": 1000.00,
        "vat_rate": 19,
        "vat_amount": 190.00,
        "gross_amount": 1190.00,
        "service_description": "IT-Beratung März 2025",
        "supply_date": "2025-03-15"
      }
    },
    {
      "position": 2,
      "filename": "rechnung_002.pdf",
      "is_valid": false,
      "errors": [
        {
          "code": "TAX_VAT_RATE_WRONG",
          "feature_id": "vat_rate",
          "severity": "HIGH",
          "expected": 19,
          "actual": 7,
          "message": "Falscher Steuersatz: 7% statt 19% für Dienstleistung"
        },
        {
          "code": "PROJECT_PERIOD_BEFORE_START",
          "feature_id": "supply_in_project_period",
          "severity": "HIGH",
          "expected": "2025-04-01 bis 2025-12-31",
          "actual": "2025-03-15",
          "message": "Leistungsdatum vor Projektbeginn"
        }
      ],
      "fields": {
        "invoice_number": "RE-2025-002",
        "invoice_date": "2025-03-16",
        "supplier_name": "Test AG",
        "supplier_vat_id": "DE111222333",
        "customer_name": "Förderprojekt GmbH",
        "customer_vat_id": "DE987654321",
        "net_amount": 500.00,
        "vat_rate": 7,
        "vat_amount": 35.00,
        "gross_amount": 535.00,
        "service_description": "Beratung",
        "supply_date": "2025-03-15"
      }
    },
    {
      "position": 3,
      "filename": "rechnung_003.pdf",
      "is_valid": false,
      "errors": [
        {
          "code": "FRAUD_SELF_INVOICE",
          "feature_id": "self_invoice_check",
          "severity": "CRITICAL",
          "expected": "Verschiedene UST-IDs",
          "actual": "DE987654321 = DE987654321",
          "message": "Selbstrechnung: Lieferant und Empfänger haben gleiche UST-ID"
        }
      ],
      "fields": {
        "invoice_number": "RE-2025-003",
        "supplier_name": "Förderprojekt GmbH",
        "supplier_vat_id": "DE987654321",
        "customer_name": "Förderprojekt GmbH",
        "customer_vat_id": "DE987654321",
        "net_amount": 5000.00
      }
    }
  ]
}
```

---

## Projektdaten-Integration

### Projektmodell (vollständig)

```python
class Project:
    id: UUID
    title: str                    # "Förderprojekt Digitalisierung 2025"
    project_number: str           # "FKZ-2025-12345"

    # Projektzeitraum (Bewilligungszeitraum)
    project_period: dict          # {"start": "2025-01-01", "end": "2025-12-31"}

    # Durchführungszeitraum (für Leistungsprüfung)
    execution_period: dict        # {"start": "2025-04-01", "end": "2025-11-30"}

    # Begünstigter (Zuwendungsempfänger)
    beneficiary_name: str         # "Muster GmbH"
    beneficiary_address: str      # "Musterstr. 1, 12345 Berlin"
    beneficiary_vat_id: str       # "DE987654321" ← NEU: Für Selbstrechnungs-Prüfung

    # Projektbeschreibung (für semantische Prüfung)
    project_description: str      # "Digitalisierung der Geschäftsprozesse..."

    # Projektstandort (Pflicht!)
    project_location: str         # "Hamburg" (für Leistungsort-Prüfung)

    # Ruleset
    ruleset_id: str               # "DE_USTG"

    # Weitere Metadaten
    funding_rate: float           # 0.7 (70% Förderquote)
    max_funding_amount: float     # 100000.00 (max. Fördersumme)
```

### Prüf-Felder Mapping

| Projektfeld | Prüfung gegen | Fehler-Code bei Abweichung |
|-------------|---------------|----------------------------|
| `execution_period.start` | `supply_date` | `PROJECT_PERIOD_BEFORE_START` |
| `execution_period.end` | `supply_date` | `PROJECT_PERIOD_AFTER_END` |
| `beneficiary_name` | `customer_name` | `PROJECT_RECIPIENT_MISMATCH` |
| `beneficiary_vat_id` | `supplier_vat_id` | `FRAUD_SELF_INVOICE` |
| `project_location` | `service_location` | `PROJECT_LOCATION_MISMATCH` |
| `project_description` | `service_description` | `SEMANTIC_*` |

### Datenfluss: Projekt → Prüfung

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PROJEKT                                                                            │
│  ════════                                                                           │
│  Title:               Förderprojekt Digitalisierung 2025                            │
│  Nummer:              FKZ-2025-12345                                                │
│  Projektzeitraum:     01.01.2025 - 31.12.2025 (Bewilligung)                         │
│  Durchführung:        01.04.2025 - 30.11.2025 (für Leistungsprüfung)                │
│  Begünstigter:        Muster GmbH                                                   │
│  Begünstigter-UST-ID: DE987654321                                                   │
│  Standort:            Hamburg                                                       │
│  Beschreibung:        Digitalisierung der Geschäftsprozesse durch Einführung        │
│                       eines ERP-Systems und Cloud-Migration...                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PRÜFUNG                                                                            │
│  ════════                                                                           │
│                                                                                     │
│  Rule Engine:                                                                       │
│  ├── Leistungsdatum "15.05.2025" ∈ [01.04.2025, 30.11.2025]? → ✓                    │
│  └── supply_in_project_period = VALID                                              │
│                                                                                     │
│  Selbstrechnungs-Prüfung:                                                           │
│  ├── supplier_vat_id "DE123456789" ≠ beneficiary_vat_id "DE987654321"? → ✓          │
│  └── self_invoice_check = VALID                                                    │
│                                                                                     │
│  Risk Checker:                                                                      │
│  ├── customer_name "Muster GmbH" ≈ beneficiary_name "Muster GmbH"? → ✓              │
│  └── recipient_is_beneficiary = VALID                                              │
│                                                                                     │
│  LLM:                                                                               │
│  ├── Leistung "ERP-Beratung" passt zu "Digitalisierung...ERP-System"? → ✓           │
│  └── semantic_project_relevance = HIGH                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Selbstrechnungs-Prüfung (NEU)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SELBSTRECHNUNGS-CHECK                                                              │
│  ═════════════════════                                                              │
│                                                                                     │
│  Prüflogik:                                                                         │
│  ├── supplier_vat_id aus Rechnung extrahieren                                       │
│  ├── Mit beneficiary_vat_id aus Projekt vergleichen                                 │
│  └── Bei Übereinstimmung: FRAUD_SELF_INVOICE (CRITICAL)                             │
│                                                                                     │
│  Beispiel VALIDE Rechnung:                                                          │
│  ├── Lieferant:    Extern GmbH (DE123456789)                                        │
│  ├── Empfänger:    Muster GmbH (DE987654321)                                        │
│  └── Ergebnis:     ✓ OK                                                             │
│                                                                                     │
│  Beispiel SELBSTRECHNUNG:                                                           │
│  ├── Lieferant:    Muster GmbH (DE987654321)  ← Gleiche UST-ID!                     │
│  ├── Empfänger:    Muster GmbH (DE987654321)  ← Gleiche UST-ID!                     │
│  └── Ergebnis:     ✗ FRAUD_SELF_INVOICE (CRITICAL)                                  │
│                                                                                     │
│  Implementierung:                                                                   │
│  if normalize(supplier_vat_id) == normalize(beneficiary_vat_id):                    │
│      return Error(FRAUD_SELF_INVOICE, severity=CRITICAL)                            │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Geklärte Fragen

1. **Lösungsdatei-Format**: PDF-Dateien werden generiert, Lösungsdatei separat (JSON)
2. **Matching**: Dateiname + Position in der Upload-Liste
3. **Feedback → RAG**: Bereits implementiert! Jede Korrektur wird als RAG-Beispiel gespeichert.
4. **Ruleset**: DE_USTG (§ 14 UStG Pflichtangaben)
5. **Prüfumfang**: Steuerrecht + Förderfähigkeit + Semantik + Wirtschaftlichkeit + Betrug
6. **Batch-Job**: Celery Beat, täglich 02:00 Uhr
7. **Fehler-Codes**: Definiert in 5 Kategorien (TAX, PROJECT, FRAUD, SEMANTIC, ECONOMIC)
8. **Merge-Default**: Manuelle Eingaben haben Vorrang vor Lösungsdatei
9. **Selbstrechnungs-Prüfung**: `FRAUD_SELF_INVOICE` bei gleicher UST-ID
10. **Projektdaten**: Erweitert um `execution_period`, `beneficiary_vat_id`, `project_description`

## Geklärte Fragen (fortgesetzt)

11. **E-Mail-Benachrichtigung**: Batch-Reports an jan.riener@vwvg.de
12. **Projektstandort**: `project_location` ist **Pflicht** (nicht optional)
13. **Förderquote**: `funding_rate` und `max_funding_amount` werden benötigt
14. **Schulungs-Ansicht**: Alle Prüfdetails (Risk/Semantic/Economic) transparent anzeigen (nur lesen)
15. **Benutzerdefinierte Kriterien**: Eigene Prüfregeln definierbar, automatisch in Batch-Config synchronisiert
16. **Generator-GUI**: Zugriff auf Batch-Jobs direkt aus der Generator-Oberfläche

---

## Implementierungs-Plan

### Phase 0: Vorbereitung (Backend)
1. [ ] Fehler-Codes als Enum definieren (`backend/app/models/enums.py`)
2. [ ] Projektmodell erweitern (`execution_period`, `beneficiary_vat_id`)
3. [ ] Selbstrechnungs-Prüfung in Risk Checker einbauen
4. [ ] Lösungsdatei-Parser implementieren

### Phase 1: Belegliste (Frontend)
1. [ ] Tabellen-Layout mit Pagination
2. [ ] Status-Spalte mit Icons (✓/⚠/✗/⏳)
3. [ ] Suche und Filter
4. [ ] Zusammenfassungs-Leiste

### Phase 2: Split-View (Frontend)
1. [ ] PDF-Viewer Komponente (react-pdf)
2. [ ] Kriterienkatalog nach Kategorien
3. [ ] Navigation (Prev/Next)

### Phase 3: Korrektur-Formular (Frontend + Backend)
1. [ ] Inline-Korrektur pro Merkmal
2. [ ] Begründungs-Feld
3. [ ] Feedback-API Anbindung
4. [ ] RAG-Learning Trigger

### Phase 4: Lösungsdatei-Import
1. [ ] Upload-Endpunkt (Backend)
2. [ ] Parser für JSON-Format
3. [ ] Matching-Logik (Dateiname + Position)
4. [ ] Upload-UI (Frontend)
5. [ ] Merge-Dialog (manuell hat Vorrang)

### Phase 5: Batch-Job
1. [ ] Celery Beat Konfiguration
2. [ ] `process_training_batch` Task
3. [ ] Auto-Feedback aus Lösungsdatei
4. [ ] Report-Generierung
5. [ ] Batch-Job UI (optional)

### Phase 6: Prüf-GUIs im Frontend (Regelwerk-Bereich)

> **Hinweis**: Der Risk Checker, die Semantische Prüfung und die Wirtschaftlichkeitsprüfung haben aktuell **keine GUI**. Diese müssen im Frontend unter Rulesets/Settings implementiert werden.

1. [ ] **Risk Checker GUI** (`/rulesets/{id}/risk-checker`)
   - [ ] Schwellenwerte konfigurieren (z.B. Betrags-Grenze für Warnung)
   - [ ] Aktivieren/Deaktivieren einzelner Regeln
   - [ ] Lieferantenhäufungs-Schwelle einstellen
   - [ ] Pauschalbetrags-Erkennung konfigurieren

2. [ ] **Semantic Check GUI** (`/rulesets/{id}/semantic`)
   - [ ] LLM-Provider auswählen (für semantische Prüfung)
   - [ ] Red-Flag Keywords verwalten (z.B. "Bewirtung", "Luxus")
   - [ ] Projektrelevanz-Schwellenwert einstellen
   - [ ] Test-Funktion: Beispiel-Beschreibung prüfen

3. [ ] **Economic Check GUI** (`/rulesets/{id}/economic`)
   - [ ] Marktüblichkeits-Prüfung aktivieren
   - [ ] Statistische Ausreißer-Erkennung (Standardabweichungen)
   - [ ] Branchen-spezifische Richtwerte (optional)
   - [ ] Preis-Benchmarks verwalten

### UI-Mockup: Regelwerk-Erweiterung

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  REGELWERK: DE_USTG (§ 14 UStG)                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ 📜 Steuer-  │ │ 📋 Projekt- │ │ ⚠️ Risk     │ │ 🤖 Semantik │ │ 💰 Wirtsch. │    │
│  │    recht    │ │    bezug    │ │   Checker   │ │             │ │             │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
│        ▲              ▲              ▲                                              │
│        │              │              │ (aktiv)                                      │
│        │              │              │                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ⚠️ RISK CHECKER KONFIGURATION                                                      │
│  ═══════════════════════════════════════════════════════════════════════════════    │
│                                                                                     │
│  Aktiviert: [✓]                                                                     │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Regel                          │ Aktiv │ Schwellenwert │ Severity         │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  Hohe Beträge                   │  [✓]  │ [50.000] €    │ [MEDIUM ▼]       │    │
│  │  Lieferantenhäufung             │  [✓]  │ [30] %        │ [LOW ▼]          │    │
│  │  Fehlender Leistungszeitraum    │  [✓]  │ -             │ [MEDIUM ▼]       │    │
│  │  Runde Pauschalbeträge          │  [✓]  │ [1.000] €     │ [LOW ▼]          │    │
│  │  Außerhalb Projektzeitraum      │  [✓]  │ -             │ [HIGH ▼]         │    │
│  │  Fehlender Projektbezug         │  [✓]  │ -             │ [MEDIUM ▼]       │    │
│  │  Empfänger-Abweichung           │  [✓]  │ -             │ [MEDIUM ▼]       │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Statistische Ausreißer:                                                            │
│  Median + [2] Standardabweichungen = Warnung                                        │
│                                                                                     │
│                                                         [Zurücksetzen] [Speichern]  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🤖 SEMANTISCHE PRÜFUNG KONFIGURATION                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Aktiviert: [✓]                                                                     │
│                                                                                     │
│  LLM-Provider: [Ollama (llama3.2) ▼]                                                │
│                                                                                     │
│  Projektrelevanz-Schwelle:                                                          │
│  [═══════════════●═══] 70%                                                          │
│  └─ Unter diesem Wert: SEMANTIC_LOW_PROJECT_RELEVANCE                               │
│                                                                                     │
│  Red-Flag Keywords (Warnung bei Erkennung):                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Bewirtung  ×  │ Luxus  ×  │ Privatfahrzeug  ×  │ Alkohol  ×  │ + Hinzufügen│    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Red-Flag Keywords (Ablehnung):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ Glücksspiel  ×  │ Parteispende  ×  │ + Hinzufügen                          │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Test-Funktion:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │ IT-Beratung für ERP-Einführung im Rahmen der Digitalisierungsinitiative    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│  [Testen] → Ergebnis: ✓ 92% Projektrelevanz, keine Red-Flags                        │
│                                                                                     │
│                                                         [Zurücksetzen] [Speichern]  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  💰 WIRTSCHAFTLICHKEITSPRÜFUNG KONFIGURATION                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Aktiviert: [✓]                                                                     │
│                                                                                     │
│  Statistische Ausreißer-Erkennung:                                                  │
│  Warnung ab: Median + [2] Standardabweichungen                                      │
│                                                                                     │
│  Preis-Benchmarks (optional):                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Leistungsart          │ Einheit      │ Max. Preis │ Quelle                 │    │
│  ├─────────────────────────────────────────────────────────────────────────────┤    │
│  │  IT-Beratung           │ Stunde       │ 180,00 €   │ Marktüblich            │    │
│  │  Softwareentwicklung   │ Stunde       │ 150,00 €   │ Marktüblich            │    │
│  │  Büromaterial          │ Pauschale    │ 500,00 €   │ Erfahrungswert         │    │
│  │  [+ Hinzufügen]                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  Automatische Marktpreis-Prüfung:                                                   │
│  [ ] Gegen öffentliche Preisdatenbanken prüfen (experimentell)                      │
│                                                                                     │
│                                                         [Zurücksetzen] [Speichern]  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 7: Schulungs-Ansicht (Training View)

> **Hinweis**: Da FlowAudit auch als **Schulungstool** dient, müssen alle Prüfkriterien transparent angezeigt werden.

1. [ ] **Prüfdetails-Komponente** (`DocumentCheckDetails.tsx`)
   - [ ] Alle Prüfregeln mit Schwellenwerten anzeigen
   - [ ] Berechnete Werte anzeigen (Median, σ, dynamische Grenzen)
   - [ ] LLM-Antworten und Konfidenz anzeigen
   - [ ] Collapsible Sections pro Kategorie

2. [ ] **JSON-Export der Prüfdetails**
   - [ ] API-Endpunkt: `GET /api/documents/{id}/check-details`
   - [ ] Vollständige Prüflogik exportieren
   - [ ] Download-Button in der UI

3. [ ] **Legende und Hilfe**
   - [ ] Info-Icons [ℹ️] mit Erklärungen
   - [ ] Legende für Symbole und Farben

### Phase 8: Benutzerdefinierte Kriterien

1. [ ] **Backend: Custom Criteria Model**
   - [ ] `CustomCriterion` SQLAlchemy Model
   - [ ] Migrations erstellen
   - [ ] CRUD-Endpunkte implementieren

2. [ ] **Backend: Prüflogik-Engine**
   - [ ] Dynamische Regel-Auswertung
   - [ ] Unterstützung für alle Logik-Typen (Schwellenwert, Regex, etc.)
   - [ ] Integration in bestehende Prüf-Pipeline

3. [ ] **Frontend: Kriterien-Verwaltung** (`/rulesets/{id}/custom`)
   - [ ] Kriterienliste mit CRUD-Operationen
   - [ ] Kriterium-Editor mit Formular
   - [ ] Logik-Typ-Auswahl mit dynamischem Formular
   - [ ] Test-Funktion

4. [ ] **Auto-Sync mit Batch-Konfiguration**
   - [ ] Celery-Task für Sync bei Änderungen
   - [ ] Automatisches Hinzufügen neuer Kriterien zu aktiven Batch-Jobs
   - [ ] Benachrichtigung bei Sync

### Phase 9: Generator-GUI

1. [ ] **Route: `/generator`**
   - [ ] Tab-Navigation (Generieren, Lösungsdatei, Batch-Jobs, Ergebnisse)
   - [ ] Projekt- und Ruleset-Auswahl

2. [ ] **Tab: Generieren**
   - [ ] Anzahl und Fehlerquote konfigurieren
   - [ ] Fehlerverteilung nach Kategorien
   - [ ] Vorschau der ersten 5 Rechnungen
   - [ ] Buttons: "Download" oder "Batch starten"

3. [ ] **Tab: Batch-Jobs**
   - [ ] Geplante Jobs anzeigen (mit Start/Pause)
   - [ ] Letzte Ausführungen mit Status
   - [ ] Laufende Jobs mit Fortschrittsanzeige
   - [ ] Job-Konfiguration (Zeitplan, Quelle, Kriterien)

4. [ ] **Tab: Ergebnisse**
   - [ ] Statistik-Kacheln (Dokumente, Fehler, RAG-Beispiele, Rate)
   - [ ] Fehlerverteilungs-Diagramm
   - [ ] Erkennungs-Analyse mit Trend
   - [ ] Export-Funktionen

5. [ ] **Backend: Generator-API**
   - [ ] `POST /api/generator/generate` - Rechnungen generieren
   - [ ] `GET /api/generator/preview` - Vorschau
   - [ ] `POST /api/generator/batch` - Batch-Job starten
   - [ ] `GET /api/batch-jobs` - Alle Jobs abrufen
   - [ ] `POST /api/batch-jobs/{id}/trigger` - Job manuell starten

### Phase 10: Tests
1. [ ] Unit-Tests für Fehler-Codes
2. [ ] Integration-Tests für Selbstrechnungs-Prüfung
3. [ ] E2E-Tests mit generierten Rechnungen
4. [ ] Performance-Tests (1000 Rechnungen)
5. [ ] Tests für Prüf-GUIs (Risk Checker, Semantic, Economic)
6. [ ] Tests für benutzerdefinierte Kriterien
7. [ ] Tests für Generator-GUI und Batch-Jobs
