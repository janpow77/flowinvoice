import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  GraduationCap,
  FolderPlus,
  Upload,
  Scissors,
  BookOpen,
  Brain,
  Shield,
  CheckCircle,
  FileText,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  Info,
  Loader2,
  X,
  Scale,
  AlertTriangle,
  Search,
  Calculator,
  Clock,
  FileCheck,
  Zap,
  Database,
  MessageSquare,
  Users,
  Building,
  Calendar,
  ListChecks,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'

interface WorkflowStep {
  id: number
  key: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  details: StepDetail[]
}

interface StepDetail {
  title: string
  description: string
  items?: string[]
}

interface RulesetListItem {
  ruleset_id: string
  title: string
  version: string
}

interface GlossaryTerm {
  term: string
  definition: string
  category: string
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    id: 1,
    key: 'project',
    title: 'Projekt erstellen',
    description: 'Ein Förderprojekt mit Begünstigten und Zeitraum anlegen',
    icon: FolderPlus,
    color: 'text-blue-500 bg-blue-500/10',
    details: [
      {
        title: 'Projektstruktur',
        description: 'Jedes Projekt enthält grundlegende Metadaten',
        items: ['Projekttitel', 'Aktenzeichen', 'Projektzeitraum (Start/Ende)', 'Durchführungsort'],
      },
      {
        title: 'Begünstigter',
        description: 'Der Zuwendungsempfänger wird mit allen relevanten Daten erfasst',
        items: ['Name/Firma', 'Adresse', 'USt-IdNr.', 'Vorsteuerabzugsberechtigung', 'Alias-Namen'],
      },
      {
        title: 'Regelwerk-Zuordnung',
        description: 'Das passende Prüfregelwerk wird ausgewählt (z.B. DE_USTG)',
      },
    ],
  },
  {
    id: 2,
    key: 'upload',
    title: 'Belege hochladen',
    description: 'PDF-Rechnungen in das Projekt hochladen',
    icon: Upload,
    color: 'text-green-500 bg-green-500/10',
    details: [
      {
        title: 'Unterstützte Formate',
        description: 'Das System akzeptiert verschiedene Dokumenttypen',
        items: ['PDF-Dokumente', 'Gescannte Rechnungen (OCR)', 'Digitale Rechnungen'],
      },
      {
        title: 'Upload-Prozess',
        description: 'Dokumente werden validiert und vorbereitet',
        items: ['Dateivalidierung', 'PDF-Parsing', 'Text-Extraktion', 'Metadaten-Erfassung'],
      },
    ],
  },
  {
    id: 3,
    key: 'chunking',
    title: 'Chunking & Vorverarbeitung',
    description: 'Dokumente werden in verarbeitbare Teile zerlegt',
    icon: Scissors,
    color: 'text-purple-500 bg-purple-500/10',
    details: [
      {
        title: 'Was ist Chunking?',
        description: 'Große Dokumente werden in kleinere "Chunks" aufgeteilt, damit sie vom LLM verarbeitet werden können.',
      },
      {
        title: 'Token-Grenzen',
        description: 'LLMs haben begrenzte Kontextfenster (z.B. 4096 oder 8192 Token). Chunks müssen kleiner sein.',
        items: ['Typische Chunk-Größe: 500-1000 Token', 'Überlappung für Kontext: 50-100 Token', 'Intelligente Trennung an Absätzen'],
      },
      {
        title: 'Chunk-Strategien',
        description: 'Verschiedene Strategien je nach Dokumenttyp',
        items: ['FIXED_SIZE: Feste Token-Anzahl', 'SEMANTIC: Nach inhaltlichen Abschnitten', 'PAGE_BASED: Seitenweise'],
      },
    ],
  },
  {
    id: 4,
    key: 'ruleset',
    title: 'Regelwerk-Anwendung',
    description: 'Prüfung gegen steuerliche Pflichtmerkmale',
    icon: BookOpen,
    color: 'text-orange-500 bg-orange-500/10',
    details: [
      {
        title: '14 Pflichtmerkmale nach §14 UStG',
        description: 'Eine ordnungsgemäße Rechnung muss folgende Angaben enthalten:',
        items: [
          '1. Vollständiger Name und Anschrift des leistenden Unternehmers',
          '2. Vollständiger Name und Anschrift des Leistungsempfängers',
          '3. Steuernummer oder USt-IdNr. des leistenden Unternehmers',
          '4. Ausstellungsdatum der Rechnung',
          '5. Fortlaufende Rechnungsnummer',
          '6. Menge und Art der Lieferung/Leistung',
          '7. Zeitpunkt der Lieferung/Leistung',
          '8. Entgelt (Nettobetrag)',
          '9. Anzuwendender Steuersatz',
          '10. Auf das Entgelt entfallender Steuerbetrag',
          '11. Ggf. Hinweis auf Steuerbefreiung',
          '12. Bei Gutschriften: Hinweis "Gutschrift"',
          '13. Bei innergemeinschaftlicher Lieferung: USt-IdNr. des Empfängers',
          '14. Bei Reverse-Charge: Hinweis "Steuerschuldnerschaft des Leistungsempfängers"',
        ],
      },
      {
        title: 'Rechtsgrundlagen',
        description: 'Relevante Paragraphen im Umsatzsteuergesetz',
        items: ['§14 UStG - Ausstellung von Rechnungen', '§14a UStG - Zusätzliche Pflichten', '§15 UStG - Vorsteuerabzug'],
      },
      {
        title: 'Sonderregel: Kleinbetragsrechnung',
        description: 'Rechnungen bis 250 EUR brutto haben reduzierte Anforderungen (§33 UStDV)',
        items: ['Name/Anschrift des Leistenden', 'Menge und Art der Leistung', 'Bruttobetrag', 'Steuersatz'],
      },
    ],
  },
  {
    id: 5,
    key: 'llm',
    title: 'LLM-Analyse',
    description: 'KI-gestützte Extraktion und semantische Prüfung',
    icon: Brain,
    color: 'text-pink-500 bg-pink-500/10',
    details: [
      {
        title: 'Prompt-Aufbau',
        description: 'Das LLM erhält einen strukturierten Prompt mit:',
        items: ['System-Prompt mit Regelwerk-Definition', 'Extrahierte Rechnungsdaten', 'Projektkontext (Begünstigter, Zeitraum)', 'RAG-Beispiele ähnlicher Rechnungen'],
      },
      {
        title: 'RAG (Retrieval-Augmented Generation)',
        description: 'Ähnliche, bereits geprüfte Rechnungen werden als Referenz herangezogen',
        items: ['Embedding-Vektoren der Rechnungstexte', 'Semantische Ähnlichkeitssuche in ChromaDB', 'Few-Shot-Learning durch Beispiele'],
      },
      {
        title: 'LLM-Output',
        description: 'Das Modell liefert strukturierte JSON-Antworten',
        items: ['Extrahierte Merkmalswerte', 'Semantische Bewertung', 'Konfidenzwerte', 'Warnungen und Hinweise'],
      },
    ],
  },
  {
    id: 6,
    key: 'checkers',
    title: 'Prüfmodule',
    description: 'Spezialisierte Prüfungen für verschiedene Aspekte',
    icon: Shield,
    color: 'text-red-500 bg-red-500/10',
    details: [
      {
        title: 'Projektzeitraum-Prüfung',
        description: 'Prüft ob das Leistungsdatum im Projektzeitraum liegt',
        items: ['Vergleich Leistungsdatum vs. Projektzeitraum', 'Toleranz für Vor-/Nachbereitungskosten', 'Warnungen bei Grenzfällen'],
      },
      {
        title: 'Risiko-Prüfung',
        description: 'Erkennung potenzieller Unregelmäßigkeiten',
        items: ['Selbstrechnung (Begünstigter = Rechnungssteller)', 'Duplikat-Erkennung', 'Runde Pauschalbeträge', 'Wochenend-/Feiertagsrechnungen'],
      },
      {
        title: 'Semantik-Prüfung',
        description: 'Inhaltliche Plausibilität der Leistungsbeschreibung',
        items: ['Projektrelevanz der Leistung', 'Qualität der Leistungsbeschreibung', 'RAG-Kontext-Abgleich'],
      },
      {
        title: 'Wirtschaftlichkeits-Prüfung',
        description: 'Finanzielle Plausibilität',
        items: ['Budgetgrenzen-Einhaltung', 'Marktübliche Einzelpreise', 'Förderquoten-Konformität'],
      },
    ],
  },
  {
    id: 7,
    key: 'result',
    title: 'Ergebnis & Feedback',
    description: 'Bewertung und Lernschleife',
    icon: CheckCircle,
    color: 'text-emerald-500 bg-emerald-500/10',
    details: [
      {
        title: 'Gesamtbewertung',
        description: 'Jede Rechnung erhält eine Gesamtbewertung',
        items: ['OK - Rechnung ist konform', 'PRÜFUNG ERFORDERLICH - Manuelle Nachprüfung nötig', 'ABGELEHNT - Schwerwiegende Mängel'],
      },
      {
        title: 'Feedback-Loop',
        description: 'Nutzer können das Ergebnis korrigieren',
        items: ['Bestätigung oder Korrektur der Bewertung', 'Anpassung einzelner Merkmalswerte', 'Kommentare und Begründungen'],
      },
      {
        title: 'RAG-Lernen',
        description: 'Validierte Rechnungen verbessern zukünftige Analysen',
        items: ['Speicherung in ChromaDB als Referenz', 'Automatisches Few-Shot-Learning', 'Kontinuierliche Qualitätsverbesserung'],
      },
    ],
  },
  {
    id: 8,
    key: 'list',
    title: 'Belegliste',
    description: 'Übersicht aller geprüften Dokumente',
    icon: FileText,
    color: 'text-cyan-500 bg-cyan-500/10',
    details: [
      {
        title: 'Dokumenten-Übersicht',
        description: 'Alle Belege eines Projekts auf einen Blick',
        items: ['Rechnungssteller', 'Datum und Betrag', 'Prüfstatus', 'Fehleranzahl'],
      },
      {
        title: 'Filter & Sortierung',
        description: 'Schnelles Auffinden relevanter Belege',
        items: ['Nach Status filtern', 'Nach Betrag sortieren', 'Zeitraumfilter', 'Volltextsuche'],
      },
      {
        title: 'Export-Optionen',
        description: 'Ergebnisse für externe Verwendung',
        items: ['PDF-Prüfbericht', 'Excel-Export', 'CSV für Weiterverarbeitung'],
      },
    ],
  },
]

