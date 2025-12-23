import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  FolderPlus,
  Upload,
  Scissors,
  BookOpen,
  Brain,
  Shield,
  CheckCircle,
  FileText,
  Info,
  X,
  Building,
  Calendar,
  ListChecks,
  MapPin,
  Euro,
  FileCheck,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  ChevronRight,
} from 'lucide-react'
import clsx from 'clsx'

// --- CSS Animationen (wie Login-Seite) ---
const cssAnimations = `
  @keyframes fishSwim {
    0%, 100% {
      transform: translateX(0) translateY(0) rotate(0deg);
    }
    25% {
      transform: translateX(20px) translateY(-10px) rotate(5deg);
    }
    50% {
      transform: translateX(0) translateY(-20px) rotate(0deg);
    }
    75% {
      transform: translateX(-20px) translateY(-10px) rotate(-5deg);
    }
  }

  .animate-fish-swim {
    animation: fishSwim 8s ease-in-out infinite;
    filter: drop-shadow(0 0 20px rgba(96, 165, 250, 0.6));
  }

  @keyframes dataFlow {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  .data-flow {
    animation: dataFlow 20s linear infinite;
  }

  .data-flow-fast {
    animation: dataFlow 15s linear infinite;
  }

  .data-flow-slow {
    animation: dataFlow 25s linear infinite reverse;
  }

  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.7; }
  }

  .binary-pulse {
    animation: binaryPulse 3s ease-in-out infinite;
  }

  @keyframes nodeGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(96, 165, 250, 0.3); }
    50% { box-shadow: 0 0 40px rgba(96, 165, 250, 0.6); }
  }

  .node-glow {
    animation: nodeGlow 2s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  .animate-float {
    animation: float 3s ease-in-out infinite;
  }

  @keyframes pulse-ring {
    0% { transform: scale(1); opacity: 1; }
    100% { transform: scale(1.5); opacity: 0; }
  }

  .pulse-ring {
    animation: pulse-ring 2s ease-out infinite;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
  }

  .animate-slide-in {
    animation: slideIn 0.5s ease-out forwards;
  }

  @keyframes progress {
    from { width: 0%; }
    to { width: 100%; }
  }
`

// Statische Binärsequenzen für das Datenwasser
const BINARY_LINES = [
  '0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0',
  '1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1',
  '0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1',
]

interface WorkflowNode {
  id: string
  title: string
  shortTitle: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  details: string[]
  glossaryTerms: { term: string; definition: string }[]
}

// Statische Regelwerke
const DEMO_RULESETS = [
  { id: 'DE_USTG', title: 'Deutschland – UStG', titleShort: 'DE (UStG)', version: '1.0.0', featuresCount: 14 },
  { id: 'EU_VAT', title: 'EU – MwSt-Richtlinie', titleShort: 'EU (MwSt)', version: '1.0.0', featuresCount: 12 },
  { id: 'AT_USTG', title: 'Österreich – UStG', titleShort: 'AT (UStG)', version: '1.0.0', featuresCount: 11 },
]

// Musterprojekt
const SAMPLE_PROJECT = {
  title: 'Digitalisierung Stadtbücherei Musterstadt',
  fileReference: 'FKZ 2024-DIG-0815',
  period: { start: '01.01.2024', end: '31.12.2024' },
  location: 'Musterstadt, Hauptstraße 1',
  beneficiary: {
    name: 'Stadtbücherei Musterstadt e.V.',
    address: 'Hauptstraße 1, 12345 Musterstadt',
    vatId: 'DE123456789',
    inputTaxDeductible: false,
  },
  sampleInvoices: [
    { name: 'IT-Service GmbH', amount: '2.380,00 €', status: 'ok' },
    { name: 'Bürobedarf Müller', amount: '89,50 €', status: 'warning' },
    { name: 'Schulungsagentur Weber', amount: '1.500,00 €', status: 'ok' },
  ],
}

