/**
 * Settings Types - Typen für Admin-Einstellungen
 *
 * Dokumenttypen, Profile und Modellkonfiguration.
 */

// ============================================================
// Document Types (Dokumenttypen)
// ============================================================

export interface DocumentTypeConfig {
  id: string
  name: string
  slug: string
  description: string
  icon?: string
  isSystem: boolean // true = kann nicht gelöscht werden
  chunkingDefaults: ChunkingConfig
  createdAt: string
  updatedAt?: string
}

export interface ChunkingConfig {
  chunkSizeTokens: number
  chunkOverlapTokens: number
  maxChunks: number
  chunkStrategy: 'fixed' | 'semantic' | 'paragraph'
}

// Standard-Dokumenttypen
export const DEFAULT_DOCUMENT_TYPES: DocumentTypeConfig[] = [
  {
    id: 'invoice',
    name: 'Rechnung',
    slug: 'invoice',
    description: 'Rechnungen und Belege für die Prüfung nach Regelwerk',
    icon: 'receipt',
    isSystem: true,
    chunkingDefaults: {
      chunkSizeTokens: 700,
      chunkOverlapTokens: 120,
      maxChunks: 6,
      chunkStrategy: 'fixed',
    },
    createdAt: new Date().toISOString(),
  },
  {
    id: 'bank_statement',
    name: 'Kontoauszug',
    slug: 'bank-statement',
    description: 'Bankauszüge und Kontonachweise',
    icon: 'landmark',
    isSystem: true,
    chunkingDefaults: {
      chunkSizeTokens: 900,
      chunkOverlapTokens: 150,
      maxChunks: 6,
      chunkStrategy: 'fixed',
    },
    createdAt: new Date().toISOString(),
  },
  {
    id: 'procurement',
    name: 'Vergabeunterlagen',
    slug: 'procurement',
    description: 'Vergabedokumentation und Ausschreibungsunterlagen',
    icon: 'file-text',
    isSystem: true,
    chunkingDefaults: {
      chunkSizeTokens: 1100,
      chunkOverlapTokens: 180,
      maxChunks: 8,
      chunkStrategy: 'fixed',
    },
    createdAt: new Date().toISOString(),
  },
  {
    id: 'other',
    name: 'Sonstiges',
    slug: 'other',
    description: 'Sonstige Dokumente ohne spezifische Kategorie',
    icon: 'file',
    isSystem: true,
    chunkingDefaults: {
      chunkSizeTokens: 900,
      chunkOverlapTokens: 150,
      maxChunks: 6,
      chunkStrategy: 'fixed',
    },
    createdAt: new Date().toISOString(),
  },
]

// ============================================================
// Models (Modelle)
// ============================================================

export interface ModelConfig {
  id: string
  name: string
  provider: 'ollama' | 'openai' | 'anthropic' | 'gemini'
  isActive: boolean
  description: string
  recommendation?: string
  hardwareHint?: string
  defaultNumCtx: number
  speedRating: 'fast' | 'medium' | 'slow'
}

export const DEFAULT_MODELS: ModelConfig[] = [
  {
    id: 'llama3.1:8b',
    name: 'Llama 3.1 8B',
    provider: 'ollama',
    isActive: true,
    description: 'Kompaktes Modell, gute Balance zwischen Geschwindigkeit und Qualität',
    recommendation: 'Empfohlen für Standard-Hardware',
    hardwareHint: 'Min. 8 GB VRAM oder 16 GB RAM',
    defaultNumCtx: 8192,
    speedRating: 'fast',
  },
  {
    id: 'qwen2.5:7b',
    name: 'Qwen 2.5 7B',
    provider: 'ollama',
    isActive: true,
    description: 'Effizientes Modell mit guter Mehrsprachunterstützung (DE/EN)',
    recommendation: 'Gut für deutsche Texte',
    hardwareHint: 'Min. 6 GB VRAM oder 12 GB RAM',
    defaultNumCtx: 8192,
    speedRating: 'fast',
  },
  {
    id: 'mistral-nemo:12b',
    name: 'Mistral Nemo 12B',
    provider: 'ollama',
    isActive: false,
    description: 'Größeres Modell für komplexe Analysen',
    recommendation: 'Für anspruchsvolle Prüfungen',
    hardwareHint: 'Min. 12 GB VRAM oder 24 GB RAM',
    defaultNumCtx: 16384,
    speedRating: 'medium',
  },
]

// ============================================================
// Profiles (LLM-Profile)
// ============================================================

export interface LLMProfile {
  id: string
  name: string
  description: string
  documentTypeId: string | 'all' // 'all' = gilt für alle
  modelId: string
  isDefault: boolean
  isActive: boolean

  // Basis-Parameter
  parameters: {
    temperature: number
    topP: number
    topK: number
    repeatPenalty: number
    numPredict: number
    stop: string[]
  }

  // Kontext
  context: {
    numCtx: number
  }

  // Performance
  performance: {
    numGpu: number | 'auto'
    numThread: number
    numBatch: number
  }

  // Chunking (überschreibt Dokumenttyp-Defaults wenn gesetzt)
  chunking?: ChunkingConfig

  createdAt: string
  updatedAt?: string
}

export const DEFAULT_PROFILE: LLMProfile = {
  id: 'default',
  name: 'Standard-Profil',
  description: 'Ausgewogene Einstellungen für die meisten Anwendungsfälle',
  documentTypeId: 'all',
  modelId: 'llama3.1:8b',
  isDefault: true,
  isActive: true,
  parameters: {
    temperature: 0.1,
    topP: 0.9,
    topK: 40,
    repeatPenalty: 1.1,
    numPredict: 1024,
    stop: ['\\n\\nEND_JSON', '```'],
  },
  context: {
    numCtx: 8192,
  },
  performance: {
    numGpu: 'auto',
    numThread: 10,
    numBatch: 384,
  },
  createdAt: new Date().toISOString(),
}

// ============================================================
// Settings Storage
// ============================================================

export interface SettingsStorage {
  schemaVersion: string
  documentTypes: DocumentTypeConfig[]
  models: ModelConfig[]
  profiles: LLMProfile[]
  activeProfileId: string
  defaultProvider: string
  lastUpdated: string
}

export const SETTINGS_SCHEMA_VERSION = '1.0.0'

// ============================================================
// Provider Status
// ============================================================

export type OllamaStatus = 'active' | 'inactive' | 'offline'

export interface ProviderStatus {
  id: string
  name: string
  status: 'online' | 'offline'
  ollamaStatus?: OllamaStatus // Nur für Ollama
  isDefault: boolean
  lastChecked?: string
  latencyMs?: number
}

// ============================================================
// Helper Functions
// ============================================================

export function getDefaultChunkingForDocType(docTypeId: string): ChunkingConfig {
  const docType = DEFAULT_DOCUMENT_TYPES.find(dt => dt.id === docTypeId)
  return docType?.chunkingDefaults || DEFAULT_DOCUMENT_TYPES.find(dt => dt.id === 'other')!.chunkingDefaults
}

export function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[äöüß]/g, match => ({ 'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss' }[match] || match))
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
}