const GLOSSARY_TERMS: GlossaryTerm[] = [
  { term: 'Chunk', definition: 'Ein Textabschnitt, der aus einem größeren Dokument extrahiert wurde, um ihn für das LLM verarbeitbar zu machen.', category: 'Technisch' },
  { term: 'Token', definition: 'Die kleinste Einheit, die ein LLM verarbeitet. Ein Wort entspricht ca. 1-3 Token. Deutsche Wörter sind oft länger.', category: 'Technisch' },
  { term: 'RAG', definition: 'Retrieval-Augmented Generation - Technik, bei der relevante Dokumente aus einer Datenbank abgerufen und dem LLM als Kontext mitgegeben werden.', category: 'Technisch' },
  { term: 'Embedding', definition: 'Numerische Vektordarstellung von Text, die semantische Ähnlichkeit erfasst. Ähnliche Texte haben ähnliche Vektoren.', category: 'Technisch' },
  { term: 'Prompt', definition: 'Die Eingabe/Anweisung an das LLM, die definiert was es tun soll und welchen Kontext es hat.', category: 'Technisch' },
  { term: 'Pflichtmerkmal', definition: 'Eine gesetzlich vorgeschriebene Angabe auf einer Rechnung nach §14 UStG.', category: 'Steuerrecht' },
  { term: 'Vorsteuerabzug', definition: 'Das Recht eines Unternehmers, die ihm in Rechnung gestellte Umsatzsteuer von seiner Steuerschuld abzuziehen (§15 UStG).', category: 'Steuerrecht' },
  { term: 'Kleinbetragsrechnung', definition: 'Rechnung bis 250 EUR brutto mit reduzierten Pflichtangaben nach §33 UStDV.', category: 'Steuerrecht' },
  { term: 'USt-IdNr.', definition: 'Umsatzsteuer-Identifikationsnummer - EU-weit eindeutige Kennung für Unternehmer.', category: 'Steuerrecht' },
  { term: 'Begünstigter', definition: 'Der Zuwendungsempfänger eines Förderprojekts, dessen Rechnungen geprüft werden.', category: 'Förderung' },
  { term: 'Projektzeitraum', definition: 'Der Bewilligungszeitraum, in dem förderfähige Ausgaben anfallen dürfen.', category: 'Förderung' },
  { term: 'LLM', definition: 'Large Language Model - KI-Modell, das natürliche Sprache versteht und generiert (z.B. GPT, Claude, Llama).', category: 'Technisch' },
  { term: 'ChromaDB', definition: 'Vektordatenbank zum Speichern und Suchen von Embeddings für RAG.', category: 'Technisch' },
  { term: 'Konfidenz', definition: 'Maß für die Sicherheit des LLM bei einer Extraktion oder Bewertung (0-100%).', category: 'Technisch' },
]

