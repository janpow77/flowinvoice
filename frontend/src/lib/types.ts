// API Response Types for FlowAudit

// ============================================================================
// User & Auth Types
// ============================================================================

export type UserRole = 'admin' | 'schueler' | 'extern';
export type ThemePreference = 'light' | 'dark' | 'system';
export type LanguageCode = 'de' | 'en';

export interface UserInfo {
  id: string;
  username: string;
  role: UserRole;
  is_admin: boolean;
  assigned_project_id: string | null;
  language: LanguageCode;
  theme: ThemePreference;
  permissions: string[];
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  organization: string | null;
  contact_info: string | null;
  language: LanguageCode;
  theme: ThemePreference;
  role: UserRole;
  is_active: boolean;
  assigned_project_id: string | null;
  access_expires_at: string | null;
  invited_by_id: string | null;
  created_at: string;
  last_active_at: string | null;
}

export interface UserListItem {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  assigned_project_id: string | null;
  last_active_at: string | null;
}

export interface UserListResponse {
  users: UserListItem[];
  total: number;
}

// ============================================================================
// Document Types
// ============================================================================

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

export interface SemanticCheck {
  passed: boolean
  project_relevance_score?: number
  description_quality_score?: number
  red_flags?: string[]
  findings?: string[]
  message?: string
}

export interface EconomicCheck {
  passed: boolean
  budget_check?: { passed: boolean; message?: string }
  price_check?: { passed: boolean; deviation_percent?: number; message?: string }
  findings?: string[]
  message?: string
}

export interface BeneficiaryMatch {
  matched: boolean
  confidence?: number
  expected_name?: string
  found_name?: string
  message?: string
}

export interface RiskFinding {
  indicator: string
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  message: string
  details?: string
  threshold?: number
  actual_value?: number
}

export interface RiskAssessment {
  findings: RiskFinding[]
  risk_score: number
  highest_severity: string
  summary: string
}

export interface AnalysisResult {
  id: string
  overall_assessment: 'ok' | 'review_needed' | 'rejected'
  confidence: number
  provider: string
  model?: string
  findings?: string[]
  semantic_check?: SemanticCheck
  economic_check?: EconomicCheck
  beneficiary_match?: BeneficiaryMatch
  risk_assessment?: RiskAssessment
  warnings?: string[]
  input_tokens?: number
  output_tokens?: number
  latency_ms?: number
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
  models?: string[]
}

// ============================================================================
// Solution File Types
// ============================================================================

export type SolutionFileFormat = 'JSON' | 'JSONL' | 'CSV';
export type MatchingStrategy = 'FILENAME' | 'FILENAME_POSITION' | 'POSITION_ONLY';
export type FeatureStatus = 'VALID' | 'INVALID' | 'WARNING' | 'MISSING' | 'PENDING' | 'CORRECTED';

export interface SolutionError {
  code: string;
  feature_id: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  expected?: unknown;
  actual?: unknown;
  message: string;
}

export interface SolutionEntry {
  position: number;
  filename: string;
  is_valid: boolean;
  errors: SolutionError[];
  fields: Record<string, unknown>;
  template?: string;
}

export interface SolutionFileUploadResponse {
  solution_file_id: string;
  format: SolutionFileFormat;
  entry_count: number;
  valid_count: number;
  invalid_count: number;
  error_count: number;
  generator_version?: string;
}

export interface MatchPreviewItem {
  document_id: string;
  document_filename: string;
  solution_filename: string;
  solution_position: number;
  is_valid: boolean;
  error_count: number;
  error_codes: string[];
  confidence: number;
  match_reason: string;
}

export interface SolutionPreviewResponse {
  solution_file_id: string;
  project_id: string;
  strategy: MatchingStrategy;
  matched_count: number;
  unmatched_documents: number;
  unmatched_solutions: number;
  match_rate: number;
  matches: MatchPreviewItem[];
  warnings: string[];
}

export interface ApplyOptionsSchema {
  strategy?: MatchingStrategy;
  overwrite_existing?: boolean;
  min_confidence?: number;
  create_rag_examples?: boolean;
  mark_as_validated?: boolean;
}

export interface AppliedCorrection {
  document_id: string;
  document_filename: string;
  errors_applied: number;
  fields_updated: number;
  rag_examples_created: number;
  status: string;
}

export interface SolutionApplyResponse {
  solution_file_id: string;
  project_id: string;
  applied_count: number;
  skipped_count: number;
  error_count: number;
  rag_examples_created: number;
  corrections: AppliedCorrection[];
  errors: string[];
}

export interface SolutionFileListItem {
  id: string;
  project_id: string;
  filename: string;
  format: SolutionFileFormat;
  entry_count: number;
  applied: boolean;
  applied_at?: string;
  created_at: string;
}

// Feature Status for Document List
export interface DocumentFeatureStatus {
  feature_id: string;
  feature_name: string;
  status: FeatureStatus;
  value?: unknown;
  expected?: unknown;
  error_code?: string;
  message?: string;
}

// ============================================================================
// Batch Job Types
// ============================================================================

export type BatchJobStatus =
  | 'PENDING'
  | 'QUEUED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type BatchJobType =
  | 'BATCH_ANALYZE'
  | 'BATCH_VALIDATE'
  | 'BATCH_EXPORT'
  | 'SOLUTION_APPLY'
  | 'RAG_REBUILD';

export interface BatchJob {
  id: string;
  job_type: BatchJobType;
  project_id?: string;
  status: BatchJobStatus;
  priority: number;
  total_items: number;
  processed_items: number;
  successful_items: number;
  failed_items: number;
  skipped_items: number;
  progress_percent: number;
  parameters?: Record<string, unknown>;
  errors: string[];
  warnings: string[];
  result?: Record<string, unknown>;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  created_by_id?: string;
}

export interface BatchJobListResponse {
  jobs: BatchJob[];
  total: number;
}