// Workflow-Knoten mit Glossar-Begriffen
const WORKFLOW_NODES: WorkflowNode[] = [
  {
    id: 'project',
    title: 'Projekt anlegen',
    shortTitle: 'Projekt',
    description: 'Förderprojekt mit Begünstigten erstellen',
    icon: FolderPlus,
    color: 'from-blue-400 to-blue-600',
    details: ['Projekttitel', 'Aktenzeichen', 'Zeitraum', 'Begünstigter', 'Regelwerk'],
    glossaryTerms: [
      { term: 'Begünstigter', definition: 'Der Zuwendungsempfänger des Förderprojekts, dessen Rechnungen geprüft werden.' },
      { term: 'Projektzeitraum', definition: 'Der Bewilligungszeitraum, in dem förderfähige Ausgaben anfallen dürfen.' },
    ],
  },
  {
    id: 'upload',
    title: 'Belege hochladen',
    shortTitle: 'Upload',
    description: 'PDF-Rechnungen ins System laden',
    icon: Upload,
    color: 'from-green-400 to-green-600',
    details: ['PDF-Upload', 'OCR-Erkennung', 'Batch-Upload', 'Validierung'],
    glossaryTerms: [
      { term: 'OCR', definition: 'Optical Character Recognition - Texterkennung aus gescannten Dokumenten.' },
    ],
  },
  {
    id: 'chunking',
    title: 'Vorverarbeitung',
    shortTitle: 'Chunking',
    description: 'Dokumente für KI aufbereiten',
    icon: Scissors,
    color: 'from-purple-400 to-purple-600',
    details: ['Text-Extraktion', 'Token-Chunking', 'Embeddings', 'Vektorspeicher'],
    glossaryTerms: [
      { term: 'Chunk', definition: 'Ein Textabschnitt aus einem Dokument, aufgeteilt für LLM-Verarbeitung.' },
      { term: 'Token', definition: 'Die kleinste Einheit für LLM-Verarbeitung. Ein Wort ≈ 1-3 Token.' },
      { term: 'Embedding', definition: 'Numerische Vektordarstellung von Text für semantische Suche.' },
    ],
  },
  {
    id: 'ruleset',
    title: 'Regelwerk',
    shortTitle: 'Regeln',
    description: 'Pflichtmerkmale nach §14 UStG',
    icon: BookOpen,
    color: 'from-orange-400 to-orange-600',
    details: ['14 Pflichtmerkmale', 'Kleinbetragsrechnung', 'Reverse-Charge', 'EU-Lieferung'],
    glossaryTerms: [
      { term: 'Pflichtmerkmal', definition: 'Gesetzlich vorgeschriebene Angabe auf einer Rechnung nach §14 UStG.' },
      { term: 'Kleinbetragsrechnung', definition: 'Rechnung bis 250€ brutto mit reduzierten Pflichtangaben (§33 UStDV).' },
    ],
  },
  {
    id: 'llm',
    title: 'KI-Analyse',
    shortTitle: 'LLM',
    description: 'Intelligente Extraktion & Bewertung',
    icon: Brain,
    color: 'from-pink-400 to-pink-600',
    details: ['RAG-System', 'Few-Shot Learning', 'Semantik-Analyse', 'Konfidenz'],
    glossaryTerms: [
      { term: 'LLM', definition: 'Large Language Model - KI-Modell für Sprachverarbeitung (GPT, Claude, Llama).' },
      { term: 'RAG', definition: 'Retrieval-Augmented Generation - Kontext aus Datenbank für bessere LLM-Antworten.' },
      { term: 'Konfidenz', definition: 'Maß für die Sicherheit des LLM bei einer Extraktion (0-100%).' },
    ],
  },
  {
    id: 'checkers',
    title: 'Prüfmodule',
    shortTitle: 'Checker',
    description: 'Spezialisierte Validierungen',
    icon: Shield,
    color: 'from-red-400 to-red-600',
    details: ['Zeitraum-Check', 'Risiko-Erkennung', 'Semantik-Prüfung', 'Wirtschaftlichkeit'],
    glossaryTerms: [
      { term: 'Selbstrechnung', definition: 'Risiko: Der Begünstigte stellt sich selbst eine Rechnung aus.' },
      { term: 'Duplikat', definition: 'Rechnung wurde möglicherweise mehrfach eingereicht.' },
    ],
  },
  {
    id: 'result',
    title: 'Ergebnis',
    shortTitle: 'Feedback',
    description: 'Bewertung und Lernschleife',
    icon: CheckCircle,
    color: 'from-emerald-400 to-emerald-600',
    details: ['Gesamtbewertung', 'Fehlerhinweise', 'Korrektur', 'RAG-Lernen'],
    glossaryTerms: [
      { term: 'Feedback-Loop', definition: 'Nutzer-Korrekturen verbessern zukünftige KI-Analysen.' },
    ],
  },
  {
    id: 'export',
    title: 'Export',
    shortTitle: 'Report',
    description: 'Dokumentation und Ausgabe',
    icon: FileText,
    color: 'from-cyan-400 to-cyan-600',
    details: ['Belegliste', 'PDF-Report', 'Excel-Export', 'Archivierung'],
    glossaryTerms: [
      { term: 'Prüfbericht', definition: 'Dokumentation aller Prüfergebnisse als PDF oder Excel.' },
    ],
  },
]

