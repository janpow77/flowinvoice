import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  ArrowLeft,
  Edit2,
  Save,
  X,
  Clock,
  FileText,
  ChevronDown,
  ChevronUp,
  Shield,
  Brain,
  TrendingUp,
  UserCheck,
  Info,
  Target,
  GitMerge,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { PrecheckError, FeatureStatus, RiskFinding } from '@/lib/types'
import { PDFViewer, DocumentSplitView, FeatureStatusBadge } from '@/components/documents'

interface FieldCorrection {
  feature_id: string
  original_value: string | number | null
  corrected_value: string | number | null
}

export default function DocumentDetail() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<'CORRECT' | 'INCORRECT' | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editedFields, setEditedFields] = useState<Record<string, string>>({})
  const [showAllFields, setShowAllFields] = useState(false)
  const [corrections, setCorrections] = useState<FieldCorrection[]>([])

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
    mutationFn: (params: { rating: 'CORRECT' | 'INCORRECT'; corrections?: FieldCorrection[] }) =>
      api.submitFeedback({
        document_id: id!,
        result_id: document?.analysis_result?.id || id!,
        rating: params.rating,
        corrections: params.corrections?.map(c => ({
          feature_id: c.feature_id,
          user_value: c.corrected_value,
        })),
      }),
    onSuccess: (_, params) => {
      setFeedbackSubmitted(params.rating)
      setIsEditing(false)
      setCorrections([])
      queryClient.invalidateQueries({ queryKey: ['document', id] })
    },
  })

  const startEditing = () => {
    if (document?.extracted_data) {
      const fields: Record<string, string> = {}
      Object.entries(document.extracted_data).forEach(([key, val]) => {
        fields[key] = String((val as { value?: string | number })?.value || '')
      })
      setEditedFields(fields)
      setIsEditing(true)
    }
  }

  const handleFieldChange = (key: string, value: string) => {
    setEditedFields(prev => ({ ...prev, [key]: value }))

    // Track correction
    const originalValue = (document?.extracted_data?.[key] as { value?: string | number })?.value || null
    const existingIndex = corrections.findIndex(c => c.feature_id === key)

    if (existingIndex >= 0) {
      const newCorrections = [...corrections]
      if (String(originalValue) === value) {
        // Remove correction if value is back to original
        newCorrections.splice(existingIndex, 1)
      } else {
        newCorrections[existingIndex] = {
          feature_id: key,
          original_value: originalValue,
          corrected_value: value,
        }
      }
      setCorrections(newCorrections)
    } else if (String(originalValue) !== value) {
      setCorrections(prev => [...prev, {
        feature_id: key,
        original_value: originalValue,
        corrected_value: value,
      }])
    }
  }

  const cancelEditing = () => {
    setIsEditing(false)
    setEditedFields({})
    setCorrections([])
  }

  const submitWithCorrections = () => {
    feedbackMutation.mutate({
      rating: corrections.length > 0 ? 'INCORRECT' : 'CORRECT',
      corrections: corrections.length > 0 ? corrections : undefined,
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 text-theme-primary animate-spin" />
      </div>
    )
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-theme-text-muted mx-auto mb-4" />
        <p className="text-theme-text-muted">{t('documentDetail.notFound')}</p>
        <Link to="/documents" className="mt-4 text-theme-primary hover:underline">
          {t('documentDetail.backToOverview')}
        </Link>
      </div>
    )
  }

  // Get feature status based on precheck errors
  const getFeatureStatus = (featureId: string): FeatureStatus => {
    const error = document.precheck_errors?.find((e: PrecheckError) => e.feature_id === featureId)
    if (!error) return 'VALID'
    if (error.severity === 'HIGH') return 'INVALID'
    if (error.severity === 'MEDIUM') return 'WARNING'
    return 'MISSING'
  }

  // Prepare fields for display
  const allFields = Object.entries(document.extracted_data || {})
  const displayFields = showAllFields ? allFields : allFields.slice(0, 8)

  // Right panel content (document details)
  const detailsPanel = (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/documents"
            className="p-2 hover:bg-theme-hover rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-theme-text-muted" />
          </Link>
          <div>
            <h2 className="text-xl font-semibold text-theme-text-primary">
              {document.original_filename}
            </h2>
            <p className="text-sm text-theme-text-muted">
              {t('documentDetail.uploadedOn')}: {new Date(document.created_at).toLocaleDateString('de-DE')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing && document.status === 'VALIDATED' && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="flex items-center px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover disabled:opacity-50"
            >
              <Play className="h-4 w-4 mr-2" />
              {analyzeMutation.isPending ? t('documentDetail.analyzing') : t('documentDetail.startAnalysis')}
            </button>
          )}
          {!isEditing && document.analysis_result && !feedbackSubmitted && (
            <button
              onClick={startEditing}
              className="flex items-center px-4 py-2 border border-theme-border text-theme-text rounded-lg hover:bg-theme-hover"
            >
              <Edit2 className="h-4 w-4 mr-2" />
              {t('documentDetail.correct')}
            </button>
          )}
        </div>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-theme-surface rounded-lg p-4 border border-theme-border">
          <p className="text-sm text-theme-text-muted">{t('documents.status')}</p>
          <div className="flex items-center gap-2 mt-1">
            {document.status === 'ANALYZED' ? (
              <CheckCircle className="h-5 w-5 text-status-success" />
            ) : document.status === 'ERROR' ? (
              <XCircle className="h-5 w-5 text-status-danger" />
            ) : (
              <Clock className="h-5 w-5 text-status-warning" />
            )}
            <span className="font-medium text-theme-text">{document.status}</span>
          </div>
        </div>

        {document.analysis_result && (
          <>
            <div
              className={clsx(
                'rounded-lg p-4 border',
                document.analysis_result.overall_assessment === 'ok'
                  ? 'bg-status-success-bg border-status-success-border'
                  : document.analysis_result.overall_assessment === 'review_needed'
                  ? 'bg-status-warning-bg border-status-warning-border'
                  : 'bg-status-danger-bg border-status-danger-border'
              )}
            >
              <p className="text-sm text-theme-text-muted">{t('documentDetail.assessment')}</p>
              <p className="font-medium mt-1">
                {document.analysis_result.overall_assessment === 'ok'
                  ? t('documentDetail.assessmentOk')
                  : document.analysis_result.overall_assessment === 'review_needed'
                  ? t('documentDetail.assessmentReview')
                  : t('documentDetail.assessmentRejected')}
              </p>
            </div>

            <div className="bg-theme-surface rounded-lg p-4 border border-theme-border">
              <p className="text-sm text-theme-text-muted">{t('documentDetail.confidence')}</p>
              <p className="font-medium mt-1 text-theme-text">
                {document.analysis_result.confidence != null
                  ? `${Math.round(document.analysis_result.confidence * 100)}%`
                  : '-'}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Extracted Fields */}
      <div className="bg-theme-card rounded-lg border border-theme-border">
        <div className="px-4 py-3 border-b border-theme-border flex items-center justify-between">
          <h3 className="font-semibold text-theme-text-primary">{t('documentDetail.extractedData')}</h3>
          {isEditing && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-theme-text-muted">
                {t('documentDetail.correctionsCount', { count: corrections.length })}
              </span>
            </div>
          )}
        </div>

        <div className="p-4 space-y-3">
          {displayFields.map(([key, val]) => {
            const value = (val as { value?: string | number })?.value
            const confidence = (val as { confidence?: number })?.confidence
            const status = getFeatureStatus(key)
            const isChanged = corrections.some(c => c.feature_id === key)

            return (
              <div
                key={key}
                className={clsx(
                  'flex items-start justify-between p-3 rounded-lg',
                  isEditing
                    ? isChanged
                      ? 'bg-status-warning-bg border border-status-warning-border'
                      : 'bg-theme-hover'
                    : 'bg-theme-hover'
                )}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <FeatureStatusBadge status={status} showLabel={false} size="sm" />
                  <span className="text-sm text-theme-text-muted truncate">
                    {key.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedFields[key] || ''}
                      onChange={e => handleFieldChange(key, e.target.value)}
                      className={clsx(
                        'px-2 py-1 text-sm border rounded',
                        isChanged
                          ? 'border-status-warning bg-white'
                          : 'border-theme-border bg-theme-surface'
                      )}
                    />
                  ) : (
                    <>
                      <span className="text-sm font-medium text-theme-text text-right">
                        {value || '-'}
                      </span>
                      {confidence !== undefined && (
                        <span className="text-xs text-theme-text-muted">
                          ({Math.round(confidence * 100)}%)
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
            )
          })}

          {allFields.length > 8 && (
            <button
              onClick={() => setShowAllFields(!showAllFields)}
              className="w-full flex items-center justify-center gap-1 py-2 text-sm text-theme-primary hover:underline"
            >
              {showAllFields ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  {t('documentDetail.showLess')}
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  {t('documentDetail.showAllFields', { count: allFields.length })}
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Precheck Errors */}
      {document.precheck_errors && document.precheck_errors.length > 0 && (
        <div className="bg-theme-card rounded-lg border border-theme-border">
          <div className="px-4 py-3 border-b border-theme-border">
            <h3 className="font-semibold text-theme-text-primary">{t('documentDetail.precheck')}</h3>
          </div>
          <div className="p-4 space-y-2">
            {document.precheck_errors.map((error: PrecheckError, i: number) => (
              <div
                key={i}
                className={clsx(
                  'p-3 rounded-lg flex items-start',
                  error.severity === 'HIGH'
                    ? 'bg-status-danger-bg'
                    : error.severity === 'MEDIUM'
                    ? 'bg-status-warning-bg'
                    : 'bg-theme-hover'
                )}
              >
                {error.severity === 'HIGH' ? (
                  <XCircle className="h-5 w-5 text-status-danger mr-2 flex-shrink-0" />
                ) : error.severity === 'MEDIUM' ? (
                  <AlertTriangle className="h-5 w-5 text-status-warning mr-2 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-theme-text-muted mr-2 flex-shrink-0" />
                )}
                <div>
                  <p className="text-sm font-medium text-theme-text">{error.feature_id}</p>
                  <p className="text-sm text-theme-text-muted">{error.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Check Results Section (Risk, Semantic, Economic) */}
      {document.analysis_result && (
        <div className="bg-theme-card rounded-lg border border-theme-border">
          <div className="px-4 py-3 border-b border-theme-border flex items-center justify-between">
            <h3 className="font-semibold text-theme-text-primary">{t('checkResults.title')}</h3>
            <div className="flex items-center gap-1">
              <Info className="h-4 w-4 text-theme-text-muted" />
              <span className="text-xs text-theme-text-muted">{t('checkResults.trainingView')}</span>
            </div>
          </div>
          <div className="p-4 space-y-4">
            {/* Risk Assessment */}
            {document.analysis_result.risk_assessment && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className={clsx(
                  'px-4 py-2 flex items-center gap-3',
                  document.analysis_result.risk_assessment.highest_severity === 'HIGH' ||
                  document.analysis_result.risk_assessment.highest_severity === 'CRITICAL'
                    ? 'bg-status-danger-bg'
                    : document.analysis_result.risk_assessment.highest_severity === 'MEDIUM'
                    ? 'bg-status-warning-bg'
                    : 'bg-status-success-bg'
                )}>
                  <Shield className="h-5 w-5" />
                  <span className="font-medium">{t('risk.check')}</span>
                  <span className="text-sm ml-auto">
                    {t('risk.score')}: {document.analysis_result.risk_assessment.risk_score}/100
                  </span>
                </div>
                {document.analysis_result.risk_assessment.findings?.length > 0 ? (
                  <div className="p-3 space-y-2">
                    {document.analysis_result.risk_assessment.findings.map((finding: RiskFinding, i: number) => (
                      <div key={i} className={clsx(
                        'p-2 rounded text-sm flex items-start gap-2',
                        finding.severity === 'HIGH' || finding.severity === 'CRITICAL'
                          ? 'bg-status-danger-bg'
                          : finding.severity === 'MEDIUM'
                          ? 'bg-status-warning-bg'
                          : 'bg-theme-hover'
                      )}>
                        <span className="font-mono text-xs px-1 py-0.5 rounded bg-theme-surface">
                          {finding.severity}
                        </span>
                        <span>{finding.message}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 text-sm text-status-success flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    {t('risk.noIndicators')}
                  </div>
                )}
              </div>
            )}

            {/* Semantic Check */}
            {document.analysis_result.semantic_check && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className={clsx(
                  'px-4 py-2 flex items-center gap-3',
                  document.analysis_result.semantic_check.passed
                    ? 'bg-status-success-bg'
                    : 'bg-status-warning-bg'
                )}>
                  <Brain className="h-5 w-5" />
                  <span className="font-medium">{t('checkResults.semantic.title')}</span>
                  {document.analysis_result.semantic_check.project_relevance_score !== undefined && (
                    <span className="text-sm ml-auto">
                      {t('checkResults.semantic.projectRelevance')}: {Math.round(document.analysis_result.semantic_check.project_relevance_score * 100)}%
                    </span>
                  )}
                </div>
                <div className="p-3 space-y-2">
                  {document.analysis_result.semantic_check.message && (
                    <p className="text-sm text-theme-text-muted">
                      {document.analysis_result.semantic_check.message}
                    </p>
                  )}
                  {document.analysis_result.semantic_check.red_flags &&
                   document.analysis_result.semantic_check.red_flags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {document.analysis_result.semantic_check.red_flags.map((flag: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 text-xs bg-status-danger-bg text-status-danger rounded-full">
                          {flag}
                        </span>
                      ))}
                    </div>
                  )}
                  {document.analysis_result.semantic_check.passed && (
                    <div className="text-sm text-status-success flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      {t('checkResults.semantic.passed')}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Economic Check */}
            {document.analysis_result.economic_check && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className={clsx(
                  'px-4 py-2 flex items-center gap-3',
                  document.analysis_result.economic_check.passed
                    ? 'bg-status-success-bg'
                    : 'bg-status-warning-bg'
                )}>
                  <TrendingUp className="h-5 w-5" />
                  <span className="font-medium">{t('checkResults.economic.title')}</span>
                </div>
                <div className="p-3 space-y-2">
                  {document.analysis_result.economic_check.message && (
                    <p className="text-sm text-theme-text-muted">
                      {document.analysis_result.economic_check.message}
                    </p>
                  )}
                  {document.analysis_result.economic_check.budget_check && (
                    <div className={clsx(
                      'p-2 rounded text-sm flex items-center gap-2',
                      document.analysis_result.economic_check.budget_check.passed
                        ? 'bg-status-success-bg text-status-success'
                        : 'bg-status-danger-bg text-status-danger'
                    )}>
                      {document.analysis_result.economic_check.budget_check.passed ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                      {t('documentDetail.budgetCheck')}: {document.analysis_result.economic_check.budget_check.message || (
                        document.analysis_result.economic_check.budget_check.passed ? t('common.success') : t('documentDetail.notPassed')
                      )}
                    </div>
                  )}
                  {document.analysis_result.economic_check.price_check && (
                    <div className={clsx(
                      'p-2 rounded text-sm flex items-center gap-2',
                      document.analysis_result.economic_check.price_check.passed
                        ? 'bg-status-success-bg text-status-success'
                        : 'bg-status-warning-bg text-status-warning'
                    )}>
                      {document.analysis_result.economic_check.price_check.passed ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <AlertTriangle className="h-4 w-4" />
                      )}
                      {t('documentDetail.priceCheck')}: {document.analysis_result.economic_check.price_check.message || (
                        document.analysis_result.economic_check.price_check.passed ? t('common.success') : t('documentDetail.deviationDetected')
                      )}
                      {document.analysis_result.economic_check.price_check.deviation_percent !== undefined && (
                        <span className="ml-auto font-mono text-xs">
                          {document.analysis_result.economic_check.price_check.deviation_percent > 0 ? '+' : ''}
                          {document.analysis_result.economic_check.price_check.deviation_percent.toFixed(1)}%
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Beneficiary Match */}
            {document.analysis_result.beneficiary_match && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className={clsx(
                  'px-4 py-2 flex items-center gap-3',
                  document.analysis_result.beneficiary_match.matched
                    ? 'bg-status-success-bg'
                    : 'bg-status-warning-bg'
                )}>
                  <UserCheck className="h-5 w-5" />
                  <span className="font-medium">{t('checkResults.beneficiary.title')}</span>
                  {document.analysis_result.beneficiary_match.confidence !== undefined && (
                    <span className="text-sm ml-auto">
                      {t('documentDetail.confidence')}: {Math.round(document.analysis_result.beneficiary_match.confidence * 100)}%
                    </span>
                  )}
                </div>
                <div className="p-3">
                  {document.analysis_result.beneficiary_match.message ? (
                    <p className="text-sm text-theme-text-muted">
                      {document.analysis_result.beneficiary_match.message}
                    </p>
                  ) : document.analysis_result.beneficiary_match.matched ? (
                    <div className="text-sm text-status-success flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      {t('checkResults.beneficiary.matched')}
                    </div>
                  ) : (
                    <div className="text-sm space-y-1">
                      {document.analysis_result.beneficiary_match.expected_name && (
                        <p>{t('checkResults.beneficiary.expected')}: <span className="font-medium">{document.analysis_result.beneficiary_match.expected_name}</span></p>
                      )}
                      {document.analysis_result.beneficiary_match.found_name && (
                        <p>{t('checkResults.beneficiary.found')}: <span className="font-medium">{document.analysis_result.beneficiary_match.found_name}</span></p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Grant Purpose Audit */}
            {document.analysis_result.grant_purpose_audit && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className={clsx(
                  'px-4 py-2 flex items-center gap-3',
                  document.analysis_result.grant_purpose_audit.overall_result === 'PASS'
                    ? 'bg-status-success-bg'
                    : document.analysis_result.grant_purpose_audit.overall_result === 'FAIL'
                    ? 'bg-status-danger-bg'
                    : 'bg-status-warning-bg'
                )}>
                  <Target className="h-5 w-5" />
                  <span className="font-medium">{t('checkResults.grantPurpose.title')}</span>
                </div>
                <div className="p-3 space-y-3">
                  {/* Dimension Results */}
                  <div className="grid grid-cols-2 gap-2">
                    {document.analysis_result.grant_purpose_audit.subject_relation && (
                      <div className={clsx(
                        'p-2 rounded text-sm',
                        document.analysis_result.grant_purpose_audit.subject_relation.result === 'PASS'
                          ? 'bg-status-success-bg'
                          : document.analysis_result.grant_purpose_audit.subject_relation.result === 'FAIL'
                          ? 'bg-status-danger-bg'
                          : 'bg-status-warning-bg'
                      )}>
                        <div className="font-medium">{t('checkResults.grantPurpose.subjectRelation')}</div>
                        <div className="text-xs opacity-75">{document.analysis_result.grant_purpose_audit.subject_relation.result}</div>
                      </div>
                    )}
                    {document.analysis_result.grant_purpose_audit.temporal_relation && (
                      <div className={clsx(
                        'p-2 rounded text-sm',
                        document.analysis_result.grant_purpose_audit.temporal_relation.result === 'PASS'
                          ? 'bg-status-success-bg'
                          : document.analysis_result.grant_purpose_audit.temporal_relation.result === 'FAIL'
                          ? 'bg-status-danger-bg'
                          : 'bg-status-warning-bg'
                      )}>
                        <div className="font-medium">{t('checkResults.grantPurpose.temporalRelation')}</div>
                        <div className="text-xs opacity-75">{document.analysis_result.grant_purpose_audit.temporal_relation.result}</div>
                      </div>
                    )}
                    {document.analysis_result.grant_purpose_audit.organizational_relation && (
                      <div className={clsx(
                        'p-2 rounded text-sm',
                        document.analysis_result.grant_purpose_audit.organizational_relation.result === 'PASS'
                          ? 'bg-status-success-bg'
                          : document.analysis_result.grant_purpose_audit.organizational_relation.result === 'FAIL'
                          ? 'bg-status-danger-bg'
                          : 'bg-status-warning-bg'
                      )}>
                        <div className="font-medium">{t('checkResults.grantPurpose.organizationalRelation')}</div>
                        <div className="text-xs opacity-75">{document.analysis_result.grant_purpose_audit.organizational_relation.result}</div>
                      </div>
                    )}
                    {document.analysis_result.grant_purpose_audit.economic_plausibility && (
                      <div className={clsx(
                        'p-2 rounded text-sm',
                        document.analysis_result.grant_purpose_audit.economic_plausibility.result === 'PASS'
                          ? 'bg-status-success-bg'
                          : document.analysis_result.grant_purpose_audit.economic_plausibility.result === 'FAIL'
                          ? 'bg-status-danger-bg'
                          : 'bg-status-warning-bg'
                      )}>
                        <div className="font-medium">{t('checkResults.grantPurpose.economicPlausibility')}</div>
                        <div className="text-xs opacity-75">{document.analysis_result.grant_purpose_audit.economic_plausibility.result}</div>
                      </div>
                    )}
                  </div>

                  {/* Overall Reasoning */}
                  {document.analysis_result.grant_purpose_audit.overall_reasoning && (
                    <div className="text-sm text-theme-text-muted border-t border-theme-border pt-2">
                      {document.analysis_result.grant_purpose_audit.overall_reasoning}
                    </div>
                  )}

                  {/* Negative Indicators */}
                  {document.analysis_result.grant_purpose_audit.negative_indicators &&
                   document.analysis_result.grant_purpose_audit.negative_indicators.length > 0 && (
                    <div className="space-y-1">
                      {document.analysis_result.grant_purpose_audit.negative_indicators.map((indicator: { description: string; severity: string }, i: number) => (
                        <div key={i} className={clsx(
                          'p-2 rounded text-sm flex items-start gap-2',
                          indicator.severity === 'HIGH' ? 'bg-status-danger-bg' : 'bg-status-warning-bg'
                        )}>
                          <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                          <span>{indicator.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Conflict Resolution */}
            {document.analysis_result.conflicts && document.analysis_result.conflicts.length > 0 && (
              <div className="border border-theme-border rounded-lg overflow-hidden">
                <div className="px-4 py-2 bg-status-warning-bg flex items-center gap-3">
                  <GitMerge className="h-5 w-5 text-status-warning" />
                  <span className="font-medium">{t('checkResults.conflicts.title')}</span>
                  <span className="text-sm ml-auto">
                    {t('checkResults.conflicts.count', { count: document.analysis_result.conflicts.length })}
                  </span>
                </div>
                <div className="p-3 space-y-2">
                  {document.analysis_result.conflicts.map((conflict: { field: string; rule_value: string; llm_value: string; resolved_by: string; resolved_value: string }, i: number) => (
                    <div key={i} className="p-2 rounded bg-theme-hover text-sm">
                      <div className="font-medium mb-1">{conflict.field}</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-theme-text-muted">{t('checkResults.conflicts.rule')}:</span> {conflict.rule_value || '-'}
                        </div>
                        <div>
                          <span className="text-theme-text-muted">{t('checkResults.conflicts.ai')}:</span> {conflict.llm_value || '-'}
                        </div>
                      </div>
                      <div className="mt-1 text-xs">
                        <span className="text-theme-text-muted">{t('checkResults.conflicts.resolvedBy')}:</span>{' '}
                        <span className="font-medium">{conflict.resolved_by}</span> → {conflict.resolved_value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {document.analysis_result.warnings && document.analysis_result.warnings.length > 0 && (
              <div className="border border-status-warning-border rounded-lg overflow-hidden">
                <div className="px-4 py-2 bg-status-warning-bg flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-status-warning" />
                  <span className="font-medium">{t('checkResults.warnings', { count: document.analysis_result.warnings.length })}</span>
                </div>
                <div className="p-3 space-y-1">
                  {document.analysis_result.warnings.map((warning: string, i: number) => (
                    <p key={i} className="text-sm text-theme-text-muted flex items-start gap-2">
                      <span className="text-status-warning">•</span>
                      {warning}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* No checks available */}
            {!document.analysis_result.risk_assessment &&
             !document.analysis_result.semantic_check &&
             !document.analysis_result.economic_check &&
             !document.analysis_result.beneficiary_match &&
             !document.analysis_result.grant_purpose_audit &&
             (!document.analysis_result.conflicts || document.analysis_result.conflicts.length === 0) &&
             (!document.analysis_result.warnings || document.analysis_result.warnings.length === 0) && (
              <div className="text-center py-4 text-theme-text-muted">
                <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>{t('checkResults.noResults')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Feedback Section */}
      {document.analysis_result && (
        <div className="bg-theme-card rounded-lg border border-theme-border p-4">
          {feedbackSubmitted ? (
            <div
              className={clsx(
                'flex items-center gap-2 px-4 py-3 rounded-lg',
                feedbackSubmitted === 'CORRECT'
                  ? 'bg-status-success-bg text-status-success'
                  : 'bg-status-warning-bg text-status-warning'
              )}
            >
              <CheckCircle className="h-5 w-5" />
              <span>
                {feedbackSubmitted === 'CORRECT'
                  ? t('documentDetail.feedback.confirmed')
                  : t('documentDetail.feedback.correctionsSent', { count: corrections.length })}
              </span>
            </div>
          ) : isEditing ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-theme-text-muted">
                  {t('documentDetail.feedback.editHint')}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={cancelEditing}
                  className="flex items-center px-4 py-2 border border-theme-border text-theme-text rounded-lg hover:bg-theme-hover"
                >
                  <X className="h-4 w-4 mr-2" />
                  {t('common.cancel')}
                </button>
                <button
                  onClick={submitWithCorrections}
                  disabled={feedbackMutation.isPending}
                  className={clsx(
                    'flex items-center px-4 py-2 rounded-lg',
                    corrections.length > 0
                      ? 'bg-status-warning text-white hover:bg-status-warning/90'
                      : 'bg-status-success text-white hover:bg-status-success/90',
                    'disabled:opacity-50'
                  )}
                >
                  {feedbackMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  {corrections.length > 0
                    ? t('documentDetail.feedback.saveCorrections', { count: corrections.length })
                    : t('documentDetail.feedback.confirmCorrect')}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <span className="text-sm text-theme-text-muted">{t('documentDetail.feedback.question')}</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => feedbackMutation.mutate({ rating: 'CORRECT' })}
                  disabled={feedbackMutation.isPending}
                  className="flex items-center px-3 py-1 text-sm text-status-success border border-status-success-border rounded-lg hover:bg-status-success-bg disabled:opacity-50"
                >
                  {feedbackMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <ThumbsUp className="h-4 w-4 mr-1" />
                  )}
                  {t('common.yes')}
                </button>
                <button
                  onClick={startEditing}
                  className="flex items-center px-3 py-1 text-sm text-status-danger border border-status-danger-border rounded-lg hover:bg-status-danger-bg"
                >
                  <ThumbsDown className="h-4 w-4 mr-1" />
                  {t('documentDetail.feedback.noCorrect')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <div className="h-[calc(100vh-8rem)]">
      <DocumentSplitView
        leftPanel={
          <PDFViewer
            documentId={id!}
            filename={document.original_filename}
            className="h-full"
          />
        }
        rightPanel={detailsPanel}
        defaultLeftWidth={50}
        minLeftWidth={30}
        maxLeftWidth={70}
      />
    </div>
  )
}
