# Qualitätssicherung (Quality Assurance)

Dieses Dokument beschreibt die Qualitätskriterien für das FlowAudit-System zur Rechnungsprüfung im öffentlichen Sektor.

---

## 1. Grundprinzipien

### 1.1 Nachvollziehbarkeit (Traceability)

Jede Prüfentscheidung muss nachvollziehbar sein:

| Kriterium | Beschreibung | Umsetzung |
|-----------|--------------|-----------|
| **Entscheidungsherkunft** | Quelle jeder Prüfaussage dokumentiert | `TruthSource`: RULE, LLM, USER |
| **Audit-Trail** | Vollständige Prüfhistorie | `FeedbackEntry`, `AnalysisResult` |
| **Versionierung** | Ruleset-Version bei Prüfung gespeichert | `ruleset_id` + `version` |
| **Zeitstempel** | Alle Aktionen mit Zeitstempel | `created_at`, `updated_at` |

### 1.2 Plausibilität (Plausibility)

Geprüfte Werte müssen plausibel sein:

- **Betragsplausibilität**: Netto + MwSt = Brutto (Toleranz: 0.01 EUR)
- **Datumsplausibilität**: Rechnungsdatum innerhalb Projektzeitraum
- **Identitätsplausibilität**: Empfänger = Begünstigter (mit Aliase-Toleranz)

### 1.3 Konsistenz (Consistency)

Daten müssen über alle Prüfebenen konsistent sein:

- **Organisatorische Konsistenz**: Rechnungsempfänger ≈ Begünstigter
- **Zeitliche Konsistenz**: Leistungsdatum ≤ Rechnungsdatum ≤ Projektenddatum
- **Betragskonsistenz**: Summen stimmen überein

---

## 2. Prüfebenen

### 2.1 Deterministische Prüfung (Rule Engine)

Regelbasierte Prüfungen ohne KI-Unterstützung:

```
┌─────────────────────────────────────────────────────────────────┐
│ STUFE 1: FORMALE PRÜFUNG                                        │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Pflichtfelder vorhanden (UStG §14 / EU VAT / HMRC)           │
│ ✓ Formatvalidierung (USt-IdNr, IBAN, Datumsformate)            │
│ ✓ Prüfziffern korrekt (USt-IdNr, IBAN)                         │
│ ✓ Betragsrechnung korrekt (Netto × MwSt-Satz = MwSt-Betrag)    │
└─────────────────────────────────────────────────────────────────┘
```

**Fehlerquellen-Kategorisierung:**

| Kategorie | Fehlertypen | Beispiel |
|-----------|-------------|----------|
| `TAX_LAW` | MISSING, WRONG_FORMAT, CALCULATION_ERROR | Fehlende Rechnungsnummer |
| `BENEFICIARY_DATA` | NAME_MISMATCH, ADDRESS_MISMATCH | Empfänger ≠ Begünstigter |
| `LOCATION_VALIDATION` | INVALID_ZIP, COUNTRY_MISMATCH | PLZ nicht zum Ort passend |

### 2.2 Semantische Prüfung (LLM)

KI-gestützte Prüfungen für komplexe Zusammenhänge:

