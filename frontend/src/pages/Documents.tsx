import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, CheckCircle, AlertTriangle, XCircle, Clock, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import { api } from '@/lib/api'

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
  const [uploading, setUploading] = useState(false)
  const queryClient = useQueryClient()

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)
    try {
      for (const file of acceptedFiles) {
        await uploadMutation.mutateAsync(file)
      }
    } finally {
      setUploading(false)
    }
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    disabled: uploading,
  })

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400',
          uploading && 'opacity-50 cursor-not-allowed'
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

      {/* Document List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Dokumente</h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-gray-500">Lade Dokumente...</div>
        ) : documents && documents.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {documents.map((doc: any) => {
              const status = statusConfig[doc.status as keyof typeof statusConfig] || statusConfig.UPLOADED
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
