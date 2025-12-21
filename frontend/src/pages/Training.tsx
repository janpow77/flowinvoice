import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  GraduationCap,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Trophy,
  Target,
  Clock,
  Info,
  Loader2,
  Play,
  Pause,
} from 'lucide-react'
import clsx from 'clsx'
import { api } from '@/lib/api'
import { PDFViewer } from '@/components/documents'

interface TrainingSession {
  projectId: string
  documents: TrainingDocument[]
  currentIndex: number
  answers: Record<string, TrainingAnswer>
  startTime: number
  showSolution: boolean
}

interface TrainingDocument {
  id: string
  filename: string
  expected_result: {
    is_valid: boolean
    errors: TrainingError[]
  }
}

interface TrainingError {
  code: string
  feature_id: string
  severity: string
  message: string
}

interface TrainingAnswer {
  is_valid: boolean
  identified_errors: string[]
  submitted_at: number
}

interface TrainingStats {
  total_documents: number
  correct_assessments: number
  correct_errors: number
  missed_errors: number
  false_positives: number
  time_spent_seconds: number
}

export default function Training() {
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [session, setSession] = useState<TrainingSession | null>(null)
  const [userAnswer, setUserAnswer] = useState<{
    is_valid: boolean | null
    identified_errors: string[]
  }>({ is_valid: null, identified_errors: [] })
  const [showResult, setShowResult] = useState(false)
  const [stats, setStats] = useState<TrainingStats>({
    total_documents: 0,
    correct_assessments: 0,
    correct_errors: 0,
    missed_errors: 0,
    false_positives: 0,
    time_spent_seconds: 0,
  })

  // Fetch projects
  const { data: projects, isLoading: loadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  // Fetch documents for training when project is selected
  const { data: documents, isLoading: loadingDocuments } = useQuery({
    queryKey: ['trainingDocuments', selectedProject],
    queryFn: async () => {
      if (!selectedProject) return []
      const docs = await api.getDocuments(selectedProject)
      // Filter documents that have solution data
      return docs.filter((doc: { analysis_result?: unknown }) => doc.analysis_result)
    },
    enabled: !!selectedProject,
  })

  const startSession = () => {
    if (!documents || documents.length === 0) return

    // Shuffle documents
    const shuffled = [...documents].sort(() => Math.random() - 0.5)

    setSession({
      projectId: selectedProject!,
      documents: shuffled.map((doc: { id: string; original_filename: string; analysis_result?: { overall_assessment?: string }; precheck_errors?: TrainingError[] }) => ({
        id: doc.id,
        filename: doc.original_filename,
        expected_result: {
          is_valid: doc.analysis_result?.overall_assessment === 'ok',
          errors: doc.precheck_errors || [],
        },
      })),
      currentIndex: 0,
      answers: {},
      startTime: Date.now(),
      showSolution: false,
    })
    setShowResult(false)
    setUserAnswer({ is_valid: null, identified_errors: [] })
    setStats({
      total_documents: shuffled.length,
      correct_assessments: 0,
      correct_errors: 0,
      missed_errors: 0,
      false_positives: 0,
      time_spent_seconds: 0,
    })
  }

  const currentDocument = session?.documents[session.currentIndex]

  const submitAnswer = () => {
    if (!session || !currentDocument || userAnswer.is_valid === null) return

    const expected = currentDocument.expected_result
    const isCorrectAssessment = userAnswer.is_valid === expected.is_valid

    // Calculate error matching
    const expectedErrorCodes = new Set(expected.errors.map(e => e.code))
    const userErrorCodes = new Set(userAnswer.identified_errors)

    let correctErrors = 0
    let missedErrors = 0
    let falsePositives = 0

    expectedErrorCodes.forEach(code => {
      if (userErrorCodes.has(code)) {
        correctErrors++
      } else {
        missedErrors++
      }
    })

    userErrorCodes.forEach(code => {
      if (!expectedErrorCodes.has(code)) {
        falsePositives++
      }
    })

    // Update stats
    setStats(prev => ({
      ...prev,
      correct_assessments: prev.correct_assessments + (isCorrectAssessment ? 1 : 0),
      correct_errors: prev.correct_errors + correctErrors,
      missed_errors: prev.missed_errors + missedErrors,
      false_positives: prev.false_positives + falsePositives,
      time_spent_seconds: Math.floor((Date.now() - session.startTime) / 1000),
    }))

    // Save answer
    setSession(prev => prev ? {
      ...prev,
      answers: {
        ...prev.answers,
        [currentDocument.id]: {
          is_valid: userAnswer.is_valid!,
          identified_errors: userAnswer.identified_errors,
          submitted_at: Date.now(),
        },
      },
    } : null)

    setShowResult(true)
  }

  const nextDocument = () => {
    if (!session) return

    if (session.currentIndex < session.documents.length - 1) {
      setSession(prev => prev ? {
        ...prev,
        currentIndex: prev.currentIndex + 1,
      } : null)
      setShowResult(false)
      setUserAnswer({ is_valid: null, identified_errors: [] })
    }
  }

  const prevDocument = () => {
    if (!session) return

    if (session.currentIndex > 0) {
      setSession(prev => prev ? {
        ...prev,
        currentIndex: prev.currentIndex - 1,
      } : null)
      setShowResult(false)
      setUserAnswer({ is_valid: null, identified_errors: [] })
    }
  }

  const toggleError = (errorCode: string) => {
    setUserAnswer(prev => ({
      ...prev,
      identified_errors: prev.identified_errors.includes(errorCode)
        ? prev.identified_errors.filter(e => e !== errorCode)
        : [...prev.identified_errors, errorCode],
    }))
  }

  const endSession = () => {
    setSession(null)
    setShowResult(false)
    setUserAnswer({ is_valid: null, identified_errors: [] })
  }

  // Available error codes for marking
  const availableErrorCodes = [
    { code: 'TAX_SUPPLIER_NAME_MISSING', label: 'Lieferantenname fehlt' },
    { code: 'TAX_VAT_ID_MISSING', label: 'USt-IdNr fehlt' },
    { code: 'TAX_VAT_ID_INVALID', label: 'USt-IdNr ungültig' },
    { code: 'TAX_INVOICE_NUMBER_MISSING', label: 'Rechnungsnummer fehlt' },
    { code: 'TAX_INVOICE_DATE_MISSING', label: 'Rechnungsdatum fehlt' },
    { code: 'TAX_GROSS_AMOUNT_MISSING', label: 'Bruttobetrag fehlt' },
    { code: 'TAX_NET_AMOUNT_MISSING', label: 'Nettobetrag fehlt' },
    { code: 'TAX_VAT_RATE_WRONG', label: 'Falscher MwSt-Satz' },
    { code: 'TAX_CALCULATION_ERROR', label: 'Rechenfehler' },
    { code: 'PROJECT_PERIOD_BEFORE_START', label: 'Vor Projektbeginn' },
    { code: 'PROJECT_PERIOD_AFTER_END', label: 'Nach Projektende' },
    { code: 'FRAUD_SELF_INVOICE', label: 'Selbstrechnung' },
    { code: 'SEMANTIC_NO_PROJECT_RELEVANCE', label: 'Keine Projektrelevanz' },
  ]

  // Project selection view
  if (!session) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-theme-primary/10 rounded-lg">
            <GraduationCap className="w-8 h-8 text-theme-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-theme-text-primary">Schulungsmodus</h1>
            <p className="text-theme-text-muted">
              Üben Sie die Rechnungsprüfung an echten Beispielen
            </p>
          </div>
        </div>

        <div className="bg-theme-card rounded-lg border border-theme-border p-6">
          <h2 className="text-lg font-semibold text-theme-text-primary mb-4">
            Projekt auswählen
          </h2>

          {loadingProjects ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-theme-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects?.map((project: { id: string; title: string; description?: string; document_count?: number }) => (
                <button
                  key={project.id}
                  onClick={() => setSelectedProject(project.id)}
                  className={clsx(
                    'p-4 rounded-lg border text-left transition-colors',
                    selectedProject === project.id
                      ? 'border-theme-primary bg-theme-primary/5'
                      : 'border-theme-border hover:border-theme-primary/50'
                  )}
                >
                  <h3 className="font-medium text-theme-text-primary">{project.title}</h3>
                  <p className="text-sm text-theme-text-muted mt-1">{project.description}</p>
                  <p className="text-xs text-theme-text-muted mt-2">
                    {project.document_count || 0} Dokumente
                  </p>
                </button>
              ))}
            </div>
          )}

          {selectedProject && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-theme-text-muted">
                {loadingDocuments ? (
                  'Lade Dokumente...'
                ) : (
                  `${documents?.length || 0} Dokumente mit Lösungen verfügbar`
                )}
              </div>
              <button
                onClick={startSession}
                disabled={!documents || documents.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                Training starten
              </button>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-status-info-bg border border-status-info-border rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-status-info mt-0.5" />
            <div>
              <p className="font-medium text-status-info">So funktioniert der Schulungsmodus</p>
              <ol className="text-sm text-status-info mt-2 space-y-1 list-decimal list-inside">
                <li>Wählen Sie ein Projekt mit vorhandenen Lösungsdaten</li>
                <li>Prüfen Sie jede Rechnung und bewerten Sie sie als korrekt oder fehlerhaft</li>
                <li>Markieren Sie alle Fehler, die Sie finden</li>
                <li>Vergleichen Sie Ihre Antwort mit der Musterlösung</li>
                <li>Lernen Sie aus Ihren Fehlern und verbessern Sie Ihre Prüfkompetenz</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Training session view
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header with stats */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={endSession}
            className="flex items-center gap-2 px-3 py-2 text-theme-text-muted hover:text-theme-text border border-theme-border rounded-lg"
          >
            <Pause className="w-4 h-4" />
            Training beenden
          </button>
          <div className="text-sm text-theme-text-muted">
            Dokument {session.currentIndex + 1} von {session.documents.length}
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm">
            <Trophy className="w-4 h-4 text-status-success" />
            <span>{stats.correct_assessments} korrekt</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Target className="w-4 h-4 text-theme-primary" />
            <span>{stats.correct_errors} Fehler gefunden</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-theme-text-muted" />
            <span>{Math.floor(stats.time_spent_seconds / 60)}:{(stats.time_spent_seconds % 60).toString().padStart(2, '0')}</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex gap-4">
        {/* PDF Viewer */}
        <div className="w-1/2 bg-theme-card rounded-lg border border-theme-border overflow-hidden">
          {currentDocument && (
            <PDFViewer
              documentId={currentDocument.id}
              filename={currentDocument.filename}
              className="h-full"
            />
          )}
        </div>

        {/* Answer panel */}
        <div className="w-1/2 flex flex-col">
          <div className="flex-1 bg-theme-card rounded-lg border border-theme-border p-6 overflow-auto">
            <h3 className="font-semibold text-theme-text-primary mb-4">
              {currentDocument?.filename}
            </h3>

            {/* Assessment buttons */}
            <div className="mb-6">
              <p className="text-sm text-theme-text-muted mb-3">Ist diese Rechnung korrekt?</p>
              <div className="flex gap-3">
                <button
                  onClick={() => setUserAnswer(prev => ({ ...prev, is_valid: true }))}
                  disabled={showResult}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border transition-colors',
                    userAnswer.is_valid === true
                      ? 'border-status-success bg-status-success-bg text-status-success'
                      : 'border-theme-border hover:border-status-success',
                    showResult && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <CheckCircle className="w-5 h-5" />
                  Korrekt
                </button>
                <button
                  onClick={() => setUserAnswer(prev => ({ ...prev, is_valid: false }))}
                  disabled={showResult}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border transition-colors',
                    userAnswer.is_valid === false
                      ? 'border-status-danger bg-status-danger-bg text-status-danger'
                      : 'border-theme-border hover:border-status-danger',
                    showResult && 'opacity-50 cursor-not-allowed'
                  )}
                >
                  <XCircle className="w-5 h-5" />
                  Fehlerhaft
                </button>
              </div>
            </div>

            {/* Error selection */}
            {userAnswer.is_valid === false && (
              <div className="mb-6">
                <p className="text-sm text-theme-text-muted mb-3">
                  Welche Fehler haben Sie gefunden?
                </p>
                <div className="grid grid-cols-2 gap-2 max-h-60 overflow-auto">
                  {availableErrorCodes.map(error => (
                    <button
                      key={error.code}
                      onClick={() => toggleError(error.code)}
                      disabled={showResult}
                      className={clsx(
                        'text-left px-3 py-2 text-sm rounded-lg border transition-colors',
                        userAnswer.identified_errors.includes(error.code)
                          ? 'border-theme-primary bg-theme-primary/10 text-theme-primary'
                          : 'border-theme-border hover:border-theme-primary/50',
                        showResult && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      {error.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Submit button */}
            {!showResult && (
              <button
                onClick={submitAnswer}
                disabled={userAnswer.is_valid === null}
                className="w-full py-3 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Antwort prüfen
              </button>
            )}

            {/* Result display */}
            {showResult && currentDocument && (
              <div className="space-y-4">
                <div
                  className={clsx(
                    'p-4 rounded-lg',
                    userAnswer.is_valid === currentDocument.expected_result.is_valid
                      ? 'bg-status-success-bg border border-status-success-border'
                      : 'bg-status-danger-bg border border-status-danger-border'
                  )}
                >
                  <div className="flex items-center gap-2">
                    {userAnswer.is_valid === currentDocument.expected_result.is_valid ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-status-success" />
                        <span className="font-medium text-status-success">Richtig bewertet!</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-status-danger" />
                        <span className="font-medium text-status-danger">
                          Falsch bewertet - Die Rechnung ist{' '}
                          {currentDocument.expected_result.is_valid ? 'korrekt' : 'fehlerhaft'}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Show expected errors */}
                {currentDocument.expected_result.errors.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-theme-text mb-2">Erwartete Fehler:</p>
                    <div className="space-y-2">
                      {currentDocument.expected_result.errors.map((error, i) => (
                        <div
                          key={i}
                          className={clsx(
                            'p-3 rounded-lg flex items-start gap-2',
                            userAnswer.identified_errors.includes(error.code)
                              ? 'bg-status-success-bg'
                              : 'bg-status-warning-bg'
                          )}
                        >
                          {userAnswer.identified_errors.includes(error.code) ? (
                            <CheckCircle className="w-4 h-4 text-status-success mt-0.5" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5" />
                          )}
                          <div>
                            <p className="text-sm font-medium">{error.code}</p>
                            <p className="text-xs text-theme-text-muted">{error.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={prevDocument}
              disabled={session.currentIndex === 0}
              className="flex items-center gap-2 px-4 py-2 border border-theme-border rounded-lg hover:bg-theme-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Zurück
            </button>

            {showResult && session.currentIndex < session.documents.length - 1 && (
              <button
                onClick={nextDocument}
                className="flex items-center gap-2 px-4 py-2 bg-theme-primary text-white rounded-lg hover:bg-theme-primary-hover"
              >
                Weiter
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {showResult && session.currentIndex === session.documents.length - 1 && (
              <button
                onClick={endSession}
                className="flex items-center gap-2 px-4 py-2 bg-status-success text-white rounded-lg hover:bg-status-success/90"
              >
                <Trophy className="w-4 h-4" />
                Training abschließen
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
