# FlowAudit – Regelwerksdefinitionen (Rulesets)
## Vollständige, versionierte und maschinenlesbare Abbildung der steuerlichen Anforderungen
## Gültig für Seminar-, Demo- und Referenzbetrieb

---

## 0. Zweck dieses Dokuments

Dieses Dokument definiert **vollständig und eindeutig** die steuerlichen Regelwerke, nach denen FlowAudit Rechnungen prüft.  
Es ist **kein Fließtext**, sondern die **„Ground Truth“** für:

- Parser & Vorprüfung
- KI-Input (PreparePayload)
- Testdaten-Generator
- UI-Anzeigen & Erläuterungen
- Statistik & Lernkurve

Alle Regeln sind:
- **explizit**
- **versioniert**
- **zweisprachig (DE/EN)**
- **maschinell nutzbar**

➡️ Dieses Dokument kann **1:1** als Datenquelle (JSON/YAML) implementiert werden.

---

## 1. Allgemeine Struktur eines Rulesets

### 1.1 Metadaten (Pflicht)

Jedes Ruleset besitzt folgende Metadaten:

```json
{
  "ruleset_id": "DE_USTG",
  "version": "1.0.0",
  "jurisdiction": "DE",
  "title_de": "Deutschland – Umsatzsteuergesetz",
  "title_en": "Germany – VAT Act",
  "legal_references": [
    {
      "law": "UStG",
      "section": "§ 14 Abs. 4",
      "description_de": "Pflichtangaben in Rechnungen",
      "description_en": "Mandatory invoice fields"
    }
  ],
  "default_language": "de",
  "supported_ui_languages": ["de", "en"],
  "currency_default": "EUR",
  "last_updated": "2025-12-15"
}
````

---

## 2. Feature-Definition (atomar & versionierbar)

### 2.1 Einheitliches Feature-Schema

Jedes steuerliche Merkmal wird als **Feature** definiert:

```json
{
  "feature_id": "invoice_number",
  "name_de": "Rechnungsnummer",
  "name_en": "Invoice number",
  "legal_basis": "§ 14 Abs. 4 Nr. 4 UStG",
  "required_level": "REQUIRED",
  "extraction_type": "STRING",
  "validation": {
    "regex": "^[A-Za-z0-9\\-/]+$",
    "min_length": 3
  },
  "semantic_meaning_de": "Eindeutige Identifikation der Rechnung",
  "semantic_meaning_en": "Unique identification of the invoice",
  "generator_rules": {
    "can_be_missing": true,
    "can_be_malformed": true,
    "typical_errors": [
      "missing",
      "duplicate",
      "non-unique"
    ]
  },
  "applies_to": {
    "standard_invoice": true,
    "small_amount_invoice": false
  }
}
```

---

## 3. 🇩🇪 Ruleset DE_USTG – Deutschland (UStG)

### 3.1 Metadaten

* **ruleset_id:** `DE_USTG`
* **Rechtsgrundlagen:**

  * § 14 Abs. 4 UStG – Pflichtangaben
  * § 15 UStG – Vorsteuerabzug
  * § 33 UStDV – Kleinbetragsrechnungen
  * § 7 BHO / LHO – Wirtschaftlichkeit & Sparsamkeit (semantisch)

---

### 3.2 Pflichtmerkmale (§ 14 Abs. 4 UStG)

#### 3.2.1 supplier_name_address

* **Name (DE):** Name und Anschrift des leistenden Unternehmers
* **Required:** REQUIRED
* **Extraction:** TEXTBLOCK
* **Validation:**

  * Mindestlänge
  * Enthält Straße + Ort
* **Besonderheit:**

  * Wird **nicht** mit Begünstigtem abgeglichen (Gegenseite)

---

#### 3.2.2 customer_name_address

* **Name (DE):** Name und Anschrift des Leistungsempfängers
* **Required:** REQUIRED
* **Validierung:**

  * Fuzzy-Match mit Begünstigtem + Alias-Liste
* **Semantische Bedeutung:**

  * Zuwendungsempfänger muss Rechnungsempfänger sein

---

#### 3.2.3 supplier_tax_or_vat_id

* **Name (DE):** Steuernummer oder Umsatzsteuer-ID
* **Required:** REQUIRED
* **Validation:**

  * Regex für DE-Steuernummer oder DE-USt-ID
* **Generator-Fehler:**

  * fehlt vollständig
  * falsches Format
  * falsches Land

---

#### 3.2.4 invoice_date

* **Required:** REQUIRED
* **Type:** DATE
* **Validierung:**

  * gültiges Datum
  * darf nicht nach heutigem Datum liegen
* **Zuwendungslogik:**

  * Muss innerhalb Projektzeitraum liegen (oder Leistungsdatum relevant)

---

#### 3.2.5 invoice_number

(siehe 2.1 Beispiel)

---

#### 3.2.6 supply_description

* **Name:** Art und Umfang der Leistung
* **Required:** REQUIRED
* **Type:** TEXTBLOCK
* **Semantik:**

  * Muss **inhaltlich** zum Projekt passen
* **KI-Aufgabe:** Semantischer Abgleich

---

#### 3.2.7 supply_date_or_period

* **Required:** REQUIRED
* **Type:** DATE or DATE_RANGE
* **Validierung:**

  * darf nicht vollständig außerhalb Projektzeitraum liegen
* **Generator:**

  * einzelne Daten
  * Zeiträume
  * ausgeschriebene Monate

---

#### 3.2.8 net_amount

* **Required:** REQUIRED
* **Type:** MONEY
* **Validierung:**

  * > 0
* **Zuwendungslogik:**

  * relevant bei Vorsteuerabzugsberechtigung

---

#### 3.2.9 vat_rate

* **Required:** REQUIRED
* **Valid Values (DE):**

  * 19%
  * 7%
* **Conditional:**

  * entfällt bei Steuerbefreiung / Reverse Charge

---

#### 3.2.10 vat_amount

* **Required:** REQUIRED
* **Validierung:**

  * net * rate == vat (Toleranz ±0,05 €)

---

#### 3.2.11 gross_amount

* **Required:** REQUIRED
* **Validierung:**

  * net + vat == gross

---

### 3.3 Sonderfall Kleinbetragsrechnung (§ 33 UStDV)

* **Schwelle:** ≤ 250 € Brutto
* **Reduzierte Merkmale:**

  * supplier_name
  * invoice_date
  * supply_description
  * gross_amount
  * vat_rate (implizit)
* **Ruleset-Logik:**

  * automatisch aktiviert bei gross_amount ≤ 250 €

---

### 3.4 Zuwendungsrechtliche Erweiterung (DE)

Diese Features sind **nicht steuerlich**, aber für FlowAudit relevant:

#### 3.4.1 project_fit_semantic

* **Type:** SEMANTIC
* **Source:** KI
* **Bewertung:**

  * passt / teilweise / unklar / passt nicht

#### 3.4.2 economic_efficiency_flag

* **Rechtsgrundlage:** § 7 BHO / LHO
* **Beispiel Honeypot:**

  * Strandliegen für IT-Projekt

---

## 4. 🇪🇺 Ruleset EU_VAT – MwSt-Systemrichtlinie

### 4.1 Metadaten

* **Rechtsgrundlage:** RL 2006/112/EG, Art. 226

---

### 4.2 Abweichungen/Ergänzungen zu DE

#### 4.2.1 supplier_vat_id

* **Required:** REQUIRED
* **Kein Ersatz durch Steuernummer**

---

#### 4.2.2 customer_vat_id

* **Conditional:** REQUIRED bei Reverse Charge / IG Lieferung

---

#### 4.2.3 reverse_charge_notice

* **Required:** CONDITIONAL
* **Validation:**

  * Enthält Text wie:

    * „Steuerschuldnerschaft des Leistungsempfängers“
    * „Reverse charge“

---

#### 4.2.4 currency_handling

* **Regel:**

  * Steuerbetrag muss in Landeswährung angegeben sein
* **Generator-Fehler:**

  * nur Fremdwährung angegeben

---

## 5. 🇬🇧 Ruleset UK_VAT – HMRC VAT Notice 700

### 5.1 Metadaten

* **Jurisdiction:** UK
* **Referenz:** HMRC VAT Notice 700

---

### 5.2 Pflichtmerkmale (UK-spezifisch)

#### 5.2.1 tax_point

* **Name:** Time of Supply (Tax Point)
* **Required:** REQUIRED
* **Validierung:**

  * falls abweichend vom Rechnungsdatum → explizit erforderlich

---

#### 5.2.2 unit_price

* **Type:** MONEY
* **Required:** REQUIRED (line-level)

---

#### 5.2.3 total_vat_amount

* **Type:** MONEY
* **Required:** REQUIRED

---

#### 5.2.4 total_amount_payable

* **Type:** MONEY
* **Required:** REQUIRED

---

## 6. Feature-Kategorien (für Statistik & Generator)

Jedes Feature gehört zu genau einer Kategorie:

* `IDENTITY`
* `DATE`
* `AMOUNT`
* `TAX`
* `TEXT`
* `SEMANTIC`
* `PROJECT_CONTEXT`

➡️ Diese Kategorien werden genutzt für:

* Fehlerstatistiken
* Lernkurven
* Generator-Schweregrade

---

## 7. Versionierung & Migration

### 7.1 Regeln

* Rulesets sind **immutable**
* Änderungen erzeugen neue Version
* Dokumente referenzieren immer:

  * ruleset_id
  * ruleset_version

### 7.2 Migration

* Alte Analysen bleiben unverändert
* Neue Analysen nutzen neue Version

---

## 8. Nutzung im System (Bindend)

* Parser nutzt `extraction_type`
* Regel-Engine nutzt `validation`
* KI erhält vollständige Featureliste im PreparePayload
* Generator nutzt `generator_rules`
* UI nutzt `name_de/en` + `explanation_de/en`
* Statistik aggregiert nach `feature_id` und Kategorie

---

## 9. Validierungs-Regex (vollständige Spezifikation)

### 9.1 Deutsche Steuernummer

**Formate (bundeslandabhängig):**
```regex
# Allgemeines Muster (mit oder ohne Schrägstriche)
^(\d{2,3}[\/\s]?\d{3,4}[\/\s]?\d{4,5})$

