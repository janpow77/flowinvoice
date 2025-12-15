/**
 * English Translations
 */

export const en = {
  // Navigation
  nav: {
    dashboard: 'Dashboard',
    projects: 'Projects',
    documents: 'Documents',
    statistics: 'Statistics',
    settings: 'Settings',
  },

  // Common
  common: {
    loading: 'Loading...',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    import: 'Import',
    upload: 'Upload',
    download: 'Download',
    yes: 'Yes',
    no: 'No',
    confirm: 'Confirm',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    active: 'Active',
    inactive: 'Inactive',
    online: 'Online',
    offline: 'Offline',
    error: 'Error',
    success: 'Success',
    warning: 'Warning',
    info: 'Info',
    noData: 'No data available',
    all: 'All',
  },

  // Dashboard
  dashboard: {
    title: 'Dashboard',
    welcome: 'Welcome to FlowAudit',
    totalDocuments: 'Total Documents',
    processedToday: 'Processed Today',
    errorRate: 'Error Rate',
    avgProcessingTime: 'Avg. Processing Time',
    recentDocuments: 'Recently Processed Documents',
    quickActions: 'Quick Actions',
    uploadInvoice: 'Upload Invoice',
    viewStatistics: 'View Statistics',
  },

  // Projects
  projects: {
    title: 'Projects',
    createProject: 'New Project',
    projectName: 'Project Name',
    description: 'Description',
    documentCount: 'Documents',
    createdAt: 'Created At',
    lastActivity: 'Last Activity',
    noProjects: 'No projects yet',
    deleteConfirm: 'Are you sure you want to delete this project?',
  },

  // Documents
  documents: {
    title: 'Documents',
    uploadDocument: 'Upload Document',
    fileName: 'File Name',
    status: 'Status',
    result: 'Result',
    uploadedAt: 'Uploaded At',
    processedAt: 'Processed At',
    noDocuments: 'No documents yet',
    dropzone: 'Drop PDF files here or click to select',
    processing: 'Processing...',
    processed: 'Processed',
    pending: 'Pending',
    failed: 'Failed',
    viewDetails: 'View Details',
    reprocess: 'Reprocess',
  },

  // Document Detail
  documentDetail: {
    title: 'Document Details',
    invoiceData: 'Invoice Data',
    auditResult: 'Audit Result',
    vendor: 'Vendor',
    invoiceNumber: 'Invoice Number',
    invoiceDate: 'Invoice Date',
    dueDate: 'Due Date',
    totalAmount: 'Total Amount',
    taxAmount: 'Tax Amount',
    netAmount: 'Net Amount',
    lineItems: 'Line Items',
    errors: 'Errors',
    warnings: 'Warnings',
    passed: 'Passed',
    feedback: 'Feedback',
    feedbackPlaceholder: 'Enter correction or comment...',
    submitFeedback: 'Submit Feedback',
    approve: 'Approve',
    reject: 'Reject',
  },

  // Statistics
  statistics: {
    title: 'Statistics',
    overview: 'Overview',
    documentsPerDay: 'Documents per Day',
    errorsByType: 'Errors by Type',
    processingTime: 'Processing Time',
    accuracy: 'Accuracy',
    totalProcessed: 'Total Processed',
    successRate: 'Success Rate',
    avgTime: 'Avg. Time',
    period: 'Period',
    last7Days: 'Last 7 Days',
    last30Days: 'Last 30 Days',
    last90Days: 'Last 90 Days',
    allTime: 'All Time',
  },

  // Settings
  settings: {
    title: 'Settings',
    language: 'Language',
    languageDescription: 'Select your preferred language',
    german: 'Deutsch',
    english: 'English',
    llmProvider: 'LLM Provider',
    llmProviderDescription: 'Select the provider for AI analysis',
    defaultRuleset: 'Default Ruleset',
    defaultRulesetDescription: 'Select the default ruleset for new documents',
    ragSettings: 'RAG Settings',
    ragDescription: 'Settings for few-shot learning with ChromaDB',
    autoLearning: 'Auto Learning',
    autoLearningDescription: 'Automatically add validated invoices to RAG',
    fewShotExamples: 'Few-Shot Examples',
    fewShotDescription: 'Number of examples in LLM prompt',
    examples: 'examples',
    systemInfo: 'System Information',
    version: 'Version',
    backend: 'Backend',
    chromadb: 'ChromaDB',
    redis: 'Redis',
  },

  // Rulesets
  rulesets: {
    DE_USTG: 'Germany (UStG)',
    EU_VAT: 'EU (VAT Directive)',
    UK_VAT: 'UK (HMRC VAT)',
    legalBasis: 'Legal Basis',
    requiredFeatures: 'Required Features',
    conditionalFeatures: 'Conditional Features',
    smallAmountInvoice: 'Small Amount Invoice',
    reducedRequirements: 'Reduced Requirements',
  },

  // Tax Selector
  taxSelector: {
    title: 'Select Tax System',
    description: 'Choose the tax system for invoice auditing',
    confirm: 'Confirm Selection',
    hint: 'The UI language selection (DE/EN) is independent of the tax system',
    currentSystem: 'Current Tax System',
    changeSystem: 'Change Tax System',
    requiredFields: 'Required Fields',
    conditionalFields: 'Conditional Fields',
    smallAmountLimit: 'Small Amount Limit',
    legalReferences: 'Legal References',
    categories: {
      IDENTITY: 'Identification',
      DATE: 'Date Information',
      AMOUNT: 'Amounts',
      TAX: 'Tax Information',
      TEXT: 'Text Fields',
      SEMANTIC: 'Semantic',
      PROJECT: 'Project Context',
    },
  },

  // Audit Results
  audit: {
    compliant: 'Compliant',
    nonCompliant: 'Non-Compliant',
    partiallyCompliant: 'Partially Compliant',
    needsReview: 'Needs Review',
    missingField: 'Missing Field',
    invalidFormat: 'Invalid Format',
    taxError: 'Tax Error',
    calculationError: 'Calculation Error',
  },

  // Processing Steps
  processing: {
    upload: 'Upload File',
    parse: 'Parse PDF',
    precheck: 'Pre-Check',
    llm: 'AI Analysis',
    result: 'Generate Result',
    pageLoading: 'Loading page...',
  },

  // Errors
  errors: {
    generic: 'An error occurred',
    network: 'Network error - please check your connection',
    notFound: 'Not found',
    unauthorized: 'Unauthorized',
    serverError: 'Server error',
    uploadFailed: 'Upload failed',
    processingFailed: 'Processing failed',
  },
};

export default en;
