import axios from 'axios'

// Token-Speicher Key (muss mit AuthContext übereinstimmen)
const TOKEN_KEY = 'flowaudit_token'

const apiClient = axios.create({
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
  // Dashboard
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
    return response.data.data
  },

  getProject: async (id: string) => {
    const response = await apiClient.get(`/projects/${id}`)
    return response.data
  },

  updateProject: async (id: string, data: {
    title?: string
    description?: string
    ruleset_id?: string
    start_date?: string
    end_date?: string
  }) => {
    const response = await apiClient.put(`/projects/${id}`, data)
    return response.data
  },

  createProject: async (data: {
    title: string
    description?: string
    ruleset_id?: string
    start_date?: string
    end_date?: string
  }) => {
    const response = await apiClient.post('/projects', data)
    return response.data
  },

  // Documents
  getDocuments: async (projectId?: string) => {
    if (!projectId) {
      // If no project specified, get all projects and aggregate documents
      const projects = await apiClient.get('/projects')
      const projectList = projects.data.data || []
      if (projectList.length === 0) return []

      // Get documents from first project for now (TODO: aggregate all)
      const response = await apiClient.get(`/projects/${projectList[0].id}/documents`)
      return response.data.data || []
    }
    const response = await apiClient.get(`/projects/${projectId}/documents`)
    return response.data.data || []
  },

  getDocument: async (id: string) => {
    const response = await apiClient.get(`/documents/${id}`)
    return response.data
  },

  uploadDocument: async (file: File, projectId: string) => {
    if (!projectId) {
      throw new Error('Project ID is required for document upload')
    }
    const formData = new FormData()
    formData.append('files', file)  // Backend expects 'files' not 'file'

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
  submitFeedback: async (data: {
    document_id: string
    result_id: string
    rating: 'CORRECT' | 'PARTIALLY_CORRECT' | 'INCORRECT'
    comment?: string
    corrections?: Record<string, unknown>[]
  }) => {
    const response = await apiClient.post('/feedback', data)
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
    return response.data.data
  },

  getRuleset: async (id: string) => {
    const response = await apiClient.get(`/rulesets/${id}`)
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
}

export default api
