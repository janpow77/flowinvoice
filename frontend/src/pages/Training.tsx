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
  Database,
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

  /* Binary Pulse - verstärkt */
  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 0.9; transform: scale(1.02); }
  }

  @keyframes binaryPulseSlow {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 0.6; }
  }

  @keyframes binaryPulseFast {
    0%, 100% { opacity: 0.4; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.03); }
  }

  .binary-pulse {
    animation: binaryPulse 2s ease-in-out infinite;
  }

  .binary-pulse-slow {
    animation: binaryPulseSlow 4s ease-in-out infinite;
  }

  .binary-pulse-fast {
    animation: binaryPulseFast 1.5s ease-in-out infinite;
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
  title: { de: string; en: string }
  shortTitle: { de: string; en: string }
  description: { de: string; en: string }
  icon: React.ComponentType<{ className?: string }>
  color: string
  colorRgb: string
  details: { de: string; en: string }[]
  glossaryTerms: { term: { de: string; en: string }; definition: { de: string; en: string } }[]
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

// Workflow-Knoten mit Glossar-Begriffen und RGB-Farben für Glow-Effekte (DE/EN)
const WORKFLOW_NODES: WorkflowNode[] = [
  {
    id: 'project',
    title: { de: 'Projekt anlegen', en: 'Create Project' },
    shortTitle: { de: 'Projekt', en: 'Project' },
    description: { de: 'Förderprojekt mit Begünstigten erstellen', en: 'Create funding project with beneficiary' },
    icon: FolderPlus,
    color: 'from-blue-400 to-blue-600',
    colorRgb: '96, 165, 250',
    details: [
      { de: 'Projekttitel', en: 'Project Title' },
      { de: 'Aktenzeichen', en: 'File Reference' },
      { de: 'Förderzeitraum', en: 'Funding Period' },
      { de: 'Begünstigter', en: 'Beneficiary' },
      { de: 'Regelwerk', en: 'Ruleset' },
    ],
    glossaryTerms: [
      { term: { de: 'Begünstigter', en: 'Beneficiary' }, definition: { de: 'Der Zuwendungsempfänger des Fördervorhabens, dessen Ausgaben geprüft werden.', en: 'The grant recipient of the funded project whose expenses are being audited.' } },
      { term: { de: 'Förderzeitraum', en: 'Funding Period' }, definition: { de: 'Der Zeitraum, in dem förderfähige Ausgaben entstehen dürfen.', en: 'The period during which eligible expenses may be incurred.' } },
      { term: { de: 'Regelwerk', en: 'Ruleset' }, definition: { de: 'Die rechtlichen und förderrechtlichen Vorgaben, nach denen die Prüfung erfolgt.', en: 'The legal and funding regulations according to which the audit is conducted.' } },
    ],
  },
  {
    id: 'upload',
    title: { de: 'Upload der Unterlagen', en: 'Upload Documents' },
    shortTitle: { de: 'Upload', en: 'Upload' },
    description: { de: 'Prüfrelevante Unterlagen hochladen', en: 'Upload audit-relevant documents' },
    icon: Upload,
    color: 'from-green-400 to-green-600',
    colorRgb: '74, 222, 128',
    details: [
      { de: 'PDF-Upload', en: 'PDF Upload' },
      { de: 'Originaldokumente', en: 'Original Documents' },
      { de: 'Batch-Upload', en: 'Batch Upload' },
      { de: 'Vollständigkeit', en: 'Completeness' },
    ],
    glossaryTerms: [
      { term: { de: 'Originaldokumente', en: 'Original Documents' }, definition: { de: 'Vom Begünstigten vorgelegte Unterlagen, z.B. Rechnungen, Kontoauszüge oder Vergabeunterlagen.', en: 'Documents submitted by the beneficiary, e.g., invoices, bank statements, or procurement documents.' } },
      { term: { de: 'Vollständigkeit', en: 'Completeness' }, definition: { de: 'Alle für die Prüfung erforderlichen Unterlagen liegen vor.', en: 'All documents required for the audit are available.' } },
    ],
  },
  {
    id: 'chunking',
    title: { de: 'Vorverarbeitung', en: 'Preprocessing' },
    shortTitle: { de: 'Chunking', en: 'Chunking' },
    description: { de: 'Dokumente technisch aufbereiten', en: 'Technically prepare documents' },
    icon: Scissors,
    color: 'from-purple-400 to-purple-600',
    colorRgb: '192, 132, 252',
    details: [
      { de: 'Text-Extraktion', en: 'Text Extraction' },
      { de: 'Token-Chunking', en: 'Token Chunking' },
      { de: 'Embeddings', en: 'Embeddings' },
      { de: 'Chunk-Overlap', en: 'Chunk Overlap' },
    ],
    glossaryTerms: [
      { term: { de: 'Chunk', en: 'Chunk' }, definition: { de: 'Ein in sich geschlossener Textabschnitt eines Dokuments, der gezielt geprüft werden kann.', en: 'A self-contained text section of a document that can be specifically audited.' } },
      { term: { de: 'Überlappung', en: 'Overlap' }, definition: { de: 'Chunks können sich überlappen, damit zusammenhängende Informationen nicht getrennt bewertet werden.', en: 'Chunks can overlap so that related information is not evaluated separately.' } },
      { term: { de: 'Embedding', en: 'Embedding' }, definition: { de: 'Ermöglicht den inhaltlichen Vergleich von Texten, unabhängig von Wortlaut oder Reihenfolge.', en: 'Enables content comparison of texts, regardless of wording or order.' } },
      { term: { de: 'Token', en: 'Token' }, definition: { de: 'Die kleinste Verarbeitungseinheit für die KI-Analyse.', en: 'The smallest processing unit for AI analysis.' } },
    ],
  },
  {
    id: 'ruleset',
    title: { de: 'Regelwerk', en: 'Ruleset' },
    shortTitle: { de: 'Regeln', en: 'Rules' },
    description: { de: 'Rechtliche Vorgaben anwenden', en: 'Apply legal requirements' },
    icon: BookOpen,
    color: 'from-orange-400 to-orange-600',
    colorRgb: '251, 146, 60',
    details: [
      { de: 'Pflichtangaben', en: 'Mandatory Info' },
      { de: 'Kleinbetragsrechnung', en: 'Small Invoice' },
      { de: 'Reverse-Charge', en: 'Reverse Charge' },
      { de: '§14 UStG', en: '§14 UStG' },
    ],
    glossaryTerms: [
      { term: { de: 'Pflichtangaben', en: 'Mandatory Information' }, definition: { de: 'Gesetzlich vorgeschriebene Angaben auf Rechnungen, z.B. nach §14 UStG.', en: 'Legally required information on invoices, e.g., according to §14 UStG.' } },
      { term: { de: 'Kleinbetragsrechnung', en: 'Small Amount Invoice' }, definition: { de: 'Rechnung mit vereinfachten Pflichtangaben bei einem Gesamtbetrag bis 250€.', en: 'Invoice with simplified mandatory information for a total amount up to €250.' } },
      { term: { de: 'Reverse-Charge', en: 'Reverse Charge' }, definition: { de: 'Verfahren, bei dem die Umsatzsteuer vom Leistungsempfänger geschuldet wird.', en: 'Procedure where VAT is owed by the service recipient.' } },
    ],
  },
  {
    id: 'llm',
    title: { de: 'KI-Analyse', en: 'AI Analysis' },
    shortTitle: { de: 'LLM', en: 'LLM' },
    description: { de: 'Strukturierte Dokumentenanalyse', en: 'Structured document analysis' },
    icon: Brain,
    color: 'from-pink-400 to-pink-600',
    colorRgb: '244, 114, 182',
    details: [
      { de: 'Lokales LLM', en: 'Local LLM' },
      { de: 'RAG-System', en: 'RAG System' },
      { de: 'Semantik-Analyse', en: 'Semantic Analysis' },
      { de: 'Konfidenz', en: 'Confidence' },
    ],
    glossaryTerms: [
      { term: { de: 'LLM', en: 'LLM' }, definition: { de: 'Das lokale Sprachmodell analysiert Dokumente direkt im System ohne externe Dienste.', en: 'The local language model analyzes documents directly in the system without external services.' } },
      { term: { de: 'RAG', en: 'RAG' }, definition: { de: 'Verfahren, bei dem das Sprachmodell auf gespeicherte Prüfinformationen zugreift und frühere bestätigte Prüfungen heranzieht.', en: 'Method where the language model accesses stored audit information and uses previous confirmed audits.' } },
      { term: { de: 'Konfidenz', en: 'Confidence' }, definition: { de: 'Maß für die Sicherheit, mit der ein Merkmal erkannt wurde. Niedrige Konfidenz = erhöhter Prüfbedarf.', en: 'Measure of certainty with which a feature was recognized. Low confidence = increased audit need.' } },
    ],
  },
  {
    id: 'checkers',
    title: { de: 'Prüfmodule', en: 'Audit Modules' },
    shortTitle: { de: 'Checker', en: 'Checker' },
    description: { de: 'Spezialisierte Validierungen', en: 'Specialized validations' },
    icon: Shield,
    color: 'from-red-400 to-red-600',
    colorRgb: '248, 113, 113',
    details: [
      { de: 'Zeitraum-Check', en: 'Period Check' },
      { de: 'Risiko-Erkennung', en: 'Risk Detection' },
      { de: 'Semantik-Prüfung', en: 'Semantic Check' },
      { de: 'Duplikat-Check', en: 'Duplicate Check' },
    ],
    glossaryTerms: [
      { term: { de: 'Zeitraum-Check', en: 'Period Check' }, definition: { de: 'Prüfung, ob Ausgaben innerhalb des förderfähigen Zeitraums angefallen sind.', en: 'Check whether expenses occurred within the eligible period.' } },
      { term: { de: 'Risiko-Erkennung', en: 'Risk Detection' }, definition: { de: 'Identifikation auffälliger Muster oder Abweichungen.', en: 'Identification of suspicious patterns or deviations.' } },
      { term: { de: 'Semantische Prüfung', en: 'Semantic Check' }, definition: { de: 'Inhaltlicher Abgleich zwischen Rechnung, Leistung und Förderzweck.', en: 'Content comparison between invoice, service, and funding purpose.' } },
    ],
  },
  {
    id: 'result',
    title: { de: 'Prüfergebnis & Korrektur', en: 'Audit Result & Correction' },
    shortTitle: { de: 'Ergebnis', en: 'Result' },
    description: { de: 'Prüfer bestätigt oder korrigiert KI-Bewertung', en: 'Auditor confirms or corrects AI assessment' },
    icon: CheckCircle,
    color: 'from-emerald-400 to-emerald-600',
    colorRgb: '52, 211, 153',
    details: [
      { de: 'Prüfer-Review', en: 'Auditor Review' },
      { de: 'Bestätigung/Korrektur', en: 'Confirm/Correct' },
      { de: 'Fehlerhinweise', en: 'Error Notes' },
      { de: 'RAG-Lernen', en: 'RAG Learning' },
    ],
    glossaryTerms: [
      { term: { de: 'Prüfer-Review', en: 'Auditor Review' }, definition: { de: 'Der Fachprüfer überprüft die KI-Bewertung und bestätigt oder korrigiert diese.', en: 'The auditor reviews the AI assessment and confirms or corrects it.' } },
      { term: { de: 'Feedback-Loop', en: 'Feedback Loop' }, definition: { de: 'Korrekturen des Prüfers fließen zurück in die Wissensbasis zur Verbesserung künftiger Analysen.', en: 'Auditor corrections flow back into the knowledge base to improve future analyses.' } },
      { term: { de: 'RAG-Lernen', en: 'RAG Learning' }, definition: { de: 'Bestätigte Bewertungen erweitern die Wissensbasis für vergleichbare Fälle.', en: 'Confirmed assessments expand the knowledge base for comparable cases.' } },
    ],
  },
  {
    id: 'export',
    title: { de: 'Prüfbericht erstellen', en: 'Generate Audit Report' },
    shortTitle: { de: 'Report', en: 'Report' },
    description: { de: 'Finale Dokumentation exportieren', en: 'Export final documentation' },
    icon: FileText,
    color: 'from-cyan-400 to-cyan-600',
    colorRgb: '34, 211, 238',
    details: [
      { de: 'Belegliste', en: 'Document List' },
      { de: 'PDF-Report', en: 'PDF Report' },
      { de: 'Excel-Export', en: 'Excel Export' },
      { de: 'Archivierung', en: 'Archiving' },
    ],
    glossaryTerms: [
      { term: { de: 'Prüfbericht', en: 'Audit Report' }, definition: { de: 'Zusammenfassende Dokumentation aller Prüfergebnisse mit Bewertungen, Hinweisen und Empfehlungen.', en: 'Summary documentation of all audit results with assessments, notes, and recommendations.' } },
      { term: { de: 'Belegliste', en: 'Document List' }, definition: { de: 'Übersicht aller geprüften Belege mit Status und Ergebnis.', en: 'Overview of all audited documents with status and result.' } },
    ],
  },
]

// Binäres Datenwasser Komponente - dicker und mehr pulsierend
const BinaryDataWater = () => (
  <div className="absolute bottom-0 left-0 right-0 h-40 overflow-hidden pointer-events-none z-10">
    <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-950/90 via-blue-900/60 to-transparent">
      <div className="data-flow-slow whitespace-nowrap font-mono text-base font-bold pt-4 binary-pulse-slow">
        <span className="text-blue-400/50">{BINARY_LINES[0]} {BINARY_LINES[0]}</span>
      </div>
      <div className="data-flow whitespace-nowrap font-mono text-base font-bold binary-pulse">
        <span className="text-cyan-400/45">{BINARY_LINES[1]} {BINARY_LINES[1]}</span>
      </div>
    </div>
    <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-blue-800/80 to-transparent">
      <div className="data-flow-fast whitespace-nowrap font-mono text-lg font-bold binary-pulse-fast">
        <span className="text-blue-300/60">{BINARY_LINES[2]} {BINARY_LINES[2]}</span>
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
  lang: 'de' | 'en'
}

const OrbitalNode = ({
  node,
  index,
  totalNodes,
  radius,
  isActive,
  isCompleted,
  onClick,
  rotationOffset,
  lang
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
          className="absolute w-28 h-28 rounded-full pulse-ring"
          style={{
            background: `radial-gradient(circle, rgba(${node.colorRgb}, 0.4) 0%, transparent 70%)`
          }}
        />
      )}

      {/* Node Circle - größer */}
      <div
        className={clsx(
          'w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300',
          'border-2 glass-panel-strong',
          isActive
            ? `bg-gradient-to-br ${node.color} border-white/40 node-glow`
            : isCompleted
            ? 'bg-emerald-500/80 border-emerald-400/60'
            : 'bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/30'
        )}
        style={{
          boxShadow: isActive
            ? `0 0 40px rgba(${node.colorRgb}, 0.5), 0 0 80px rgba(${node.colorRgb}, 0.3)`
            : isCompleted
            ? '0 0 25px rgba(52, 211, 153, 0.4)'
            : '0 4px 20px rgba(0,0,0,0.2)'
        }}
      >
        {isCompleted && !isActive ? (
          <CheckCircle className="w-9 h-9 text-white" />
        ) : (
          <Icon className="w-9 h-9 text-white" />
        )}
      </div>

      {/* Label - größer */}
      <div
        className={clsx(
          'mt-3 px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300',
          isActive
            ? 'bg-white/20 text-white backdrop-blur-sm'
            : 'text-white/80'
        )}
      >
        {node.shortTitle[lang]}
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
      {/* Outer Glow Ring - größer */}
      <div
        className="absolute -inset-12 rounded-full opacity-40"
        style={{
          background: `radial-gradient(circle, rgba(${currentNode.colorRgb}, 0.5) 0%, transparent 70%)`
        }}
      />

      {/* Progress Ring - größer */}
      <svg className="absolute -inset-6 w-[calc(100%+48px)] h-[calc(100%+48px)]" viewBox="0 0 160 160">
        <circle
          cx="80"
          cy="80"
          r="72"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="5"
        />
        <circle
          cx="80"
          cy="80"
          r="72"
          fill="none"
          stroke={`rgba(${currentNode.colorRgb}, 0.8)`}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={`${2 * Math.PI * 72}`}
          strokeDashoffset={`${2 * Math.PI * 72 * (1 - progress / 100)}`}
          transform="rotate(-90 80 80)"
          style={{ transition: 'stroke-dashoffset 0.1s linear' }}
        />
      </svg>

      {/* Core Circle - größer */}
      <div
        className={clsx(
          'w-32 h-32 rounded-full flex flex-col items-center justify-center',
          'glass-panel-strong core-pulse'
        )}
        style={{
          background: `linear-gradient(135deg, rgba(${currentNode.colorRgb}, 0.3) 0%, rgba(${currentNode.colorRgb}, 0.1) 100%)`,
          boxShadow: `0 0 50px rgba(${currentNode.colorRgb}, 0.5), 0 0 100px rgba(${currentNode.colorRgb}, 0.3), inset 0 0 40px rgba(255,255,255,0.1)`
        }}
      >
        <Icon className="w-14 h-14 text-white mb-1" />
        <span className="text-white/90 text-sm font-semibold">Flow</span>
      </div>
    </div>
  )
}