// Binäres Datenwasser Komponente
const BinaryDataWater = () => (
  <div className="absolute bottom-0 left-0 right-0 h-32 overflow-hidden pointer-events-none">
    <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-blue-950/80 via-blue-900/50 to-transparent">
      <div className="data-flow-slow whitespace-nowrap font-mono text-xs pt-4">
        <span className="text-blue-400/30">{BINARY_LINES[0]} {BINARY_LINES[0]}</span>
      </div>
      <div className="data-flow whitespace-nowrap font-mono text-xs">
        <span className="text-cyan-400/25">{BINARY_LINES[1]} {BINARY_LINES[1]}</span>
      </div>
    </div>
    <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-blue-800/70 to-transparent">
      <div className="data-flow-fast whitespace-nowrap font-mono text-sm binary-pulse">
        <span className="text-blue-300/40">{BINARY_LINES[2]} {BINARY_LINES[2]}</span>
      </div>
    </div>
  </div>
)

export default function Training() {
  const { i18n } = useTranslation()
  const lang = i18n.language

  const [selectedRulesetId, setSelectedRulesetId] = useState<string>('DE_USTG')
  const [currentStep, setCurrentStep] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [showGlossary, setShowGlossary] = useState(false)
  const [showSampleProject, setShowSampleProject] = useState(false)
  const [progress, setProgress] = useState<number>(0)

  const selectedRuleset = DEMO_RULESETS.find(r => r.id === selectedRulesetId) || DEMO_RULESETS[0]
  const currentNode = WORKFLOW_NODES[currentStep]

  const STEP_DURATION = 5000 // 5 Sekunden pro Schritt

  // Auto-Animation
  useEffect(() => {
    if (!isPlaying) return

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          // Nächster Schritt
          setCurrentStep(step => {
            if (step >= WORKFLOW_NODES.length - 1) {
              setIsPlaying(false)
              return step
            }
            return step + 1
          })
          return 0
        }
        return prev + (100 / (STEP_DURATION / 100))
      })
    }, 100)

    return () => clearInterval(progressInterval)
  }, [isPlaying])

  // Reset progress wenn Schritt manuell gewechselt wird
  useEffect(() => {
    setProgress(0)
  }, [currentStep])

  const handlePlay = useCallback(() => {
    setIsPlaying(true)
    setProgress(0)
  }, [])

  const handlePause = useCallback(() => {
    setIsPlaying(false)
  }, [])

  const handleReset = useCallback(() => {
    setIsPlaying(false)
    setCurrentStep(0)
    setProgress(0)
  }, [])

  const handleStepClick = useCallback((index: number) => {
    setCurrentStep(index)
    setIsPlaying(false)
    setProgress(0)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 relative overflow-hidden">
      <style>{cssAnimations}</style>

      {/* Binäres Datenwasser am unteren Rand */}
      <BinaryDataWater />

      {/* Schwimmender Fisch */}
      <div className="absolute top-20 right-10 z-10 animate-fish-swim pointer-events-none">
        <img src="/auditlogo.png" alt="FlowAudit" className="w-20 h-20 object-contain" />
      </div>

      {/* Deko-Blasen */}
      <div className="absolute top-1/4 left-10 w-4 h-4 bg-blue-300/20 rounded-full animate-bounce" style={{ animationDuration: '4s' }} />
      <div className="absolute top-1/3 right-1/4 w-3 h-3 bg-blue-200/15 rounded-full animate-bounce" style={{ animationDelay: '1s', animationDuration: '5s' }} />

      {/* Hauptinhalt */}
      <div className="relative z-20 p-6 pb-40">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
              <img src="/auditlogo.png" alt="FlowAudit" className="w-10 h-10 object-contain" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white drop-shadow-lg">
                {lang === 'de' ? 'Interaktive Schulung' : 'Interactive Training'}
              </h1>
              <p className="text-blue-200 text-sm">
                {lang === 'de' ? 'Wählen Sie ein Regelwerk und starten Sie die Animation' : 'Select a ruleset and start the animation'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedRulesetId}
              onChange={(e) => setSelectedRulesetId(e.target.value)}
              className="px-4 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white text-sm focus:ring-2 focus:ring-blue-300"
            >
              {DEMO_RULESETS.map((rs) => (
                <option key={rs.id} value={rs.id} className="bg-blue-900 text-white">{rs.titleShort}</option>
              ))}
            </select>

            <button
              onClick={() => setShowSampleProject(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
            >
              <FolderPlus className="w-4 h-4" />
              Musterprojekt
            </button>

            <button
              onClick={() => setShowGlossary(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
            >
              <Info className="w-4 h-4" />
              Glossar
            </button>
          </div>
        </div>

        {/* Steuerung */}
        <div className="flex items-center justify-center gap-4 mb-6">
          <button
            onClick={handleReset}
            className="p-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full hover:bg-white/20 transition-colors"
            title="Zurücksetzen"
          >
            <RotateCcw className="w-5 h-5 text-white" />
          </button>

          <button
            onClick={isPlaying ? handlePause : handlePlay}
            className={clsx(
              'flex items-center gap-2 px-8 py-3 rounded-full font-semibold transition-all text-lg',
              isPlaying
                ? 'bg-yellow-500 hover:bg-yellow-400 text-yellow-900'
                : 'bg-emerald-500 hover:bg-emerald-400 text-white'
            )}
          >
            {isPlaying ? (
              <>
                <Pause className="w-6 h-6" />
                Pause
              </>
            ) : (
              <>
                <Play className="w-6 h-6" />
                {currentStep === 0 ? 'Animation starten' : 'Fortsetzen'}
              </>
            )}
          </button>

          <div className="text-white/70 text-sm">
            Schritt {currentStep + 1} / {WORKFLOW_NODES.length}
          </div>
        </div>

        {/* Fortschrittsbalken */}
        <div className="bg-white/10 backdrop-blur-sm rounded-full h-3 mb-6 overflow-hidden border border-white/20">
          <div className="flex h-full">
            {WORKFLOW_NODES.map((node, index) => (
              <div
                key={node.id}
                className="relative flex-1 cursor-pointer"
                onClick={() => handleStepClick(index)}
              >
                <div
                  className={clsx(
                    'h-full transition-all duration-300',
                    index < currentStep
                      ? 'bg-emerald-500'
                      : index === currentStep
                      ? 'bg-blue-400'
                      : 'bg-transparent'
                  )}
                  style={{
                    width: index === currentStep ? `${progress}%` : index < currentStep ? '100%' : '0%'
                  }}
                />
                {index < WORKFLOW_NODES.length - 1 && (
                  <div className="absolute right-0 top-0 bottom-0 w-px bg-white/20" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Schritt-Indikatoren */}
        <div className="flex justify-between mb-8 px-2">
          {WORKFLOW_NODES.map((node, index) => {
            const Icon = node.icon
            const isActive = index === currentStep
            const isCompleted = index < currentStep

            return (
              <button
                key={node.id}
                onClick={() => handleStepClick(index)}
                className={clsx(
                  'flex flex-col items-center gap-1 transition-all duration-300',
                  isActive && 'scale-110'
                )}
              >
                <div className={clsx(
                  'w-10 h-10 rounded-full flex items-center justify-center transition-all',
                  isActive
                    ? `bg-gradient-to-br ${node.color} ring-4 ring-white/30`
                    : isCompleted
                    ? 'bg-emerald-500'
                    : 'bg-white/10 border border-white/20'
                )}>
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5 text-white" />
                  ) : (
                    <Icon className={clsx('w-5 h-5', isActive ? 'text-white' : 'text-white/60')} />
                  )}
                </div>
                <span className={clsx(
                  'text-xs transition-colors',
                  isActive ? 'text-white font-semibold' : 'text-white/50'
                )}>
                  {node.shortTitle}
                </span>
              </button>
            )
          })}
        </div>

        {/* Hauptbereich: Aktiver Schritt */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Schritt-Details */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6 animate-slide-in" key={currentStep}>
              <div className="flex items-center gap-4 mb-6">
                <div className={clsx('w-16 h-16 rounded-2xl bg-gradient-to-br flex items-center justify-center', currentNode.color)}>
                  <currentNode.icon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">{currentStep + 1}. {currentNode.title}</h2>
                  <p className="text-blue-200">{currentNode.description}</p>
                </div>
              </div>

              {/* Details des Schritts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                {currentNode.details.map((detail, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10 animate-slide-in"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <ChevronRight className="w-5 h-5 text-emerald-400" />
                    <span className="text-white">{detail}</span>
                  </div>
                ))}
              </div>

              {/* Regelwerk-Info bei Schritt 4 */}
              {currentNode.id === 'ruleset' && (
                <div className="p-4 bg-orange-500/20 border border-orange-400/30 rounded-xl">
                  <h4 className="font-semibold text-orange-300 mb-2">Ausgewähltes Regelwerk</h4>
                  <p className="text-white">{selectedRuleset.title}</p>
                  <p className="text-orange-200/80 text-sm mt-1">{selectedRuleset.featuresCount} Pflichtmerkmale werden geprüft</p>
                </div>
              )}
            </div>
          </div>

          {/* Glossar-Begriffe für aktuellen Schritt */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-300" />
                <h3 className="font-semibold text-white">Begriffe in diesem Schritt</h3>
              </div>

              {currentNode.glossaryTerms.length > 0 ? (
                <div className="space-y-3">
                  {currentNode.glossaryTerms.map((term, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-white/5 rounded-xl border border-white/10 animate-slide-in"
                      style={{ animationDelay: `${idx * 150}ms` }}
                    >
                      <h4 className="font-semibold text-blue-300 mb-1">{term.term}</h4>
                      <p className="text-sm text-white/80">{term.definition}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-white/50 text-sm">Keine speziellen Begriffe in diesem Schritt.</p>
              )}

              {/* Musterprojekt-Kurzinfo */}
              <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <FolderPlus className="w-4 h-4 text-blue-300" />
                  <span className="text-sm font-medium text-white">Beispiel-Projekt</span>
                </div>
                <p className="text-xs text-white/70">{SAMPLE_PROJECT.title}</p>
                <p className="text-xs text-white/50 mt-1">
                  {SAMPLE_PROJECT.beneficiary.name}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Musterprojekt Modal */}
      {showSampleProject && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-b from-blue-800 to-blue-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col border border-white/20">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <FolderPlus className="w-6 h-6 text-blue-300" />
                <h3 className="text-lg font-semibold text-white">Musterprojekt</h3>
              </div>
              <button onClick={() => setShowSampleProject(false)} className="p-2 hover:bg-white/10 rounded-lg">
                <X className="w-5 h-5 text-white/70" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6 space-y-6">
              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold text-white mb-3">Projektdaten</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Titel</p>
                      <p className="text-white">{SAMPLE_PROJECT.title}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Aktenzeichen</p>
                      <p className="text-white">{SAMPLE_PROJECT.fileReference}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Zeitraum</p>
                      <p className="text-white">{SAMPLE_PROJECT.period.start} – {SAMPLE_PROJECT.period.end}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Ort</p>
                      <p className="text-white">{SAMPLE_PROJECT.location}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold text-white mb-3">Begünstigter</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Name</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">USt-IdNr.</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.vatId}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Adresse</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.address}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Euro className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">Vorsteuerabzug</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.inputTaxDeductible ? 'Ja' : 'Nein'}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-3">Beispiel-Rechnungen</h4>
                <div className="space-y-2">
                  {SAMPLE_PROJECT.sampleInvoices.map((inv, idx) => (
                    <div
                      key={idx}
                      className={clsx(
                        'flex items-center justify-between p-3 rounded-lg border',
                        inv.status === 'ok' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-yellow-500/10 border-yellow-500/30'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <FileText className={inv.status === 'ok' ? 'w-4 h-4 text-emerald-400' : 'w-4 h-4 text-yellow-400'} />
                        <span className="text-sm text-white">{inv.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-blue-200">{inv.amount}</span>
                        {inv.status === 'ok' ? (
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/10">
              <button
                onClick={() => setShowSampleProject(false)}
                className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-lg transition-colors font-medium"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Glossar Modal */}
      {showGlossary && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-b from-blue-800 to-blue-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col border border-white/20">
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <Info className="w-6 h-6 text-blue-300" />
                <h3 className="text-lg font-semibold text-white">Alle Begriffe</h3>
              </div>
              <button onClick={() => setShowGlossary(false)} className="p-2 hover:bg-white/10 rounded-lg">
                <X className="w-5 h-5 text-white/70" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6">
              <div className="space-y-4">
                {WORKFLOW_NODES.map((node) => (
                  node.glossaryTerms.length > 0 && (
                    <div key={node.id}>
                      <h4 className="text-sm font-semibold text-white/60 mb-2 flex items-center gap-2">
                        <node.icon className="w-4 h-4" />
                        {node.title}
                      </h4>
                      <div className="space-y-2">
                        {node.glossaryTerms.map((term, idx) => (
                          <div key={idx} className="p-4 bg-white/5 border border-white/10 rounded-lg">
                            <h5 className="font-semibold text-blue-300">{term.term}</h5>
                            <p className="text-sm text-white/80 mt-1">{term.definition}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/10">
              <button
                onClick={() => setShowGlossary(false)}
                className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-lg transition-colors font-medium"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
