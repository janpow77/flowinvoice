/**
 * SettingsDocumentTypes - Dokumenttypen & Chunking (Admin)
 *
 * Verwaltung von Dokumenttypen und deren Chunking-Defaults.
 * Daten werden vom Backend geladen und gespeichert.
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import {
  FileText,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  AlertCircle,
  Info,
  ChevronRight,
  Lock,
  Loader2,
  AlertTriangle,
} from 'lucide-react'
import api from '@/lib/api'
import {
  DocumentTypeConfig,
  generateSlug,
} from '@/lib/settings-types'

interface Props {
  isAdmin: boolean
}

export function SettingsDocumentTypes({ isAdmin }: Props) {
  useTranslation() // Hook for future i18n
  const queryClient = useQueryClient()
  const [selectedTypeId, setSelectedTypeId] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [editForm, setEditForm] = useState<Partial<DocumentTypeConfig> | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Load document types from backend
  const { data: documentTypes = [], isLoading, error } = useQuery({
    queryKey: ['documentTypes'],
    queryFn: api.getDocumentTypes,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: {
      name: string
      slug: string
      description?: string
      chunk_size_tokens?: number
      chunk_overlap_tokens?: number
      max_chunks?: number
      chunk_strategy?: string
    }) => api.createDocumentType(data),
    onSuccess: (newType) => {
      queryClient.invalidateQueries({ queryKey: ['documentTypes'] })
      setSelectedTypeId(newType.id)
      setIsEditing(false)
      setIsCreating(false)
      setEditForm(null)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: {
      id: string
      data: {
        name?: string
        description?: string
        chunk_size_tokens?: number
        chunk_overlap_tokens?: number
        max_chunks?: number
        chunk_strategy?: string
      }
    }) => api.updateDocumentType(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documentTypes'] })
      setIsEditing(false)
      setEditForm(null)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocumentType(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documentTypes'] })
      setDeleteConfirm(null)
      if (selectedTypeId === deleteConfirm) {
        setSelectedTypeId(null)
      }
    },
  })

  const selectedType = documentTypes.find((dt: DocumentTypeConfig) => dt.id === selectedTypeId)

  const handleCreate = () => {
    setIsCreating(true)
    setIsEditing(true)
    setSelectedTypeId(null)
    setEditForm({
      name: '',
      description: '',
      chunkingDefaults: {
        chunkSizeTokens: 900,
        chunkOverlapTokens: 150,
        maxChunks: 6,
        chunkStrategy: 'fixed',
      },
    })
  }

  const handleEdit = (type: DocumentTypeConfig) => {
    setIsEditing(true)
    setIsCreating(false)
    setEditForm({ ...type })
  }

  const handleSave = () => {
    if (!editForm || !editForm.name) return

    if (isCreating) {
      const slug = generateSlug(editForm.name)

      // Check for duplicates
      if (documentTypes.some((dt: DocumentTypeConfig) => dt.slug === slug)) {
        alert('Ein Dokumenttyp mit diesem Namen existiert bereits.')
        return
      }

      createMutation.mutate({
        name: editForm.name,
        slug: slug,
        description: editForm.description || '',
        chunk_size_tokens: editForm.chunkingDefaults?.chunkSizeTokens,
        chunk_overlap_tokens: editForm.chunkingDefaults?.chunkOverlapTokens,
        max_chunks: editForm.chunkingDefaults?.maxChunks,
        chunk_strategy: editForm.chunkingDefaults?.chunkStrategy,
      })
    } else if (selectedTypeId) {
      updateMutation.mutate({
        id: selectedTypeId,
        data: {
          name: editForm.name,
          description: editForm.description || '',
          chunk_size_tokens: editForm.chunkingDefaults?.chunkSizeTokens,
          chunk_overlap_tokens: editForm.chunkingDefaults?.chunkOverlapTokens,
          max_chunks: editForm.chunkingDefaults?.maxChunks,
          chunk_strategy: editForm.chunkingDefaults?.chunkStrategy,
        },
      })
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setIsCreating(false)
    setEditForm(null)
  }

  const handleDelete = (id: string) => {
    const type = documentTypes.find((dt: DocumentTypeConfig) => dt.id === id)
    if (type?.isSystem) return
    deleteMutation.mutate(id)
  }

  const isSaving = createMutation.isPending || updateMutation.isPending
  const isDeleting = deleteMutation.isPending

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-accent-primary" />
        <span className="ml-2 text-theme-text-muted">Lade Dokumenttypen...</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="bg-status-danger-bg border border-status-danger-border rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-status-danger mt-0.5" />
          <div>
            <p className="font-medium text-status-danger">
              Fehler beim Laden der Dokumenttypen
            </p>
            <p className="text-sm text-status-danger mt-1">
              {error instanceof Error ? error.message : 'Unbekannter Fehler'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-status-info-bg border border-status-info-border rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-status-info mt-0.5" />
          <div className="text-sm text-status-info">
            <p className="font-medium mb-1">Warum Dokumenttypen?</p>
            <p>
              Dokumenttypen ermöglichen optimierte Verarbeitungseinstellungen für verschiedene Belegarten.
              Jeder Typ hat eigene Chunking-Defaults, die bestimmen, wie Dokumente für die KI-Analyse
              aufgeteilt werden.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Document Type List */}
        <div className="lg:col-span-1">
          <div className="bg-theme-card rounded-lg border border-theme-border-default">
            <div className="p-4 border-b border-theme-border-default flex items-center justify-between">
              <h3 className="font-semibold text-theme-text-primary">Dokumenttypen</h3>
              {isAdmin && (
                <button
                  onClick={handleCreate}
                  className="p-1.5 text-accent-primary hover:bg-accent-primary/10 rounded-lg"
                  title="Neuer Dokumenttyp"
                >
                  <Plus className="h-5 w-5" />
                </button>
              )}
            </div>
            <div className="divide-y divide-theme-border-default">
              {documentTypes.map((type: DocumentTypeConfig) => (
                <button
                  key={type.id}
                  onClick={() => {
                    setSelectedTypeId(type.id)
                    setIsEditing(false)
                    setIsCreating(false)
                    setEditForm(null)
                  }}
                  className={clsx(
                    'w-full px-4 py-3 text-left flex items-center justify-between transition-colors',
                    selectedTypeId === type.id
                      ? 'bg-accent-primary/10'
                      : 'hover:bg-theme-hover'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-theme-text-muted" />
                    <div>
                      <p className={clsx(
                        'font-medium',
                        selectedTypeId === type.id
                          ? 'text-accent-primary'
                          : 'text-theme-text-primary'
                      )}>
                        {type.name}
                      </p>
                      {type.isSystem && (
                        <span className="text-xs text-theme-text-muted">System</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-theme-text-muted" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Detail/Edit Panel */}
        <div className="lg:col-span-2">
          {isEditing && editForm ? (
            // Edit Form
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-theme-text-primary">
                  {isCreating ? 'Neuer Dokumenttyp' : 'Dokumenttyp bearbeiten'}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    disabled={isSaving}
                    className="px-3 py-1.5 text-theme-text-muted hover:bg-theme-hover rounded-lg disabled:opacity-50"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="px-3 py-1.5 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover flex items-center gap-1 disabled:opacity-50"
                  >
                    {isSaving ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    Speichern
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={editForm.name || ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                    placeholder="z.B. Lieferschein"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    Beschreibung
                  </label>
                  <textarea
                    value={editForm.description || ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                    placeholder="Kurze Beschreibung des Dokumenttyps"
                  />
                </div>

                {/* Chunking Settings */}
                <div className="pt-4 border-t border-theme-border-default">
                  <h4 className="font-medium text-theme-text-primary mb-3">
                    Chunking-Einstellungen
                  </h4>
                  <p className="text-xs text-theme-text-muted mb-4">
                    Chunking teilt lange Dokumente in Abschnitte, damit das Modell gezielt relevante Stellen verarbeitet.
                  </p>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Chunk-Größe (Tokens)
                      </label>
                      <input
                        type="number"
                        value={editForm.chunkingDefaults?.chunkSizeTokens || 900}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            chunkingDefaults: {
                              ...editForm.chunkingDefaults!,
                              chunkSizeTokens: parseInt(e.target.value) || 900,
                            },
                          })
                        }
                        min={200}
                        max={2000}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Überlappung (Tokens)
                      </label>
                      <input
                        type="number"
                        value={editForm.chunkingDefaults?.chunkOverlapTokens || 150}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            chunkingDefaults: {
                              ...editForm.chunkingDefaults!,
                              chunkOverlapTokens: parseInt(e.target.value) || 150,
                            },
                          })
                        }
                        min={0}
                        max={500}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Max. Chunks
                      </label>
                      <input
                        type="number"
                        value={editForm.chunkingDefaults?.maxChunks || 6}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            chunkingDefaults: {
                              ...editForm.chunkingDefaults!,
                              maxChunks: parseInt(e.target.value) || 6,
                            },
                          })
                        }
                        min={1}
                        max={20}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Strategie
                      </label>
                      <select
                        value={editForm.chunkingDefaults?.chunkStrategy || 'fixed'}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            chunkingDefaults: {
                              ...editForm.chunkingDefaults!,
                              chunkStrategy: e.target.value as 'fixed' | 'semantic' | 'paragraph',
                            },
                          })
                        }
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      >
                        <option value="fixed">Feste Größe</option>
                        <option value="paragraph">Absätze</option>
                        <option value="semantic">Semantisch</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : selectedType ? (
            // Detail View
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-theme-text-primary">
                    {selectedType.name}
                  </h3>
                  {selectedType.isSystem && (
                    <span className="text-xs text-theme-text-muted flex items-center gap-1 mt-1">
                      <Lock className="h-3 w-3" />
                      System-Dokumenttyp (nicht löschbar)
                    </span>
                  )}
                </div>
                {isAdmin && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(selectedType)}
                      className="px-3 py-1.5 text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1"
                    >
                      <Pencil className="h-4 w-4" />
                      Bearbeiten
                    </button>
                    {!selectedType.isSystem && (
                      <button
                        onClick={() => setDeleteConfirm(selectedType.id)}
                        className="px-3 py-1.5 text-status-danger hover:bg-status-danger-bg rounded-lg flex items-center gap-1"
                      >
                        <Trash2 className="h-4 w-4" />
                        Löschen
                      </button>
                    )}
                  </div>
                )}
              </div>

              <p className="text-theme-text-muted mb-6">
                {selectedType.description || 'Keine Beschreibung'}
              </p>

              {/* Chunking Defaults */}
              <div className="pt-4 border-t border-theme-border-default">
                <h4 className="font-medium text-theme-text-primary mb-4">
                  Chunking-Defaults
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Chunk-Größe</p>
                    <p className="text-lg font-semibold text-theme-text-primary">
                      {selectedType.chunkingDefaults.chunkSizeTokens}
                    </p>
                    <p className="text-xs text-theme-text-muted">Tokens</p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Überlappung</p>
                    <p className="text-lg font-semibold text-theme-text-primary">
                      {selectedType.chunkingDefaults.chunkOverlapTokens}
                    </p>
                    <p className="text-xs text-theme-text-muted">Tokens</p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Max. Chunks</p>
                    <p className="text-lg font-semibold text-theme-text-primary">
                      {selectedType.chunkingDefaults.maxChunks}
                    </p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Strategie</p>
                    <p className="text-lg font-semibold text-theme-text-primary capitalize">
                      {selectedType.chunkingDefaults.chunkStrategy}
                    </p>
                  </div>
                </div>
              </div>

              {/* Delete Confirmation */}
              {deleteConfirm === selectedType.id && (
                <div className="mt-6 p-4 bg-status-danger-bg border border-status-danger-border rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-status-danger mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-status-danger">
                        Dokumenttyp löschen?
                      </p>
                      <p className="text-sm text-status-danger mt-1">
                        Alle Profile, die diesen Dokumenttyp verwenden, werden auf "Alle" umgestellt.
                      </p>
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => handleDelete(selectedType.id)}
                          disabled={isDeleting}
                          className="px-3 py-1.5 bg-status-danger text-white rounded-lg hover:bg-status-danger/90 text-sm flex items-center gap-1 disabled:opacity-50"
                        >
                          {isDeleting && <Loader2 className="h-4 w-4 animate-spin" />}
                          Ja, löschen
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="px-3 py-1.5 bg-theme-hover text-theme-text-secondary rounded-lg hover:bg-theme-card border border-theme-border-default text-sm"
                        >
                          Abbrechen
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Empty State
            <div className="bg-theme-card rounded-lg border border-theme-border-default p-12 text-center">
              <FileText className="h-12 w-12 text-theme-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-medium text-theme-text-primary mb-2">
                Dokumenttyp auswählen
              </h3>
              <p className="text-theme-text-muted">
                Wähle einen Dokumenttyp aus der Liste, um Details anzuzeigen.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
