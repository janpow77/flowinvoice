import { useState, useEffect, useCallback, useMemo } from 'react'
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
  Zap,
} from 'lucide-react'
import clsx from 'clsx'

// --- CSS Animationen für 3D Orbital Infografik ---
const cssAnimations = `
  /* Orbital Rotation */
  @keyframes orbitRotate {
    from { transform: rotateZ(0deg); }
    to { transform: rotateZ(360deg); }
  }

  @keyframes orbitRotateSlow {
    from { transform: rotateZ(0deg); }
    to { transform: rotateZ(-360deg); }
  }

  /* Core Pulsing */
  @keyframes corePulse {
    0%, 100% {
      transform: scale(1);
      box-shadow: 0 0 40px rgba(96, 165, 250, 0.4), 0 0 80px rgba(96, 165, 250, 0.2);
    }
    50% {
      transform: scale(1.05);
      box-shadow: 0 0 60px rgba(96, 165, 250, 0.6), 0 0 120px rgba(96, 165, 250, 0.3);
    }
  }

  .core-pulse {
    animation: corePulse 3s ease-in-out infinite;
  }

  /* Node Glow */
  @keyframes nodeGlow {
    0%, 100% {
      box-shadow: 0 0 20px rgba(96, 165, 250, 0.3);
      filter: brightness(1);
    }
    50% {
      box-shadow: 0 0 40px rgba(96, 165, 250, 0.6);
      filter: brightness(1.1);
    }
  }

  .node-glow {
    animation: nodeGlow 2s ease-in-out infinite;
  }

  /* Data Flow Animation */
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

  /* Binary Pulse */
  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.7; }
  }

  .binary-pulse {
    animation: binaryPulse 3s ease-in-out infinite;
  }

  /* Fish Swim */
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

  /* Connector Flow */
  @keyframes connectorFlow {
    0% { stroke-dashoffset: 20; }
    100% { stroke-dashoffset: 0; }
  }

  .connector-flow {
    stroke-dasharray: 10, 5;
    animation: connectorFlow 1s linear infinite;
  }

  /* Float Animation */
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  .animate-float {
    animation: float 3s ease-in-out infinite;
  }

  /* Slide In */
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .animate-slide-in {
    animation: slideIn 0.5s ease-out forwards;
  }

  /* Pulse Ring */
  @keyframes pulseRing {
    0% { transform: scale(1); opacity: 1; }
    100% { transform: scale(2); opacity: 0; }
  }

  .pulse-ring {
    animation: pulseRing 2s ease-out infinite;
  }

  /* Particle Float */
  @keyframes particleFloat {
    0%, 100% {
      transform: translateY(0) translateX(0) scale(1);
      opacity: 0.6;
    }
    25% {
      transform: translateY(-20px) translateX(10px) scale(1.2);
      opacity: 0.8;
    }
    50% {
      transform: translateY(-40px) translateX(-5px) scale(0.8);
      opacity: 0.4;
    }
    75% {
      transform: translateY(-20px) translateX(-15px) scale(1.1);
      opacity: 0.7;
    }
  }

  /* Zoom Focus */
  @keyframes zoomFocus {
    from { transform: scale(1); }
    to { transform: scale(1.15); }
  }

  /* 3D Perspective Container */
  .perspective-container {
    perspective: 1200px;
    transform-style: preserve-3d;
  }

  .orbital-stage {
    transform-style: preserve-3d;
    transform: rotateX(20deg);
  }

  /* Glassmorphism */
  .glass-panel {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .glass-panel-strong {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.2);
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
  colorRgb: string
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

// Workflow-Knoten mit Glossar-Begriffen und RGB-Farben für Glow-Effekte
const WORKFLOW_NODES: WorkflowNode[] = [
  {
    id: 'project',
    title: 'Projekt anlegen',
    shortTitle: 'Projekt',
    description: 'Förderprojekt mit Begünstigten erstellen',
    icon: FolderPlus,
    color: 'from-blue-400 to-blue-600',
    colorRgb: '96, 165, 250',
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
    colorRgb: '74, 222, 128',
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
    colorRgb: '192, 132, 252',
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
    colorRgb: '251, 146, 60',
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
    colorRgb: '244, 114, 182',
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
    colorRgb: '248, 113, 113',
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
    colorRgb: '52, 211, 153',
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
    colorRgb: '34, 211, 238',
    details: ['Belegliste', 'PDF-Report', 'Excel-Export', 'Archivierung'],
    glossaryTerms: [
      { term: 'Prüfbericht', definition: 'Dokumentation aller Prüfergebnisse als PDF oder Excel.' },
    ],
  },
]

// Binäres Datenwasser Komponente
const BinaryDataWater = () => (
  <div className="absolute bottom-0 left-0 right-0 h-32 overflow-hidden pointer-events-none z-10">
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

// SVG Bezier Connectors zwischen Nodes
interface ConnectorProps {
  fromAngle: number
  toAngle: number
  radius: number
  isActive: boolean
  color: string
}

const OrbitalConnector = ({ fromAngle, toAngle, radius, isActive, color }: ConnectorProps) => {
  const fromRad = (fromAngle * Math.PI) / 180
  const toRad = (toAngle * Math.PI) / 180

  const x1 = Math.cos(fromRad) * radius
  const y1 = Math.sin(fromRad) * radius
  const x2 = Math.cos(toRad) * radius
  const y2 = Math.sin(toRad) * radius

  // Control points for curved path
  const midAngle = (fromAngle + toAngle) / 2
  const midRad = (midAngle * Math.PI) / 180
  const controlRadius = radius * 0.7
  const cx = Math.cos(midRad) * controlRadius
  const cy = Math.sin(midRad) * controlRadius

  return (
    <path
      d={`M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`}
      fill="none"
      stroke={isActive ? color : 'rgba(255,255,255,0.15)'}
      strokeWidth={isActive ? 3 : 1.5}
      className={isActive ? 'connector-flow' : ''}
      style={{
        filter: isActive ? `drop-shadow(0 0 8px ${color})` : 'none',
        transition: 'all 0.5s ease'
      }}
    />
  )
}

// Orbital Node Component
interface OrbitalNodeProps {
  node: WorkflowNode
  index: number
  totalNodes: number
  radius: number
  isActive: boolean
  isCompleted: boolean
  onClick: () => void
  rotationOffset: number
}

const OrbitalNode = ({
  node,
  index,
  totalNodes,
  radius,
  isActive,
  isCompleted,
  onClick,
  rotationOffset
}: OrbitalNodeProps) => {
  const baseAngle = (360 / totalNodes) * index - 90 // Start from top
  const angle = baseAngle + rotationOffset
  const angleRad = (angle * Math.PI) / 180

  const x = Math.cos(angleRad) * radius
  const y = Math.sin(angleRad) * radius

  const Icon = node.icon

  return (
    <div
      className={clsx(
        'absolute flex flex-col items-center cursor-pointer transition-all duration-500',
        isActive && 'z-30'
      )}
      style={{
        left: `calc(50% + ${x}px)`,
        top: `calc(50% + ${y}px)`,
        transform: `translate(-50%, -50%) ${isActive ? 'scale(1.2)' : 'scale(1)'}`,
      }}
      onClick={onClick}
    >
      {/* Pulse Ring for Active Node */}
      {isActive && (
        <div
          className="absolute w-20 h-20 rounded-full pulse-ring"
          style={{
            background: `radial-gradient(circle, rgba(${node.colorRgb}, 0.4) 0%, transparent 70%)`
          }}
        />
      )}

      {/* Node Circle */}
      <div
        className={clsx(
          'w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300',
          'border-2 glass-panel-strong',
          isActive
            ? `bg-gradient-to-br ${node.color} border-white/40 node-glow`
            : isCompleted
            ? 'bg-emerald-500/80 border-emerald-400/60'
            : 'bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/30'
        )}
        style={{
          boxShadow: isActive
            ? `0 0 30px rgba(${node.colorRgb}, 0.5), 0 0 60px rgba(${node.colorRgb}, 0.3)`
            : isCompleted
            ? '0 0 20px rgba(52, 211, 153, 0.4)'
            : '0 4px 20px rgba(0,0,0,0.2)'
        }}
      >
        {isCompleted && !isActive ? (
          <CheckCircle className="w-7 h-7 text-white" />
        ) : (
          <Icon className="w-7 h-7 text-white" />
        )}
      </div>

      {/* Label */}
      <div
        className={clsx(
          'mt-2 px-3 py-1 rounded-lg text-xs font-medium transition-all duration-300',
          isActive
            ? 'bg-white/20 text-white backdrop-blur-sm'
            : 'text-white/70'
        )}
      >
        {node.shortTitle}
      </div>
    </div>
  )
}

// Central Core Component
interface CentralCoreProps {
  currentNode: WorkflowNode
  progress: number
}

const CentralCore = ({ currentNode, progress }: CentralCoreProps) => {
  const Icon = currentNode.icon

  return (
    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
      {/* Outer Glow Ring */}
      <div
        className="absolute -inset-8 rounded-full opacity-30"
        style={{
          background: `radial-gradient(circle, rgba(${currentNode.colorRgb}, 0.4) 0%, transparent 70%)`
        }}
      />

      {/* Progress Ring */}
      <svg className="absolute -inset-4 w-[calc(100%+32px)] h-[calc(100%+32px)]" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="4"
        />
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke={`rgba(${currentNode.colorRgb}, 0.8)`}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={`${2 * Math.PI * 54}`}
          strokeDashoffset={`${2 * Math.PI * 54 * (1 - progress / 100)}`}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 0.1s linear' }}
        />
      </svg>

      {/* Core Circle */}
      <div
        className={clsx(
          'w-24 h-24 rounded-full flex flex-col items-center justify-center',
          'glass-panel-strong core-pulse'
        )}
        style={{
          background: `linear-gradient(135deg, rgba(${currentNode.colorRgb}, 0.3) 0%, rgba(${currentNode.colorRgb}, 0.1) 100%)`,
          boxShadow: `0 0 40px rgba(${currentNode.colorRgb}, 0.4), 0 0 80px rgba(${currentNode.colorRgb}, 0.2), inset 0 0 30px rgba(255,255,255,0.1)`
        }}
      >
        <Icon className="w-10 h-10 text-white mb-1" />
        <span className="text-white/80 text-xs font-medium">Flow</span>
      </div>
    </div>
  )
}

// Floating Particles
const FloatingParticles = () => {
  const particles = useMemo(() =>
    Array.from({ length: 12 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 2 + Math.random() * 4,
      delay: Math.random() * 5,
      duration: 4 + Math.random() * 4
    })), []
  )

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map(p => (
        <div
          key={p.id}
          className="absolute rounded-full bg-blue-300/30"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            animation: `particleFloat ${p.duration}s ease-in-out infinite`,
            animationDelay: `${p.delay}s`
          }}
        />
      ))}
    </div>
  )
}

export default function Training() {
  const { i18n } = useTranslation()
  const lang = i18n.language

  const [selectedRulesetId, setSelectedRulesetId] = useState<string>('DE_USTG')
  const [currentStep, setCurrentStep] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [showGlossary, setShowGlossary] = useState(false)
  const [showSampleProject, setShowSampleProject] = useState(false)
  const [progress, setProgress] = useState<number>(0)
  const [rotationOffset, setRotationOffset] = useState<number>(0)

  const selectedRuleset = DEMO_RULESETS.find(r => r.id === selectedRulesetId) || DEMO_RULESETS[0]
  const currentNode = WORKFLOW_NODES[currentStep]

  const STEP_DURATION = 5000 // 5 Sekunden pro Schritt
  const ORBIT_RADIUS = 280 // Radius der Umlaufbahn (größer da Panels seitlich)

  // Auto-Animation mit Orbital-Rotation
  useEffect(() => {
    if (!isPlaying) return

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
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

      // Sanfte Orbital-Rotation während Animation
      setRotationOffset(prev => (prev + 0.2) % 360)
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
    setRotationOffset(0)
  }, [])

  const handleStepClick = useCallback((index: number) => {
    setCurrentStep(index)
    setIsPlaying(false)
    setProgress(0)
  }, [])

  // Berechne Winkel für Connectors
  const getNodeAngle = (index: number) => {
    return (360 / WORKFLOW_NODES.length) * index - 90
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 relative overflow-hidden">
      <style>{cssAnimations}</style>

      {/* Floating Particles */}
      <FloatingParticles />

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
        <div className="flex items-center justify-between flex-wrap gap-4 mb-4">
          {/* Linke Seite: Logo, Titel und Auswahlfelder */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="p-3 glass-panel rounded-xl">
              <img src="/auditlogo.png" alt="FlowAudit" className="w-10 h-10 object-contain" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white drop-shadow-lg">
                {lang === 'de' ? 'Interaktive Schulung' : 'Interactive Training'}
              </h1>
              <p className="text-blue-200 text-sm">
                {lang === 'de' ? '3D Workflow-Visualisierung' : '3D Workflow Visualization'}
              </p>
            </div>

            {/* Auswahlfelder - jetzt links */}
            <div className="flex items-center gap-3 ml-4">
              <select
                value={selectedRulesetId}
                onChange={(e) => setSelectedRulesetId(e.target.value)}
                className="px-4 py-2 glass-panel rounded-lg text-white text-sm focus:ring-2 focus:ring-blue-300"
              >
                {DEMO_RULESETS.map((rs) => (
                  <option key={rs.id} value={rs.id} className="bg-blue-900 text-white">{rs.titleShort}</option>
                ))}
              </select>

              <button
                onClick={() => setShowSampleProject(true)}
                className="flex items-center gap-2 px-4 py-2 glass-panel text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
              >
                <FolderPlus className="w-4 h-4" />
                Musterprojekt
              </button>

              <button
                onClick={() => setShowGlossary(true)}
                className="flex items-center gap-2 px-4 py-2 glass-panel text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
              >
                <Info className="w-4 h-4" />
                Glossar
              </button>
            </div>
          </div>
        </div>

        {/* Steuerung */}
        <div className="flex items-center justify-center gap-4 mb-4">
          <button
            onClick={handleReset}
            className="p-3 glass-panel rounded-full hover:bg-white/20 transition-colors"
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

          <div className="text-white/70 text-sm flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Schritt {currentStep + 1} / {WORKFLOW_NODES.length}
          </div>
        </div>

        {/* Hauptbereich: Links Panel | Orbital | Rechts Panel */}
        <div className="flex flex-col xl:flex-row gap-6 items-start justify-center">

          {/* Linkes Panel - Schritt-Details */}
          <div className="w-full xl:w-80 flex-shrink-0 order-2 xl:order-1">
            <div className="glass-panel-strong rounded-2xl p-5 animate-slide-in" key={currentStep}>
              <div className="flex items-center gap-3 mb-4">
                <div className={clsx('w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center', currentNode.color)}>
                  <currentNode.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">{currentStep + 1}. {currentNode.title}</h2>
                  <p className="text-blue-200 text-sm">{currentNode.description}</p>
                </div>
              </div>

              {/* Details des Schritts */}
              <div className="space-y-2">
                {currentNode.details.map((detail, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 p-2 bg-white/5 rounded-lg border border-white/10 animate-slide-in"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-white text-sm">{detail}</span>
                  </div>
                ))}
              </div>

              {/* Regelwerk-Info bei Schritt 4 */}
              {currentNode.id === 'ruleset' && (
                <div className="mt-4 p-3 bg-orange-500/20 border border-orange-400/30 rounded-xl">
                  <h4 className="font-semibold text-orange-300 text-sm mb-1">Ausgewähltes Regelwerk</h4>
                  <p className="text-white text-sm">{selectedRuleset.title}</p>
                  <p className="text-orange-200/80 text-xs mt-1">{selectedRuleset.featuresCount} Pflichtmerkmale</p>
                </div>
              )}
            </div>
          </div>

          {/* 3D Orbital Infographic - Mitte */}
          <div className="perspective-container flex-shrink-0 order-1 xl:order-2">
            <div
              className="orbital-stage relative"
              style={{
                width: ORBIT_RADIUS * 2 + 160,
                height: ORBIT_RADIUS * 2 + 160
              }}
            >
              {/* SVG Connectors Layer */}
              <svg
                className="absolute inset-0 w-full h-full pointer-events-none"
                viewBox={`${-ORBIT_RADIUS - 80} ${-ORBIT_RADIUS - 80} ${(ORBIT_RADIUS + 80) * 2} ${(ORBIT_RADIUS + 80) * 2}`}
              >
                {/* Orbital Ring */}
                <circle
                  cx="0"
                  cy="0"
                  r={ORBIT_RADIUS}
                  fill="none"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="2"
                  strokeDasharray="8, 4"
                />

                {/* Connectors between nodes */}
                {WORKFLOW_NODES.map((_, index) => {
                  const nextIndex = (index + 1) % WORKFLOW_NODES.length
                  const isActiveConnector = index === currentStep
                  return (
                    <OrbitalConnector
                      key={`connector-${index}`}
                      fromAngle={getNodeAngle(index) + rotationOffset}
                      toAngle={getNodeAngle(nextIndex) + rotationOffset}
                      radius={ORBIT_RADIUS}
                      isActive={isActiveConnector}
                      color={`rgba(${WORKFLOW_NODES[index].colorRgb}, 0.8)`}
                    />
                  )
                })}
              </svg>

              {/* Central Core */}
              <CentralCore currentNode={currentNode} progress={progress} />

              {/* Orbital Nodes */}
              {WORKFLOW_NODES.map((node, index) => (
                <OrbitalNode
                  key={node.id}
                  node={node}
                  index={index}
                  totalNodes={WORKFLOW_NODES.length}
                  radius={ORBIT_RADIUS}
                  isActive={index === currentStep}
                  isCompleted={index < currentStep}
                  onClick={() => handleStepClick(index)}
                  rotationOffset={rotationOffset}
                />
              ))}
            </div>
          </div>

          {/* Rechtes Panel - Glossar/Begriffe */}
          <div className="w-full xl:w-80 flex-shrink-0 order-3">
            <div className="glass-panel-strong rounded-2xl p-5 h-full">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-300" />
                <h3 className="font-semibold text-white text-base">Begriffe</h3>
              </div>

              {currentNode.glossaryTerms.length > 0 ? (
                <div className="space-y-3">
                  {currentNode.glossaryTerms.map((term, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white/5 rounded-xl border border-white/10 animate-slide-in"
                      style={{ animationDelay: `${idx * 150}ms` }}
                    >
                      <h4 className="font-semibold text-blue-300 text-sm mb-1">{term.term}</h4>
                      <p className="text-xs text-white/90 leading-relaxed">{term.definition}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-white/50 text-sm">Keine speziellen Begriffe.</p>
              )}

              {/* Musterprojekt-Kurzinfo */}
              <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <FolderPlus className="w-4 h-4 text-blue-300" />
                  <span className="text-xs font-medium text-white">Beispiel-Projekt</span>
                </div>
                <p className="text-xs text-white/80">{SAMPLE_PROJECT.title}</p>
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