```
┌─────────────────────────────────────────────────────────────────┐
│ STUFE 2: SEMANTISCHE PRÜFUNG                                    │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Leistungsbeschreibung plausibel zum Projekt                  │
│ ✓ Wirtschaftlichkeit der Beträge                                │
│ ✓ Begünstigtenabgleich (auch bei Schreibweisen-Varianten)      │
│ ✓ Kontextuelle Warnsignale erkennen                            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Manuelle Prüfung (User Override)

Prüfer-Entscheidung bei Konflikten:

- LLM und Rule Engine widersprechen sich
- Grenzfälle bei Namensabweichungen
- Fachliche Einschätzung erforderlich

---

## 3. Begünstigtendaten (Beneficiary Master Data)

### 3.1 Pflichtfelder

| Feld | Beschreibung | Validierung |
|------|--------------|-------------|
| `beneficiary_name` | Name des Zuwendungsempfängers | Nicht leer, keine Dummy-Marker |
| `legal_form` | Rechtsform (GmbH, e.V., etc.) | Optional, Enum-validiert |
| `street` | Straße und Hausnummer | Nicht leer |
| `zip` | Postleitzahl | Format-validiert (DE: 5 Ziffern) |
| `city` | Stadt | Nicht leer |
| `country` | Ländercode | ISO 3166-1 alpha-2 |

### 3.2 Optionale Felder

| Feld | Beschreibung | Verwendung |
|------|--------------|------------|
| `vat_id` | USt-Identifikationsnummer | Prüfziffernvalidierung |
| `tax_number` | Steuernummer | Format-Prüfung |
| `aliases` | Alternative Schreibweisen | Fuzzy-Matching |
| `input_tax_deductible` | Vorsteuerabzugsberechtigt | Wirtschaftlichkeitsprüfung |

### 3.3 Abgleichlogik

```
Rechnungsempfänger ("customer_name" auf Rechnung)
         │
         ▼
┌─────────────────────────────────────────────┐
│ MATCHING-ALGORITHMUS                         │
├─────────────────────────────────────────────┤
│ 1. Exakter Match: beneficiary_name          │
│ 2. Alias-Match: aliases[]                   │
│ 3. Fuzzy-Match: Levenshtein ≤ 3            │
│ 4. Enthaltener Match: Name in Empfänger     │
└─────────────────────────────────────────────┘
         │
         ▼
    MATCH_SCORE (0.0 - 1.0)

    ≥ 0.95: EXACT_MATCH (grün)
    ≥ 0.80: LIKELY_MATCH (gelb)
    < 0.80: MISMATCH (rot)
