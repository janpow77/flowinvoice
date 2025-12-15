import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, AlertTriangle, XCircle, Play, ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { PrecheckError } from '@/lib/types'

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<'CORRECT' | 'INCORRECT' | null>(null)

  const { data: document, isLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.getDocument(id!),
    enabled: !!id,
  })

  const analyzeMutation = useMutation({
    mutationFn: () => api.analyzeDocument(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] })
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: (rating: 'CORRECT' | 'INCORRECT') =>
      api.submitFeedback({
        document_id: id!,
        result_id: document?.analysis_result?.id || id!,
        rating: rating === 'CORRECT' ? 'CORRECT' : 'INCORRECT',
      }),
    onSuccess: (_, rating) => {
      setFeedbackSubmitted(rating)
      queryClient.invalidateQueries({ queryKey: ['document', id] })
    },
  })

  if (isLoading) {
    return <div className="animate-pulse">Lade Dokument...</div>
  }

  if (!document) {
    return <div>Dokument nicht gefunden</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{document.original_filename}</h2>
          <p className="text-sm text-gray-500">
            Hochgeladen: {new Date(document.created_at).toLocaleDateString('de-DE')}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {document.status === 'VALIDATED' && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <Play className="h-4 w-4 mr-2" />
              {analyzeMutation.isPending ? 'Analysiere...' : 'KI-Analyse starten'}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extracted Data */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Extrahierte Daten</h3>

          {document.extracted_data ? (
            <div className="space-y-3">
              {Object.entries(document.extracted_data).map(([key, val]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-sm text-gray-500">{key}</span>
                  <span className="text-sm font-medium text-gray-900">
                    {(val as { value?: string })?.value || '-'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Keine Daten extrahiert</p>
          )}
        </div>

        {/* Precheck Errors */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vorprüfung</h3>

          {document.precheck_errors && document.precheck_errors.length > 0 ? (
            <div className="space-y-2">
              {document.precheck_errors.map((error: PrecheckError, i: number) => (
                <div
                  key={i}
                  className={clsx(
                    'p-3 rounded-lg flex items-start',
                    error.severity === 'HIGH' ? 'bg-red-50' :
                    error.severity === 'MEDIUM' ? 'bg-yellow-50' : 'bg-gray-50'
                  )}
                >
                  {error.severity === 'HIGH' ? (
                    <XCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0" />
                  ) : error.severity === 'MEDIUM' ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-gray-400 mr-2 flex-shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{error.feature_id}</p>
                    <p className="text-sm text-gray-500">{error.message}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : document.precheck_passed ? (
            <div className="flex items-center text-green-600">
              <CheckCircle className="h-5 w-5 mr-2" />
              <span>Alle Vorprüfungen bestanden</span>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Keine Vorprüfung durchgeführt</p>
          )}
        </div>

        {/* Analysis Result */}
        {document.analysis_result && (
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">KI-Analyse</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Overall Assessment */}
              <div className={clsx(
                'p-4 rounded-lg',
                document.analysis_result.overall_assessment === 'ok' ? 'bg-green-50' :
                document.analysis_result.overall_assessment === 'review_needed' ? 'bg-yellow-50' :
                document.analysis_result.overall_assessment === 'rejected' ? 'bg-red-50' :
                'bg-gray-50'
              )}>
                <p className="text-sm font-medium text-gray-500">Gesamtbewertung</p>
                <p className={clsx(
                  'text-lg font-semibold',
                  document.analysis_result.overall_assessment === 'ok' ? 'text-green-700' :
                  document.analysis_result.overall_assessment === 'review_needed' ? 'text-yellow-700' :
                  document.analysis_result.overall_assessment === 'rejected' ? 'text-red-700' :
                  'text-gray-700'
                )}>
                  {document.analysis_result.overall_assessment === 'ok' ? 'In Ordnung' :
                   document.analysis_result.overall_assessment === 'review_needed' ? 'Prüfung erforderlich' :
                   document.analysis_result.overall_assessment === 'rejected' ? 'Abgelehnt' :
                   document.analysis_result.overall_assessment || 'Unbekannt'}
                </p>
              </div>

              {/* Confidence */}
              <div className="p-4 rounded-lg bg-gray-50">
                <p className="text-sm font-medium text-gray-500">Konfidenz</p>
                <p className="text-lg font-semibold text-gray-900">
                  {document.analysis_result.confidence != null
                    ? `${Math.round(document.analysis_result.confidence * 100)}%`
                    : '-'}
                </p>
              </div>

              {/* Provider */}
              <div className="p-4 rounded-lg bg-gray-50">
                <p className="text-sm font-medium text-gray-500">Provider</p>
                <p className="text-lg font-semibold text-gray-900">
                  {document.analysis_result.provider || 'Unbekannt'}
                </p>
              </div>
            </div>

            {/* Feedback Buttons */}
            <div className="mt-6 flex items-center space-x-4">
              <span className="text-sm text-gray-500">War diese Analyse korrekt?</span>
              {feedbackSubmitted ? (
                <span className={clsx(
                  'flex items-center px-3 py-1 text-sm rounded-lg',
                  feedbackSubmitted === 'CORRECT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                )}>
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Feedback gesendet
                </span>
              ) : (
                <>
                  <button
                    onClick={() => feedbackMutation.mutate('CORRECT')}
                    disabled={feedbackMutation.isPending}
                    className="flex items-center px-3 py-1 text-sm text-green-600 border border-green-200 rounded-lg hover:bg-green-50 disabled:opacity-50"
                  >
                    {feedbackMutation.isPending ? (
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <ThumbsUp className="h-4 w-4 mr-1" />
                    )}
                    Ja
                  </button>
                  <button
                    onClick={() => feedbackMutation.mutate('INCORRECT')}
                    disabled={feedbackMutation.isPending}
                    className="flex items-center px-3 py-1 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
                  >
                    {feedbackMutation.isPending ? (
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <ThumbsDown className="h-4 w-4 mr-1" />
                    )}
                    Nein
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
