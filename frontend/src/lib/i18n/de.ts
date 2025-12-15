/**
 * Deutsche Übersetzungen
 */

export const de = {
  // Navigation
  nav: {
    dashboard: 'Dashboard',
    projects: 'Projekte',
    documents: 'Dokumente',
    statistics: 'Statistik',
    settings: 'Einstellungen',
  },

  // Common
  common: {
    loading: 'Laden...',
    save: 'Speichern',
    cancel: 'Abbrechen',
    delete: 'Löschen',
    edit: 'Bearbeiten',
    create: 'Erstellen',
    search: 'Suchen',
    filter: 'Filter',
    export: 'Exportieren',
    import: 'Importieren',
    upload: 'Hochladen',
    download: 'Herunterladen',
    yes: 'Ja',
    no: 'Nein',
    confirm: 'Bestätigen',
    close: 'Schließen',
    back: 'Zurück',
    next: 'Weiter',
    active: 'Aktiv',
    inactive: 'Inaktiv',
    online: 'Online',
    offline: 'Offline',
    error: 'Fehler',
    success: 'Erfolg',
    warning: 'Warnung',
    info: 'Info',
    noData: 'Keine Daten vorhanden',
    all: 'Alle',
  },

  // Dashboard
  dashboard: {
    title: 'Dashboard',
    welcome: 'Willkommen bei FlowAudit',
    totalDocuments: 'Dokumente gesamt',
    processedToday: 'Heute verarbeitet',
    errorRate: 'Fehlerrate',
    avgProcessingTime: 'Durchschn. Verarbeitungszeit',
    recentDocuments: 'Zuletzt verarbeitete Dokumente',
    quickActions: 'Schnellaktionen',
    uploadInvoice: 'Rechnung hochladen',
    viewStatistics: 'Statistiken anzeigen',
  },

  // Projects
  projects: {
    title: 'Projekte',
    createProject: 'Neues Projekt',
    projectName: 'Projektname',
    description: 'Beschreibung',
    documentCount: 'Dokumente',
    createdAt: 'Erstellt am',
    lastActivity: 'Letzte Aktivität',
    noProjects: 'Noch keine Projekte vorhanden',
    deleteConfirm: 'Möchten Sie dieses Projekt wirklich löschen?',
  },

  // Documents
  documents: {
    title: 'Dokumente',
    uploadDocument: 'Dokument hochladen',
    fileName: 'Dateiname',
    status: 'Status',
    result: 'Ergebnis',
    uploadedAt: 'Hochgeladen am',
    processedAt: 'Verarbeitet am',
    noDocuments: 'Noch keine Dokumente vorhanden',
    dropzone: 'PDF-Dateien hier ablegen oder klicken zum Auswählen',
    processing: 'Wird verarbeitet...',
    processed: 'Verarbeitet',
    pending: 'Ausstehend',
    failed: 'Fehlgeschlagen',
    viewDetails: 'Details anzeigen',
    reprocess: 'Erneut verarbeiten',
  },

  // Document Detail
  documentDetail: {
    title: 'Dokumentdetails',
    invoiceData: 'Rechnungsdaten',
    auditResult: 'Prüfergebnis',
    vendor: 'Lieferant',
    invoiceNumber: 'Rechnungsnummer',
    invoiceDate: 'Rechnungsdatum',
    dueDate: 'Fälligkeitsdatum',
    totalAmount: 'Gesamtbetrag',
    taxAmount: 'Steuerbetrag',
    netAmount: 'Nettobetrag',
    lineItems: 'Positionen',
    errors: 'Fehler',
    warnings: 'Warnungen',
    passed: 'Bestanden',
    feedback: 'Feedback',
    feedbackPlaceholder: 'Korrektur oder Anmerkung eingeben...',
    submitFeedback: 'Feedback senden',
    approve: 'Genehmigen',
    reject: 'Ablehnen',
  },

  // Statistics
  statistics: {
    title: 'Statistik',
    overview: 'Übersicht',
    documentsPerDay: 'Dokumente pro Tag',
    errorsByType: 'Fehler nach Typ',
    processingTime: 'Verarbeitungszeit',
    accuracy: 'Genauigkeit',
    totalProcessed: 'Gesamt verarbeitet',
    successRate: 'Erfolgsrate',
    avgTime: 'Durchschn. Zeit',
    period: 'Zeitraum',
    last7Days: 'Letzte 7 Tage',
    last30Days: 'Letzte 30 Tage',
    last90Days: 'Letzte 90 Tage',
    allTime: 'Gesamter Zeitraum',
  },

  // Settings
  settings: {
    title: 'Einstellungen',
    language: 'Sprache',
    languageDescription: 'Wählen Sie Ihre bevorzugte Sprache',
    german: 'Deutsch',
    english: 'English',
    llmProvider: 'LLM-Provider',
    llmProviderDescription: 'Wählen Sie den Provider für die KI-Analyse',
    defaultRuleset: 'Standard-Regelwerk',
    defaultRulesetDescription: 'Wählen Sie das Standard-Regelwerk für neue Dokumente',
    ragSettings: 'RAG-Einstellungen',
    ragDescription: 'Einstellungen für das Few-Shot-Learning mit ChromaDB',
    autoLearning: 'Automatisches Lernen',
    autoLearningDescription: 'Validierte Rechnungen automatisch in RAG aufnehmen',
    fewShotExamples: 'Few-Shot-Beispiele',
    fewShotDescription: 'Anzahl der Beispiele im LLM-Prompt',
    examples: 'Beispiele',
    systemInfo: 'System-Information',
    version: 'Version',
    backend: 'Backend',
    chromadb: 'ChromaDB',
    redis: 'Redis',
  },

  // Rulesets
  rulesets: {
    DE_USTG: 'Deutschland (UStG)',
    EU_VAT: 'EU (MwSt-Richtlinie)',
    UK_VAT: 'UK (HMRC VAT)',
  },

  // Audit Results
  audit: {
    compliant: 'Konform',
    nonCompliant: 'Nicht konform',
    partiallyCompliant: 'Teilweise konform',
    needsReview: 'Prüfung erforderlich',
    missingField: 'Feld fehlt',
    invalidFormat: 'Ungültiges Format',
    taxError: 'Steuerfehler',
    calculationError: 'Berechnungsfehler',
  },

  // Processing Steps
  processing: {
    upload: 'Datei hochladen',
    parse: 'PDF analysieren',
    precheck: 'Vorprüfung',
    llm: 'KI-Analyse',
    result: 'Ergebnis erstellen',
    pageLoading: 'Seite wird geladen...',
  },

  // Errors
  errors: {
    generic: 'Ein Fehler ist aufgetreten',
    network: 'Netzwerkfehler - bitte prüfen Sie Ihre Verbindung',
    notFound: 'Nicht gefunden',
    unauthorized: 'Nicht autorisiert',
    serverError: 'Serverfehler',
    uploadFailed: 'Upload fehlgeschlagen',
    processingFailed: 'Verarbeitung fehlgeschlagen',
  },
};

export default de;
