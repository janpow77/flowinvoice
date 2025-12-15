// API Response Types for FlowAudit

export type DocumentStatus =
  | 'UPLOADED'
  | 'PARSING'
  | 'VALIDATING'
  | 'VALIDATED'
  | 'ANALYZING'
  | 'ANALYZED'
  | 'REVIEWED'
  | 'EXPORTED'
  | 'ERROR'

export interface ExtractedDataField {
  value: string | number | null
  confidence?: number
  source?: string
}

export interface ExtractedData {
  gross_amount?: ExtractedDataField
  net_amount?: ExtractedDataField
  vat_amount?: ExtractedDataField
  vat_rate?: ExtractedDataField
  invoice_number?: ExtractedDataField
  invoice_date?: ExtractedDataField
  supplier_name?: ExtractedDataField
  supplier_address?: ExtractedDataField
  customer_name?: ExtractedDataField
  [key: string]: ExtractedDataField | undefined
}

export interface PrecheckError {
  feature_id: string
  message: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  details?: string
}

export interface AnalysisResult {
  id: string
  overall_assessment: 'ok' | 'review_needed' | 'rejected'
  confidence: number
  provider: string
  findings?: string[]
  created_at: string
}

export interface Document {
  id: string
  project_id?: string
  original_filename: string
  filename: string
  file_size_bytes?: number
  mime_type: string
  status: DocumentStatus
  error_message?: string
  extracted_data?: ExtractedData
  precheck_errors?: PrecheckError[]
  precheck_passed?: boolean
  analysis_result?: AnalysisResult
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  title: string
  description?: string
  ruleset_id: string
  start_date: string
  end_date: string
  document_count?: number
  created_at: string
  updated_at: string
}

export interface LLMProvider {
  id: string
  name: string
  available: boolean
  models: string[]
  is_default?: boolean
}

export interface RulesetInfo {
  id: string
  name: string
  description?: string
  version?: string
}

export interface DashboardStats {
  total_documents: number
  approved: number
  pending_review: number
  rejected: number
}

export interface ProviderInfo {
  provider: string
  default_model: string
  is_default: boolean
  available?: boolean
}
