import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Upload,
  FileJson,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Trash2,
  Play,
  Eye,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { SolutionFileListItem, SolutionPreviewResponse } from '@/lib/types'

interface SolutionFileUploadProps {
  projectId: string
  onApplied?: () => void
}

export default function SolutionFileUpload({
  projectId,
  onApplied,
}: SolutionFileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<SolutionFileListItem | null>(null)
  const [preview, setPreview] = useState<SolutionPreviewResponse | null>(null)
  const queryClient = useQueryClient()

  // Fetch existing solution files
  const { data: solutionFiles, isLoading } = useQuery({
    queryKey: ['solutionFiles', projectId],
    queryFn: () => api.getSolutionFiles(projectId),
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadSolutionFile(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['solutionFiles', projectId] })
    },
  })

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: (solutionFileId: string) =>
      api.previewSolutionMatching(projectId, solutionFileId),
    onSuccess: (data) => {
      setPreview(data)
    },
  })

  // Apply mutation
  const applyMutation = useMutation({
    mutationFn: (solutionFileId: string) =>
      api.applySolutionFile(projectId, solutionFileId, {
        create_rag_examples: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['solutionFiles', projectId] })
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      setPreview(null)
      setSelectedFile(null)
      onApplied?.()
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (solutionFileId: string) =>
      api.deleteSolutionFile(projectId, solutionFileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['solutionFiles', projectId] })
      setSelectedFile(null)
      setPreview(null)
    },
  })

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      setUploading(true)
      try {
        await uploadMutation.mutateAsync(acceptedFiles[0])
      } finally {
        setUploading(false)
      }
    },
    [uploadMutation]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'application/x-ndjson': ['.jsonl'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  const handlePreview = async (file: SolutionFileListItem) => {
    setSelectedFile(file)
    await previewMutation.mutateAsync(file.id)
  }

  const handleApply = async () => {
    if (!selectedFile) return
    await applyMutation.mutateAsync(selectedFile.id)
  }

  const handleDelete = async (file: SolutionFileListItem) => {
    if (confirm(`Lösungsdatei "${file.filename}" wirklich löschen?`)) {
      await deleteMutation.mutateAsync(file.id)
    }
  }

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-theme-primary bg-theme-primary/5'
            : 'border-theme-border hover:border-theme-primary/50',
          uploading && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-8 h-8 mx-auto mb-2 text-theme-text-muted" />
        {isDragActive ? (
          <p className="text-theme-text">Datei hier ablegen...</p>
        ) : (
          <div>
            <p className="text-theme-text font-medium">
              Lösungsdatei hochladen
            </p>
            <p className="text-sm text-theme-text-muted mt-1">
              JSON, JSONL oder CSV - Klicken oder hierher ziehen
            </p>
          </div>
        )}
      </div>

      {/* Existing Solution Files */}
      {isLoading ? (
        <div className="text-center text-theme-text-muted py-4">Laden...</div>
      ) : solutionFiles && solutionFiles.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-theme-text">
            Vorhandene Lösungsdateien
          </h4>
          <div className="space-y-2">
            {solutionFiles.map((file: SolutionFileListItem) => (
              <div
                key={file.id}
                className={clsx(
                  'flex items-center justify-between p-3 rounded-lg border',
                  selectedFile?.id === file.id
                    ? 'border-theme-primary bg-theme-primary/5'
                    : 'border-theme-border bg-theme-surface'
                )}
              >
                <div className="flex items-center gap-3">
                  <FileJson className="w-5 h-5 text-theme-text-muted" />
                  <div>
                    <p className="text-sm font-medium text-theme-text">
                      {file.filename}
                    </p>
                    <p className="text-xs text-theme-text-muted">
                      {file.entry_count} Einträge | {file.format}
                      {file.applied && (
                        <span className="ml-2 text-status-success">
                          Angewendet
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePreview(file)}
                    className="p-1.5 text-theme-text-muted hover:text-theme-primary transition-colors"
                    title="Vorschau"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(file)}
                    className="p-1.5 text-theme-text-muted hover:text-status-danger transition-colors"
                    title="Löschen"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Preview Panel */}
      {preview && selectedFile && (
        <div className="border border-theme-border rounded-lg p-4 bg-theme-surface">
          <h4 className="text-sm font-medium text-theme-text mb-3">
            Vorschau: {selectedFile.filename}
          </h4>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-theme-bg rounded-lg">
              <p className="text-2xl font-bold text-status-success">
                {preview.matched_count}
              </p>
              <p className="text-xs text-theme-text-muted">Zugeordnet</p>
            </div>
            <div className="text-center p-3 bg-theme-bg rounded-lg">
              <p className="text-2xl font-bold text-status-warning">
                {preview.unmatched_documents}
              </p>
              <p className="text-xs text-theme-text-muted">Ohne Lösung</p>
            </div>
            <div className="text-center p-3 bg-theme-bg rounded-lg">
              <p className="text-2xl font-bold text-theme-text-muted">
                {preview.unmatched_solutions}
              </p>
              <p className="text-xs text-theme-text-muted">Übrige Lösungen</p>
            </div>
            <div className="text-center p-3 bg-theme-bg rounded-lg">
              <p className="text-2xl font-bold text-theme-primary">
                {(preview.match_rate * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-theme-text-muted">Match-Rate</p>
            </div>
          </div>

          {/* Warnings */}
          {preview.warnings.length > 0 && (
            <div className="mb-4 p-3 bg-status-warning-bg border border-status-warning-border rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-status-warning">
                    Hinweise
                  </p>
                  <ul className="text-xs text-status-warning mt-1 space-y-1">
                    {preview.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Matches Table */}
          {preview.matches.length > 0 && (
            <div className="mb-4 max-h-60 overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-theme-bg sticky top-0">
                  <tr>
                    <th className="text-left p-2 font-medium text-theme-text-muted">
                      Dokument
                    </th>
                    <th className="text-left p-2 font-medium text-theme-text-muted">
                      Status
                    </th>
                    <th className="text-left p-2 font-medium text-theme-text-muted">
                      Fehler
                    </th>
                    <th className="text-right p-2 font-medium text-theme-text-muted">
                      Konfidenz
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-theme-border">
                  {preview.matches.slice(0, 10).map((match) => (
                    <tr key={match.document_id}>
                      <td className="p-2 text-theme-text">
                        {match.document_filename}
                      </td>
                      <td className="p-2">
                        {match.is_valid ? (
                          <span className="inline-flex items-center gap-1 text-status-success">
                            <CheckCircle className="w-4 h-4" />
                            OK
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-status-danger">
                            <XCircle className="w-4 h-4" />
                            Fehler
                          </span>
                        )}
                      </td>
                      <td className="p-2 text-theme-text-muted">
                        {match.error_count > 0 ? (
                          <span className="text-status-danger">
                            {match.error_count} Fehler
                          </span>
                        ) : (
                          <span>-</span>
                        )}
                      </td>
                      <td className="p-2 text-right">
                        <span
                          className={clsx(
                            match.confidence >= 0.8
                              ? 'text-status-success'
                              : match.confidence >= 0.6
                              ? 'text-status-warning'
                              : 'text-status-danger'
                          )}
                        >
                          {(match.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {preview.matches.length > 10 && (
                <p className="text-xs text-theme-text-muted text-center py-2">
                  ... und {preview.matches.length - 10} weitere
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setPreview(null)
                setSelectedFile(null)
              }}
              className="px-4 py-2 text-sm text-theme-text-muted hover:text-theme-text transition-colors"
            >
              Abbrechen
            </button>
            <button
              onClick={handleApply}
              disabled={applyMutation.isPending || preview.matched_count === 0}
              className={clsx(
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                'bg-theme-primary text-white hover:bg-theme-primary-hover',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'inline-flex items-center gap-2'
              )}
            >
              <Play className="w-4 h-4" />
              {applyMutation.isPending
                ? 'Wird angewendet...'
                : `${preview.matched_count} Zuordnungen anwenden`}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