```

---

## 4. Testdaten-Generator

### 4.1 Anforderungen an generierte Rechnungen

**Verbotene Muster:**
- Keine Dummy-Marker: "TEST", "XXX", "DUMMY", "Lorem Ipsum"
- Keine offensichtlichen Platzhalter
- Keine unrealistischen Beträge (0.00 EUR, 999999.99 EUR)

**Pflichtanforderungen:**
- Alle Pflichtfelder gem. aktivem Ruleset befüllt
- Plausible USt-IdNr (Format-korrekt, ggf. absichtlich ungültig für Testfälle)
- Realistische Beträge innerhalb Template-Spannen

### 4.2 Begünstigten-Integration

Bei aktivierter Begünstigten-Verknüpfung:

```python
# Generator-Einstellungen
{
    "use_beneficiary_data": true,
    "beneficiary": {
        "beneficiary_name": "Förderverein Musterstadt e.V.",
        "legal_form": "e.V.",
        "street": "Hauptstraße 1",
        "zip": "12345",
        "city": "Musterstadt",
        "aliases": ["Förderverein Musterstadt", "FV Musterstadt"]
    },
    "project_context": {
        "project_id": "PRJ-2025-001",
        "project_name": "Jugendförderung 2025"
    }
}
```

**Generierte Rechnung:**
- `customer_name` = Begünstigter (oder Alias-Variante)
- `customer_address` = Adresse des Begünstigten
- Projekt-Referenz in Leistungsbeschreibung optional

### 4.3 Fehlerinjektion für Testfälle

| Fehlerart | Beschreibung | Severity |
|-----------|--------------|----------|
| `beneficiary_name_typo` | Tippfehler im Empfängernamen | 1 |
| `beneficiary_wrong_address` | Falsche Adresse | 2 |
| `beneficiary_alias_used` | Alias statt Hauptname | 1 |
| `beneficiary_completely_wrong` | Falscher Empfänger | 5 |
| `vat_id_invalid_checksum` | USt-IdNr mit falscher Prüfziffer | 3 |
| `vat_id_missing` | USt-IdNr fehlt | 2 |

---

## 5. Qualitätsmetriken

### 5.1 System-Metriken

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Parsing-Genauigkeit** | ≥ 95% | Extrahierte Felder / Erwartete Felder |
| **Precheck-Abdeckung** | 100% | Geprüfte Pflichtfelder / Alle Pflichtfelder |
| **LLM-Konsistenz** | ≥ 90% | Gleiche Eingabe → Gleiche Bewertung |
| **Antwortzeit** | < 30s | Parse + Precheck + LLM (Median) |

### 5.2 Didaktische Metriken

Für den Seminarbetrieb:

| Metrik | Beschreibung |
|--------|--------------|
| **Fehler-Erkennungsrate** | Anteil erkannter injizierter Fehler |
| **False-Positive-Rate** | Fälschlich als fehlerhaft markierte korrekte Rechnungen |
| **Lernfortschritt** | Verbesserung über mehrere Durchläufe |

---

## 6. Übersetzungskonzept (Conceptual Translation)

### 6.1 Begünstigten-Terminologie

| Konzept | Deutsch | English |
|---------|---------|---------|
| Begünstigter | Zuwendungsempfänger, Begünstigter | Beneficiary, Grant Recipient |
| Vorsteuerabzug | Vorsteuerabzugsberechtigt | Input Tax Deductible |
| Fördermittel | Zuwendung, Fördermittel | Grant, Funding |
| Aktenzeichen | Aktenzeichen, Geschäftszeichen | File Reference, Case Number |

### 6.2 Prüfkategorien

| Kategorie | Deutsch | English |
|-----------|---------|---------|
| Formale Prüfung | Formale Anforderungen | Formal Requirements |
| Betragsrechnung | Betragsrechnung | Amount Calculation |
| Empfängerabgleich | Begünstigtenabgleich | Beneficiary Matching |
| Zeitliche Prüfung | Zeitraum-Validierung | Period Validation |

### 6.3 Fehlermeldungen

| Code | Deutsch | English |
|------|---------|---------|
| `BENEFICIARY_MISMATCH` | Empfänger stimmt nicht mit Begünstigtem überein | Invoice recipient does not match beneficiary |
| `BENEFICIARY_ALIAS_MATCH` | Empfänger entspricht Alias des Begünstigten | Recipient matches beneficiary alias |
| `VAT_ID_INVALID` | USt-IdNr ungültig | VAT ID invalid |
| `PERIOD_EXCEEDED` | Leistung außerhalb Projektzeitraum | Service outside project period |

---

## 7. Checkliste für Qualitätssicherung

### 7.1 Vor dem Einsatz

- [ ] Rulesets korrekt konfiguriert
- [ ] Begünstigtendaten vollständig erfasst
- [ ] Projektzeitraum definiert
- [ ] LLM-Provider erreichbar und konfiguriert

### 7.2 Im Seminarbetrieb

- [ ] Testdaten mit bekannten Fehlern generiert
- [ ] Lösungsdatei für Dozenten verfügbar
- [ ] Keine Dummy-Marker in Testdaten

### 7.3 Produktiveinsatz

- [ ] Audit-Trail aktiviert
- [ ] Backup-Strategie definiert
- [ ] Datenschutz-Anforderungen erfüllt
- [ ] Vier-Augen-Prinzip bei kritischen Entscheidungen

---

## Anhang: Fehlerquellen-Matrix

| Fehlerquelle | Regelbasiert | LLM | Manuell |
|--------------|:------------:|:---:|:-------:|
| Fehlende Pflichtfelder | ✓ | | |
| Formatfehler | ✓ | | |
| Rechenfehler | ✓ | ✓ | |
| Ungültige Prüfziffern | ✓ | | |
| Begünstigten-Abweichung | ✓ | ✓ | ✓ |
| Zeitraum-Überschreitung | ✓ | | |
| Semantische Unstimmigkeiten | | ✓ | ✓ |
| Wirtschaftlichkeit | | ✓ | ✓ |