export default function Training() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language

  const [selectedRuleset, setSelectedRuleset] = useState<string>('DE_USTG')
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [showGlossary, setShowGlossary] = useState(false)
  const [expandedDetail, setExpandedDetail] = useState<number | null>(null)
  const [glossaryFilter, setGlossaryFilter] = useState<string>('all')

  // Fetch rulesets
  const { data: rulesets, isLoading: loadingRulesets } = useQuery({
    queryKey: ['rulesets'],
    queryFn: () => api.getRulesets(),
  })

  // Fetch selected ruleset details
  const { data: rulesetDetail } = useQuery({
    queryKey: ['ruleset', selectedRuleset],
    queryFn: () => api.getRuleset(selectedRuleset),
    enabled: !!selectedRuleset,
  })

  // Auto-play animation
  useEffect(() => {
    if (!isPlaying) return

    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= WORKFLOW_STEPS.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 4000)

    return () => clearInterval(timer)
  }, [isPlaying])

  const handlePrevStep = useCallback(() => {
    setCurrentStep((prev) => Math.max(0, prev - 1))
    setIsPlaying(false)
  }, [])

  const handleNextStep = useCallback(() => {
    setCurrentStep((prev) => Math.min(WORKFLOW_STEPS.length - 1, prev + 1))
    setIsPlaying(false)
  }, [])

  const handleStepClick = useCallback((index: number) => {
    setCurrentStep(index)
    setIsPlaying(false)
  }, [])

  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => !prev)
  }, [])

  const currentWorkflowStep = WORKFLOW_STEPS[currentStep]

  // Get features from ruleset for step 4
  const rulesetFeatures = rulesetDetail?.features || []
  const requiredFeatures = rulesetFeatures.filter((f: { required_level: string }) => f.required_level === 'REQUIRED')
  const conditionalFeatures = rulesetFeatures.filter((f: { required_level: string }) => f.required_level === 'CONDITIONAL')

  const filteredGlossary = glossaryFilter === 'all'
    ? GLOSSARY_TERMS
    : GLOSSARY_TERMS.filter(t => t.category === glossaryFilter)

  const glossaryCategories = ['all', ...new Set(GLOSSARY_TERMS.map(t => t.category))]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-theme-primary/10 rounded-lg">
            <GraduationCap className="w-8 h-8 text-theme-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-theme-text-primary">
              {lang === 'de' ? 'Interaktive Schulung' : 'Interactive Training'}
            </h1>
            <p className="text-theme-text-muted">
              {lang === 'de'
                ? 'Verstehen Sie den Prüfprozess Schritt für Schritt'
                : 'Understand the audit process step by step'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Ruleset Selector */}
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-theme-text-muted" />
            <select
              value={selectedRuleset}
              onChange={(e) => setSelectedRuleset(e.target.value)}
              disabled={loadingRulesets}
              className="px-3 py-2 bg-theme-input border border-theme-border rounded-lg text-theme-text-primary focus:ring-2 focus:ring-theme-primary"
            >
              {rulesets?.map((rs: RulesetListItem) => (
                <option key={rs.ruleset_id} value={rs.ruleset_id}>
                  {rs.title} (v{rs.version})
                </option>
              ))}
            </select>
          </div>

          {/* Glossary Button */}
          <button
            onClick={() => setShowGlossary(true)}
            className="flex items-center gap-2 px-4 py-2 bg-theme-hover text-theme-text-secondary rounded-lg hover:bg-theme-selected transition-colors"
          >
            <Info className="w-5 h-5" />
            {lang === 'de' ? 'Glossar' : 'Glossary'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-theme-card rounded-lg border border-theme-border p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-theme-text-secondary">
            {lang === 'de' ? 'Workflow-Fortschritt' : 'Workflow Progress'}
          </span>
          <span className="text-sm text-theme-text-muted">
            {currentStep + 1} / {WORKFLOW_STEPS.length}
          </span>
        </div>

        {/* Step indicators */}
        <div className="flex items-center gap-1">
          {WORKFLOW_STEPS.map((step, index) => (
            <button
              key={step.id}
              onClick={() => handleStepClick(index)}
              className={clsx(
                'flex-1 h-2 rounded-full transition-all duration-300',
                index === currentStep
                  ? 'bg-theme-primary'
                  : index < currentStep
                  ? 'bg-theme-primary/50'
                  : 'bg-theme-border'
              )}
              title={step.title}
            />
          ))}
        </div>

        {/* Step labels */}
        <div className="flex items-center justify-between mt-2 overflow-x-auto">
          {WORKFLOW_STEPS.map((step, index) => {
            const Icon = step.icon
            return (
              <button
                key={step.id}
                onClick={() => handleStepClick(index)}
                className={clsx(
                  'flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-colors min-w-[80px]',
                  index === currentStep
                    ? 'bg-theme-primary/10'
                    : 'hover:bg-theme-hover'
                )}
              >
                <Icon className={clsx(
                  'w-5 h-5',
                  index === currentStep ? 'text-theme-primary' : 'text-theme-text-muted'
                )} />
                <span className={clsx(
                  'text-xs whitespace-nowrap',
                  index === currentStep ? 'text-theme-primary font-medium' : 'text-theme-text-muted'
                )}>
                  {step.title}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Play Controls */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={handlePrevStep}
          disabled={currentStep === 0}
          className="p-2 bg-theme-hover rounded-lg hover:bg-theme-selected disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-6 h-6 text-theme-text-secondary" />
        </button>

        <button
          onClick={togglePlay}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors',
            isPlaying
              ? 'bg-status-warning text-white'
              : 'bg-theme-primary text-white hover:bg-theme-primary-hover'
          )}
        >
          {isPlaying ? (
            <>
              <Pause className="w-5 h-5" />
              {lang === 'de' ? 'Pause' : 'Pause'}
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              {lang === 'de' ? 'Abspielen' : 'Play'}
            </>
          )}
        </button>

        <button
          onClick={handleNextStep}
          disabled={currentStep === WORKFLOW_STEPS.length - 1}
          className="p-2 bg-theme-hover rounded-lg hover:bg-theme-selected disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-6 h-6 text-theme-text-secondary" />
        </button>
      </div>

      {/* Current Step Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <div className={clsx(
            'bg-theme-card rounded-xl border border-theme-border overflow-hidden transition-all duration-500',
            isPlaying && 'ring-2 ring-theme-primary ring-offset-2 ring-offset-theme-bg'
          )}>
            {/* Step Header */}
            <div className={clsx('p-6', currentWorkflowStep.color.replace('text-', 'bg-').replace('-500', '-500/20'))}>
              <div className="flex items-center gap-4">
                <div className={clsx('p-4 rounded-xl', currentWorkflowStep.color)}>
                  <currentWorkflowStep.icon className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-theme-text-primary">
                    {currentStep + 1}. {currentWorkflowStep.title}
                  </h2>
                  <p className="text-theme-text-secondary mt-1">
                    {currentWorkflowStep.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Step Details */}
            <div className="p-6 space-y-4">
              {/* Special content for Ruleset step */}
              {currentWorkflowStep.key === 'ruleset' && rulesetDetail && (
                <div className="mb-6 p-4 bg-status-info-bg border border-status-info-border rounded-lg">
                  <h3 className="font-semibold text-status-info mb-2">
                    Ausgewähltes Regelwerk: {lang === 'de' ? rulesetDetail.title_de : rulesetDetail.title_en}
                  </h3>
                  <p className="text-sm text-status-info">
                    {requiredFeatures.length} Pflichtmerkmale, {conditionalFeatures.length} bedingte Merkmale definiert
                  </p>
                </div>
              )}

              {currentWorkflowStep.details.map((detail, idx) => (
                <div
                  key={idx}
                  className="border border-theme-border rounded-lg overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedDetail(expandedDetail === idx ? null : idx)}
                    className="w-full flex items-center justify-between p-4 hover:bg-theme-hover transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-theme-primary/10 flex items-center justify-center text-theme-primary font-bold">
                        {idx + 1}
                      </div>
                      <div className="text-left">
                        <h3 className="font-semibold text-theme-text-primary">{detail.title}</h3>
                        <p className="text-sm text-theme-text-muted">{detail.description}</p>
                      </div>
                    </div>
                    <ChevronRight className={clsx(
                      'w-5 h-5 text-theme-text-muted transition-transform',
                      expandedDetail === idx && 'rotate-90'
                    )} />
                  </button>

                  {expandedDetail === idx && detail.items && (
                    <div className="px-4 pb-4 bg-theme-hover border-t border-theme-border">
                      <ul className="mt-3 space-y-2">
                        {detail.items.map((item, itemIdx) => (
                          <li key={itemIdx} className="flex items-start gap-2 text-sm text-theme-text-secondary">
                            <CheckCircle className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Side Panel - Visual Animation */}
        <div className="lg:col-span-1">
          <div className="bg-theme-card rounded-xl border border-theme-border p-6 sticky top-4">
            <h3 className="font-semibold text-theme-text-primary mb-4">
              {lang === 'de' ? 'Visualisierung' : 'Visualization'}
            </h3>

            {/* Animated visualization based on current step */}
            <div className="aspect-square bg-theme-hover rounded-lg flex items-center justify-center relative overflow-hidden">
              {/* Step 1: Project */}
              {currentWorkflowStep.key === 'project' && (
                <div className="text-center space-y-4 animate-fade-in">
                  <FolderPlus className="w-16 h-16 text-blue-500 mx-auto animate-bounce" />
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 justify-center text-sm text-theme-text-secondary">
                      <Building className="w-4 h-4" />
                      <span>Begünstigter</span>
                    </div>
                    <div className="flex items-center gap-2 justify-center text-sm text-theme-text-secondary">
                      <Calendar className="w-4 h-4" />
                      <span>Projektzeitraum</span>
                    </div>
                    <div className="flex items-center gap-2 justify-center text-sm text-theme-text-secondary">
                      <BookOpen className="w-4 h-4" />
                      <span>Regelwerk</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Upload */}
              {currentWorkflowStep.key === 'upload' && (
                <div className="text-center space-y-4">
                  <div className="relative">
                    <Upload className="w-16 h-16 text-green-500 mx-auto" />
                    <div className="absolute -top-2 -right-2 flex gap-1">
                      <FileText className="w-6 h-6 text-status-danger animate-bounce" style={{ animationDelay: '0ms' }} />
                      <FileText className="w-6 h-6 text-status-danger animate-bounce" style={{ animationDelay: '200ms' }} />
                      <FileText className="w-6 h-6 text-status-danger animate-bounce" style={{ animationDelay: '400ms' }} />
                    </div>
                  </div>
                  <p className="text-sm text-theme-text-muted">PDFs hochladen</p>
                </div>
              )}

              {/* Step 3: Chunking */}
              {currentWorkflowStep.key === 'chunking' && (
                <div className="text-center space-y-4">
                  <div className="flex items-center justify-center gap-2">
                    <FileText className="w-12 h-12 text-purple-500" />
                    <Scissors className="w-8 h-8 text-purple-500 animate-pulse" />
                    <div className="flex flex-col gap-1">
                      <div className="w-8 h-3 bg-purple-500/30 rounded animate-pulse" />
                      <div className="w-8 h-3 bg-purple-500/50 rounded animate-pulse" style={{ animationDelay: '100ms' }} />
                      <div className="w-8 h-3 bg-purple-500/70 rounded animate-pulse" style={{ animationDelay: '200ms' }} />
                    </div>
                  </div>
                  <p className="text-sm text-theme-text-muted">Chunks erstellen</p>
                </div>
              )}

              {/* Step 4: Ruleset */}
              {currentWorkflowStep.key === 'ruleset' && (
                <div className="text-center space-y-4">
                  <BookOpen className="w-16 h-16 text-orange-500 mx-auto" />
                  <div className="flex flex-wrap gap-1 justify-center px-4">
                    {[1,2,3,4,5,6,7].map((n) => (
                      <div
                        key={n}
                        className="w-6 h-6 bg-orange-500/20 rounded text-xs flex items-center justify-center text-orange-500 font-medium animate-pulse"
                        style={{ animationDelay: `${n * 100}ms` }}
                      >
                        {n}
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-theme-text-muted">14 Pflichtmerkmale prüfen</p>
                </div>
              )}

              {/* Step 5: LLM */}
              {currentWorkflowStep.key === 'llm' && (
                <div className="text-center space-y-4">
                  <Brain className="w-16 h-16 text-pink-500 mx-auto animate-pulse" />
                  <div className="flex items-center justify-center gap-2">
                    <Database className="w-6 h-6 text-theme-text-muted" />
                    <Zap className="w-4 h-4 text-yellow-500 animate-ping" />
                    <MessageSquare className="w-6 h-6 text-theme-text-muted" />
                  </div>
                  <p className="text-sm text-theme-text-muted">RAG + LLM-Analyse</p>
                </div>
              )}

              {/* Step 6: Checkers */}
              {currentWorkflowStep.key === 'checkers' && (
                <div className="grid grid-cols-2 gap-3 p-4">
                  <div className="p-3 bg-theme-card rounded-lg text-center">
                    <Clock className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                    <span className="text-xs">Zeitraum</span>
                  </div>
                  <div className="p-3 bg-theme-card rounded-lg text-center">
                    <AlertTriangle className="w-6 h-6 text-yellow-500 mx-auto mb-1" />
                    <span className="text-xs">Risiko</span>
                  </div>
                  <div className="p-3 bg-theme-card rounded-lg text-center">
                    <Search className="w-6 h-6 text-purple-500 mx-auto mb-1" />
                    <span className="text-xs">Semantik</span>
                  </div>
                  <div className="p-3 bg-theme-card rounded-lg text-center">
                    <Calculator className="w-6 h-6 text-green-500 mx-auto mb-1" />
                    <span className="text-xs">Wirtschaft</span>
                  </div>
                </div>
              )}

              {/* Step 7: Result */}
              {currentWorkflowStep.key === 'result' && (
                <div className="text-center space-y-4">
                  <div className="flex items-center justify-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-status-success-bg flex items-center justify-center">
                      <CheckCircle className="w-6 h-6 text-status-success" />
                    </div>
                    <div className="w-12 h-12 rounded-full bg-status-warning-bg flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-status-warning" />
                    </div>
                    <div className="w-12 h-12 rounded-full bg-status-danger-bg flex items-center justify-center">
                      <X className="w-6 h-6 text-status-danger" />
                    </div>
                  </div>
                  <p className="text-sm text-theme-text-muted">Bewertung & Feedback</p>
                </div>
              )}

              {/* Step 8: List */}
              {currentWorkflowStep.key === 'list' && (
                <div className="text-center space-y-3 px-4">
                  <ListChecks className="w-12 h-12 text-cyan-500 mx-auto" />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 p-2 bg-status-success-bg rounded text-xs">
                      <FileCheck className="w-4 h-4 text-status-success" />
                      <span className="flex-1 text-left">Rechnung-001.pdf</span>
                      <CheckCircle className="w-4 h-4 text-status-success" />
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-status-warning-bg rounded text-xs">
                      <FileCheck className="w-4 h-4 text-status-warning" />
                      <span className="flex-1 text-left">Rechnung-002.pdf</span>
                      <AlertTriangle className="w-4 h-4 text-status-warning" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick info about current step */}
            <div className="mt-4 p-3 bg-status-info-bg border border-status-info-border rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-status-info mt-0.5 flex-shrink-0" />
                <p className="text-xs text-status-info">
                  {currentWorkflowStep.key === 'project' && 'Projekte bilden den Container für alle Belege und definieren den Prüfkontext.'}
                  {currentWorkflowStep.key === 'upload' && 'Mehrere PDFs können gleichzeitig hochgeladen werden.'}
                  {currentWorkflowStep.key === 'chunking' && 'Chunking ermöglicht die Verarbeitung beliebig langer Dokumente.'}
                  {currentWorkflowStep.key === 'ruleset' && 'Das Regelwerk definiert alle zu prüfenden Merkmale.'}
                  {currentWorkflowStep.key === 'llm' && 'RAG verbessert die Genauigkeit durch Beispiele aus der Vergangenheit.'}
                  {currentWorkflowStep.key === 'checkers' && 'Jedes Prüfmodul kann individuell konfiguriert werden.'}
                  {currentWorkflowStep.key === 'result' && 'Feedback verbessert kontinuierlich die Erkennungsqualität.'}
                  {currentWorkflowStep.key === 'list' && 'Export ermöglicht die Integration in andere Systeme.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Glossary Modal */}
      {showGlossary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-theme-elevated rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border">
              <div className="flex items-center gap-3">
                <Info className="w-6 h-6 text-theme-primary" />
                <h3 className="text-lg font-semibold text-theme-text-primary">
                  {lang === 'de' ? 'Fachbegriffe-Glossar' : 'Glossary'}
                </h3>
              </div>
              <button
                onClick={() => setShowGlossary(false)}
                className="p-2 hover:bg-theme-hover rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-theme-text-muted" />
              </button>
            </div>

            {/* Filter */}
            <div className="px-6 py-3 border-b border-theme-border bg-theme-hover">
              <div className="flex gap-2 flex-wrap">
                {glossaryCategories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setGlossaryFilter(cat)}
                    className={clsx(
                      'px-3 py-1 text-sm rounded-full transition-colors',
                      glossaryFilter === cat
                        ? 'bg-theme-primary text-white'
                        : 'bg-theme-card text-theme-text-secondary hover:bg-theme-selected'
                    )}
                  >
                    {cat === 'all' ? (lang === 'de' ? 'Alle' : 'All') : cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
              <div className="space-y-3">
                {filteredGlossary.map((term, idx) => (
                  <div key={idx} className="p-4 bg-theme-card border border-theme-border rounded-lg">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-semibold text-theme-text-primary">{term.term}</h4>
                      <span className="text-xs px-2 py-0.5 bg-theme-hover rounded-full text-theme-text-muted">
                        {term.category}
                      </span>
                    </div>
                    <p className="text-sm text-theme-text-secondary mt-2">{term.definition}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-theme-border bg-theme-hover">
              <button
                onClick={() => setShowGlossary(false)}
                className="w-full px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover transition-colors"
              >
                {lang === 'de' ? 'Schließen' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSS for animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out;
        }
      `}</style>
    </div>
  )
}
