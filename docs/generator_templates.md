# FlowAudit – Generator-Templates
## Spezifikation der 5 Rechnungs-Templates für den PDF-Generator
## Version: 1.0.0

---

## 0. Zweck dieses Dokuments

Dieses Dokument spezifiziert die **5 Templates** für den Rechnungs-Generator:

- Layout und visuelle Struktur
- Typografische Varianten
- Platzhalter und Felder
- Fehlerinjektionspunkte
- Beispiel-Rendering

Der Generator erzeugt **realistische Dummy-Rechnungen** für Training und Demo.

---

## 1. Gemeinsame Spezifikation

### 1.1 Technische Basis

| Aspekt | Spezifikation |
|--------|---------------|
| **PDF-Bibliothek** | ReportLab oder WeasyPrint |
| **Seitenformat** | A4 (210 × 297 mm) |
| **Ränder** | 20-25 mm (variiert pro Template) |
| **Schriftarten** | 3-4 verschiedene (Arial, Times, Helvetica, Courier) |
| **Sprachen** | Deutsch und Englisch |
| **Encoding** | UTF-8 |

### 1.2 Gemeinsame Datenfelder

Alle Templates müssen folgende Felder unterstützen:

```python
class InvoiceData(BaseModel):
    # Lieferant
    supplier_name: str
    supplier_street: str
    supplier_zip_city: str
    supplier_country: str | None
    supplier_tax_id: str | None      # Steuernummer
    supplier_vat_id: str | None      # USt-ID
    supplier_phone: str | None
    supplier_email: str | None
    supplier_website: str | None
    supplier_bank_name: str | None
    supplier_iban: str | None
    supplier_bic: str | None

    # Empfänger
    customer_name: str
    customer_street: str
    customer_zip_city: str
    customer_country: str | None
    customer_vat_id: str | None      # Für B2B/Reverse Charge

    # Rechnung
    invoice_number: str
    invoice_date: date
    delivery_date: date | None       # Lieferdatum (einzeln)
    service_period_start: date | None
    service_period_end: date | None
    payment_terms: str | None
    due_date: date | None

    # Positionen
    line_items: list[LineItem]

    # Beträge
    net_total: Decimal
    vat_rate: Decimal               # z.B. 0.19
    vat_amount: Decimal
    gross_total: Decimal

    # Optionale Texte
    intro_text: str | None
    footer_text: str | None
    payment_reference: str | None
```

### 1.3 Fehlerinjektions-Arten

| Fehler-ID | Beschreibung | Betroffene Features |
|-----------|--------------|---------------------|
| `MISSING_TAX_ID` | Keine Steuernummer/USt-ID | supplier_tax_or_vat_id |
| `INVALID_TAX_ID` | Falsches Format | supplier_tax_or_vat_id |
| `MISSING_DATE` | Kein Rechnungsdatum | invoice_date |
| `FUTURE_DATE` | Datum in der Zukunft | invoice_date |
| `MISSING_PERIOD` | Kein Leistungszeitraum | supply_date_or_period |
| `VAGUE_PERIOD` | Unklarer Zeitraum | supply_date_or_period |
| `MISSING_NUMBER` | Keine Rechnungsnummer | invoice_number |
| `WRONG_MATH` | Netto + MwSt ≠ Brutto | net_amount, vat_amount |
| `MISSING_SUPPLIER` | Unvollständige Adresse | supplier_name_address |
| `MISSING_CUSTOMER` | Unvollständige Adresse | customer_name_address |
| `VAGUE_DESCRIPTION` | Unspezifische Leistung | supply_description |
| `WRONG_VAT_RATE` | Falscher Steuersatz | vat_rate |
| `MISSING_VAT_AMOUNT` | Keine MwSt ausgewiesen | vat_amount |

---

## 2. Template T1: HANDWERK (Handwerker-Rechnung)

### 2.1 Charakteristik

| Aspekt | Beschreibung |
|--------|--------------|
| **Branche** | Handwerk (Elektro, Sanitär, Schreiner) |
| **Stil** | Schlicht, sachlich, oft alt-modisch |
| **Besonderheit** | Material + Arbeitszeit getrennt |
| **Typische Fehler** | Fehlende Steuernummer, vage Leistungsbeschreibung |

