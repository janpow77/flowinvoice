import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { FolderOpen, Plus, Calendar, FileText, X, AlertCircle, Loader2, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { Project, RulesetInfo } from '@/lib/types'

interface CreateProjectForm {
  title: string
  description: string
  ruleset_id: string
  start_date: string
  end_date: string
}

interface DeleteConfirmState {
  isOpen: boolean
  projectId: string | null
  projectTitle: string
}

export default function Projects() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState<CreateProjectForm>({
    title: '',
    description: '',
    ruleset_id: 'DE_USTG',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  })

  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  const { data: rulesets } = useQuery({
    queryKey: ['rulesets'],
    queryFn: () => api.getRulesets(),
  })

  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
    isOpen: false,
    projectId: null,
    projectTitle: '',
  })

  const createProjectMutation = useMutation({
    mutationFn: (data: CreateProjectForm) => api.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsModalOpen(false)
      resetForm()
    },
  })

  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: string) => api.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setDeleteConfirm({ isOpen: false, projectId: null, projectTitle: '' })
    },
  })

  const handleDeleteClick = (e: React.MouseEvent, project: Project) => {
    e.preventDefault()
    e.stopPropagation()
    setDeleteConfirm({
      isOpen: true,
      projectId: project.id,
      projectTitle: project.title,
    })
  }

  const confirmDelete = () => {
    if (deleteConfirm.projectId) {
      deleteProjectMutation.mutate(deleteConfirm.projectId)
    }
  }

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      ruleset_id: 'DE_USTG',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.title.trim()) {
      createProjectMutation.mutate(formData)
    }
  }

  const openModal = () => {
    resetForm()
    setIsModalOpen(true)
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-accent-primary animate-spin" />
        <span className="ml-3 text-theme-text-muted">{t('common.loading')}</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-status-danger" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-status-danger">{t('common.error')}</h3>
            <p className="text-sm text-status-danger mt-1">
              {t('errors.generic')}: {(error as Error).message}
            </p>
          </div>
        </div>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}
          className="mt-4 px-4 py-2 bg-status-danger-bg text-status-danger rounded-lg hover:opacity-80 transition-colors"
        >
          {t('common.back')}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-theme-text-primary">{t('projects.title')}</h2>
        <button
          onClick={openModal}
          className="flex items-center px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          {t('projects.createProject')}
        </button>
      </div>

      {/* Project Grid */}
      {projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: Project) => (
            <div
              key={project.id}
              className="bg-theme-card rounded-lg border border-theme-border-default p-6 hover:shadow-md transition-shadow relative group"
            >
              <Link to={`/projects/${project.id}`} className="block">
                <div className="flex items-start">
                  <div className="p-2 bg-accent-primary/10 rounded-lg">
                    <FolderOpen className="h-6 w-6 text-accent-primary" />
                  </div>
                  <div className="ml-4 flex-1 pr-8">
                    <h3 className="font-medium text-theme-text-primary">{project.title}</h3>
                    <p className="text-sm text-theme-text-muted mt-1 line-clamp-2">
                      {project.description || t('projects.noDescription')}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center text-sm text-theme-text-muted space-x-4">
                  <span className="flex items-center">
                    <FileText className="h-4 w-4 mr-1" />
                    {project.document_count || 0} {t('projects.documentCount')}
                  </span>
                  <span className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    {new Date(project.created_at).toLocaleDateString('de-DE')}
                  </span>
                </div>
              </Link>

              {/* Delete Button */}
              <button
                onClick={(e) => handleDeleteClick(e, project)}
                className="absolute top-4 right-4 p-1.5 text-theme-text-muted hover:text-status-danger hover:bg-status-danger-bg rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                title={t('common.delete')}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-theme-card rounded-lg border border-theme-border-default p-12 text-center">
          <FolderOpen className="h-12 w-12 text-theme-text-muted mx-auto" />
          <h3 className="mt-4 text-lg font-medium text-theme-text-primary">{t('projects.noProjects')}</h3>
          <p className="mt-2 text-sm text-theme-text-muted">
            {t('projects.description')}
          </p>
          <button
            onClick={openModal}
            className="mt-4 px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover transition-colors"
          >
            {t('projects.createProject')}
          </button>
        </div>
      )}

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/50 transition-opacity"
              onClick={() => setIsModalOpen(false)}
            />

            {/* Modal */}
            <div className="relative bg-theme-elevated rounded-xl shadow-xl w-full max-w-lg">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border-default">
                <h3 className="text-lg font-semibold text-theme-text-primary">
                  {t('projects.createProject')}
                </h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-1 text-theme-text-muted hover:text-theme-text-primary rounded-lg hover:bg-theme-hover"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit}>
                <div className="px-6 py-4 space-y-4">
                  {/* Error Display */}
                  {createProjectMutation.error && (
                    <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-3 flex items-center text-sm text-status-danger">
                      <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                      {(createProjectMutation.error as Error).message}
                    </div>
                  )}

                  {/* Project Name */}
                  <div>
                    <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                      {t('projects.projectName')} *
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      className="w-full px-3 py-2 bg-theme-input border border-theme-border-default rounded-lg text-theme-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                      placeholder={t('projects.projectName')}
                      required
                      autoFocus
                    />
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                      {t('projects.description')}
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="w-full px-3 py-2 bg-theme-input border border-theme-border-default rounded-lg text-theme-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                      placeholder={t('projects.description')}
                      rows={3}
                    />
                  </div>

                  {/* Ruleset */}
                  <div>
                    <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                      {t('settings.defaultRuleset')}
                    </label>
                    <select
                      value={formData.ruleset_id}
                      onChange={(e) => setFormData({ ...formData, ruleset_id: e.target.value })}
                      className="w-full px-3 py-2 bg-theme-input border border-theme-border-default rounded-lg text-theme-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                    >
                      {rulesets && rulesets.length > 0 ? (
                        rulesets.map((ruleset: RulesetInfo) => (
                          <option key={ruleset.id} value={ruleset.id}>
                            {t(`rulesets.${ruleset.id}`, { defaultValue: ruleset.name })}
                          </option>
                        ))
                      ) : (
                        <>
                          <option value="DE_USTG">{t('rulesets.DE_USTG')}</option>
                          <option value="EU_VAT">{t('rulesets.EU_VAT')}</option>
                          <option value="UK_VAT">{t('rulesets.UK_VAT')}</option>
                        </>
                      )}
                    </select>
                  </div>

                  {/* Date Range */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('projectContext.projectPeriod')} (Start)
                      </label>
                      <input
                        type="date"
                        value={formData.start_date}
                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                        className="w-full px-3 py-2 bg-theme-input border border-theme-border-default rounded-lg text-theme-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        {t('projectContext.projectPeriod')} (Ende)
                      </label>
                      <input
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                        className="w-full px-3 py-2 bg-theme-input border border-theme-border-default rounded-lg text-theme-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                      />
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-theme-border-subtle bg-theme-hover rounded-b-xl">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-theme-text-secondary bg-theme-card border border-theme-border-default rounded-lg hover:bg-theme-hover transition-colors"
                  >
                    {t('common.cancel')}
                  </button>
                  <button
                    type="submit"
                    disabled={createProjectMutation.isPending || !formData.title.trim()}
                    className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {createProjectMutation.isPending && (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    )}
                    {t('common.create')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm.isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/50 transition-opacity"
              onClick={() => setDeleteConfirm({ isOpen: false, projectId: null, projectTitle: '' })}
            />

            {/* Modal */}
            <div className="relative bg-theme-elevated rounded-xl shadow-xl w-full max-w-md p-6">
              <div className="flex items-center mb-4">
                <div className="p-2 bg-status-danger-bg rounded-lg">
                  <Trash2 className="h-6 w-6 text-status-danger" />
                </div>
                <h3 className="ml-3 text-lg font-semibold text-theme-text-primary">
                  {t('projects.deleteProject')}
                </h3>
              </div>

              <p className="text-theme-text-secondary mb-2">
                {t('projects.deleteConfirmMessage')}
              </p>
              <p className="font-medium text-theme-text-primary mb-4">
                "{deleteConfirm.projectTitle}"
              </p>
              <p className="text-sm text-status-danger mb-6">
                {t('projects.deleteWarning')}
              </p>

              {deleteProjectMutation.error && (
                <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-3 mb-4 flex items-center text-sm text-status-danger">
                  <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                  {(deleteProjectMutation.error as Error).message}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setDeleteConfirm({ isOpen: false, projectId: null, projectTitle: '' })}
                  className="px-4 py-2 text-theme-text-secondary bg-theme-card border border-theme-border-default rounded-lg hover:bg-theme-hover transition-colors"
                  disabled={deleteProjectMutation.isPending}
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={confirmDelete}
                  disabled={deleteProjectMutation.isPending}
                  className="px-4 py-2 bg-status-danger text-white rounded-lg hover:opacity-80 transition-colors disabled:opacity-50 flex items-center"
                >
                  {deleteProjectMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  {t('common.delete')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
