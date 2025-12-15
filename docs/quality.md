# Verbesserungskatalog für das KI-gestützte Rechnungsauswertungssystem  
## Schwerpunkt: fachliche Robustheit, Nachvollziehbarkeit und didaktische Qualität

Dieser Verbesserungskatalog beschreibt gezielte Weiterentwicklungsmaßnahmen für das KI-gestützte System zur Analyse von Rechnungen im Kontext von Förder-, Prüf- und Schulungsszenarien.  
Er basiert auf einer systematischen Analyse der bestehenden Konzeption, Architektur und Dokumentation und adressiert ausschließlich identifizierte Schwächen.

Der Katalog versteht sich nicht als Kritik, sondern als **Qualitätssicherungs- und Reifegradinstrument**, das die fachliche Belastbarkeit, Transparenz und didaktische Eignung des Systems weiter erhöht.

---

## 1. Zuwendungszweckprüfung: fehlende fachliche Operationalisierung

### Ausgangslage

Die Prüfung des Vorhabenzusammenhangs (Zuwendungszweck) ist konzeptionell korrekt angelegt, bleibt jedoch auf einer beschreibenden Ebene.  
Es fehlt eine feste Struktur, anhand derer die KI ihre Bewertung nachvollziehbar, konsistent und prüfungslogisch ableitet.

Insbesondere ist derzeit nicht eindeutig erkennbar:
- nach welchen Kriterien der Zusammenhang geprüft wird,
- wann ein Zusammenhang als gegeben, nicht gegeben oder unklar gilt,
- wie einzelne Teilbewertungen zur Gesamtaussage führen.

### Verbesserungsziel

Die Zuwendungszweckprüfung soll von einer abstrakten Beschreibung zu einem **klar strukturierten, regelhaften Prüfvorgang** weiterentwickelt werden, der auch didaktisch vermittelbar ist.

### Maßnahmen

**1.1 Einführung eines verbindlichen Prüfrasters**

Die Prüfung des Zuwendungszwecks erfolgt stets anhand eines festen Rasters mit vier Dimensionen:
- sachlicher Zusammenhang,
- zeitlicher Zusammenhang,
- organisatorischer Zusammenhang,
- wirtschaftliche Plausibilität.

Jede Dimension wird separat geprüft und dokumentiert.

**1.2 Standardisierte Einzelbewertung**

Für jede Prüfdimension gibt das System zwingend aus:
- ein Prüfergebnis (`PASS`, `FAIL`, `UNCLEAR`),
- eine kurze, fachlich formulierte Begründung,
- die herangezogene Text- oder Dokumentenevidenz.

Freiformulierungen ohne Bezug auf dieses Raster sind zu vermeiden.

**1.3 Algorithmische Gesamtaussage**

Die Gesamtbewertung des Zuwendungszwecks wird nicht frei formuliert, sondern logisch aus den Einzelbewertungen abgeleitet.  
Dabei gilt:
- mindestens ein `FAIL` → Gesamtbewertung `FAIL`,
- kein `FAIL`, aber mindestens ein `UNCLEAR` → Gesamtbewertung `UNCLEAR`,
- ausschließlich `PASS` → Gesamtbewertung `PASS`.

Die Herleitung der Gesamtaussage muss für Schulungszwecke explizit erkennbar sein.

**1.4 Explizite Negativindikatoren**

Das System benennt typische Negativindikatoren ausdrücklich, z. B.:
- Leistungsbeschreibung ohne erkennbaren Projektbezug,
- Leistungszeitraum außerhalb der Förderperiode,
- Rechnungsempfänger nicht identisch mit dem Begünstigten,
- pauschale Allgemeinleistungen ohne Projektzuordnung.

Diese Indikatoren sind nicht automatisch als Verstoß zu werten, müssen aber als solche kenntlich gemacht werden.

---

## 2. Konfliktauflösung zwischen Regelprüfung und KI-Analyse