### 2.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [LOGO platzhalter]           Elektro Müller GmbH               │
│                               Handwerkerstraße 15               │
│                               12345 Musterstadt                 │
│                               Tel: 0123 456789                  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  An:                                                            │
│  ┌────────────────────────┐                                     │
│  │ Kunde Name             │                                     │
│  │ Kundenstraße 1         │                                     │
│  │ 54321 Kundenstadt      │                                     │
│  └────────────────────────┘                                     │
│                                                                  │
│                               Rechnungsnummer: R-2025-0042      │
│                               Datum: 15.03.2025                 │
│                               Steuernummer: 12/345/67890        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  R E C H N U N G                                                │
│                                                                  │
│  Für Arbeiten im Zeitraum: 01.03.2025 - 10.03.2025             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Pos │ Beschreibung                    │ Menge │ Preis    │ │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │  1  │ Material: Kabel NYM-J 3x1,5    │ 50 m  │  125,00 €│ │ │
│  │  2  │ Material: Steckdosen           │ 10 St │   89,00 €│ │ │
│  │  3  │ Arbeitszeit Montage            │ 8 Std │  480,00 €│ │ │
│  │  4  │ Anfahrt                        │ 1     │   35,00 €│ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                               Nettobetrag:        729,00 €      │
│                               MwSt. 19%:          138,51 €      │
│                               ─────────────────────────────     │
│                               Gesamtbetrag:       867,51 €      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Zahlbar innerhalb von 14 Tagen ohne Abzug.                     │
│  Bankverbindung: Sparkasse Musterstadt                          │
│  IBAN: DE89 3704 0044 0532 0130 00                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Typografische Varianten

| Variante | Schriftart | Überschrift | Tabelle |
|----------|------------|-------------|---------|
| T1-A | Arial | Fett, 14pt | Rahmen |
| T1-B | Times | Normal, 12pt | Linien |
| T1-C | Courier | Großbuchstaben | Kein Rahmen |

### 2.4 Datums-Varianten

- `DD.MM.YYYY` (Standard)
- `D. MMMM YYYY` ("15. März 2025")
- Zeitraum: `DD.MM. - DD.MM.YYYY`

---

## 3. Template T2: SUPERMARKT (Kassenbonähnlich)

### 3.1 Charakteristik

| Aspekt | Beschreibung |
|--------|--------------|
| **Branche** | Einzelhandel, Gastronomie |
| **Stil** | Kompakt, viele Positionen |
| **Besonderheit** | Kurze Beschreibungen, EAN-Nummern |
| **Typische Fehler** | Fehlende Adresse, gemischte MwSt-Sätze |

### 3.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│              ╔═══════════════════════════════════╗              │
│              ║   BÜROMARKT MEIER GMBH & CO. KG   ║              │
│              ║      Einkaufszentrum Ost 42       ║              │
│              ║        98765 Handelsstadt         ║              │
│              ║     USt-IdNr.: DE 123456789       ║              │
│              ╚═══════════════════════════════════╝              │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  Kunde: Muster GmbH              Rechnung Nr: 2025/03/00142    │
│  Lieferadresse:                  Datum: 15.03.2025             │
│  Industrieweg 5                  Kundennr: K-4711              │
│  11111 Gewerbepark                                              │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Art.Nr.   Bezeichnung                      Menge    Betrag    │
│  ─────────────────────────────────────────────────────────────  │
│  4006381   Kopierpapier A4 500 Bl.           5     24,95 €     │
│  4006382   Ordner breit blau                10     29,90 €     │
│  4006383   Kugelschreiber 10er              20     19,80 €     │
│  4006384   Textmarker Set 4-fach             5     12,45 €     │
│  4006385   Heftklammern 1000 St.            10      9,90 €     │
│  4006386   Locher 20 Blatt                   2     15,98 €     │
│  4006387   Tacker Standard                   2     11,98 €     │
│  4006388   Druckerpapier A4 2500            10    149,00 €     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│                                Zwischensumme:     273,96 €      │
│                                MwSt 19%:           52,05 €      │
│                                ═════════════════════════════    │
│                                GESAMT:            326,01 €      │
│                                                                  │
│  Leistungsdatum entspricht Rechnungsdatum.                     │
│  Zahlbar bis: 29.03.2025                                       │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│       Vielen Dank für Ihren Einkauf!                            │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Typografische Varianten

| Variante | Schriftart | Besonderheit |
|----------|------------|--------------|
| T2-A | Monospace (Courier) | Kassenbon-Stil |
| T2-B | Sans-Serif (Arial) | Modern, clean |
| T2-C | Mixed | Logo groß, Rest klein |

