# Implementierungsplan: Steuersystem-Auswahl & Netzwerkzugang

## Übersicht

Dieses Dokument beschreibt die Implementierung von:
1. **Steuersystem-Auswahl (Flaggenwahl)** - Beim Laden eines Vorhabens
2. **Kriterienkatalog-Anzeige** - Je nach gewähltem Steuersystem
3. **Netzwerkzugang** - Lokal im LAN + via Cloudflare im Internet

---

## 1. Steuersystem-Auswahl (Tax System Selector)

### 1.1 Anforderungen (aus requirements.md)

```
Startscreen: Flaggenwahl
- 🇩🇪 → Ruleset DE_USTG (UStG §14)
- 🇪🇺 → Ruleset EU_VAT (MwSt-Systemrichtlinie)
- 🇬🇧 → Ruleset UK_VAT (HMRC VAT Notice 700)

Wichtig: Sprachwahl (DE/EN UI) ist unabhängig vom Ruleset
```

### 1.2 UI-Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Vorhaben: "Baumaßnahme Aschaffenburg"                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Steuersystem für Prüfung wählen:                               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │     🇩🇪      │  │     🇪🇺      │  │     🇬🇧      │             │
│  │   UStG §14  │  │  MwStSystRL │  │  HMRC VAT   │             │
│  │  Deutschland│  │  EU-Recht   │  │     UK      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         ▲                                                       │
│         │ Klick                                                 │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  📜 Kriterienkatalog: UStG §14 Abs. 4                       ││
│  │                                                              ││
│  │  Pflichtangaben nach deutschem Umsatzsteuergesetz:          ││
│  │                                                              ││
│  │  ☑ supplier_name_address    - Name und Anschrift Lieferant ││
│  │  ☑ customer_name_address    - Name und Anschrift Empfänger ││
│  │  ☑ supplier_tax_or_vat_id   - Steuernummer oder USt-ID     ││
│  │  ☑ invoice_date             - Rechnungsdatum               ││
│  │  ☑ invoice_number           - Rechnungsnummer              ││
│  │  ☑ supply_description       - Art und Umfang der Leistung  ││
│  │  ☑ supply_date_or_period    - Liefer-/Leistungszeitraum    ││
│  │  ☑ net_amount               - Nettobetrag                  ││
│  │  ☑ vat_rate                 - Steuersatz (19% / 7%)        ││
│  │  ☑ vat_amount               - Steuerbetrag                 ││
│  │  ☑ gross_amount             - Bruttobetrag                 ││
│  │                                                              ││
│  │  Sonderfall: Kleinbetragsrechnung ≤250€ (§33 UStDV)         ││
│  │  Reduzierte Pflichtangaben bei Kleinbeträgen                ││
│  │                                                              ││
│  │  [ Abbrechen ]                    [ Auswahl bestätigen ]    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Komponenten-Struktur

```
frontend/src/
├── components/
│   ├── tax-selector/
│   │   ├── TaxSystemSelector.tsx      # Flaggen-Auswahl
│   │   ├── TaxSystemCard.tsx          # Einzelne Flaggen-Karte
│   │   ├── CriteriaCatalog.tsx        # Kriterienkatalog-Modal
│   │   ├── FeatureList.tsx            # Liste der Pflichtmerkmale
│   │   └── index.ts
│   └── ...
├── lib/
│   └── rulesets/
│       ├── types.ts                   # TypeScript-Typen
│       ├── DE_USTG.ts                 # Deutsche Regeln
│       ├── EU_VAT.ts                  # EU-Regeln
│       ├── UK_VAT.ts                  # UK-Regeln
│       └── index.ts
└── pages/
    └── ProjectDetail.tsx              # Integriert TaxSystemSelector
```

### 1.4 Implementierungs-Schritte

#### Schritt 1: Ruleset-Datenstrukturen (Frontend)

```typescript
// frontend/src/lib/rulesets/types.ts
export interface RulesetFeature {
  feature_id: string;
  name_de: string;
  name_en: string;
  legal_basis: string;
  required_level: 'REQUIRED' | 'CONDITIONAL' | 'OPTIONAL';
  category: 'IDENTITY' | 'DATE' | 'AMOUNT' | 'TAX' | 'TEXT' | 'SEMANTIC';
  explanation_de: string;
  explanation_en: string;
}

export interface Ruleset {
  ruleset_id: string;
  version: string;
  jurisdiction: string;
  flag: string;  // Emoji
  title_de: string;
  title_en: string;
  legal_references: LegalReference[];
  features: RulesetFeature[];
  small_amount_threshold?: number;
  small_amount_features?: string[];
}

export type RulesetId = 'DE_USTG' | 'EU_VAT' | 'UK_VAT';
```

