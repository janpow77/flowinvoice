import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, CheckCircle, XCircle, Clock, Eye, AlertCircle, RefreshCw, FolderOpen } from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { Document, DocumentStatus, Project } from '@/lib/types'

const statusConfig = {
  UPLOADED: { icon: Clock, color: 'text-theme-text-muted', label: 'Hochgeladen' },
  PARSING: { icon: Clock, color: 'text-status-info', label: 'Parsing...' },
  VALIDATING: { icon: Clock, color: 'text-status-info', label: 'Validiere...' },
  VALIDATED: { icon: CheckCircle, color: 'text-status-success', label: 'Validiert' },
  ANALYZING: { icon: Clock, color: 'text-status-warning', label: 'Analysiere...' },
  ANALYZED: { icon: CheckCircle, color: 'text-status-success', label: 'Analysiert' },
  REVIEWED: { icon: CheckCircle, color: 'text-status-success', label: 'Geprüft' },
  EXPORTED: { icon: CheckCircle, color: 'text-status-success', label: 'Exportiert' },
  ERROR: { icon: XCircle, color: 'text-status-danger', label: 'Fehler' },
}

export default function Documents() {
  const { t } = useTranslation()
  const [uploading, setUploading] = useState(false)
  const [uploadErrors, setUploadErrors] = useState<string[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Fetch projects to get a project ID for uploads
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
    retry: 2,
  })

  // Use selected project or first available
  const activeProjectId = selectedProjectId || (projects && projects.length > 0 ? projects[0].id : null)

  const { data: documents, isLoading, error, refetch } = useQuery({
    queryKey: ['documents', activeProjectId],
    queryFn: () => api.getDocuments(activeProjectId || undefined),
    enabled: !!activeProjectId,
    retry: 2,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      if (!activeProjectId) {
        throw new Error('Kein Projekt ausgewählt')
      }
      return api.uploadDocument(file, activeProjectId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)
    setUploadErrors([])
    const errors: string[] = []

    for (const file of acceptedFiles) {
      try {
        await uploadMutation.mutateAsync(file)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unbekannter Fehler'
        errors.push(`${file.name}: ${message}`)
      }
    }

    if (errors.length > 0) {
      setUploadErrors(errors)
    }
    setUploading(false)
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    disabled: uploading,
  })

  // Error state
  if (error) {
    return (
      <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-status-danger" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-status-danger">{t('common.error')}</h3>
            <p className="text-sm text-status-danger mt-1">
              {t('errors.network')}
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-status-danger-bg text-status-danger rounded-lg hover:opacity-80 transition-colors flex items-center"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('common.retry')}
        </button>
      </div>
    )
  }

  // Show message if no projects exist
  if (projects && projects.length === 0) {
    return (
      <div className="bg-status-warning-bg border border-status-warning-border rounded-lg p-6">
        <div className="flex items-center">
          <FolderOpen className="h-6 w-6 text-status-warning" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-status-warning">Kein Projekt vorhanden</h3>
            <p className="text-sm text-status-warning mt-1">
              Bitte erstellen Sie zuerst ein Projekt, bevor Sie Dokumente hochladen.
            </p>
          </div>
        </div>
        <Link
          to="/projects"
          className="mt-4 inline-block px-4 py-2 bg-status-warning-bg text-status-warning rounded-lg hover:opacity-80 transition-colors"
        >
          Zu den Projekten
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Project Selector */}
      {projects && projects.length > 1 && (
        <div className="flex items-center space-x-4">
          <label htmlFor="project-select" className="text-sm font-medium text-theme-text-secondary">
            Projekt:
          </label>
          <select
            id="project-select"
            value={activeProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="block w-64 px-3 py-2 bg-theme-input border border-theme-border-default rounded-md shadow-sm text-theme-text-primary focus:outline-none focus:ring-accent-primary focus:border-accent-primary"
          >
            {projects.map((project: Project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-accent-primary bg-theme-selected'
            : 'border-theme-border-default hover:border-accent-primary',
          (uploading || !activeProjectId) && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload className={clsx(
          'h-12 w-12 mx-auto',
          isDragActive ? 'text-accent-primary' : 'text-theme-text-muted'
        )} />
        <p className="mt-4 text-lg font-medium text-theme-text-primary">
          {uploading ? 'Wird hochgeladen...' :
           isDragActive ? 'Hier ablegen' : 'PDF-Rechnung hochladen'}
        </p>
        <p className="mt-2 text-sm text-theme-text-muted">
          Ziehen Sie eine PDF-Datei hierher oder klicken Sie zum Auswählen
        </p>
      </div>

      {/* Upload Errors */}
      {uploadErrors.length > 0 && (
        <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-status-danger mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-status-danger">
                {uploadErrors.length === 1 ? 'Upload fehlgeschlagen' : `${uploadErrors.length} Uploads fehlgeschlagen`}
              </h3>
              <ul className="mt-2 text-sm text-status-danger list-disc list-inside">
                {uploadErrors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
              <button
                onClick={() => setUploadErrors([])}
                className="mt-2 text-sm text-status-danger hover:opacity-80 underline"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document List */}
      <div className="bg-theme-card rounded-lg border border-theme-border-default">
        <div className="px-6 py-4 border-b border-theme-border-default">
          <h2 className="text-lg font-semibold text-theme-text-primary">Dokumente</h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-theme-text-muted">Lade Dokumente...</div>
        ) : documents && documents.length > 0 ? (
          <div className="divide-y divide-theme-border-subtle">
            {documents.map((doc: Document) => {
              const status = statusConfig[doc.status as DocumentStatus] || statusConfig.UPLOADED
              const StatusIcon = status.icon

              return (
                <div
                  key={doc.id}
                  className="px-6 py-4 flex items-center justify-between hover:bg-theme-hover"
                >
                  <div className="flex items-center">
                    <FileText className="h-8 w-8 text-theme-text-muted" />
                    <div className="ml-4">
                      <p className="font-medium text-theme-text-primary">{doc.original_filename}</p>
                      <p className="text-sm text-theme-text-muted">
                        {new Date(doc.created_at).toLocaleDateString('de-DE')}
                        {doc.extracted_data?.gross_amount && (
                          <span className="ml-2">
                            • {doc.extracted_data.gross_amount.value} €
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <span className={clsx('flex items-center text-sm', status.color)}>
                      <StatusIcon className="h-4 w-4 mr-1" />
                      {status.label}
                    </span>

                    <Link
                      to={`/documents/${doc.id}`}
                      className="p-2 text-theme-text-muted hover:text-theme-text-primary"
                    >
                      <Eye className="h-5 w-5" />
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FileText className="h-12 w-12 text-theme-text-muted mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-theme-text-primary">Keine Dokumente</h3>
            <p className="mt-2 text-sm text-theme-text-muted">
              Laden Sie eine PDF-Rechnung hoch, um mit der Prüfung zu beginnen.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