---

## 4. Template T3: CORPORATE (Konzern-Rechnung)

### 4.1 Charakteristik

| Aspekt | Beschreibung |
|--------|--------------|
| **Branche** | IT-Dienstleister, Beratung, Konzerne |
| **Stil** | Professionell, viel Leerraum, Logo prominent |
| **Besonderheit** | Projektreferenzen, Bestellnummern |
| **Typische Fehler** | Leistungsbeschreibung zu allgemein |

### 4.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌────────────────┐                                             │
│  │                │                                             │
│  │   [LOGO]       │        TechConsult Solutions GmbH           │
│  │                │        Digital Innovation Partner           │
│  └────────────────┘                                             │
│                                                                  │
│                         Technologiepark 100 | 80333 München     │
│                         Tel +49 89 123456-0 | Fax -99           │
│                         info@techconsult.example                │
│                         www.techconsult.example                 │
│                                                                  │
│                         USt-IdNr. DE987654321                   │
│                         Handelsregister: HRB 12345              │
│                         Geschäftsführer: Dr. Max Mustermann     │
│                                                                  │
│  ════════════════════════════════════════════════════════════   │
│                                                                  │
│                                                                  │
│  Empfänger:                    Rechnungsdaten:                  │
│                                                                  │
│  Stadt Aschaffenburg           Rechnungsnummer: INV-2025-00042  │
│  Amt für Digitalisierung       Rechnungsdatum:  15.03.2025      │
│  Dalbergstraße 15              Kundennummer:    C-12345         │
│  63739 Aschaffenburg           Projekt-Ref:     PRJ-2025-001    │
│                                Bestellnummer:   PO-2025-0815    │
│                                                                  │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│  Leistungszeitraum: 01.02.2025 - 28.02.2025                    │
│                                                                  │
│  Pos  Beschreibung                                    Betrag    │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│   1   IT-Beratungsleistungen gemäß Rahmenvertrag              │
│       vom 15.01.2025                                            │
│       - Anforderungsanalyse (40 Std. × 150,00 €)   6.000,00 €  │
│       - Konzepterstellung (24 Std. × 150,00 €)     3.600,00 €  │
│       - Projektmanagement (16 Std. × 120,00 €)     1.920,00 €  │
│                                                                  │
│   2   Reisekosten pauschal                            480,00 €  │
│                                                                  │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│                              Nettobetrag:        12.000,00 €    │
│                              Umsatzsteuer 19%:    2.280,00 €    │
│                                                                  │
│                              Rechnungsbetrag:    14.280,00 €    │
│                                                                  │
│  ════════════════════════════════════════════════════════════   │
│                                                                  │
│  Zahlungsbedingungen: 30 Tage netto                            │
│  Bankverbindung: Deutsche Bank München                          │
│  IBAN: DE89 7007 0024 0123 4567 89 | BIC: DEUTDEDB               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Typografische Varianten

| Variante | Schriftart | Logo-Position | Farbe |
|----------|------------|---------------|-------|
| T3-A | Helvetica | Links oben | Blau |
| T3-B | Arial | Rechts oben | Grau |
| T3-C | Custom Sans | Mittig | Schwarz |

---

## 5. Template T4: FREELANCER (Freiberufler-Rechnung)

### 5.1 Charakteristik

| Aspekt | Beschreibung |
|--------|--------------|
| **Branche** | Kreative, Übersetzer, Dozenten |
| **Stil** | Persönlich, einfach, oft ohne Logo |
| **Besonderheit** | Keine USt-ID (Kleinunternehmer möglich) |
| **Typische Fehler** | Fehlende Angaben, Reverse Charge unklar |