# Spezifische Varianten:
# Bayern:        123/456/78901 oder 123 456 78901
# NRW:           123/4567/8901
# Berlin:        12/345/67890
# Standard:      XX/XXX/XXXXX oder XXX/XXX/XXXXX
```

**Python-Implementierung:**
```python
GERMAN_TAX_ID_PATTERNS = [
    r"^\d{2}/\d{3}/\d{5}$",           # 12/345/67890 (Berlin, etc.)
    r"^\d{3}/\d{3}/\d{5}$",           # 123/456/78901 (Bayern)
    r"^\d{3}/\d{4}/\d{4}$",           # 123/4567/8901 (NRW)
    r"^\d{2}\s?\d{3}\s?\d{5}$",       # Mit Leerzeichen
    r"^\d{10,11}$",                   # Ohne Trennzeichen
]

def validate_german_tax_id(value: str) -> bool:
    """Prüft ob Wert einer deutschen Steuernummer entspricht."""
    normalized = value.strip()
    return any(re.match(p, normalized) for p in GERMAN_TAX_ID_PATTERNS)
```

### 9.2 Deutsche Umsatzsteuer-Identifikationsnummer (USt-ID)

```regex
# Format: DE + 9 Ziffern
^DE\s?\d{9}$
```

**Python-Implementierung:**
```python
GERMAN_VAT_ID_PATTERN = r"^DE\s?\d{9}$"