### Ausgangslage

Die Systemarchitektur sieht eine Kombination aus regelbasierter Prüfung und KI-Analyse vor.  
Die konkrete Priorität und der Umgang mit widersprüchlichen Ergebnissen sind jedoch nicht normiert.

### Verbesserungsziel

Konflikte zwischen Regelprüfung und KI-Bewertung sollen **transparent, reproduzierbar und didaktisch erklärbar** behandelt werden.

### Maßnahmen

**2.1 Feste Prioritätslogik**

Für Schulungszwecke gilt folgende einfache und verbindliche Reihenfolge:
1. Regelbasierte Prüfungen (harte Regeln, z. B. Pflichtangaben)
2. KI-basierte semantische Analysen
3. Keine automatische Überstimmung von Regeln durch KI

Die KI darf Regelverstöße erläutern, aber nicht relativieren.

**2.2 Einheitlicher Konfliktstatus**

Bei widersprüchlichen Ergebnissen wird zwingend ein Konfliktstatus ausgegeben, z. B.:
`CONFLICT_RULE_KI`.

Zusätzlich sind beide Sichtweisen kurz darzustellen:
- Ergebnis der Regelprüfung,
- Ergebnis der KI-Analyse.

Eine automatische Entscheidung ist in diesem Fall zu unterlassen.

---

## 3. Unklare Ergebnisse („UNCLEAR“) klar definieren

### Ausgangslage

Der Status „unclear“ ist vorgesehen, jedoch nicht fachlich abgegrenzt.  
Dies birgt die Gefahr einer inflationären oder uneinheitlichen Nutzung.

### Verbesserungsziel

„UNCLEAR“ soll ein **präzise definierter Ausnahmezustand** sein, kein Ausweichlabel.

### Maßnahmen

**3.1 Klare Kriterien für UNCLEAR**

Der Status `UNCLEAR` darf nur vergeben werden, wenn mindestens eines der folgenden Kriterien erfüllt ist:
- relevante Informationen fehlen vollständig,
- vorhandene Informationen sind mehrdeutig,
- mehrere fachlich plausible Interpretationen sind möglich.

**3.2 Begründungspflicht**

Jeder UNCLEAR-Status muss enthalten:
- eine Beschreibung der Unklarheit,
- einen Hinweis, welche Information zur Klärung erforderlich wäre.

---

## 4. Risikomodul (Modul 3) inhaltlich schärfen

### Ausgangslage

Das Risikomodul ist optional angelegt und inhaltlich offen.  
Für Schulungszwecke fehlt ein greifbarer Mindeststandard.

### Verbesserungsziel

Das Risikomodul soll als **sensibilisierendes Prüfmodul** dienen, nicht als rechtliche Bewertung.

### Maßnahmen

**4.1 Einführung eines festen Minimal-Risikokerns**

Unabhängig von Vergaberechtstiefe prüft das System stets einfache Risikohinweise, z. B.:
- ungewöhnlich hohe Einzelbeträge,
- auffällige Lieferantenhäufung,
- fehlende Leistungszeiträume,
- runde Pauschalbeträge ohne Erläuterung.

**4.2 Klare didaktische Abgrenzung**

Das System muss ausdrücklich kennzeichnen:
„Hinweis auf mögliches Risiko – keine rechtliche Bewertung“.

---

## 5. Versionierung und Nachvollziehbarkeit verpflichtend machen

### Ausgangslage

Versionierungsmechanismen sind vorgesehen, aber nicht zwingend Bestandteil jedes Ergebnisses.

### Verbesserungsziel

Jedes Analyseergebnis soll **vollständig reproduzierbar** sein.

### Maßnahmen

**5.1 Pflicht-Metadaten**

Jeder Auswertungsbericht enthält zwingend:
- Dokument-Fingerprint,
- Ruleset-ID und -Version,
- Prompt-Version,
- Modellkennung,
- Datum und Uhrzeit.

