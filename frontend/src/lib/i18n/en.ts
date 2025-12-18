/**
 * English Translations
 */

export const en = {
  // Navigation
  nav: {
    dashboard: 'Dashboard',
    projects: 'Projects',
    documents: 'Documents',
    rulesets: 'Rulesets',
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
    retry: 'Retry',
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
    contact: 'Contact',
    contactPerson: 'Contact Person',
    performance: 'Performance',
    performanceDescription: 'Number of workers for API and background processes (1-8)',
    apiWorkers: 'API Workers',
    apiWorkersDescription: 'Process parallel HTTP requests',
    backgroundWorkers: 'Background Workers',
    backgroundWorkersDescription: 'PDF processing and LLM analysis',
    workers: 'workers',
    restartRequired: 'Restart Required',
    restartHint: 'Changes will take effect after Docker container restart',
    // GPU Settings
    gpuSettings: 'GPU & Thermal Protection',
    gpuDescription: 'Control GPU utilization and automatic throttling on overheating',
    liveStatus: 'Live Status',
    statusHealthy: 'Healthy',
    statusWarning: 'Warning',
    statusCritical: 'Critical',
    throttleActive: 'Throttling active',
    gpuMemory: 'GPU Memory',
    gpuMemoryDescription: 'VRAM fraction for LLM inference',
    parallelRequests: 'Parallel Requests',
    parallelRequestsDescription: 'Concurrent LLM requests',
    contextSize: 'Context Size',
    contextSizeDescription: 'Token window (higher = more VRAM)',
    thermalThrottle: 'Emergency Temperature',
    thermalThrottleDescription: 'Auto-throttle when overheating',
    conservative: 'Conservative',
    default: 'Default',
    aggressive: 'Aggressive',
  },

  // Rulesets
  rulesets: {
    title: 'Rulesets',
    description: 'Manage audit rulesets for different tax systems',
    DE_USTG: 'Germany (UStG)',
    EU_VAT: 'EU (VAT Directive)',
    UK_VAT: 'UK (HMRC VAT)',
    legalBasis: 'Legal Basis',
    requiredFeatures: 'Required Features',
    conditionalFeatures: 'Conditional Features',
    smallAmountInvoice: 'Small Amount Invoice',
    reducedRequirements: 'Reduced Requirements',
    // Actions
    createRuleset: 'New Ruleset',
    editRuleset: 'Edit Ruleset',
    view: 'View',
    edit: 'Edit',
    noRulesets: 'No rulesets available',
    noRulesetsDesc: 'Create your first ruleset for invoice auditing',
    // Detail view
    legalReferences: 'Legal References',
    features: 'Features',
    featuresCount: 'features',
    // Form fields
    basicInfo: 'Basic Information',
    rulesetId: 'Ruleset ID',
    version: 'Version',
    titleDe: 'Title (German)',
    titleEn: 'Title (English)',
    jurisdiction: 'Jurisdiction',
    currency: 'Currency',
    // Features
    addFeature: 'Add Feature',
    noFeatures: 'No features defined',
    addFirstFeature: 'Add first feature',
    // Required levels
    required: 'Required',
    conditional: 'Conditional',
    optional: 'Optional',
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

  // Beneficiary (Grant Recipient)
  beneficiary: {
    title: 'Beneficiary',
    subtitle: 'Grant Recipient',
    name: 'Beneficiary Name',
    legalForm: 'Legal Form',
    street: 'Street and Number',
    zip: 'Postal Code',
    city: 'City',
    country: 'Country',
    vatId: 'VAT Identification Number',
    taxNumber: 'Tax Number',
    aliases: 'Alternative Names',
    inputTaxDeductible: 'Input Tax Deductible',
    // Matching status
    matching: {
      title: 'Beneficiary Matching',
      exactMatch: 'Exact Match',
      aliasMatch: 'Alias Match',
      likelyMatch: 'Likely Match',
      mismatch: 'No Match',
      notChecked: 'Not Checked',
    },
    // Error messages
    errors: {
      mismatch: 'Invoice recipient does not match beneficiary',
      aliasUsed: 'Recipient matches beneficiary alias',
      wrongAddress: 'Address differs from beneficiary',
      nameTypo: 'Possible typo in recipient name',
    },
  },

  // Project Context
  projectContext: {
    title: 'Project Context',
    projectId: 'Project ID',
    projectName: 'Project Name',
    fileReference: 'File Reference',
    projectPeriod: 'Project Period',
    fundingType: 'Funding Type',
    fundingRate: 'Funding Rate',
    totalBudget: 'Total Budget',
    eligibleCosts: 'Eligible Costs',
    approvalDate: 'Approval Date',
    approvingAuthority: 'Approving Authority',
    implementationLocation: 'Implementation Location',
  },

  // Quality Assurance
  quality: {
    title: 'Quality Assurance',
    traceability: 'Traceability',
    plausibility: 'Plausibility',
    consistency: 'Consistency',
    truthSource: {
      rule: 'Rule-based',
      llm: 'AI-based',
      user: 'Manual',
    },
    checks: {
      formal: 'Formal Check',
      semantic: 'Semantic Check',
      organizational: 'Organizational Consistency',
      temporal: 'Temporal Consistency',
      economic: 'Economic Viability',
    },
  },

  // Generator
  generator: {
    title: 'Test Data Generator',
    description: 'Creates test invoices for training purposes',
    count: 'Count',
    templates: 'Templates',
    errorRate: 'Error Rate',
    severity: 'Severity',
    useBeneficiaryData: 'Use Beneficiary Data',
    beneficiaryDataHint: 'Generated invoices will consistently use the specified beneficiary data',
    noDummyMarkers: 'No dummy markers allowed',
    errorTypes: {
      missingInvoiceNumber: 'Missing Invoice Number',
      invalidVatId: 'Invalid VAT ID',
      missingDate: 'Missing Date',
      calculationError: 'Calculation Error',
      missingDescription: 'Missing Description',
      beneficiaryNameTypo: 'Recipient Name Typo',
      beneficiaryAliasUsed: 'Alias Used Instead of Main Name',
      beneficiaryWrongAddress: 'Wrong Address',
      beneficiaryCompletelyWrong: 'Completely Wrong Recipient',
    },
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

  // Grant Purpose Audit
  grantPurpose: {
    title: 'Grant Purpose Audit',
    subtitle: 'Funding Eligibility Check',
    dimensions: {
      subject: 'Subject Relation',
      temporal: 'Temporal Relation',
      organizational: 'Organizational Relation',
      economic: 'Economic Plausibility',
    },
    results: {
      pass: 'Pass',
      fail: 'Fail',
      unclear: 'Unclear',
    },
    negativeIndicators: {
      noProjectReference: 'Service description without project reference',
      outsidePeriod: 'Service outside funding period',
      recipientMismatch: 'Recipient does not match beneficiary',
      genericService: 'Generic services without specifics',
      highAmount: 'Unusually high amount',
      missingPeriod: 'Missing service period',
    },
    overallResult: 'Overall Result',
    reasoning: 'Reasoning',
    evidence: 'Evidence',
  },

  // Conflict Resolution
  conflict: {
    title: 'Conflict Resolution',
    status: {
      noConflict: 'No Conflicts',
      ruleVsLlm: 'Conflict: Rule vs. AI',
      ruleVsUser: 'Conflict: Rule vs. Manual',
      llmVsUser: 'Conflict: AI vs. Manual',
    },
    priority: {
      description: 'Priority Order',
      rule: '1. Rule-based (highest priority)',
      llm: '2. AI Analysis',
      user: '3. Manual Override (overrides all)',
    },
    resolvedBy: 'Resolved by',
  },

  // Risk Assessment
  risk: {
    title: 'Risk Assessment',
    disclaimer: 'NOTE: Potential risk detected – not a legal assessment',
    indicators: {
      highAmount: 'Unusually high amount',
      vendorClustering: 'Notable vendor concentration',
      missingPeriod: 'Missing service period',
      roundAmount: 'Round lump sum amount',
      outsidePeriod: 'Service outside project period',
      noReference: 'Missing project reference',
      recipientMismatch: 'Recipient mismatch',
    },
    severity: {
      info: 'Information',
      low: 'Low',
      medium: 'Medium',
      high: 'High',
      critical: 'Critical',
    },
    score: 'Risk Score',
    findings: 'Risk Findings',
    noRisks: 'No notable risks detected',
  },

  // Analysis Status
  analysisStatus: {
    completed: 'Completed',
    reviewNeeded: 'Review Needed',
    documentUnreadable: 'Document Unreadable',
    insufficientText: 'Insufficient Text Extracted',
    rulesetNotApplicable: 'Ruleset Not Applicable',
    analysisAborted: 'Analysis Aborted',
    timeout: 'Timeout',
    systemError: 'System Error',
  },

  // UNCLEAR Status
  unclearStatus: {
    title: 'Unclear Status',
    reasons: {
      missingInfo: 'Relevant information missing',
      ambiguousData: 'Ambiguous information',
      multipleInterpretations: 'Multiple interpretations possible',
      insufficientContext: 'Insufficient context',
      conflictingSources: 'Conflicting sources',
    },
    requiredClarification: 'Required Clarification',
    affectedFields: 'Affected Fields',
  },

  // Metadata / Versioning
  metadata: {
    title: 'Analysis Metadata',
    documentFingerprint: 'Document Fingerprint',
    rulesetVersion: 'Ruleset Version',
    promptVersion: 'Prompt Version',
    modelId: 'Model ID',
    analysisTimestamp: 'Analysis Timestamp',
    systemVersion: 'System Version',
    invalidMetadata: 'Invalid Metadata',
  },

  // QA Scenarios
  qaScenarios: {
    title: 'QA Reference Scenarios',
    refCorrect: 'Correct Invoice',
    refMissingField: 'Missing Required Field',
    refUnclearPurpose: 'Unclear Grant Purpose',
    refWrongRecipient: 'Wrong Recipient',
    refOutsidePeriod: 'Outside Project Period',
    refHighAmount: 'Unusually High Amount',
    expectedResult: 'Expected Result',
    actualResult: 'Actual Result',
    testPassed: 'Test Passed',
    testFailed: 'Test Failed',
  },
};

export default en;