### 5.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                                    Maria Schneider              │
│                                    Freiberufliche Übersetzerin  │
│                                    Sprachweg 7                  │
│                                    50667 Köln                   │
│                                                                  │
│                                    Tel: 0221 9876543            │
│                                    maria@schneider-uebersetzt.de│
│                                                                  │
│                                    Steuernummer: 217/5432/1234  │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  An:                                                            │
│  Verlag Beispiel GmbH                                           │
│  Buchstraße 99                                                  │
│  10115 Berlin                                                   │
│                                                                  │
│                                                                  │
│                                                                  │
│                      R E C H N U N G                            │
│                                                                  │
│                      Nummer: 2025-012                           │
│                      Datum:  15. März 2025                      │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Leistung:                                                      │
│                                                                  │
│  Übersetzung des Manuskripts "Technische Dokumentation          │
│  Produktlinie X" vom Deutschen ins Englische                    │
│                                                                  │
│  Umfang: 45 Normseiten × 28,00 € pro Seite                     │
│                                                                  │
│  Leistungszeitraum: 01.03.2025 - 12.03.2025                    │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Honorar:                                          1.260,00 €   │
│  Umsatzsteuer 19%:                                   239,40 €   │
│                                                     ──────────  │
│  Gesamtbetrag:                                     1.499,40 €   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Bitte überweisen Sie den Betrag innerhalb von 14 Tagen auf:   │
│  IBAN: DE12 3456 7890 1234 5678 90                              │
│  Verwendungszweck: Rechnung 2025-012                            │
│                                                                  │
│                                                                  │
│  Mit freundlichen Grüßen                                        │
│  Maria Schneider                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Sondervariante: Kleinunternehmer

```
│  Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.            │
│                                                                  │
│  Gesamtbetrag:                                     1.260,00 €   │
```

### 5.4 Typografische Varianten

| Variante | Schriftart | Stil |
|----------|------------|------|
| T4-A | Times New Roman | Klassisch, förmlich |
| T4-B | Georgia | Elegant, literarisch |
| T4-C | Arial | Modern, schlicht |

---

## 6. Template T5: MINIMAL (Minimalistische Rechnung)

### 6.1 Charakteristik

| Aspekt | Beschreibung |
|--------|--------------|
| **Branche** | Diverse, oft kleine Betriebe |
| **Stil** | Extrem sparsam, wenig Formatierung |
| **Besonderheit** | Grenzt an unvollständig |
| **Typische Fehler** | Viele Pflichtangaben fehlen |

### 6.2 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Müller & Sohn                                                  │
│  Hauptstr. 1, 99999 Kleinstadt                                  │
│  St.Nr. 123/456/78901                                           │
│                                                                  │
│  An: Firma ABC                                                  │
│      Industriestr. 5                                            │
│      88888 Großstadt                                            │
│                                                                  │
│  Rechnung 42 vom 15.3.25                                        │
│                                                                  │
│  Reparaturarbeiten                              850,00          │
│  + 19% MwSt                                     161,50          │
│  ────────────────────────────────────────────────────           │
│  Summe                                        1.011,50 €        │
│                                                                  │
│  Zahlung auf Konto DE11 2222 3333 4444 5555 66                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Typische Mängel (für Training)

- Adresse unvollständig (nur Straße, keine PLZ)
- Datum abgekürzt
- Keine USt-ID
- Leistungszeitraum fehlt
- Leistungsbeschreibung minimal

### 6.4 Typografische Varianten

| Variante | Schriftart | Besonderheit |
|----------|------------|--------------|
| T5-A | Courier | Schreibmaschinen-Stil |
| T5-B | Arial Narrow | Eng, platzsparend |
| T5-C | Handschrift-Font | Fast handgeschrieben |

---

## 7. Datumformat-Varianten

### 7.1 Unterstützte Formate

| Format-ID | Beispiel (DE) | Beispiel (EN) |
|-----------|---------------|---------------|
| `DATE_DOTS` | 15.03.2025 | 15.03.2025 |
| `DATE_SLASHES` | 15/03/2025 | 03/15/2025 |
| `DATE_DASHES` | 2025-03-15 | 2025-03-15 |
| `DATE_LONG_DE` | 15. März 2025 | March 15, 2025 |
| `DATE_MONTH_YEAR` | März 2025 | March 2025 |
| `RANGE_DOTS` | 01.03. - 15.03.2025 | 01.03. - 15.03.2025 |
| `RANGE_LONG` | 1. bis 15. März 2025 | March 1-15, 2025 |
| `QUARTER` | Q1/2025 | Q1/2025 |
| `MONTH_NAME` | März 2025 | March 2025 |
| `SINGLE_DAY` | Lieferdatum: 15.03.2025 | Delivery: 03/15/2025 |

### 7.2 Konfigurations-Profil

