import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Dashboard
  getStats: async () => {
    const response = await apiClient.get('/stats/dashboard')
    return response.data
  },

  getDetailedStats: async () => {
    const response = await apiClient.get('/stats')
    return response.data
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
    const params = projectId ? { project_id: projectId } : {}
    const response = await apiClient.get('/documents', { params })
    return response.data.data
  },

  getDocument: async (id: string) => {
    const response = await apiClient.get(`/documents/${id}`)
    return response.data
  },

  uploadDocument: async (file: File, projectId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) {
      formData.append('project_id', projectId)
    }

    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  analyzeDocument: async (id: string, provider?: string, model?: string) => {
    const response = await apiClient.post(`/documents/${id}/analyze`, {
      provider,
      model,
    })
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