Ergebnisse ohne diese Metadaten gelten als nicht valide.

**5.2 Sichtbarkeit der Metadaten**

Die Metadaten sollen sichtbar ausgegeben werden (z. B. Fußzeile), um Abhängigkeiten und Modellwirkung transparent zu machen.

---

## 6. RAG-Nutzung begrenzen und absichern

### Ausgangslage

RAG-Mechanismen sind vorgesehen, bergen aber ohne Leitplanken das Risiko fachlicher Drift.

### Verbesserungsziel

RAG soll **unterstützen und erklären**, nicht entscheiden.

### Maßnahmen

**6.1 Begrenzter Einfluss**

RAG-Beispiele dürfen:
- Entscheidungen nicht ersetzen,
- nur ergänzend verwendet werden,
- klar als frühere Vergleichsfälle gekennzeichnet sein.

**6.2 Fachliche Konsistenz**

Ein RAG-Beispiel darf nur genutzt werden, wenn:
- gleicher Dokumenttyp,
- gleiches Ruleset,
- gleiche Prüfdimension vorliegt.

---

## 7. Fehler- und Abbruchzustände explizit vorsehen

### Ausgangslage

Die Systemlogik fokussiert auf erfolgreiche Analysen.  
Didaktisch relevante Fehlerzustände sind nicht explizit modelliert.

### Verbesserungsziel

Nicht-Bewertbarkeit soll als **valider Systemzustand** anerkannt werden.

### Maßnahmen

**7.1 Definierte Fehlerzustände**

Das System soll u. a. ausgeben können:
- `DOCUMENT_UNREADABLE`
- `INSUFFICIENT_TEXT`
- `RULESET_NOT_APPLICABLE`
- `ANALYSIS_ABORTED`

**7.2 Klare Abgrenzung**

Ein Fehlerzustand ist kein Systemversagen, sondern ein fachlich relevantes Ergebnis.

---

## 8. Datenschutz: Datenklassifikation konkretisieren

### Ausgangslage

Technische Schutzmaßnahmen sind beschrieben, die inhaltliche Datenklassifikation bleibt abstrakt.

### Verbesserungsziel

Transparenz darüber, **welche Daten zu welchem Zweck verarbeitet werden**.

### Maßnahmen

**8.1 Einfache Datenklassen**

Mindestens folgende Klassen sind zu unterscheiden:
- Rechnungsdokumente,
- extrahierter Text,
- Analyseergebnisse,
- Trainings-/Beispieldaten.

**8.2 Dokumentation der Zweckbindung**

Für jede Klasse sind Zweck, Speicherort und konzeptionelle Löschlogik zu dokumentieren.

---

## 9. Generator als systematisches QS-Instrument nutzen

### Ausgangslage

Der Generator ist technisch stark, wird aber noch nicht konsequent als QS-Werkzeug eingesetzt.

### Verbesserungsziel

Der Generator soll als **Referenz- und Regressionstest-Motor** dienen.

### Maßnahmen

**9.1 Referenzszenarien**

Es sind feste Szenarien zu definieren, z. B.:
- formal korrekte Rechnung,
- fehlende Pflichtangabe,
- unklarer Zuwendungszweck,
- sachlich unpassende Leistung.

**9.2 Vergleichbarkeit erzwingen**

Bei identischem Szenario sind vergleichbare Ergebnisse zu erwarten.  
Abweichungen sind explizit als Modell- oder Prompt-Effekt zu kennzeichnen.

---

## Abschlussbemerkung

Die vorgeschlagenen Maßnahmen stärken nicht nur die technische und fachliche Qualität des Systems, sondern erhöhen insbesondere dessen **didaktischen Wert**.  
Das System wird dadurch nicht nur zu einem Analysewerkzeug, sondern zu einem **Lerninstrument für prüferisches Denken im Kontext von KI-gestützter Verwaltungskontrolle**.