// RAG Database Visualization Component
interface RAGDatabaseProps {
  isActive: boolean
  lang: 'de' | 'en'
}

const RAGDatabase = ({ isActive, lang }: RAGDatabaseProps) => {
  return (
    <div
      className={clsx(
        'absolute z-15 transition-all duration-500',
        isActive ? 'opacity-100 scale-100' : 'opacity-60 scale-95'
      )}
      style={{
        left: 'calc(50% + 180px)',
        top: 'calc(50% - 20px)',
        transform: 'translate(-50%, -50%)'
      }}
    >
      {/* RAG Database Container */}
      <div className="relative">
        {/* Glow effect when active */}
        {isActive && (
          <div
            className="absolute -inset-4 rounded-2xl opacity-50 animate-pulse"
            style={{
              background: 'radial-gradient(circle, rgba(244, 114, 182, 0.4) 0%, transparent 70%)'
            }}
          />
        )}

        {/* Database Icon Container */}
        <div
          className={clsx(
            'w-16 h-20 rounded-xl flex flex-col items-center justify-center glass-panel-strong border-2 transition-all duration-300',
            isActive
              ? 'border-pink-400/60 bg-pink-500/20'
              : 'border-white/20 bg-white/5'
          )}
          style={{
            boxShadow: isActive
              ? '0 0 30px rgba(244, 114, 182, 0.4), 0 0 60px rgba(244, 114, 182, 0.2)'
              : '0 4px 20px rgba(0,0,0,0.2)'
          }}
        >
          <Database className={clsx('w-8 h-8', isActive ? 'text-pink-300' : 'text-white/70')} />
          <span className="text-xs font-semibold text-white/80 mt-1">RAG</span>
        </div>

        {/* Input Arrow (data coming in - learning) */}
        <div className="absolute -left-16 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <span className="text-xs text-cyan-300/80 font-medium whitespace-nowrap">
            {lang === 'de' ? 'Lernen' : 'Learn'}
          </span>
          <svg width="40" height="20" className="overflow-visible">
            <defs>
              <linearGradient id="arrowGradientIn" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(34, 211, 238, 0.3)" />
                <stop offset="100%" stopColor="rgba(34, 211, 238, 0.8)" />
              </linearGradient>
            </defs>
            <path
              d="M 0 10 L 30 10"
              stroke="url(#arrowGradientIn)"
              strokeWidth="2"
              fill="none"
              className={isActive ? 'connector-flow' : ''}
            />
            <polygon
              points="30,5 40,10 30,15"
              fill="rgba(34, 211, 238, 0.8)"
            />
          </svg>
        </div>

        {/* Output Arrow (data going out - retrieval) */}
        <div className="absolute -right-16 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <svg width="40" height="20" className="overflow-visible">
            <defs>
              <linearGradient id="arrowGradientOut" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(52, 211, 153, 0.8)" />
                <stop offset="100%" stopColor="rgba(52, 211, 153, 0.3)" />
              </linearGradient>
            </defs>
            <path
              d="M 10 10 L 40 10"
              stroke="url(#arrowGradientOut)"
              strokeWidth="2"
              fill="none"
              className={isActive ? 'connector-flow' : ''}
            />
            <polygon
              points="0,5 10,10 0,15"
              fill="rgba(52, 211, 153, 0.8)"
              transform="rotate(180 5 10)"
            />
          </svg>
          <span className="text-xs text-emerald-300/80 font-medium whitespace-nowrap">
            {lang === 'de' ? 'Abrufen' : 'Retrieve'}
          </span>
        </div>

        {/* Label */}
        <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
          <span className="text-xs text-white/60 font-medium">
            {lang === 'de' ? 'Wissensbasis' : 'Knowledge Base'}
          </span>
        </div>
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
  const lang = (i18n.language === 'de' ? 'de' : 'en') as 'de' | 'en'

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
  const ORBIT_RADIUS = 400 // Radius der Umlaufbahn (maximiert für großen Kreis)

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
                {lang === 'de' ? 'Musterprojekt' : 'Sample Project'}
              </button>

              <button
                onClick={() => setShowGlossary(true)}
                className="flex items-center gap-2 px-4 py-2 glass-panel text-white rounded-lg hover:bg-white/20 transition-colors text-sm"
              >
                <Info className="w-4 h-4" />
                {lang === 'de' ? 'Glossar' : 'Glossary'}
              </button>
            </div>
          </div>
        </div>

        {/* Hauptbereich: Links Panel | Orbital | Rechts Panel */}
        <div className="flex flex-col xl:flex-row gap-4 items-start justify-between max-w-[1600px] mx-auto">

          {/* Linkes Panel - Schritt-Details - ganz links */}
          <div className="w-full xl:w-72 flex-shrink-0 order-2 xl:order-1 xl:self-center">
            <div className="glass-panel-strong rounded-2xl p-5 animate-slide-in" key={currentStep}>
              <div className="flex items-center gap-3 mb-4">
                <div className={clsx('w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center', currentNode.color)}>
                  <currentNode.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">{currentStep + 1}. {currentNode.title[lang]}</h2>
                  <p className="text-blue-200 text-sm">{currentNode.description[lang]}</p>
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
                    <span className="text-white text-sm">{detail[lang]}</span>
                  </div>
                ))}
              </div>

              {/* Regelwerk-Info bei Schritt 4 */}
              {currentNode.id === 'ruleset' && (
                <div className="mt-4 p-3 bg-orange-500/20 border border-orange-400/30 rounded-xl">
                  <h4 className="font-semibold text-orange-300 text-sm mb-1">
                    {lang === 'de' ? 'Ausgewähltes Regelwerk' : 'Selected Ruleset'}
                  </h4>
                  <p className="text-white text-sm">{selectedRuleset.title}</p>
                  <p className="text-orange-200/80 text-xs mt-1">
                    {selectedRuleset.featuresCount} {lang === 'de' ? 'Pflichtmerkmale' : 'mandatory fields'}
                  </p>
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

              {/* RAG Database - shows for LLM and Result/Feedback steps */}
              <RAGDatabase
                isActive={currentStep === 4 || currentStep === 6}
                lang={lang}
              />

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
                  lang={lang}
                />
              ))}
            </div>
          </div>

          {/* Rechtes Panel - Glossar/Begriffe - ganz rechts */}
          <div className="w-full xl:w-72 flex-shrink-0 order-3 xl:self-center">
            <div className="glass-panel-strong rounded-2xl p-5 h-full">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-300" />
                <h3 className="font-semibold text-white text-base">
                  {lang === 'de' ? 'Begriffe' : 'Terms'}
                </h3>
              </div>

              {currentNode.glossaryTerms.length > 0 ? (
                <div className="space-y-3">
                  {currentNode.glossaryTerms.map((term, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white/5 rounded-xl border border-white/10 animate-slide-in"
                      style={{ animationDelay: `${idx * 150}ms` }}
                    >
                      <h4 className="font-semibold text-blue-300 text-sm mb-1">{term.term[lang]}</h4>
                      <p className="text-xs text-white/90 leading-relaxed">{term.definition[lang]}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-white/50 text-sm">
                  {lang === 'de' ? 'Keine speziellen Begriffe.' : 'No special terms.'}
                </p>
              )}

              {/* Musterprojekt-Kurzinfo */}
              <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <FolderPlus className="w-4 h-4 text-blue-300" />
                  <span className="text-xs font-medium text-white">
                    {lang === 'de' ? 'Beispiel-Projekt' : 'Sample Project'}
                  </span>
                </div>
                <p className="text-xs text-white/80">{SAMPLE_PROJECT.title}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Steuerung - unten */}
        <div className="flex items-center justify-center gap-4 mt-6">
          <button
            onClick={handleReset}
            className="p-3 glass-panel rounded-full hover:bg-white/20 transition-colors"
            title={lang === 'de' ? 'Zurücksetzen' : 'Reset'}
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
                {lang === 'de' ? 'Pause' : 'Pause'}
              </>
            ) : (
              <>
                <Play className="w-6 h-6" />
                {currentStep === 0
                  ? (lang === 'de' ? 'Animation starten' : 'Start Animation')
                  : (lang === 'de' ? 'Fortsetzen' : 'Continue')
                }
              </>
            )}
          </button>

          <div className="text-white/70 text-sm flex items-center gap-2">
            <Zap className="w-4 h-4" />
            {lang === 'de' ? 'Schritt' : 'Step'} {currentStep + 1} / {WORKFLOW_NODES.length}
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
                <h3 className="text-lg font-semibold text-white">
                  {lang === 'de' ? 'Musterprojekt' : 'Sample Project'}
                </h3>
              </div>
              <button onClick={() => setShowSampleProject(false)} className="p-2 hover:bg-white/10 rounded-lg">
                <X className="w-5 h-5 text-white/70" />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6 space-y-6">
              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold text-white mb-3">
                  {lang === 'de' ? 'Projektdaten' : 'Project Data'}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Titel' : 'Title'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.title}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Aktenzeichen' : 'File Reference'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.fileReference}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Zeitraum' : 'Period'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.period.start} – {SAMPLE_PROJECT.period.end}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Ort' : 'Location'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.location}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <h4 className="font-semibold text-white mb-3">{lang === 'de' ? 'Begünstigter' : 'Beneficiary'}</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Name' : 'Name'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'USt-IdNr.' : 'VAT ID'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.vatId}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Adresse' : 'Address'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.address}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Euro className="w-4 h-4 text-blue-300" />
                    <div>
                      <p className="text-blue-200/60 text-xs">{lang === 'de' ? 'Vorsteuerabzug' : 'Input Tax Deductible'}</p>
                      <p className="text-white">{SAMPLE_PROJECT.beneficiary.inputTaxDeductible ? (lang === 'de' ? 'Ja' : 'Yes') : (lang === 'de' ? 'Nein' : 'No')}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-3">{lang === 'de' ? 'Beispiel-Rechnungen' : 'Sample Invoices'}</h4>
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
                {lang === 'de' ? 'Schließen' : 'Close'}
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
                <h3 className="text-lg font-semibold text-white">
                  {lang === 'de' ? 'Alle Begriffe' : 'All Terms'}
                </h3>
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
                        {node.title[lang]}
                      </h4>
                      <div className="space-y-2">
                        {node.glossaryTerms.map((term, idx) => (
                          <div key={idx} className="p-4 bg-white/5 border border-white/10 rounded-lg">
                            <h5 className="font-semibold text-blue-300">{term.term[lang]}</h5>
                            <p className="text-sm text-white/80 mt-1">{term.definition[lang]}</p>
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
                {lang === 'de' ? 'Schließen' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