#### Schritt 2: TaxSystemSelector-Komponente

```typescript
// frontend/src/components/tax-selector/TaxSystemSelector.tsx
interface TaxSystemSelectorProps {
  projectId: string;
  currentRuleset?: RulesetId;
  onSelect: (rulesetId: RulesetId) => void;
}

export function TaxSystemSelector({ projectId, currentRuleset, onSelect }: TaxSystemSelectorProps) {
  const { t } = useTranslation();
  const [showCatalog, setShowCatalog] = useState<RulesetId | null>(null);

  const rulesets: { id: RulesetId; flag: string; name: string }[] = [
    { id: 'DE_USTG', flag: '🇩🇪', name: t('rulesets.DE_USTG') },
    { id: 'EU_VAT', flag: '🇪🇺', name: t('rulesets.EU_VAT') },
    { id: 'UK_VAT', flag: '🇬🇧', name: t('rulesets.UK_VAT') },
  ];

  return (
    <div>
      <h3>{t('settings.selectTaxSystem')}</h3>
      <div className="grid grid-cols-3 gap-4">
        {rulesets.map((rs) => (
          <TaxSystemCard
            key={rs.id}
            flag={rs.flag}
            name={rs.name}
            isSelected={currentRuleset === rs.id}
            onClick={() => setShowCatalog(rs.id)}
          />
        ))}
      </div>

      {showCatalog && (
        <CriteriaCatalog
          rulesetId={showCatalog}
          onClose={() => setShowCatalog(null)}
          onConfirm={() => {
            onSelect(showCatalog);
            setShowCatalog(null);
          }}
        />
      )}
    </div>
  );
}
```

#### Schritt 3: CriteriaCatalog-Modal

```typescript
// frontend/src/components/tax-selector/CriteriaCatalog.tsx
interface CriteriaCatalogProps {
  rulesetId: RulesetId;
  onClose: () => void;
  onConfirm: () => void;
}

export function CriteriaCatalog({ rulesetId, onClose, onConfirm }: CriteriaCatalogProps) {
  const { t, i18n } = useTranslation();
  const ruleset = getRuleset(rulesetId);
  const lang = i18n.language as 'de' | 'en';

  return (
    <div className="modal-backdrop">
      <div className="modal modal-lg">
        <div className="modal-header">
          <h2>
            {ruleset.flag} {lang === 'de' ? ruleset.title_de : ruleset.title_en}
          </h2>
        </div>
        <div className="modal-body">
          <p className="text-sm text-gray-500 mb-4">
            {t('rulesets.legalBasis')}: {ruleset.legal_references[0].section}
          </p>

          <h3 className="font-semibold mb-2">{t('rulesets.requiredFeatures')}</h3>
          <div className="space-y-2">
            {ruleset.features
              .filter(f => f.required_level === 'REQUIRED')
              .map((feature) => (
                <FeatureItem key={feature.feature_id} feature={feature} lang={lang} />
              ))}
          </div>

          {ruleset.small_amount_threshold && (
            <div className="mt-4 p-3 bg-info-50 rounded-lg">
              <h4 className="font-medium text-info-700">
                {t('rulesets.smallAmountInvoice')} (≤ {ruleset.small_amount_threshold}€)
              </h4>
              <p className="text-sm text-info-600">
                {t('rulesets.reducedRequirements')}
              </p>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <Button variant="ghost" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button variant="primary" onClick={onConfirm}>
            {t('common.confirm')}
          </Button>
        </div>
      </div>
    </div>
  );
}
```

#### Schritt 4: Backend API-Endpunkte

```python
# backend/app/api/routes_rulesets.py
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/rulesets", tags=["rulesets"])

@router.get("/")
async def list_rulesets():
    """Alle verfügbaren Rulesets auflisten."""
    return [
        {"id": "DE_USTG", "name_de": "Deutschland (UStG)", "name_en": "Germany (VAT Act)", "flag": "🇩🇪"},
        {"id": "EU_VAT", "name_de": "EU (MwSt-Richtlinie)", "name_en": "EU (VAT Directive)", "flag": "🇪🇺"},
        {"id": "UK_VAT", "name_de": "UK (HMRC VAT)", "name_en": "UK (HMRC VAT)", "flag": "🇬🇧"},
    ]

@router.get("/{ruleset_id}")
async def get_ruleset(ruleset_id: str):
    """Vollständiges Ruleset mit allen Features laden."""
    # Lädt aus JSON-Dateien oder DB
    pass

@router.get("/{ruleset_id}/features")
async def get_ruleset_features(ruleset_id: str):
    """Nur Features eines Rulesets laden."""
    pass
```

---

## 2. Netzwerkzugang

### 2.1 Lokaler Netzwerkzugang (LAN)