def validate_german_vat_id(value: str) -> bool:
    """Prüft deutsche USt-ID (DE + 9 Ziffern)."""
    normalized = value.strip().upper().replace(" ", "")
    return bool(re.match(r"^DE\d{9}$", normalized))
```

### 9.3 EU-Umsatzsteuer-Identifikationsnummern

```python
EU_VAT_ID_PATTERNS = {
    "AT": r"^ATU\d{8}$",                    # Österreich
    "BE": r"^BE0?\d{9,10}$",                # Belgien
    "BG": r"^BG\d{9,10}$",                  # Bulgarien
    "CY": r"^CY\d{8}[A-Z]$",                # Zypern
    "CZ": r"^CZ\d{8,10}$",                  # Tschechien
    "DE": r"^DE\d{9}$",                     # Deutschland
    "DK": r"^DK\d{8}$",                     # Dänemark
    "EE": r"^EE\d{9}$",                     # Estland
    "EL": r"^EL\d{9}$",                     # Griechenland
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",     # Spanien
    "FI": r"^FI\d{8}$",                     # Finnland
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",          # Frankreich
    "HR": r"^HR\d{11}$",                    # Kroatien
    "HU": r"^HU\d{8}$",                     # Ungarn
    "IE": r"^IE\d{7}[A-Z]{1,2}$",           # Irland
    "IT": r"^IT\d{11}$",                    # Italien
    "LT": r"^LT(\d{9}|\d{12})$",            # Litauen
    "LU": r"^LU\d{8}$",                     # Luxemburg
    "LV": r"^LV\d{11}$",                    # Lettland
    "MT": r"^MT\d{8}$",                     # Malta
    "NL": r"^NL\d{9}B\d{2}$",               # Niederlande
    "PL": r"^PL\d{10}$",                    # Polen
    "PT": r"^PT\d{9}$",                     # Portugal
    "RO": r"^RO\d{2,10}$",                  # Rumänien
    "SE": r"^SE\d{12}$",                    # Schweden
    "SI": r"^SI\d{8}$",                     # Slowenien
    "SK": r"^SK\d{10}$",                    # Slowakei
}

