# Implementierungsplan: Verbesserungskatalog

Dieser Plan beschreibt die Umsetzung des Verbesserungskatalogs für das KI-gestützte Rechnungsauswertungssystem.

---

## Übersicht der Maßnahmen

| Nr. | Bereich | Priorität | Status |
|-----|---------|-----------|--------|
| 1 | Zuwendungszweckprüfung | Hoch | Geplant |
| 2 | Konfliktauflösung Rule/KI | Hoch | Geplant |
| 3 | UNCLEAR-Status Definition | Mittel | Geplant |
| 4 | Risikomodul | Mittel | Geplant |
| 5 | Versionierung & Metadaten | Hoch | Geplant |
| 6 | RAG-Nutzung begrenzen | Niedrig | Geplant |
| 7 | Fehler- und Abbruchzustände | Hoch | Geplant |
| 8 | Datenklassifikation | Niedrig | Geplant |
| 9 | Generator als QS-Instrument | Mittel | Geplant |

---

## 1. Zuwendungszweckprüfung (Grant Purpose Audit)

### Dateien
- `backend/app/schemas/grant_purpose.py` (NEU)
- `backend/app/services/grant_purpose_checker.py` (NEU)
- `backend/app/models/enums.py` (Erweitern)

### Struktur

```
Prüfraster (4 Dimensionen):
├── Sachlicher Zusammenhang (SUBJECT_RELATION)
├── Zeitlicher Zusammenhang (TEMPORAL_RELATION)
├── Organisatorischer Zusammenhang (ORGANIZATIONAL_RELATION)
└── Wirtschaftliche Plausibilität (ECONOMIC_PLAUSIBILITY)

Bewertung pro Dimension:
├── PASS - Kriterium erfüllt
├── FAIL - Kriterium nicht erfüllt
└── UNCLEAR - Nicht eindeutig bewertbar

Gesamtbewertung (algorithmisch):
├── min. 1x FAIL → FAIL
├── 0x FAIL, min. 1x UNCLEAR → UNCLEAR
└── nur PASS → PASS
```

### Negativindikatoren (explizit zu prüfen)
- Leistungsbeschreibung ohne Projektbezug
- Leistungszeitraum außerhalb Förderperiode
- Rechnungsempfänger ≠ Begünstigter
- Pauschale Allgemeinleistungen

---

## 2. Konfliktauflösung Rule vs. KI

### Dateien
- `backend/app/models/enums.py` (ConflictStatus hinzufügen)
- `backend/app/schemas/result.py` (Erweitern)
- `backend/app/services/conflict_resolver.py` (NEU)

### Prioritätslogik
```
1. Regelbasierte Prüfung (RULE) - höchste Priorität
2. KI-Analyse (LLM) - nachgelagert
3. Manuelle Korrektur (USER) - übersteuert beides
```

### Konfliktstatus
- `NO_CONFLICT` - Übereinstimmung
- `CONFLICT_RULE_LLM` - Widerspruch zwischen Regel und KI
- `CONFLICT_RULE_USER` - Manuelle Überschreibung von Regel
- `CONFLICT_LLM_USER` - Manuelle Überschreibung von KI

---

## 3. UNCLEAR-Status Definition

### Kriterien für UNCLEAR
1. Relevante Informationen fehlen vollständig
2. Vorhandene Informationen sind mehrdeutig
3. Mehrere fachlich plausible Interpretationen möglich

### Begründungspflicht
```json
{
  "status": "UNCLEAR",
  "unclear_reason": "Beschreibung der Unklarheit",
  "required_clarification": "Benötigte Information zur Klärung"
}
```

---

## 4. Risikomodul

### Dateien
- `backend/app/schemas/risk.py` (NEU)
- `backend/app/services/risk_checker.py` (NEU)

### Minimal-Risikokern (immer prüfen)
- Ungewöhnlich hohe Einzelbeträge (> Median + 2σ)
- Auffällige Lieferantenhäufung
- Fehlende Leistungszeiträume
- Runde Pauschalbeträge ohne Erläuterung
- Leistungen außerhalb Projektzeitraum

### Didaktische Kennzeichnung
```
"HINWEIS: Mögliches Risiko erkannt – keine rechtliche Bewertung"
```