#### Vite-Konfiguration anpassen

```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Wichtig: Auf allen Interfaces lauschen
    port: 3000,
    strictPort: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
})
```

#### Docker Compose für LAN-Zugang

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "0.0.0.0:3000:80"  # Auf allen Interfaces
    environment:
      - VITE_API_URL=http://${HOST_IP:-localhost}:8000/api
```

#### Firewall-Regeln (Ubuntu)

```bash
# Frontend-Port öffnen
sudo ufw allow 3000/tcp comment 'FlowAudit Frontend'

# Backend-Port öffnen (falls direkt erreichbar sein soll)
sudo ufw allow 8000/tcp comment 'FlowAudit API'

# Status prüfen
sudo ufw status
```

### 2.2 Cloudflare Tunnel (Internet-Zugang)

#### Schritt 1: Cloudflare Account & Zero Trust

1. Cloudflare-Account erstellen (cloudflare.com)
2. Domain zu Cloudflare hinzufügen (oder Subdomain nutzen)
3. Zero Trust Dashboard öffnen: dash.teams.cloudflare.com

#### Schritt 2: Tunnel erstellen

```bash
# cloudflared installieren
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Mit Cloudflare authentifizieren
cloudflared tunnel login

# Tunnel erstellen
cloudflared tunnel create flowaudit

# Tunnel-ID notieren (z.B. abc123-def456-...)
```

#### Schritt 3: Tunnel-Konfiguration

```yaml
# deploy/cloudflared/config.yml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  # Frontend
  - hostname: flowaudit.yourdomain.com
    service: http://frontend:80

  # API (optional - für direkten API-Zugang)
  - hostname: api.flowaudit.yourdomain.com
    service: http://backend:8000

  # Catch-all
  - service: http_status:404
```

#### Schritt 4: Docker Compose mit Cloudflare

```yaml
# docker-compose.prod.yml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --config /etc/cloudflared/config.yml run
    volumes:
      - ./deploy/cloudflared:/etc/cloudflared:ro
      - cloudflared-creds:/root/.cloudflared:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  cloudflared-creds:
    external: true  # Manuell erstellen mit Credentials
```

#### Schritt 5: DNS-Eintrag erstellen

```bash
# DNS-Route für Tunnel erstellen
cloudflared tunnel route dns flowaudit flowaudit.yourdomain.com
```

### 2.3 Sicherheit bei Cloudflare-Zugang

#### Cloudflare Access konfigurieren (empfohlen)

```yaml
# Zero Trust > Access > Applications

Application:
  Name: FlowAudit
  Session Duration: 24h

Policy:
  Name: Allowed Users
  Action: Allow
  Rules:
    - Email Domain: @yourdomain.com
    # ODER
    - Emails: user1@example.com, user2@example.com
    # ODER
    - One-time PIN (für Gäste)
```

---

## 3. Zusammenfassung der Implementierung

### Phase 1: Tax System Selector (Frontend)

| Schritt | Beschreibung | Geschätzte Dateien |
|---------|--------------|-------------------|
| 1.1 | Ruleset-Typen definieren | 1 Datei |
| 1.2 | Ruleset-Daten (DE/EU/UK) | 3 Dateien |
| 1.3 | TaxSystemSelector-Komponente | 4 Dateien |
| 1.4 | Integration in ProjectDetail | 1 Datei (Edit) |
| 1.5 | Übersetzungen ergänzen | 2 Dateien (Edit) |

### Phase 2: Backend API (Optional, falls Rulesets dynamisch)

| Schritt | Beschreibung | Geschätzte Dateien |
|---------|--------------|-------------------|
| 2.1 | API-Routen für Rulesets | 1 Datei |
| 2.2 | Ruleset-Modelle | 1 Datei |

### Phase 3: Netzwerkzugang

| Schritt | Beschreibung | Geschätzte Dateien |
|---------|--------------|-------------------|
| 3.1 | Vite-Config anpassen | 1 Datei (Edit) |
| 3.2 | Docker Compose für LAN | 1 Datei (Edit) |
| 3.3 | Cloudflare Tunnel Setup | 2 neue Dateien |
| 3.4 | Dokumentation | 1 Datei |

---

## 4. Nächste Schritte

Soll ich mit der Implementierung beginnen? Vorgeschlagene Reihenfolge:

1. **TaxSystemSelector** - Flaggen-Komponente mit Modal
2. **Ruleset-Daten** - Vollständige Feature-Listen für DE/EU/UK
3. **CriteriaCatalog** - Modal mit Pflichtmerkmalen
4. **Vite/Docker** - Netzwerkkonfiguration
5. **Cloudflare** - Tunnel-Setup-Anleitung

Möchten Sie alle Schritte oder nur bestimmte Teile?