def validate_eu_vat_id(value: str, country_code: str = None) -> bool:
    """Prüft EU-USt-ID, optional mit Ländercode-Einschränkung."""
    normalized = value.strip().upper().replace(" ", "").replace("-", "")

    if country_code:
        pattern = EU_VAT_ID_PATTERNS.get(country_code)
        return bool(pattern and re.match(pattern, normalized))

    # Länderpräfix aus Wert extrahieren
    if len(normalized) >= 2:
        prefix = normalized[:2]
        pattern = EU_VAT_ID_PATTERNS.get(prefix)
        return bool(pattern and re.match(pattern, normalized))

    return False
```

### 9.4 UK VAT-Nummer

```regex
# Standard: GB + 9 oder 12 Ziffern
^GB\s?\d{9}$
^GB\s?\d{12}$

# Alternativer Format mit Trennzeichen
^GB\s?\d{3}\s?\d{4}\s?\d{2}$
```

**Python-Implementierung:**
```python
UK_VAT_PATTERNS = [
    r"^GB\d{9}$",           # Standard 9-stellig
    r"^GB\d{12}$",          # 12-stellig (mit Suffix)
    r"^GB\s?\d{3}\s?\d{4}\s?\d{2}$",  # Mit Leerzeichen
]

def validate_uk_vat_id(value: str) -> bool:
    """Prüft UK VAT-Nummer."""
    normalized = value.strip().upper().replace(" ", "").replace("-", "")
    return any(re.match(p, normalized) for p in UK_VAT_PATTERNS)
```

### 9.5 IBAN-Validierung

```regex
# Allgemeines IBAN-Muster (bis 34 Zeichen)
^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$