```python
class DateFormatProfile(BaseModel):
    invoice_date_format: str = "DATE_DOTS"
    delivery_date_format: str = "DATE_DOTS"
    period_format: str = "RANGE_DOTS"
    due_date_format: str = "DATE_DOTS"

# Beispiel-Profile
PROFILE_GERMAN_STANDARD = DateFormatProfile(
    invoice_date_format="DATE_DOTS",
    period_format="RANGE_DOTS"
)

PROFILE_GERMAN_FORMAL = DateFormatProfile(
    invoice_date_format="DATE_LONG_DE",
    period_format="RANGE_LONG"
)

PROFILE_ISO = DateFormatProfile(
    invoice_date_format="DATE_DASHES",
    period_format="RANGE_DOTS"
)
```

---

## 8. Generator-Konfiguration

### 8.1 Fehlerinjektions-Einstellungen

```python
class GeneratorConfig(BaseModel):
    # Allgemein
    count: int = 20                    # Anzahl zu generierender Rechnungen
    ruleset_id: str = "DE_USTG"        # Anzuwendendes Regelwerk
    language: str = "de"               # DE oder EN

    # Templates
    templates_enabled: list[str] = [
        "T1_HANDWERK",
        "T2_SUPERMARKT",
        "T3_CORPORATE",
        "T4_FREELANCER",
        "T5_MINIMAL"
    ]
    template_weights: dict[str, float] = {
        "T1_HANDWERK": 0.25,
        "T2_SUPERMARKT": 0.15,
        "T3_CORPORATE": 0.25,
        "T4_FREELANCER": 0.20,
        "T5_MINIMAL": 0.15
    }

    # Fehlerraten
    error_rate_total: float = 30.0      # % der Rechnungen mit Fehlern
    errors_per_invoice: int = 2         # Max. Fehler pro fehlerhafter Rechnung

    # Feature-spezifische Fehlerraten (% der Fehler)
    feature_error_weights: dict[str, float] = {
        "supplier_tax_or_vat_id": 20.0,
        "invoice_number": 5.0,
        "invoice_date": 5.0,
        "supply_date_or_period": 15.0,
        "supply_description": 20.0,
        "supplier_name_address": 10.0,
        "customer_name_address": 5.0,
        "net_amount": 5.0,
        "vat_amount": 10.0,
        "gross_amount": 5.0
    }

    # Varianz
    date_format_profiles: list[str] = [
        "GERMAN_STANDARD",
        "GERMAN_FORMAL",
        "ISO"
    ]
    typography_variance: bool = True    # Schriftarten variieren
    layout_variance: bool = True        # Layout-Varianten nutzen

    # Aliase (für Fuzzy-Matching-Tests)
    customer_alias_probability: float = 10.0  # % mit alternativer Schreibweise
```

### 8.2 Beispiel: Generator-Aufruf

```python
# API Request
POST /api/generator/run
{
    "project_id": "prj_001",
    "ruleset_id": "DE_USTG",
    "language": "de",
    "count": 50,
    "templates_enabled": ["T1_HANDWERK", "T3_CORPORATE", "T5_MINIMAL"],
    "error_rate_total": 40.0,
    "errors_per_invoice": 2,
    "feature_error_weights": {
        "supplier_tax_or_vat_id": 30.0,
        "supply_date_or_period": 25.0,
        "supply_description": 25.0,
        "vat_amount": 20.0
    },
    "date_format_profiles": ["GERMAN_STANDARD", "GERMAN_FORMAL"]
}
```

---

## 9. Solutions-Datei Format

### 9.1 Struktur

```
# FlowAudit Generator Solutions
# Generated: 2025-12-15 14:30:00
# Ruleset: DE_USTG
# Count: 50
# Error Rate: 40%
# Templates: T1_HANDWERK, T3_CORPORATE, T5_MINIMAL

INV_0001.pdf | CORRECT | T1_HANDWERK | -
INV_0002.pdf | ERROR | T3_CORPORATE | supplier_tax_or_vat_id:MISSING
INV_0003.pdf | CORRECT | T5_MINIMAL | -
INV_0004.pdf | ERROR | T1_HANDWERK | supply_date_or_period:VAGUE, vat_amount:WRONG_MATH
INV_0005.pdf | ERROR | T3_CORPORATE | supply_description:VAGUE
...
```

### 9.2 Manifest-Datei (JSON)

