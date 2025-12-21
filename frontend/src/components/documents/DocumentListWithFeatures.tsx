import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  FileText,
  Eye,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Clock,
  Filter,
  Download,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import type { Document, DocumentStatus, FeatureStatus } from '@/lib/types'
import FeatureStatusBadge from './FeatureStatusBadge'

interface DocumentListWithFeaturesProps {
  projectId: string
  onDocumentSelect?: (documentId: string) => void
  selectedDocumentId?: string | null
}

type SortField = 'filename' | 'date' | 'amount' | 'status' | 'errors'
type SortDirection = 'asc' | 'desc'

interface FilterState {
  status: DocumentStatus | 'ALL'
  hasErrors: 'all' | 'with_errors' | 'no_errors'
  search: string
}

const statusConfig: Record<DocumentStatus, {
  icon: typeof CheckCircle
  color: string
  label: string
}> = {
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

// Aggregate feature status from document
function getDocumentFeatureStats(doc: Document): {
  valid: number
  invalid: number
  warning: number
  missing: number
  total: number
  overallStatus: FeatureStatus
} {
  const stats = { valid: 0, invalid: 0, warning: 0, missing: 0, total: 0 }

  // Check precheck errors
  if (doc.precheck_errors) {
    for (const error of doc.precheck_errors) {
      stats.total++
      if (error.severity === 'HIGH') {
        stats.invalid++
      } else if (error.severity === 'MEDIUM') {
        stats.warning++
      }
    }
  }

  // Determine overall status
  let overallStatus: FeatureStatus = 'VALID'
  if (stats.invalid > 0) {
    overallStatus = 'INVALID'
  } else if (stats.warning > 0) {
    overallStatus = 'WARNING'
  } else if (stats.missing > 0) {
    overallStatus = 'MISSING'
  }

  return { ...stats, overallStatus }
}

export default function DocumentListWithFeatures({
  projectId,
  onDocumentSelect,
  selectedDocumentId,
}: DocumentListWithFeaturesProps) {
  const [sortField, setSortField] = useState<SortField>('filename')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [filters, setFilters] = useState<FilterState>({
    status: 'ALL',
    hasErrors: 'all',
    search: '',
  })
  const [showFilters, setShowFilters] = useState(false)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: () => api.getDocuments(projectId),
    enabled: !!projectId,
  })

  // Filter and sort documents
  const filteredDocuments = useMemo(() => {
    if (!documents) return []

    let filtered = [...documents]

    // Apply status filter
    if (filters.status !== 'ALL') {
      filtered = filtered.filter(doc => doc.status === filters.status)
    }

    // Apply error filter
    if (filters.hasErrors === 'with_errors') {
      filtered = filtered.filter(doc => {
        const stats = getDocumentFeatureStats(doc)
        return stats.invalid > 0 || stats.warning > 0
      })
    } else if (filters.hasErrors === 'no_errors') {
      filtered = filtered.filter(doc => {
        const stats = getDocumentFeatureStats(doc)
        return stats.invalid === 0 && stats.warning === 0
      })
    }

    // Apply search filter
    if (filters.search) {
      const search = filters.search.toLowerCase()
      filtered = filtered.filter(doc =>
        doc.original_filename.toLowerCase().includes(search) ||
        doc.extracted_data?.supplier_name?.value?.toString().toLowerCase().includes(search) ||
        doc.extracted_data?.invoice_number?.value?.toString().toLowerCase().includes(search)
      )
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'filename':
          comparison = a.original_filename.localeCompare(b.original_filename)
          break
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'amount': {
          const amountA = parseFloat(String(a.extracted_data?.gross_amount?.value || 0))
          const amountB = parseFloat(String(b.extracted_data?.gross_amount?.value || 0))
          comparison = amountA - amountB
          break
        }
        case 'status':
          comparison = (a.status || '').localeCompare(b.status || '')
          break
        case 'errors': {
          const errorsA = getDocumentFeatureStats(a).invalid
          const errorsB = getDocumentFeatureStats(b).invalid
          comparison = errorsA - errorsB
          break
        }
      }

      return sortDirection === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [documents, filters, sortField, sortDirection])

  // Summary stats
  const summaryStats = useMemo(() => {
    if (!documents) return { total: 0, valid: 0, invalid: 0, warning: 0, pending: 0 }

    const stats = { total: documents.length, valid: 0, invalid: 0, warning: 0, pending: 0 }

    for (const doc of documents) {
      const docStats = getDocumentFeatureStats(doc)
      if (docStats.overallStatus === 'VALID') stats.valid++
      else if (docStats.overallStatus === 'INVALID') stats.invalid++
      else if (docStats.overallStatus === 'WARNING') stats.warning++
      else stats.pending++
    }

    return stats
  }, [documents])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    )
  }

  if (isLoading) {
    return (
      <div className="bg-theme-card rounded-lg border border-theme-border p-8 text-center">
        <Clock className="w-8 h-8 mx-auto mb-2 text-theme-text-muted animate-pulse" />
        <p className="text-theme-text-muted">Lade Dokumente...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary Bar */}
      <div className="grid grid-cols-5 gap-4">
        <div className="bg-theme-card rounded-lg border border-theme-border p-4 text-center">
          <p className="text-2xl font-bold text-theme-text">{summaryStats.total}</p>
          <p className="text-xs text-theme-text-muted">Gesamt</p>
        </div>
        <div className="bg-theme-card rounded-lg border border-theme-border p-4 text-center">
          <p className="text-2xl font-bold text-status-success">{summaryStats.valid}</p>
          <p className="text-xs text-theme-text-muted">Korrekt</p>
        </div>
        <div className="bg-theme-card rounded-lg border border-theme-border p-4 text-center">
          <p className="text-2xl font-bold text-status-danger">{summaryStats.invalid}</p>
          <p className="text-xs text-theme-text-muted">Fehlerhaft</p>
        </div>
        <div className="bg-theme-card rounded-lg border border-theme-border p-4 text-center">
          <p className="text-2xl font-bold text-status-warning">{summaryStats.warning}</p>
          <p className="text-xs text-theme-text-muted">Warnungen</p>
        </div>
        <div className="bg-theme-card rounded-lg border border-theme-border p-4 text-center">
          <p className="text-2xl font-bold text-theme-text-muted">{summaryStats.pending}</p>
          <p className="text-xs text-theme-text-muted">Ausstehend</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-theme-card rounded-lg border border-theme-border p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
                showFilters
                  ? 'bg-theme-primary text-white'
                  : 'bg-theme-surface text-theme-text-muted hover:text-theme-text'
              )}
            >
              <Filter className="w-4 h-4" />
              Filter
            </button>
            <input
              type="text"
              placeholder="Suchen..."
              value={filters.search}
              onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="px-3 py-1.5 text-sm border border-theme-border rounded-lg bg-theme-surface text-theme-text focus:ring-1 focus:ring-theme-primary focus:border-theme-primary"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-theme-text-muted">
              {filteredDocuments.length} von {documents?.length || 0} Dokumenten
            </span>
            <button
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-theme-text-muted hover:text-theme-text transition-colors"
              title="Als CSV exportieren"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-theme-border grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-theme-text-muted mb-1">Status</label>
              <select
                value={filters.status}
                onChange={e => setFilters(prev => ({ ...prev, status: e.target.value as DocumentStatus | 'ALL' }))}
                className="w-full px-3 py-2 text-sm border border-theme-border rounded-lg bg-theme-surface text-theme-text"
              >
                <option value="ALL">Alle</option>
                <option value="UPLOADED">Hochgeladen</option>
                <option value="VALIDATING">Validiere...</option>
                <option value="VALIDATED">Validiert</option>
                <option value="ANALYZING">Analysiere...</option>
                <option value="ANALYZED">Analysiert</option>
                <option value="REVIEWED">Geprüft</option>
                <option value="ERROR">Fehler</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-theme-text-muted mb-1">Fehler</label>
              <select
                value={filters.hasErrors}
                onChange={e => setFilters(prev => ({ ...prev, hasErrors: e.target.value as 'all' | 'with_errors' | 'no_errors' }))}
                className="w-full px-3 py-2 text-sm border border-theme-border rounded-lg bg-theme-surface text-theme-text"
              >
                <option value="all">Alle</option>
                <option value="with_errors">Mit Fehlern</option>
                <option value="no_errors">Ohne Fehler</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Document Table */}
      <div className="bg-theme-card rounded-lg border border-theme-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-theme-surface">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('filename')}
                    className="flex items-center gap-1 font-medium text-theme-text-muted hover:text-theme-text"
                  >
                    Dateiname
                    <SortIcon field="filename" />
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('date')}
                    className="flex items-center gap-1 font-medium text-theme-text-muted hover:text-theme-text"
                  >
                    Datum
                    <SortIcon field="date" />
                  </button>
                </th>
                <th className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleSort('amount')}
                    className="flex items-center gap-1 font-medium text-theme-text-muted hover:text-theme-text ml-auto"
                  >
                    Betrag
                    <SortIcon field="amount" />
                  </button>
                </th>
                <th className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleSort('status')}
                    className="flex items-center gap-1 font-medium text-theme-text-muted hover:text-theme-text mx-auto"
                  >
                    Status
                    <SortIcon field="status" />
                  </button>
                </th>
                <th className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleSort('errors')}
                    className="flex items-center gap-1 font-medium text-theme-text-muted hover:text-theme-text mx-auto"
                  >
                    Prüfung
                    <SortIcon field="errors" />
                  </button>
                </th>
                <th className="px-4 py-3 w-16"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-theme-border">
              {filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <FileText className="w-12 h-12 mx-auto mb-3 text-theme-text-muted" />
                    <p className="text-theme-text-muted">Keine Dokumente gefunden</p>
                  </td>
                </tr>
              ) : (
                filteredDocuments.map(doc => {
                  const status = statusConfig[doc.status as DocumentStatus] || statusConfig.UPLOADED
                  const StatusIcon = status.icon
                  const featureStats = getDocumentFeatureStats(doc)
                  const isSelected = selectedDocumentId === doc.id

                  return (
                    <tr
                      key={doc.id}
                      onClick={() => onDocumentSelect?.(doc.id)}
                      className={clsx(
                        'hover:bg-theme-surface cursor-pointer transition-colors',
                        isSelected && 'bg-theme-primary/5 border-l-4 border-theme-primary'
                      )}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-theme-text-muted flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="font-medium text-theme-text truncate">
                              {doc.original_filename}
                            </p>
                            {doc.extracted_data?.supplier_name?.value && (
                              <p className="text-xs text-theme-text-muted truncate">
                                {doc.extracted_data.supplier_name.value}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-theme-text-muted">
                        {doc.extracted_data?.invoice_date?.value ||
                          new Date(doc.created_at).toLocaleDateString('de-DE')}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-theme-text">
                        {doc.extracted_data?.gross_amount?.value
                          ? `${parseFloat(String(doc.extracted_data.gross_amount.value)).toLocaleString('de-DE', {
                              minimumFractionDigits: 2,
                            })} €`
                          : '-'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={clsx('inline-flex items-center gap-1 text-sm', status.color)}>
                          <StatusIcon className="w-4 h-4" />
                          <span className="hidden sm:inline">{status.label}</span>
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <FeatureStatusBadge status={featureStats.overallStatus} size="sm" />
                        {featureStats.invalid > 0 && (
                          <span className="ml-1 text-xs text-status-danger">
                            ({featureStats.invalid})
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/documents/${doc.id}`}
                          onClick={e => e.stopPropagation()}
                          className="p-1.5 text-theme-text-muted hover:text-theme-primary transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