# Deutsche IBAN (22 Zeichen)
^DE\d{20}$
```

**Python-Implementierung:**
```python
def validate_iban(value: str) -> bool:
    """Prüft IBAN-Format (nicht Prüfziffer)."""
    normalized = value.strip().upper().replace(" ", "")

    # Ländercode + 2 Prüfziffern + BBAN
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$", normalized):
        return False

    # Längenprüfung nach Land
    IBAN_LENGTHS = {
        "DE": 22, "AT": 20, "CH": 21, "FR": 27, "IT": 27,
        "ES": 24, "NL": 18, "BE": 16, "PL": 28, "GB": 22
    }

    country = normalized[:2]
    expected_length = IBAN_LENGTHS.get(country)

    if expected_length and len(normalized) != expected_length:
        return False

    return True
```

### 9.6 Rechnungsnummer

```regex
# Flexible Muster (keine strenge Validierung)
^[A-Za-z0-9\-\/\.]+$

# Typische Muster:
# 2025-001, R-2025-0042, INV/2025/00001, 20250315-001
```

**Python-Implementierung:**
```python
INVOICE_NUMBER_PATTERN = r"^[A-Za-z0-9\-\/\.]{3,30}$"

def validate_invoice_number(value: str) -> bool:
    """Prüft ob Rechnungsnummer plausibel ist."""
    normalized = value.strip()
    return bool(re.match(INVOICE_NUMBER_PATTERN, normalized))
```

### 9.7 Datumsformate

```python
DATE_PATTERNS = {
    "DD.MM.YYYY": r"^\d{1,2}\.\d{1,2}\.\d{4}$",
    "DD/MM/YYYY": r"^\d{1,2}/\d{1,2}/\d{4}$",
    "YYYY-MM-DD": r"^\d{4}-\d{2}-\d{2}$",
    "D. MMMM YYYY": r"^\d{1,2}\.\s*[A-Za-zäöüÄÖÜß]+\s+\d{4}$",
    "MMMM YYYY": r"^[A-Za-zäöüÄÖÜß]+\s+\d{4}$",
}

MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def parse_date(value: str, locale: str = "de") -> date | None:
    """Versucht Datum aus verschiedenen Formaten zu parsen."""
    from dateutil.parser import parse

    try:
        return parse(value, dayfirst=(locale == "de")).date()
    except:
        return None
```

### 9.8 Geldbeträge

```regex
# Mit Dezimalkomma (DE)
^\d{1,3}(?:\.\d{3})*,\d{2}\s*€?$

# Mit Dezimalpunkt (EN)
^\d{1,3}(?:,\d{3})*\.\d{2}\s*(?:€|EUR)?$

# Ohne Tausendertrennzeichen
^\d+[,\.]\d{2}\s*(?:€|EUR)?$
```

**Python-Implementierung:**
```python
AMOUNT_PATTERNS_DE = [
    r"^(\d{1,3}(?:\.\d{3})*),(\d{2})\s*€?$",  # 1.234,56 €
    r"^(\d+),(\d{2})\s*€?$",                   # 1234,56
]

AMOUNT_PATTERNS_EN = [
    r"^(\d{1,3}(?:,\d{3})*)\.(\d{2})\s*(?:€|EUR)?$",  # 1,234.56 EUR
    r"^(\d+)\.(\d{2})\s*(?:€|EUR)?$",                  # 1234.56
]

def parse_amount(value: str, locale: str = "de") -> Decimal | None:
    """Parst Geldbetrag aus String."""
    patterns = AMOUNT_PATTERNS_DE if locale == "de" else AMOUNT_PATTERNS_EN

    for pattern in patterns:
        match = re.match(pattern, value.strip())
        if match:
            integer_part = match.group(1).replace(".", "").replace(",", "")
            decimal_part = match.group(2)
            return Decimal(f"{integer_part}.{decimal_part}")

    return None
