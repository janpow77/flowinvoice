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

## 9. Didaktische Kernbotschaft

> FlowAudit prüft nicht „mit KI“,
> sondern **gegen Recht**,
> mit **strukturierter Datenverarbeitung**,
> unterstützt durch **KI dort, wo Regeln enden**.

Dieses Ruleset-Dokument ist die explizite Umsetzung dieser Philosophie.