---

## 5. Versionierung & Metadaten

### Pflicht-Metadaten pro Analyseergebnis
```json
{
  "metadata": {
    "document_fingerprint": "sha256:...",
    "ruleset_id": "DE_USTG",
    "ruleset_version": "2024.1",
    "prompt_version": "1.0.0",
    "model_id": "gpt-4-turbo",
    "analysis_timestamp": "2025-01-15T14:30:00Z",
    "system_version": "1.2.0"
  }
}
```

### Validierung
Ergebnisse ohne vollständige Metadaten sind als `INVALID` zu markieren.

---

## 6. RAG-Nutzung begrenzen

### Einschränkungen
- Max. 3 Beispiele pro Analyse
- Nur bei gleichem Dokumenttyp
- Nur bei gleichem Ruleset
- Nur bei gleicher Prüfdimension

### Kennzeichnung
```
"Hinweis: Dieses Beispiel stammt aus einem früheren Vergleichsfall"
```

---

## 7. Fehler- und Abbruchzustände

### Neue Zustände (AnalysisStatus Enum)
```python
class AnalysisStatus(str, Enum):
    # Erfolgreiche Zustände
    COMPLETED = "COMPLETED"
    REVIEW_NEEDED = "REVIEW_NEEDED"

    # Fehlerzustände (fachlich relevant)
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"
    INSUFFICIENT_TEXT = "INSUFFICIENT_TEXT"
    RULESET_NOT_APPLICABLE = "RULESET_NOT_APPLICABLE"
    ANALYSIS_ABORTED = "ANALYSIS_ABORTED"
    TIMEOUT = "TIMEOUT"

    # Systemfehler
    SYSTEM_ERROR = "SYSTEM_ERROR"
```

---

## 8. Datenklassifikation

### Datenklassen
| Klasse | Zweck | Speicherort | Löschlogik |
|--------|-------|-------------|------------|
| Rechnungsdokumente | Analyse | /data/uploads | Nach Projektende |
| Extrahierter Text | Verarbeitung | PostgreSQL | Mit Dokument |
| Analyseergebnisse | Audit-Trail | PostgreSQL | 10 Jahre |
| Trainings-/Beispieldaten | RAG/Learning | ChromaDB | Manuell |

---

## 9. Generator als QS-Instrument

### Referenzszenarien
1. `REF_CORRECT` - Formal korrekte Rechnung
2. `REF_MISSING_FIELD` - Fehlende Pflichtangabe
3. `REF_UNCLEAR_PURPOSE` - Unklarer Zuwendungszweck
4. `REF_WRONG_RECIPIENT` - Falscher Empfänger
5. `REF_OUTSIDE_PERIOD` - Außerhalb Projektzeitraum
6. `REF_HIGH_AMOUNT` - Ungewöhnlich hoher Betrag

### Vergleichbarkeit
Bei identischem Szenario müssen Ergebnisse vergleichbar sein.
Abweichungen sind als Modell- oder Prompt-Effekt zu kennzeichnen.

---

## Implementierungsreihenfolge

### Phase 1: Grundlagen (Backend)
1. ✅ Fehlende Enums ergänzen (ErrorSource, Severity, AnalysisStatus)
2. ✅ Grant Purpose Schema und Checker implementieren
3. ✅ Conflict Resolution implementieren
4. ✅ Versionierungs-Metadaten hinzufügen

### Phase 2: Erweiterungen
5. ✅ Risikomodul implementieren
6. ✅ UNCLEAR-Begründungspflicht (in Grant Purpose und Result Schemas)
7. ✅ Fehlerzustände definieren (AnalysisStatus Enum)

### Phase 3: QS-Werkzeuge
8. ✅ Generator-Referenzszenarien (qa_scenarios.py)
9. 🔄 RAG-Einschränkungen (Backend-Logik vorhanden, UI ausstehend)
10. ✅ Datenklassifikation dokumentieren (data_classification.md)

### Phase 4: Frontend-Integration
11. ✅ Übersetzungen für neue Konzepte (checkerSettings, checkResults, risk, grantPurpose, conflict)
12. ✅ UI-Komponenten für neue Prüfungen (Grant Purpose Audit, Conflict Resolution)
