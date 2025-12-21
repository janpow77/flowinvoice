/**
 * SettingsProfiles - Profile & Modelle (Admin)
 *
 * Profilverwaltung und Modellkatalog.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import clsx from 'clsx'
import {
  Layers,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  Copy,
  Star,
  AlertCircle,
  Info,
  ChevronRight,
  Cpu,
  Download,
  Upload,
  RotateCcw,
} from 'lucide-react'
import {
  LLMProfile,
  ModelConfig,
  DEFAULT_PROFILE,
  DEFAULT_MODELS,
  DocumentTypeConfig,
  DEFAULT_DOCUMENT_TYPES,
  SETTINGS_SCHEMA_VERSION,
} from '@/lib/settings-types'

interface Props {
  isAdmin: boolean
}

const PROFILES_STORAGE_KEY = 'flowaudit_profiles'
const MODELS_STORAGE_KEY = 'flowaudit_models'
const DOC_TYPES_STORAGE_KEY = 'flowaudit_document_types'

type TabView = 'profiles' | 'models'

export function SettingsProfiles({ isAdmin }: Props) {
  useTranslation() // Hook for future i18n
  const [activeView, setActiveView] = useState<TabView>('profiles')
  const [profiles, setProfiles] = useState<LLMProfile[]>([])
  const [models, setModels] = useState<ModelConfig[]>([])
  const [documentTypes, setDocumentTypes] = useState<DocumentTypeConfig[]>([])

  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [editForm, setEditForm] = useState<Partial<LLMProfile> | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Load data from localStorage
  useEffect(() => {
    // Profiles
    const storedProfiles = localStorage.getItem(PROFILES_STORAGE_KEY)
    if (storedProfiles) {
      try {
        setProfiles(JSON.parse(storedProfiles))
      } catch {
        setProfiles([DEFAULT_PROFILE])
      }
    } else {
      setProfiles([DEFAULT_PROFILE])
    }

    // Models
    const storedModels = localStorage.getItem(MODELS_STORAGE_KEY)
    if (storedModels) {
      try {
        setModels(JSON.parse(storedModels))
      } catch {
        setModels(DEFAULT_MODELS)
      }
    } else {
      setModels(DEFAULT_MODELS)
    }

    // Document Types
    const storedDocTypes = localStorage.getItem(DOC_TYPES_STORAGE_KEY)
    if (storedDocTypes) {
      try {
        setDocumentTypes(JSON.parse(storedDocTypes))
      } catch {
        setDocumentTypes(DEFAULT_DOCUMENT_TYPES)
      }
    } else {
      setDocumentTypes(DEFAULT_DOCUMENT_TYPES)
    }
  }, [])

  const saveProfiles = (p: LLMProfile[]) => {
    setProfiles(p)
    localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(p))
  }

  const saveModels = (m: ModelConfig[]) => {
    setModels(m)
    localStorage.setItem(MODELS_STORAGE_KEY, JSON.stringify(m))
  }

  const selectedProfile = profiles.find(p => p.id === selectedProfileId)
  const activeModels = models.filter(m => m.isActive)

  const handleCreateProfile = () => {
    setIsCreating(true)
    setIsEditing(true)
    setSelectedProfileId(null)
    setEditForm({
      name: '',
      description: '',
      documentTypeId: 'all',
      modelId: activeModels[0]?.id || 'llama3.1:8b',
      isDefault: false,
      isActive: true,
      parameters: { ...DEFAULT_PROFILE.parameters },
      context: { ...DEFAULT_PROFILE.context },
      performance: { ...DEFAULT_PROFILE.performance },
    })
  }

  const handleEditProfile = (profile: LLMProfile) => {
    setIsEditing(true)
    setIsCreating(false)
    setEditForm({ ...profile })
  }

  const handleDuplicateProfile = (profile: LLMProfile) => {
    const newProfile: LLMProfile = {
      ...profile,
      id: `${profile.id}-copy-${Date.now()}`,
      name: `${profile.name} (Kopie)`,
      isDefault: false,
      createdAt: new Date().toISOString(),
      updatedAt: undefined,
    }
    saveProfiles([...profiles, newProfile])
    setSelectedProfileId(newProfile.id)
  }

  const handleSaveProfile = () => {
    if (!editForm || !editForm.name) return

    if (isCreating) {
      const newProfile: LLMProfile = {
        id: `profile-${Date.now()}`,
        name: editForm.name,
        description: editForm.description || '',
        documentTypeId: editForm.documentTypeId || 'all',
        modelId: editForm.modelId || activeModels[0]?.id || 'llama3.1:8b',
        isDefault: editForm.isDefault || false,
        isActive: editForm.isActive !== false,
        parameters: editForm.parameters || DEFAULT_PROFILE.parameters,
        context: editForm.context || DEFAULT_PROFILE.context,
        performance: editForm.performance || DEFAULT_PROFILE.performance,
        createdAt: new Date().toISOString(),
      }

      // If setting as default, unset others
      let updated = [...profiles]
      if (newProfile.isDefault) {
        updated = updated.map(p => ({ ...p, isDefault: false }))
      }
      saveProfiles([...updated, newProfile])
      setSelectedProfileId(newProfile.id)
    } else if (selectedProfileId) {
      let updated = profiles.map(p =>
        p.id === selectedProfileId
          ? { ...p, ...editForm, updatedAt: new Date().toISOString() } as LLMProfile
          : p
      )

      // If setting as default, unset others
      if (editForm.isDefault) {
        updated = updated.map(p =>
          p.id === selectedProfileId ? p : { ...p, isDefault: false }
        )
      }
      saveProfiles(updated)
    }

    setIsEditing(false)
    setIsCreating(false)
    setEditForm(null)
  }

  const handleDeleteProfile = (id: string) => {
    const profile = profiles.find(p => p.id === id)
    if (profile?.isDefault) return

    const updated = profiles.filter(p => p.id !== id)
    saveProfiles(updated)
    setDeleteConfirm(null)
    if (selectedProfileId === id) {
      setSelectedProfileId(null)
    }
  }

  const handleToggleModel = (modelId: string) => {
    const updated = models.map(m =>
      m.id === modelId ? { ...m, isActive: !m.isActive } : m
    )
    saveModels(updated)
  }

  const handleExport = () => {
    const exportData = {
      schemaVersion: SETTINGS_SCHEMA_VERSION,
      profiles,
      models,
      documentTypes,
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `flowaudit-settings-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string)
        if (data.profiles) saveProfiles(data.profiles)
        if (data.models) saveModels(data.models)
        if (data.documentTypes) {
          setDocumentTypes(data.documentTypes)
          localStorage.setItem(DOC_TYPES_STORAGE_KEY, JSON.stringify(data.documentTypes))
        }
        alert('Import erfolgreich!')
      } catch {
        alert('Import fehlgeschlagen: Ungültiges Format')
      }
    }
    reader.readAsText(file)
    event.target.value = ''
  }

  const handleResetToDefaults = () => {
    if (confirm('Alle Einstellungen auf Standardwerte zurücksetzen?')) {
      saveProfiles([DEFAULT_PROFILE])
      saveModels(DEFAULT_MODELS)
      setDocumentTypes(DEFAULT_DOCUMENT_TYPES)
      localStorage.setItem(DOC_TYPES_STORAGE_KEY, JSON.stringify(DEFAULT_DOCUMENT_TYPES))
      setSelectedProfileId(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Sub-Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveView('profiles')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              activeView === 'profiles'
                ? 'bg-accent-primary/10 text-accent-primary'
                : 'text-theme-text-muted hover:bg-theme-hover'
            )}
          >
            <Layers className="h-4 w-4 inline mr-2" />
            Profile
          </button>
          <button
            onClick={() => setActiveView('models')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              activeView === 'models'
                ? 'bg-accent-primary/10 text-accent-primary'
                : 'text-theme-text-muted hover:bg-theme-hover'
            )}
          >
            <Cpu className="h-4 w-4 inline mr-2" />
            Modelle
          </button>
        </div>

        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="px-3 py-1.5 text-sm text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
            <label className="px-3 py-1.5 text-sm text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1 cursor-pointer">
              <Upload className="h-4 w-4" />
              Import
              <input type="file" accept=".json" onChange={handleImport} className="hidden" />
            </label>
            <button
              onClick={handleResetToDefaults}
              className="px-3 py-1.5 text-sm text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1"
            >
              <RotateCcw className="h-4 w-4" />
              Reset
            </button>
          </div>
        )}
      </div>

      {activeView === 'profiles' ? (
        // Profiles View
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Profile List */}
          <div className="lg:col-span-1">
            <div className="bg-theme-card rounded-lg border border-theme-border-default">
              <div className="p-4 border-b border-theme-border-default flex items-center justify-between">
                <h3 className="font-semibold text-theme-text-primary">Profile</h3>
                {isAdmin && (
                  <button
                    onClick={handleCreateProfile}
                    className="p-1.5 text-accent-primary hover:bg-accent-primary/10 rounded-lg"
                    title="Neues Profil"
                  >
                    <Plus className="h-5 w-5" />
                  </button>
                )}
              </div>
              <div className="divide-y divide-theme-border-default">
                {profiles.map((profile) => (
                  <button
                    key={profile.id}
                    onClick={() => {
                      setSelectedProfileId(profile.id)
                      setIsEditing(false)
                      setIsCreating(false)
                      setEditForm(null)
                    }}
                    className={clsx(
                      'w-full px-4 py-3 text-left flex items-center justify-between transition-colors',
                      selectedProfileId === profile.id
                        ? 'bg-accent-primary/10'
                        : 'hover:bg-theme-hover'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <Layers className="h-4 w-4 text-theme-text-muted" />
                      <div>
                        <p className={clsx(
                          'font-medium flex items-center gap-1',
                          selectedProfileId === profile.id
                            ? 'text-accent-primary'
                            : 'text-theme-text-primary'
                        )}>
                          {profile.name}
                          {profile.isDefault && (
                            <Star className="h-3 w-3 text-status-warning fill-current" />
                          )}
                        </p>
                        <span className="text-xs text-theme-text-muted">
                          {profile.documentTypeId === 'all' ? 'Alle Dokumenttypen' :
                            documentTypes.find(dt => dt.id === profile.documentTypeId)?.name || profile.documentTypeId}
                        </span>
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
                    {isCreating ? 'Neues Profil' : 'Profil bearbeiten'}
                  </h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => { setIsEditing(false); setIsCreating(false); setEditForm(null) }}
                      className="px-3 py-1.5 text-theme-text-muted hover:bg-theme-hover rounded-lg"
                    >
                      <X className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleSaveProfile}
                      className="px-3 py-1.5 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-hover flex items-center gap-1"
                    >
                      <Save className="h-4 w-4" />
                      Speichern
                    </button>
                  </div>
                </div>

                <div className="space-y-6">
                  {/* Basic Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Name *
                      </label>
                      <input
                        type="text"
                        value={editForm.name || ''}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Dokumenttyp
                      </label>
                      <select
                        value={editForm.documentTypeId || 'all'}
                        onChange={(e) => setEditForm({ ...editForm, documentTypeId: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      >
                        <option value="all">Alle Dokumenttypen</option>
                        {documentTypes.map(dt => (
                          <option key={dt.id} value={dt.id}>{dt.name}</option>
                        ))}
                      </select>
                    </div>
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
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                        Modell
                      </label>
                      <select
                        value={editForm.modelId || ''}
                        onChange={(e) => setEditForm({ ...editForm, modelId: e.target.value })}
                        className="w-full px-3 py-2 border border-theme-border-default rounded-lg bg-theme-input text-theme-text-primary focus:ring-2 focus:ring-accent-primary"
                      >
                        {activeModels.map(m => (
                          <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-center gap-4 pt-6">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editForm.isDefault || false}
                          onChange={(e) => setEditForm({ ...editForm, isDefault: e.target.checked })}
                          className="w-4 h-4 text-accent-primary border-theme-border-default rounded focus:ring-accent-primary"
                        />
                        <span className="text-sm text-theme-text-secondary">Standard-Profil</span>
                      </label>
                    </div>
                  </div>

                  {/* Parameters */}
                  <div className="pt-4 border-t border-theme-border-default">
                    <h4 className="font-medium text-theme-text-primary mb-3">Parameter</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Temperature</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="0.2"
                          value={editForm.parameters?.temperature || 0.1}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            parameters: { ...editForm.parameters!, temperature: parseFloat(e.target.value) || 0.1 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Top P</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="1"
                          value={editForm.parameters?.topP || 0.9}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            parameters: { ...editForm.parameters!, topP: parseFloat(e.target.value) || 0.9 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Top K</label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={editForm.parameters?.topK || 40}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            parameters: { ...editForm.parameters!, topK: parseInt(e.target.value) || 40 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Repeat Penalty</label>
                        <input
                          type="number"
                          step="0.1"
                          min="1"
                          max="2"
                          value={editForm.parameters?.repeatPenalty || 1.1}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            parameters: { ...editForm.parameters!, repeatPenalty: parseFloat(e.target.value) || 1.1 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Num Predict</label>
                        <input
                          type="number"
                          min="256"
                          max="2048"
                          value={editForm.parameters?.numPredict || 1024}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            parameters: { ...editForm.parameters!, numPredict: parseInt(e.target.value) || 1024 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-theme-text-muted mb-1">Num Ctx</label>
                        <input
                          type="number"
                          min="2048"
                          max="32768"
                          step="1024"
                          value={editForm.context?.numCtx || 8192}
                          onChange={(e) => setEditForm({
                            ...editForm,
                            context: { numCtx: parseInt(e.target.value) || 8192 }
                          })}
                          className="w-full px-2 py-1 text-sm border border-theme-border-default rounded bg-theme-input text-theme-text-primary"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : selectedProfile ? (
              // Profile Detail View
              <div className="bg-theme-card rounded-lg border border-theme-border-default p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-theme-text-primary flex items-center gap-2">
                      {selectedProfile.name}
                      {selectedProfile.isDefault && (
                        <Star className="h-4 w-4 text-status-warning fill-current" />
                      )}
                    </h3>
                    <p className="text-sm text-theme-text-muted mt-1">
                      {selectedProfile.description || 'Keine Beschreibung'}
                    </p>
                  </div>
                  {isAdmin && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDuplicateProfile(selectedProfile)}
                        className="px-3 py-1.5 text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1"
                        title="Duplizieren"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEditProfile(selectedProfile)}
                        className="px-3 py-1.5 text-theme-text-muted hover:bg-theme-hover rounded-lg flex items-center gap-1"
                      >
                        <Pencil className="h-4 w-4" />
                        Bearbeiten
                      </button>
                      {!selectedProfile.isDefault && (
                        <button
                          onClick={() => setDeleteConfirm(selectedProfile.id)}
                          className="px-3 py-1.5 text-status-danger hover:bg-status-danger-bg rounded-lg flex items-center gap-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Profile Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Modell</p>
                    <p className="font-medium text-theme-text-primary">
                      {models.find(m => m.id === selectedProfile.modelId)?.name || selectedProfile.modelId}
                    </p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Dokumenttyp</p>
                    <p className="font-medium text-theme-text-primary">
                      {selectedProfile.documentTypeId === 'all' ? 'Alle' :
                        documentTypes.find(dt => dt.id === selectedProfile.documentTypeId)?.name || '-'}
                    </p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Kontext</p>
                    <p className="font-medium text-theme-text-primary">
                      {selectedProfile.context.numCtx} Tokens
                    </p>
                  </div>
                  <div className="bg-theme-hover p-3 rounded-lg">
                    <p className="text-xs text-theme-text-muted">Temperature</p>
                    <p className="font-medium text-theme-text-primary">
                      {selectedProfile.parameters.temperature}
                    </p>
                  </div>
                </div>

                {/* Delete Confirmation */}
                {deleteConfirm === selectedProfile.id && (
                  <div className="p-4 bg-status-danger-bg border border-status-danger-border rounded-lg">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="h-5 w-5 text-status-danger mt-0.5" />
                      <div className="flex-1">
                        <p className="font-medium text-status-danger">Profil löschen?</p>
                        <p className="text-sm text-status-danger mt-1">
                          Diese Aktion kann nicht rückgängig gemacht werden.
                        </p>
                        <div className="mt-3 flex gap-2">
                          <button
                            onClick={() => handleDeleteProfile(selectedProfile.id)}
                            className="px-3 py-1.5 bg-status-danger text-white rounded-lg hover:bg-status-danger/90 text-sm"
                          >
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
              <div className="bg-theme-card rounded-lg border border-theme-border-default p-12 text-center">
                <Layers className="h-12 w-12 text-theme-text-muted mx-auto mb-4" />
                <h3 className="text-lg font-medium text-theme-text-primary mb-2">
                  Profil auswählen
                </h3>
                <p className="text-theme-text-muted">
                  Wähle ein Profil aus der Liste, um Details anzuzeigen.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        // Models View
        <div className="bg-theme-card rounded-lg border border-theme-border-default">
          <div className="p-4 border-b border-theme-border-default">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-status-info mt-0.5" />
              <div className="text-sm text-theme-text-muted">
                <p className="font-medium text-theme-text-primary mb-1">Modellkatalog</p>
                <p>Aktiviere/deaktiviere Modelle für die Verwendung in Profilen. Deaktivierte Modelle stehen bei der Profilerstellung nicht zur Auswahl.</p>
              </div>
            </div>
          </div>
          <div className="divide-y divide-theme-border-default">
            {models.map((model) => (
              <div key={model.id} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Cpu className={clsx(
                    'h-8 w-8 p-1.5 rounded-lg',
                    model.isActive
                      ? 'bg-status-success-bg text-status-success'
                      : 'bg-theme-hover text-theme-text-muted'
                  )} />
                  <div>
                    <p className="font-medium text-theme-text-primary">{model.name}</p>
                    <p className="text-sm text-theme-text-muted">{model.description}</p>
                    {model.hardwareHint && (
                      <p className="text-xs text-theme-text-muted mt-1">{model.hardwareHint}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={clsx(
                    'text-xs px-2 py-1 rounded',
                    model.speedRating === 'fast' && 'bg-status-success-bg text-status-success',
                    model.speedRating === 'medium' && 'bg-status-warning-bg text-status-warning',
                    model.speedRating === 'slow' && 'bg-status-danger-bg text-status-danger'
                  )}>
                    {model.speedRating === 'fast' && 'Schnell'}
                    {model.speedRating === 'medium' && 'Mittel'}
                    {model.speedRating === 'slow' && 'Langsam'}
                  </span>
                  {isAdmin && (
                    <button
                      onClick={() => handleToggleModel(model.id)}
                      className={clsx(
                        'w-10 h-6 rounded-full relative transition-colors',
                        model.isActive ? 'bg-status-success' : 'bg-theme-hover'
                      )}
                    >
                      <span className={clsx(
                        'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                        model.isActive ? 'left-4' : 'left-0.5'
                      )} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
