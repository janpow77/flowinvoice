import axios from 'axios'
import type { UserInfo } from './types'

// Token-Speicher Key (muss mit AuthContext übereinstimmen)
const TOKEN_KEY = 'flowaudit_token'

// Authenticated API client (with token interceptor)
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Public API client (for unauthenticated endpoints like login)
const apiClientPublic = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Fügt Authorization Header hinzu
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor: Behandelt 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token ungültig oder abgelaufen - zum Login umleiten
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('flowaudit_token_expiry')

      // Nur umleiten wenn nicht bereits auf Login-Seite
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  // ============================================
  // Auth (public endpoints - no token required)
  // ============================================

  /** Login with username/password - returns access_token */
  login: async (username: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    const response = await apiClientPublic.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  /** Check if Google OAuth is enabled */
  isGoogleAuthEnabled: async (): Promise<boolean> => {
    const response = await apiClientPublic.get('/auth/google/enabled')
    return response.data.enabled
  },

  /** Get Google OAuth URL for redirect */
  getGoogleAuthUrl: async (): Promise<{ auth_url: string; state: string }> => {
    const response = await apiClientPublic.get('/auth/google/url')
    return response.data
  },

  /** Exchange Google OAuth code for token */
  googleCallback: async (code: string, state?: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await apiClientPublic.post('/auth/google/callback', { code, state })
    return response.data
  },

  // ============================================
  // User (authenticated endpoints)
  // ============================================

  /** Get current user info */
  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await apiClient.get('/users/me')
    return response.data
  },

  /** Get current user info with specific token (for initial auth) */
  getCurrentUserWithToken: async (token: string): Promise<UserInfo> => {
    const response = await apiClientPublic.get('/users/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },

  // ============================================
  // Dashboard
  // ============================================
  getStats: async () => {
    const response = await apiClient.get('/stats/global')
    return response.data
  },

  getDetailedStats: async () => {
    // Aggregate stats from multiple endpoints
    const [feedback, llm, rag, system] = await Promise.all([
      apiClient.get('/stats/feedback'),
      apiClient.get('/stats/llm'),
      apiClient.get('/stats/rag'),
      apiClient.get('/stats/system'),
    ])
    return {
      feedback: feedback.data,
      llm: llm.data,
      rag: rag.data,
      system: system.data,
    }
  },

  // Projects
  getProjects: async () => {
    const response = await apiClient.get('/projects')
    // Map backend format to frontend format
    return (response.data.data || []).map((p: Record<string, unknown>) => ({
      id: p.project_id,
      title: p.project_title,
      description: p.file_reference,
      ruleset_id: p.ruleset_id_hint || 'DE_USTG',
      document_count: p.document_count || 0,
      created_at: p.created_at,
      updated_at: p.created_at,
      beneficiary_name: p.beneficiary_name,
      beneficiary: p.beneficiary as Record<string, unknown> | undefined,
      is_active: p.is_active,
    }))
  },

  getProject: async (id: string) => {
    const response = await apiClient.get(`/projects/${id}`)
    // Return backend structure directly (ProjectDetail expects this format)
    return response.data
  },

  updateProject: async (id: string, data: {
    title?: string
    description?: string
    ruleset_id?: string
    start_date?: string
    end_date?: string
    beneficiary?: {
      name?: string
      street?: string
      zip?: string
      city?: string
      vat_id?: string
      tax_number?: string
    }
    project?: {
      project_title?: string
      file_reference?: string
      project_description?: string
      implementation?: {
        location_name?: string
        city?: string
      }
      project_period?: {
        start: string
        end: string
      }
    }
  }) => {
    // Transform Frontend-Daten in Backend-Schema
    const backendData: Record<string, unknown> = {}

    if (data.ruleset_id) {
      backendData.ruleset_id_hint = data.ruleset_id
    }

    // Direct beneficiary update
    if (data.beneficiary) {
      backendData.beneficiary = data.beneficiary
    }

    // Direct project update
    if (data.project) {
      backendData.project = data.project
    } else if (data.title || data.description || data.start_date || data.end_date) {
      // Legacy: transform old format
      backendData.project = {
        ...(data.title && { project_title: data.title }),
        ...(data.description && { project_description: data.description }),
        ...((data.start_date && data.end_date) && {
          project_period: { start: data.start_date, end: data.end_date }
        }),
      }
    }

    const response = await apiClient.put(`/projects/${id}`, backendData)
    return response.data
  },

  createProject: async (data: {
    title: string
    description?: string
    ruleset_id?: string
    start_date?: string
    end_date?: string
  }) => {
    // Transform Frontend-Daten in Backend-Schema
    const backendData = {
      ruleset_id_hint: data.ruleset_id || null,
      ui_language_hint: 'de',
      beneficiary: {
        name: data.title, // Projektname als Begünstigter-Name (Platzhalter)
        street: 'Nicht angegeben',
        zip: '00000',
        city: 'Nicht angegeben',
        country: 'DE',
      },
      project: {
        project_title: data.title,
        project_description: data.description || null,
        project_period: data.start_date && data.end_date ? {
          start: data.start_date,
          end: data.end_date,
        } : null,
      },
    }
    const response = await apiClient.post('/projects', backendData)
    return response.data
  },

  deleteProject: async (id: string) => {
    await apiClient.delete(`/projects/${id}`)
  },

  // Documents
  getDocuments: async (projectId?: string) => {
    if (!projectId) {
      // If no project specified, get all projects and aggregate documents
      const projects = await apiClient.get('/projects')
      const projectList = projects.data.data || []
      if (projectList.length === 0) return []

      // Fetch documents from all projects in parallel
      const documentPromises = projectList.map((project: { id: string }) =>
        apiClient.get(`/projects/${project.id}/documents`)
          .then(res => res.data.data || [])
          .catch(() => []) // Ignore errors for individual projects
      )
      const documentsPerProject = await Promise.all(documentPromises)
      return documentsPerProject.flat()
    }
    const response = await apiClient.get(`/projects/${projectId}/documents`)
    return response.data.data || []
  },

  getDocument: async (id: string) => {
    const response = await apiClient.get(`/documents/${id}`)
    return response.data
  },

  getDocumentFileUrl: (id: string) => {
    // Returns the URL for the document file (PDF)
    // Token is handled by the browser's Authorization header
    const token = localStorage.getItem(TOKEN_KEY)
    return `/api/documents/${id}/file${token ? `?token=${encodeURIComponent(token)}` : ''}`
  },

  getDocumentFileBlob: async (id: string) => {
    const response = await apiClient.get(`/documents/${id}/file`, {
      responseType: 'blob',
    })
    return response.data
  },

  getDocumentLlmRuns: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/llm-runs`)
    return response.data.data || []
  },

  uploadDocument: async (file: File, projectId: string, documentType: string = 'INVOICE') => {
    if (!projectId) {
      throw new Error('Project ID is required for document upload')
    }
    const formData = new FormData()
    formData.append('files', file)  // Backend expects 'files' not 'file'
    formData.append('document_type', documentType)

    const response = await apiClient.post(`/projects/${projectId}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  analyzeDocument: async (id: string, provider?: string, model?: string) => {
    const params: Record<string, string> = {}
    if (provider) params.provider = provider
    if (model) params.model = model

    const response = await apiClient.post(`/documents/${id}/analyze`, null, { params })
    return response.data
  },

  // LLM Providers
  getLLMProviders: async () => {
    const response = await apiClient.get('/llm/providers')
    return response.data.providers
  },

  getLLMHealth: async () => {
    const response = await apiClient.get('/llm/health')
    return response.data.providers
  },

  setDefaultProvider: async (provider: string) => {
    const response = await apiClient.post('/llm/default', { provider })
    return response.data
  },

  // Feedback
  getDocumentFeedback: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/feedback`)
    return response.data.data || []
  },

  getDocumentFinal: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/final`)
    return response.data
  },

  finalizeDocument: async (documentId: string) => {
    const response = await apiClient.post(`/documents/${documentId}/finalize`)
    return response.data
  },

  submitFeedback: async (data: {
    document_id: string
    result_id: string
    rating: 'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT'
    comment?: string
    corrections?: Array<{ feature_id: string; user_value: unknown; note?: string }>
    accept_result?: boolean
  }) => {
    // Transform Frontend-Daten in Backend-Schema
    // Rating-Mapping: Frontend -> Backend
    const ratingMap: Record<string, string> = {
      'CORRECT': 'CORRECT',
      'PARTIALLY_CORRECT': 'PARTIAL',
      'INCORRECT': 'WRONG',
    }

    const backendData = {
      final_result_id: data.result_id,
      rating: ratingMap[data.rating] || data.rating,
      comment: data.comment || null,
      overrides: data.corrections || [],
      accept_result: data.accept_result || false,
    }

    // Backend-Endpoint ist /documents/{document_id}/feedback
    const response = await apiClient.post(`/documents/${data.document_id}/feedback`, backendData)
    return response.data
  },

  // RAG
  getRAGStats: async () => {
    const response = await apiClient.get('/rag/stats')
    return response.data
  },

  searchRAG: async (query: string, collectionType?: string) => {
    const response = await apiClient.post('/rag/search', {
      query,
      collection_type: collectionType,
    })
    return response.data
  },

  // Settings
  getSettings: async () => {
    const response = await apiClient.get('/settings')
    return response.data
  },

  updateSettings: async (settings: Record<string, unknown>) => {
    const response = await apiClient.put('/settings', settings)
    return response.data
  },

  // Performance Settings
  getPerformanceSettings: async () => {
    const response = await apiClient.get('/settings/performance')
    return response.data
  },

  updatePerformanceSettings: async (settings: {
    uvicorn_workers?: number
    celery_concurrency?: number
  }) => {
    const params = new URLSearchParams()
    if (settings.uvicorn_workers !== undefined) {
      params.append('uvicorn_workers', settings.uvicorn_workers.toString())
    }
    if (settings.celery_concurrency !== undefined) {
      params.append('celery_concurrency', settings.celery_concurrency.toString())
    }
    const response = await apiClient.put(`/settings/performance?${params.toString()}`)
    return response.data
  },

  // Rulesets
  getRulesets: async () => {
    const response = await apiClient.get('/rulesets')
    // Transform API response to match RulesetListItem interface in Rulesets.tsx
    return response.data.data.map((r: { ruleset_id: string; title: string; version?: string; language_support?: string[] }) => ({
      ruleset_id: r.ruleset_id,
      title: r.title,
      version: r.version || '1.0.0',
      language_support: r.language_support,
    }))
  },

  getRuleset: async (id: string) => {
    const response = await apiClient.get(`/rulesets/${id}`)
    return response.data
  },

  createRuleset: async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/rulesets', data, {
      headers: { 'X-Role': 'admin' },
    })
    return response.data
  },

  updateRuleset: async (id: string, version: string, data: Record<string, unknown>) => {
    const response = await apiClient.put(`/rulesets/${id}/${version}`, data, {
      headers: { 'X-Role': 'admin' },
    })
    return response.data
  },

  getRulesetLlmSchema: async (id: string, version?: string) => {
    const params = version ? `?version=${version}` : ''
    const response = await apiClient.get(`/rulesets/${id}/llm-schema${params}`)
    return response.data
  },

  // Ruleset Checker Settings
  getRulesetCheckerSettings: async (rulesetId: string) => {
    const response = await apiClient.get(`/rulesets/${rulesetId}/checkers`)
    return response.data
  },

  updateRulesetCheckerSettings: async (rulesetId: string, data: {
    risk_checker?: {
      enabled: boolean
      severity_threshold: string
      check_self_invoice: boolean
      check_duplicate_invoice: boolean
      check_round_amounts: boolean
      check_weekend_dates: boolean
      round_amount_threshold: number
    }
    semantic_checker?: {
      enabled: boolean
      severity_threshold: string
      check_project_relevance: boolean
      check_description_quality: boolean
      min_relevance_score: number
      use_rag_context: boolean
    }
    economic_checker?: {
      enabled: boolean
      severity_threshold: string
      check_budget_limits: boolean
      check_unit_prices: boolean
      check_funding_rate: boolean
      max_deviation_percent: number
    }
  }) => {
    const response = await apiClient.put(`/rulesets/${rulesetId}/checkers`, data, {
      headers: { 'X-Role': 'admin' },
    })
    return response.data
  },

  resetRulesetCheckerSettings: async (rulesetId: string) => {
    await apiClient.delete(`/rulesets/${rulesetId}/checkers`, {
      headers: { 'X-Role': 'admin' },
    })
  },

  // Ruleset Samples
  getRulesetSamples: async (rulesetId: string) => {
    const response = await apiClient.get(`/rulesets/${rulesetId}/samples`)
    return response.data.data  // Return array from {data: [...], total, stats}
  },

  getRulesetSample: async (rulesetId: string, sampleId: string) => {
    const response = await apiClient.get(`/rulesets/${rulesetId}/samples/${sampleId}`)
    return response.data
  },

  uploadRulesetSample: async (rulesetId: string, file: File, description?: string, version?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) formData.append('description', description)
    if (version) formData.append('ruleset_version', version)

    const response = await apiClient.post(`/rulesets/${rulesetId}/samples`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-Role': 'admin',
      },
    })
    return response.data
  },

  updateRulesetSample: async (rulesetId: string, sampleId: string, data: {
    description?: string
    ground_truth?: Record<string, unknown>
  }) => {
    const response = await apiClient.put(`/rulesets/${rulesetId}/samples/${sampleId}`, data, {
      headers: { 'X-Role': 'admin' },
    })
    return response.data
  },

  approveRulesetSample: async (rulesetId: string, sampleId: string, groundTruth?: Record<string, unknown>) => {
    const response = await apiClient.post(
      `/rulesets/${rulesetId}/samples/${sampleId}/approve`,
      groundTruth ? { ground_truth: groundTruth } : {},
      { headers: { 'X-Role': 'admin' } }
    )
    return response.data
  },

  rejectRulesetSample: async (rulesetId: string, sampleId: string, reason?: string) => {
    const response = await apiClient.post(
      `/rulesets/${rulesetId}/samples/${sampleId}/reject`,
      reason ? { reason } : {},
      { headers: { 'X-Role': 'admin' } }
    )
    return response.data
  },

  deleteRulesetSample: async (rulesetId: string, sampleId: string) => {
    const response = await apiClient.delete(`/rulesets/${rulesetId}/samples/${sampleId}`, {
      headers: { 'X-Role': 'admin' },
    })
    return response.data
  },

  // Project Statistics
  getProjectStats: async (projectId: string) => {
    const response = await apiClient.get(`/projects/${projectId}/stats`)
    return response.data
  },

  // Feature Names (from Rulesets)
  getFeatureNames: async (rulesetId: string = 'DE_USTG') => {
    const response = await apiClient.get(`/stats/feature-names/${rulesetId}`)
    return response.data
  },

  getAllFeatureNames: async () => {
    const response = await apiClient.get('/stats/all-feature-names')
    return response.data
  },

  // System Monitoring
  getSystemMetrics: async () => {
    const response = await apiClient.get('/system/metrics')
    return response.data
  },

  getGpuSettings: async () => {
    const response = await apiClient.get('/system/gpu')
    return response.data
  },

  updateGpuSettings: async (settings: {
    gpu_memory_fraction?: number
    num_gpu_layers?: number
    num_parallel?: number
    context_size?: number
    thermal_throttle_temp?: number
  }) => {
    const params = new URLSearchParams()
    if (settings.gpu_memory_fraction !== undefined) {
      params.append('gpu_memory_fraction', settings.gpu_memory_fraction.toString())
    }
    if (settings.num_gpu_layers !== undefined) {
      params.append('num_gpu_layers', settings.num_gpu_layers.toString())
    }
    if (settings.num_parallel !== undefined) {
      params.append('num_parallel', settings.num_parallel.toString())
    }
    if (settings.context_size !== undefined) {
      params.append('context_size', settings.context_size.toString())
    }
    if (settings.thermal_throttle_temp !== undefined) {
      params.append('thermal_throttle_temp', settings.thermal_throttle_temp.toString())
    }
    const response = await apiClient.put(`/system/gpu?${params.toString()}`)
    return response.data
  },

  getDetailedHealth: async () => {
    const response = await apiClient.get('/system/health/detailed')
    return response.data
  },

  // Provider API Keys
  setProviderApiKey: async (provider: string, apiKey: string) => {
    const response = await apiClient.put(
      `/settings/providers/${provider}/api-key`,
      { api_key: apiKey }
    )
    return response.data
  },

  deleteProviderApiKey: async (provider: string) => {
    const response = await apiClient.delete(`/settings/providers/${provider}/api-key`)
    return response.data
  },

  testProvider: async (provider: string) => {
    const response = await apiClient.post(`/settings/providers/${provider}/test`)
    return response.data
  },

  // Ollama Models
  getOllamaModels: async () => {
    const response = await apiClient.get('/settings/providers/LOCAL_OLLAMA/models')
    return response.data
  },

  pullOllamaModel: async (modelName: string) => {
    const response = await apiClient.post('/settings/providers/LOCAL_OLLAMA/models/pull', {
      model_name: modelName,
    })
    return response.data
  },

  // Document Types
  getDocumentTypes: async () => {
    const response = await apiClient.get('/settings/document-types')
    // Map backend format to frontend format
    return (response.data.data || []).map((dt: Record<string, unknown>) => ({
      id: dt.id,
      name: dt.name,
      slug: dt.slug,
      description: dt.description || '',
      isSystem: dt.is_system,
      chunkingDefaults: {
        chunkSizeTokens: dt.chunk_size_tokens,
        chunkOverlapTokens: dt.chunk_overlap_tokens,
        maxChunks: dt.max_chunks,
        chunkStrategy: dt.chunk_strategy,
      },
      createdAt: dt.created_at,
      updatedAt: dt.updated_at,
    }))
  },

  createDocumentType: async (data: {
    name: string
    slug: string
    description?: string
    chunk_size_tokens?: number
    chunk_overlap_tokens?: number
    max_chunks?: number
    chunk_strategy?: string
  }) => {
    const response = await apiClient.post('/settings/document-types', data, {
      headers: { 'X-Role': 'admin' },
    })
    const dt = response.data
    return {
      id: dt.id,
      name: dt.name,
      slug: dt.slug,
      description: dt.description || '',
      isSystem: dt.is_system,
      chunkingDefaults: {
        chunkSizeTokens: dt.chunk_size_tokens,
        chunkOverlapTokens: dt.chunk_overlap_tokens,
        maxChunks: dt.max_chunks,
        chunkStrategy: dt.chunk_strategy,
      },
      createdAt: dt.created_at,
      updatedAt: dt.updated_at,
    }
  },

  updateDocumentType: async (id: string, data: {
    name?: string
    description?: string
    chunk_size_tokens?: number
    chunk_overlap_tokens?: number
    max_chunks?: number
    chunk_strategy?: string
  }) => {
    const response = await apiClient.put(`/settings/document-types/${id}`, data, {
      headers: { 'X-Role': 'admin' },
    })
    const dt = response.data
    return {
      id: dt.id,
      name: dt.name,
      slug: dt.slug,
      description: dt.description || '',
      isSystem: dt.is_system,
      chunkingDefaults: {
        chunkSizeTokens: dt.chunk_size_tokens,
        chunkOverlapTokens: dt.chunk_overlap_tokens,
        maxChunks: dt.max_chunks,
        chunkStrategy: dt.chunk_strategy,
      },
      createdAt: dt.created_at,
      updatedAt: dt.updated_at,
    }
  },

  deleteDocumentType: async (id: string) => {
    await apiClient.delete(`/settings/document-types/${id}`, {
      headers: { 'X-Role': 'admin' },
    })
  },

  // Generator
  getGeneratorTemplates: async () => {
    const response = await apiClient.get('/generator/templates')
    return response.data.data
  },

  runGenerator: async (options: {
    project_id?: string
    ruleset_id?: string
    count?: number
    templates_enabled?: string[]
    error_rate_total?: number
    severity?: number
    alias_noise_probability?: number
    beneficiary_data?: {
      beneficiary_name: string
      street: string
      zip: string
      city: string
      country?: string
      vat_id?: string
    }
    project_context?: {
      project_number?: string
      execution_location?: string
    }
  }) => {
    const params = new URLSearchParams()
    if (options.project_id) params.append('project_id', options.project_id)
    if (options.ruleset_id) params.append('ruleset_id', options.ruleset_id)
    if (options.count) params.append('count', options.count.toString())
    if (options.error_rate_total !== undefined) params.append('error_rate_total', options.error_rate_total.toString())
    if (options.severity !== undefined) params.append('severity', options.severity.toString())
    if (options.alias_noise_probability !== undefined) params.append('alias_noise_probability', options.alias_noise_probability.toString())
    if (options.templates_enabled) {
      options.templates_enabled.forEach(t => params.append('templates_enabled', t))
    }

    const response = await apiClient.post(`/generator/run?${params.toString()}`, {
      beneficiary_data: options.beneficiary_data,
      project_context: options.project_context,
    }, {
      headers: {
        'X-API-Key': localStorage.getItem('flowaudit_admin_key') || 'admin',
      },
    })
    return response.data
  },

  getGeneratorJob: async (jobId: string) => {
    const response = await apiClient.get(`/generator/jobs/${jobId}`)
    return response.data
  },

  getGeneratorSolutions: async (jobId: string) => {
    const response = await apiClient.get(`/generator/jobs/${jobId}/solutions`, {
      headers: {
        'X-API-Key': localStorage.getItem('flowaudit_admin_key') || 'admin',
      },
    })
    return response.data
  },

  // Solution Files
  getSolutionFiles: async (projectId: string) => {
    const response = await apiClient.get(`/projects/${projectId}/solutions`)
    return response.data
  },

  uploadSolutionFile: async (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post(`/projects/${projectId}/solutions/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getSolutionFile: async (projectId: string, solutionFileId: string) => {
    const response = await apiClient.get(`/projects/${projectId}/solutions/${solutionFileId}`)
    return response.data
  },

  previewSolutionMatching: async (projectId: string, solutionFileId: string, strategy?: string) => {
    const params = strategy ? `?strategy=${strategy}` : ''
    const response = await apiClient.post(
      `/projects/${projectId}/solutions/${solutionFileId}/preview${params}`
    )
    return response.data
  },

  applySolutionFile: async (projectId: string, solutionFileId: string, options?: {
    strategy?: string
    overwrite_existing?: boolean
    min_confidence?: number
    create_rag_examples?: boolean
    mark_as_validated?: boolean
  }) => {
    const response = await apiClient.post(
      `/projects/${projectId}/solutions/${solutionFileId}/apply`,
      options || {}
    )
    return response.data
  },

  deleteSolutionFile: async (projectId: string, solutionFileId: string) => {
    await apiClient.delete(`/projects/${projectId}/solutions/${solutionFileId}`)
  },

  // Batch Jobs
  getBatchJobs: async (params?: {
    project_id?: string
    status?: string
    job_type?: string
    limit?: number
    offset?: number
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.project_id) queryParams.append('project_id', params.project_id)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.job_type) queryParams.append('job_type', params.job_type)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    const response = await apiClient.get(`/batch-jobs?${queryParams.toString()}`)
    return response.data
  },

  getBatchJob: async (jobId: string) => {
    const response = await apiClient.get(`/batch-jobs/${jobId}`)
    return response.data
  },

  createBatchJob: async (data: {
    job_type: string
    project_id?: string
    parameters?: Record<string, unknown>
    priority?: number
    scheduled_at?: string
    depends_on_job_id?: string
  }) => {
    const response = await apiClient.post('/batch-jobs', data)
    return response.data
  },

  cancelBatchJob: async (jobId: string) => {
    await apiClient.delete(`/batch-jobs/${jobId}`)
  },

  retryBatchJob: async (jobId: string) => {
    const response = await apiClient.post(`/batch-jobs/${jobId}/retry`)
    return response.data
  },

  createBatchAnalyzeJob: async (projectId: string, params?: {
    document_ids?: string[]
    use_rag?: boolean
    provider_id?: string
    skip_analyzed?: boolean
  }) => {
    const response = await apiClient.post(`/batch-jobs/analyze?project_id=${projectId}`, params || {})
    return response.data
  },
}

export default api
