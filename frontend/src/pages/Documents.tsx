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
  UPLOADED: { icon: Clock, color: 'text-gray-500', label: 'Hochgeladen' },
  PARSING: { icon: Clock, color: 'text-blue-500', label: 'Parsing...' },
  VALIDATING: { icon: Clock, color: 'text-blue-500', label: 'Validiere...' },
  VALIDATED: { icon: CheckCircle, color: 'text-green-500', label: 'Validiert' },
  ANALYZING: { icon: Clock, color: 'text-yellow-500', label: 'Analysiere...' },
  ANALYZED: { icon: CheckCircle, color: 'text-green-500', label: 'Analysiert' },
  REVIEWED: { icon: CheckCircle, color: 'text-green-500', label: 'Geprüft' },
  EXPORTED: { icon: CheckCircle, color: 'text-green-500', label: 'Exportiert' },
  ERROR: { icon: XCircle, color: 'text-red-500', label: 'Fehler' },
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
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-red-600" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-red-800">{t('common.error')}</h3>
            <p className="text-sm text-red-600 mt-1">
              {t('errors.network')}
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center"
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
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center">
          <FolderOpen className="h-6 w-6 text-yellow-600" />
          <div className="ml-3">
            <h3 className="text-lg font-medium text-yellow-800">Kein Projekt vorhanden</h3>
            <p className="text-sm text-yellow-600 mt-1">
              Bitte erstellen Sie zuerst ein Projekt, bevor Sie Dokumente hochladen.
            </p>
          </div>
        </div>
        <Link
          to="/projects"
          className="mt-4 inline-block px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
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
          <label htmlFor="project-select" className="text-sm font-medium text-gray-700">
            Projekt:
          </label>
          <select
            id="project-select"
            value={activeProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="block w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
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
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400',
          (uploading || !activeProjectId) && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload className={clsx(
          'h-12 w-12 mx-auto',
          isDragActive ? 'text-primary-500' : 'text-gray-400'
        )} />
        <p className="mt-4 text-lg font-medium text-gray-900">
          {uploading ? 'Wird hochgeladen...' :
           isDragActive ? 'Hier ablegen' : 'PDF-Rechnung hochladen'}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Ziehen Sie eine PDF-Datei hierher oder klicken Sie zum Auswählen
        </p>
      </div>

      {/* Upload Errors */}
      {uploadErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {uploadErrors.length === 1 ? 'Upload fehlgeschlagen' : `${uploadErrors.length} Uploads fehlgeschlagen`}
              </h3>
              <ul className="mt-2 text-sm text-red-600 list-disc list-inside">
                {uploadErrors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
              <button
                onClick={() => setUploadErrors([])}
                className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Dokumente</h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500">Lade Dokumente...</div>
        ) : documents && documents.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {documents.map((doc: Document) => {
              const status = statusConfig[doc.status as DocumentStatus] || statusConfig.UPLOADED
              const StatusIcon = status.icon

              return (
                <div
                  key={doc.id}
                  className="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
                >
                  <div className="flex items-center">
                    <FileText className="h-8 w-8 text-gray-400" />
                    <div className="ml-4">
                      <p className="font-medium text-gray-900">{doc.original_filename}</p>
                      <p className="text-sm text-gray-500">
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
                      className="p-2 text-gray-400 hover:text-gray-600"
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
            <FileText className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Keine Dokumente</h3>
            <p className="mt-2 text-sm text-gray-500">
              Laden Sie eine PDF-Rechnung hoch, um mit der Prüfung zu beginnen.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