```

---

## 10. Vollständige Feature-Liste EU_VAT

### 10.1 Pflichtmerkmale (Art. 226 MwSt-Systemrichtlinie)

| Feature-ID | Name (EN) | Name (DE) | Rechtsgrundlage |
|------------|-----------|-----------|-----------------|
| `invoice_date` | Date of issue | Rechnungsdatum | Art. 226 Nr. 1 |
| `invoice_number` | Sequential number | Fortlaufende Nummer | Art. 226 Nr. 2 |
| `supplier_vat_id` | Supplier VAT ID | USt-ID Lieferant | Art. 226 Nr. 3 |
| `customer_vat_id` | Customer VAT ID (B2B) | USt-ID Kunde | Art. 226 Nr. 4 |
| `supplier_name_address` | Supplier name and address | Name/Anschrift Lieferant | Art. 226 Nr. 5 |
| `customer_name_address` | Customer name and address | Name/Anschrift Kunde | Art. 226 Nr. 6 |
| `supply_description` | Description of goods/services | Leistungsbeschreibung | Art. 226 Nr. 6 |
| `quantity` | Quantity | Menge | Art. 226 Nr. 6 |
| `supply_date` | Date of supply | Lieferdatum | Art. 226 Nr. 7 |
| `payment_date` | Payment date (if different) | Zahlungsdatum | Art. 226 Nr. 7 |
| `taxable_amount` | Taxable amount per rate | Bemessungsgrundlage | Art. 226 Nr. 8 |
| `unit_price` | Unit price (excl. VAT) | Einzelpreis (netto) | Art. 226 Nr. 9 |
| `vat_rate` | VAT rate applied | Steuersatz | Art. 226 Nr. 10 |
| `vat_amount` | VAT amount | Steuerbetrag | Art. 226 Nr. 10 |
| `exemption_reason` | Exemption/RC reference | Steuerbefreiungsgrund | Art. 226 Nr. 11 |
| `reverse_charge_notice` | Reverse charge notice | Reverse-Charge-Hinweis | Art. 226 Nr. 11a |
| `margin_scheme_notice` | Margin scheme notice | Differenzbesteuerung | Art. 226 Nr. 14 |

### 10.2 Feature-Schema EU_VAT

```json
{
  "ruleset_id": "EU_VAT",
  "version": "1.0.0",
  "jurisdiction": "EU",
  "legal_references": [
    {
      "law": "MwSt-Systemrichtlinie",
      "section": "Art. 226",
      "description_de": "Pflichtangaben in Rechnungen",
      "description_en": "Mandatory invoice particulars"
    }
  ],
  "features": [
    {
      "feature_id": "supplier_vat_id",
      "name_de": "USt-ID des Lieferanten",
      "name_en": "Supplier VAT ID",
      "legal_basis": "Art. 226 Nr. 3",
      "required_level": "REQUIRED",
      "extraction_type": "STRING",
      "validation": {
        "pattern": "EU_VAT_ID",
        "note": "Muss gültige EU-USt-ID sein"
      },
      "generator_rules": {
        "can_be_missing": true,
        "can_be_malformed": true,
        "typical_errors": ["missing", "invalid_country", "wrong_format"]
      }
    },
    {
      "feature_id": "customer_vat_id",
      "name_de": "USt-ID des Kunden (B2B)",
      "name_en": "Customer VAT ID (B2B)",
      "legal_basis": "Art. 226 Nr. 4",
      "required_level": "CONDITIONAL",
      "condition": "B2B transaction or intra-community supply",
      "extraction_type": "STRING",
      "validation": {
        "pattern": "EU_VAT_ID"
      }
    },
    {
      "feature_id": "reverse_charge_notice",
      "name_de": "Reverse-Charge-Hinweis",
      "name_en": "Reverse charge notice",
      "legal_basis": "Art. 226 Nr. 11a",
      "required_level": "CONDITIONAL",
      "condition": "Reverse charge applies",
      "extraction_type": "TEXTBLOCK",
      "validation": {
        "must_contain_one_of": [
          "Reverse charge",
          "Steuerschuldnerschaft des Leistungsempfängers",
          "VAT due by the customer"
        ]
      }
    }
  ],
  "special_rules": {
    "small_amount_threshold_eur": 400,
    "small_amount_reduced_fields": [
      "invoice_date",
      "supplier_name_address",
      "supply_description",
      "vat_rate",
      "gross_amount"
    ]
  }
}
```

---

## 11. Vollständige Feature-Liste UK_VAT

### 11.1 Pflichtmerkmale (HMRC VAT Notice 700)

| Feature-ID | Name (EN) | Rechtsgrundlage |
|------------|-----------|-----------------|
| `supplier_name_address` | Supplier name, address, VAT number | VAT Notice 700 |
| `invoice_number` | Unique identifying number | VAT Notice 700 |
| `invoice_date` | Date of issue | VAT Notice 700 |
| `tax_point` | Time of supply (tax point) | VAT Notice 700 |
| `customer_name_address` | Customer name and address | VAT Notice 700 |
| `supply_description` | Description of goods/services | VAT Notice 700 |
| `quantity` | Quantity of goods | VAT Notice 700 |
| `unit_price` | Unit price (excl. VAT) | VAT Notice 700 |
| `vat_rate` | Rate of VAT | VAT Notice 700 |
| `total_excl_vat` | Total excluding VAT | VAT Notice 700 |
| `total_vat` | Total VAT charged | VAT Notice 700 |
| `total_incl_vat` | Total amount payable | VAT Notice 700 |

### 11.2 Feature-Schema UK_VAT

```json
{
  "ruleset_id": "UK_VAT",
  "version": "1.0.0",
  "jurisdiction": "UK",
  "legal_references": [
    {
      "law": "VAT Act 1994",
      "section": "Schedule 11",
      "description_en": "VAT invoice requirements"
    },
    {
      "law": "HMRC VAT Notice 700",
      "section": "Section 16",
      "description_en": "VAT invoices"
    }
  ],
  "features": [
    {
      "feature_id": "supplier_vat_number",
      "name_en": "Supplier VAT registration number",
      "legal_basis": "VAT Notice 700",
      "required_level": "REQUIRED",
      "extraction_type": "STRING",
      "validation": {
        "pattern": "UK_VAT_ID"
      }
    },
    {
      "feature_id": "tax_point",
      "name_en": "Time of supply (tax point)",
      "legal_basis": "VAT Notice 700",
      "required_level": "REQUIRED",
      "extraction_type": "DATE",
      "semantic_meaning_en": "Date when VAT becomes due - may differ from invoice date",
      "generator_rules": {
        "can_be_missing": true,
        "typical_errors": ["missing", "different_from_invoice_date_unclear"]
      }
    },
    {
      "feature_id": "unit_price",
      "name_en": "Unit price excluding VAT",
      "legal_basis": "VAT Notice 700",
      "required_level": "REQUIRED",
      "extraction_type": "MONEY",
      "validation": {
        "currency": "GBP",
        "min_value": 0.01
      }
    }
  ],
  "vat_rates": {
    "standard": 20.0,
    "reduced": 5.0,
    "zero": 0.0
  },
  "special_rules": {
    "simplified_invoice_threshold_gbp": 250,
    "simplified_invoice_fields": [
      "supplier_name_address",
      "supplier_vat_number",
      "invoice_date",
      "supply_description",
      "vat_rate",
      "total_incl_vat"
    ]
  }
}
```

---

## 12. Kleinbetragsrechnungen (Übersicht)

| Jurisdiktion | Schwelle | Reduzierte Pflichtangaben |
|--------------|----------|---------------------------|
| **DE (§ 33 UStDV)** | ≤ 250 € brutto | supplier_name, invoice_date, supply_description, gross_amount, vat_rate |
| **EU (Art. 238)** | ≤ 400 € brutto | invoice_date, supplier_name_address, supply_description, vat_rate, gross_amount |
| **UK (Simplified)** | ≤ £250 brutto | supplier_name_address, supplier_vat_number, invoice_date, supply_description, vat_rate, total_incl_vat |

---

## 13. Didaktische Kernbotschaft

> FlowAudit prüft nicht „mit KI",
> sondern **gegen Recht**,
> mit **strukturierter Datenverarbeitung**,
> unterstützt durch **KI dort, wo Regeln enden**.

Dieses Ruleset-Dokument ist die explizite Umsetzung dieser Philosophie.
