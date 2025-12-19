/**
 * SettingsDocumentTypes - Dokumenttypen & Chunking (Admin)
 *
 * Verwaltung von Dokumenttypen und deren Chunking-Defaults.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
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
} from 'lucide-react'
import {
  DocumentTypeConfig,
  ChunkingConfig,
  DEFAULT_DOCUMENT_TYPES,
  generateSlug,
} from '@/lib/settings-types'

interface Props {
  isAdmin: boolean
}

const STORAGE_KEY = 'flowaudit_document_types'

export function SettingsDocumentTypes({ isAdmin }: Props) {
  useTranslation() // Hook for future i18n
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeConfig[]>([])
  const [selectedTypeId, setSelectedTypeId] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [editForm, setEditForm] = useState<Partial<DocumentTypeConfig> | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Load from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        setDocumentTypes(JSON.parse(stored))
      } catch {
        setDocumentTypes(DEFAULT_DOCUMENT_TYPES)
      }
    } else {
      setDocumentTypes(DEFAULT_DOCUMENT_TYPES)
    }
  }, [])

  // Save to localStorage
  const saveDocumentTypes = (types: DocumentTypeConfig[]) => {
    setDocumentTypes(types)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(types))
  }

  const selectedType = documentTypes.find(dt => dt.id === selectedTypeId)

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
      const newType: DocumentTypeConfig = {
        id: generateSlug(editForm.name),
        name: editForm.name,
        slug: generateSlug(editForm.name),
        description: editForm.description || '',
        isSystem: false,
        chunkingDefaults: editForm.chunkingDefaults as ChunkingConfig,
        createdAt: new Date().toISOString(),
      }

      // Check for duplicates
      if (documentTypes.some(dt => dt.id === newType.id)) {
        alert('Ein Dokumenttyp mit diesem Namen existiert bereits.')
        return
      }

      saveDocumentTypes([...documentTypes, newType])
      setSelectedTypeId(newType.id)
    } else if (selectedTypeId) {
      const updated = documentTypes.map(dt =>
        dt.id === selectedTypeId
          ? { ...dt, ...editForm, updatedAt: new Date().toISOString() }
          : dt
      )
      saveDocumentTypes(updated)
    }

    setIsEditing(false)
    setIsCreating(false)
    setEditForm(null)
  }

  const handleCancel = () => {
    setIsEditing(false)
    setIsCreating(false)
    setEditForm(null)
  }

  const handleDelete = (id: string) => {
    const type = documentTypes.find(dt => dt.id === id)
    if (type?.isSystem) return

    const updated = documentTypes.filter(dt => dt.id !== id)
    saveDocumentTypes(updated)
    setDeleteConfirm(null)
    if (selectedTypeId === id) {
      setSelectedTypeId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-700 dark:text-blue-300">
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
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 dark:text-white">Dokumenttypen</h3>
              {isAdmin && (
                <button
                  onClick={handleCreate}
                  className="p-1.5 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg"
                  title="Neuer Dokumenttyp"
                >
                  <Plus className="h-5 w-5" />
                </button>
              )}
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {documentTypes.map((type) => (
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
                      ? 'bg-primary-50 dark:bg-primary-900/20'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className={clsx(
                        'font-medium',
                        selectedTypeId === type.id
                          ? 'text-primary-700 dark:text-primary-300'
                          : 'text-gray-900 dark:text-white'
                      )}>
                        {type.name}
                      </p>
                      {type.isSystem && (
                        <span className="text-xs text-gray-400">System</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Detail/Edit Panel */}
        <div className="lg:col-span-2">
          {isEditing && editForm ? (
            // Edit Form
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {isCreating ? 'Neuer Dokumenttyp' : 'Dokumenttyp bearbeiten'}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCancel}
                    className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-1"
                  >
                    <Save className="h-4 w-4" />
                    Speichern
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={editForm.name || ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    placeholder="z.B. Lieferschein"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Beschreibung
                  </label>
                  <textarea
                    value={editForm.description || ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    placeholder="Kurze Beschreibung des Dokumenttyps"
                  />
                </div>

                {/* Chunking Settings */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                    Chunking-Einstellungen
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                    Chunking teilt lange Dokumente in Abschnitte, damit das Modell gezielt relevante Stellen verarbeitet.
                  </p>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
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
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedType.name}
                  </h3>
                  {selectedType.isSystem && (
                    <span className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                      <Lock className="h-3 w-3" />
                      System-Dokumenttyp (nicht löschbar)
                    </span>
                  )}
                </div>
                {isAdmin && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(selectedType)}
                      className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg flex items-center gap-1"
                    >
                      <Pencil className="h-4 w-4" />
                      Bearbeiten
                    </button>
                    {!selectedType.isSystem && (
                      <button
                        onClick={() => setDeleteConfirm(selectedType.id)}
                        className="px-3 py-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg flex items-center gap-1"
                      >
                        <Trash2 className="h-4 w-4" />
                        Löschen
                      </button>
                    )}
                  </div>
                )}
              </div>

              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {selectedType.description || 'Keine Beschreibung'}
              </p>

              {/* Chunking Defaults */}
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="font-medium text-gray-900 dark:text-white mb-4">
                  Chunking-Defaults
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Chunk-Größe</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedType.chunkingDefaults.chunkSizeTokens}
                    </p>
                    <p className="text-xs text-gray-400">Tokens</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Überlappung</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedType.chunkingDefaults.chunkOverlapTokens}
                    </p>
                    <p className="text-xs text-gray-400">Tokens</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Max. Chunks</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedType.chunkingDefaults.maxChunks}
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Strategie</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                      {selectedType.chunkingDefaults.chunkStrategy}
                    </p>
                  </div>
                </div>
              </div>

              {/* Delete Confirmation */}
              {deleteConfirm === selectedType.id && (
                <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-red-800 dark:text-red-300">
                        Dokumenttyp löschen?
                      </p>
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                        Alle Profile, die diesen Dokumenttyp verwenden, werden auf "Alle" umgestellt.
                      </p>
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => handleDelete(selectedType.id)}
                          className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                        >
                          Ja, löschen
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
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
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Dokumenttyp auswählen
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                Wähle einen Dokumenttyp aus der Liste, um Details anzuzeigen.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