```json
{
  "generator_run_id": "gen_20251215_143000",
  "created_at": "2025-12-15T14:30:00Z",
  "config": {
    "ruleset_id": "DE_USTG",
    "count": 50,
    "error_rate": 40.0,
    "templates_used": ["T1_HANDWERK", "T3_CORPORATE", "T5_MINIMAL"]
  },
  "statistics": {
    "total_invoices": 50,
    "correct_invoices": 30,
    "error_invoices": 20,
    "errors_by_feature": {
      "supplier_tax_or_vat_id": 8,
      "supply_date_or_period": 6,
      "supply_description": 5,
      "vat_amount": 4
    },
    "invoices_by_template": {
      "T1_HANDWERK": 18,
      "T3_CORPORATE": 17,
      "T5_MINIMAL": 15
    }
  },
  "files": [
    {
      "filename": "INV_0001.pdf",
      "sha256": "a1b2c3...",
      "template": "T1_HANDWERK",
      "has_errors": false,
      "errors": []
    },
    {
      "filename": "INV_0002.pdf",
      "sha256": "d4e5f6...",
      "template": "T3_CORPORATE",
      "has_errors": true,
      "errors": [
        {"feature_id": "supplier_tax_or_vat_id", "error_type": "MISSING"}
      ]
    }
  ]
}
```

---

## 10. Preview-Generierung

### 10.1 Vorschaubilder für UI

Für jedes Template wird ein statisches Vorschaubild generiert:

| Template | Preview-Datei | Größe |
|----------|---------------|-------|
| T1_HANDWERK | `preview_t1.png` | 200×280 px |
| T2_SUPERMARKT | `preview_t2.png` | 200×280 px |
| T3_CORPORATE | `preview_t3.png` | 200×280 px |
| T4_FREELANCER | `preview_t4.png` | 200×280 px |
| T5_MINIMAL | `preview_t5.png` | 200×280 px |

### 10.2 API-Endpoint

```
GET /api/generator/templates
→ [
    {
      "template_id": "T1_HANDWERK",
      "name_de": "Handwerker",
      "name_en": "Craftsman",
      "description_de": "Klassische Handwerkerrechnung mit Material und Arbeitszeit",
      "preview_url": "/api/generator/templates/T1_HANDWERK/preview"
    },
    ...
  ]

GET /api/generator/templates/T1_HANDWERK/preview
→ image/png (200×280)
```

---

## 11. Wichtige Hinweise

### 11.1 Keine erkennbaren Marker

Die generierten Rechnungen dürfen **keine offensichtlichen "Dummy"-Marker** enthalten:
- Keine "BEISPIEL" oder "TEST" Texte
- Keine Muster-IBANs wie "DE00 0000 0000 ..."
- Keine offensichtlichen Platzhalter

### 11.2 Realistische Daten

```python
# Beispiel: Name-Generator
SUPPLIER_NAMES_DE = [
    "Müller Elektrotechnik GmbH",
    "Bau & Boden Schmidt KG",
    "IT-Service Weber",
    "Haustechnik Braun GmbH & Co. KG",
    "Bürobedarf Hoffmann e.K."
]

# Beispiel: Straßen-Generator
STREETS_DE = [
    "Industriestraße", "Gewerbepark", "Handwerkerweg",
    "Am Bahnhof", "Hauptstraße", "Marktplatz"
]
```

### 11.3 Rechnungsempfänger = Begünstigter

**Wichtig:** Der Rechnungsempfänger (customer) **muss** dem Begünstigten (beneficiary) aus dem Projektprofil entsprechen:

```python
def generate_invoice(project: Project, config: GeneratorConfig) -> InvoiceData:
    # Der Rechnungsempfänger wird aus dem Projekt übernommen
    invoice.customer_name = project.beneficiary.name
    invoice.customer_street = project.beneficiary.street
    invoice.customer_zip_city = f"{project.beneficiary.zip} {project.beneficiary.city}"

    # Optional: Alias-Varianten für Fuzzy-Matching-Tests
    if random() < config.customer_alias_probability / 100:
        invoice.customer_name = random.choice(project.beneficiary.aliases)
```

Dies stellt sicher, dass:
- Der semantische Abgleich (Zuwendungsempfänger = Rechnungsempfänger) testbar ist
- Alias-Schreibweisen (z.B. "Stadt Aschaffenburg" vs. "Stadtverwaltung Aschaffenburg") trainiert werden können
- Die Projektbindung korrekt geprüft wird

### 11.4 Solutions niemals in DB

Die `solutions.txt` und `manifest.json` werden **ausschließlich** im Dateisystem gespeichert:
- `/data/generated/{batch_id}/solutions.txt`
- `/data/generated/{batch_id}/manifest.json`

Sie werden **niemals** in die Datenbank importiert, um Bias beim Training zu vermeiden.
