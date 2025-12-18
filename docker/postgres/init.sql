-- Pfad: /docker/postgres/init.sql
-- FlowAudit Database Initialization
-- Erstellt die Grundstruktur für das Seminarsystem

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
CREATE TYPE document_status AS ENUM (
    'UPLOADED',
    'PARSING',
    'PARSED',
    'PRECHECKED',
    'PREPARED',
    'LLM_RUNNING',
    'LLM_DONE',
    'REVIEW_PENDING',
    'ACCEPTED',
    'REJECTED',
    'EXPORTED',
    'ERROR'
);

CREATE TYPE check_status AS ENUM (
    'PRESENT',
    'MISSING',
    'UNCLEAR'
);

CREATE TYPE rule_check_status AS ENUM (
    'OK',
    'WARN',
    'FAIL',
    'UNKNOWN'
);

CREATE TYPE truth_source AS ENUM (
    'RULE',
    'LLM',
    'USER'
);

CREATE TYPE provider_type AS ENUM (
    'LOCAL_OLLAMA',
    'OPENAI',
    'ANTHROPIC',
    'GEMINI'
);

CREATE TYPE feedbackrating AS ENUM (
    'CORRECT',
    'PARTIAL',
    'WRONG'
);

CREATE TYPE relation_level AS ENUM (
    'YES',
    'PARTIAL',
    'UNCLEAR',
    'NO'
);

CREATE TYPE location_match_status AS ENUM (
    'MATCH',
    'PARTIAL',
    'MISMATCH',
    'UNCLEAR'
);

CREATE TYPE error_source_category AS ENUM (
    'TAX_LAW',
    'BENEFICIARY_DATA',
    'LOCATION_VALIDATION'
);

CREATE TYPE tax_law_error_type AS ENUM (
    'MISSING',
    'WRONG_FORMAT',
    'CONFUSED_WITH_OTHER',
    'CALCULATION_ERROR',
    'WRONG_RATE',
    'NOT_UNIQUE',
    'UNCLEAR',
    'OUT_OF_PROJECT_PERIOD',
    'INVALID_CHECKSUM',
    'COUNTRY_MISMATCH'
);

-- Rulesets table
CREATE TABLE rulesets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ruleset_id VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    jurisdiction VARCHAR(10) NOT NULL,
    title_de VARCHAR(255) NOT NULL,
    title_en VARCHAR(255) NOT NULL,
    legal_references JSONB NOT NULL DEFAULT '[]',
    default_language VARCHAR(5) NOT NULL DEFAULT 'de',
    supported_ui_languages VARCHAR(5)[] NOT NULL DEFAULT ARRAY['de', 'en'],
    currency_default VARCHAR(3) NOT NULL DEFAULT 'EUR',
    features JSONB NOT NULL DEFAULT '[]',
    special_rules JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (ruleset_id, version)
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ruleset_id_hint VARCHAR(50),
    ui_language_hint VARCHAR(5) DEFAULT 'de',
    beneficiary JSONB NOT NULL,
    project JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on project for searching
CREATE INDEX idx_projects_beneficiary_name ON projects ((beneficiary->>'name'));
CREATE INDEX idx_projects_project_title ON projects ((project->>'project_title'));

-- Documents (Invoices) table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    storage_path VARCHAR(1000) NOT NULL,
    status document_status DEFAULT 'UPLOADED',
    ruleset_id VARCHAR(50),
    ruleset_version VARCHAR(20),
    ui_language VARCHAR(5) DEFAULT 'de',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_sha256 ON documents(sha256);
CREATE INDEX idx_documents_status ON documents(status);

-- Parse runs table
CREATE TABLE parse_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    engine VARCHAR(50) NOT NULL DEFAULT 'HYBRID',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    raw_text TEXT,
    pages JSONB,
    extracted JSONB,
    timings_ms JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_parse_runs_document ON parse_runs(document_id);

-- Precheck runs table
CREATE TABLE precheck_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    checks JSONB NOT NULL DEFAULT '[]',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_precheck_runs_document ON precheck_runs(document_id);

-- Prepare payloads table (INPUT-JSON an KI)
CREATE TABLE prepare_payloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    ruleset JSONB NOT NULL,
    ui_language VARCHAR(5) NOT NULL,
    project_context JSONB,
    parsing_summary JSONB,
    deterministic_precheck_results JSONB,
    features JSONB NOT NULL,
    extracted_text TEXT,
    required_output_schema JSONB,
    rag_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prepare_payloads_document ON prepare_payloads(document_id);

-- LLM runs table
CREATE TABLE llm_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    payload_id UUID REFERENCES prepare_payloads(id),
    provider provider_type NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    timings_ms JSONB,
    token_usage JSONB,
    raw_response_text TEXT,
    structured_response JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_llm_runs_document ON llm_runs(document_id);
CREATE INDEX idx_llm_runs_provider ON llm_runs(provider);

-- LLM run logs table
CREATE TABLE llm_run_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_run_id UUID REFERENCES llm_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    data JSONB
);

CREATE INDEX idx_llm_run_logs_run ON llm_run_logs(llm_run_id);

-- Final results table
CREATE TABLE final_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    llm_run_id UUID REFERENCES llm_runs(id),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    computed JSONB,
    fields JSONB NOT NULL DEFAULT '[]',
    overall JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_final_results_document ON final_results(document_id);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    final_result_id UUID REFERENCES final_results(id),
    rating feedbackrating NOT NULL,
    comment TEXT,
    overrides JSONB DEFAULT '[]',
    accept_result BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_document ON feedback(document_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);

-- RAG examples table
CREATE TABLE rag_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    feedback_id UUID REFERENCES feedback(id),
    project_id UUID REFERENCES projects(id),
    ruleset_id VARCHAR(50) NOT NULL,
    feature_id VARCHAR(100) NOT NULL,
    correction_type VARCHAR(50),
    original_text_snippet TEXT,
    original_llm_result JSONB,
    corrected_result JSONB,
    embedding_text TEXT,
    embedding VECTOR(384),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rag_examples_ruleset ON rag_examples(ruleset_id);
CREATE INDEX idx_rag_examples_feature ON rag_examples(feature_id);

-- Training examples table
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id),
    project_id UUID REFERENCES projects(id),
    module INTEGER NOT NULL,
    label_json JSONB NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_training_examples_module ON training_examples(module);

-- Training datasets table
CREATE TABLE training_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ruleset_id VARCHAR(50),
    example_count INTEGER DEFAULT 0,
    train_file_path VARCHAR(1000),
    val_file_path VARCHAR(1000),
    manifest JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training runs table
CREATE TABLE training_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES training_datasets(id),
    base_model VARCHAR(100) NOT NULL,
    epochs INTEGER NOT NULL,
    learning_rate FLOAT NOT NULL,
    lora_rank INTEGER,
    seed INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    metrics JSONB,
    artifacts_path VARCHAR(1000),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Model registry table
CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    provider provider_type NOT NULL,
    base_model VARCHAR(100),
    training_run_id UUID REFERENCES training_runs(id),
    trained_examples_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT false,
    metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Settings table
CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys table (encrypted storage)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider provider_type NOT NULL UNIQUE,
    encrypted_key BYTEA NOT NULL,
    key_preview VARCHAR(50),
    is_valid BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit events table
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    user_role VARCHAR(20),
    data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_events_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);

-- Export jobs table
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    format VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    file_path VARCHAR(1000),
    options JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Generator jobs table
CREATE TABLE generator_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    ruleset_id VARCHAR(50) NOT NULL,
    language VARCHAR(5) NOT NULL DEFAULT 'de',
    count INTEGER NOT NULL,
    templates_enabled VARCHAR(50)[] NOT NULL,
    settings JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    output_dir VARCHAR(1000),
    solutions_file VARCHAR(1000),
    generated_files JSONB DEFAULT '[]',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Insert default settings
INSERT INTO settings (key, value) VALUES
    ('active_provider', '"LOCAL_OLLAMA"'),
    ('inference', '{"temperature": 0.2, "max_tokens": 2000, "timeout_sec": 120, "parallel_requests": 2, "retry_on_error": true, "max_retries": 3}'),
    ('generator', '{"output_dir": "/data/exports", "solutions_dir": "/data/exports", "enable_admin_menu": true}'),
    ('rag', '{"enabled": true, "top_k": 3, "similarity_threshold": 0.25}'),
    ('logging', '{"verbose": false}');

-- Insert default rulesets
INSERT INTO rulesets (ruleset_id, version, jurisdiction, title_de, title_en, legal_references, features) VALUES
(
    'DE_USTG',
    '1.0.0',
    'DE',
    'Deutschland - Umsatzsteuergesetz',
    'Germany - VAT Act',
    '[{"law": "UStG", "section": "§ 14 Abs. 4", "description_de": "Pflichtangaben in Rechnungen", "description_en": "Mandatory invoice fields"}]',
    '[
        {"feature_id": "supplier_name_address", "name_de": "Name und Anschrift des leistenden Unternehmers", "name_en": "Supplier name and address", "legal_basis": "§ 14 Abs. 4 Nr. 1 UStG", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "customer_name_address", "name_de": "Name und Anschrift des Leistungsempfängers", "name_en": "Customer name and address", "legal_basis": "§ 14 Abs. 4 Nr. 1 UStG", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "supplier_tax_or_vat_id", "name_de": "Steuernummer oder USt-IdNr.", "name_en": "Tax number or VAT ID", "legal_basis": "§ 14 Abs. 4 Nr. 2 UStG", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "TAX"},
        {"feature_id": "invoice_date", "name_de": "Rechnungsdatum", "name_en": "Invoice date", "legal_basis": "§ 14 Abs. 4 Nr. 3 UStG", "required_level": "REQUIRED", "extraction_type": "DATE", "category": "DATE"},
        {"feature_id": "invoice_number", "name_de": "Rechnungsnummer", "name_en": "Invoice number", "legal_basis": "§ 14 Abs. 4 Nr. 4 UStG", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "IDENTITY"},
        {"feature_id": "supply_description", "name_de": "Art und Umfang der Leistung", "name_en": "Description of goods/services", "legal_basis": "§ 14 Abs. 4 Nr. 5 UStG", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "TEXT"},
        {"feature_id": "supply_date_or_period", "name_de": "Leistungszeitpunkt/-zeitraum", "name_en": "Date/period of supply", "legal_basis": "§ 14 Abs. 4 Nr. 6 UStG", "required_level": "REQUIRED", "extraction_type": "DATE_RANGE", "category": "DATE"},
        {"feature_id": "net_amount", "name_de": "Nettobetrag", "name_en": "Net amount", "legal_basis": "§ 14 Abs. 4 Nr. 7 UStG", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"},
        {"feature_id": "vat_rate", "name_de": "Steuersatz", "name_en": "VAT rate", "legal_basis": "§ 14 Abs. 4 Nr. 8 UStG", "required_level": "REQUIRED", "extraction_type": "PERCENTAGE", "category": "TAX"},
        {"feature_id": "vat_amount", "name_de": "Steuerbetrag", "name_en": "VAT amount", "legal_basis": "§ 14 Abs. 4 Nr. 8 UStG", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "TAX"},
        {"feature_id": "gross_amount", "name_de": "Bruttobetrag", "name_en": "Gross amount", "legal_basis": "§ 14 Abs. 4 UStG", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"}
    ]'
),
(
    'EU_VAT',
    '1.0.0',
    'EU',
    'EU MwSt-Systemrichtlinie',
    'EU VAT Directive',
    '[{"law": "MwSt-Systemrichtlinie", "section": "Art. 226", "description_de": "Pflichtangaben in Rechnungen", "description_en": "Mandatory invoice particulars"}]',
    '[
        {"feature_id": "invoice_date", "name_de": "Rechnungsdatum", "name_en": "Date of issue", "legal_basis": "Art. 226 Nr. 1", "required_level": "REQUIRED", "extraction_type": "DATE", "category": "DATE"},
        {"feature_id": "invoice_number", "name_de": "Fortlaufende Nummer", "name_en": "Sequential number", "legal_basis": "Art. 226 Nr. 2", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "IDENTITY"},
        {"feature_id": "supplier_vat_id", "name_de": "USt-IdNr. Lieferant", "name_en": "Supplier VAT ID", "legal_basis": "Art. 226 Nr. 3", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "TAX"},
        {"feature_id": "customer_vat_id", "name_de": "USt-IdNr. Kunde (B2B)", "name_en": "Customer VAT ID (B2B)", "legal_basis": "Art. 226 Nr. 4", "required_level": "CONDITIONAL", "extraction_type": "STRING", "category": "TAX"},
        {"feature_id": "supplier_name_address", "name_de": "Name/Anschrift Lieferant", "name_en": "Supplier name and address", "legal_basis": "Art. 226 Nr. 5", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "customer_name_address", "name_de": "Name/Anschrift Kunde", "name_en": "Customer name and address", "legal_basis": "Art. 226 Nr. 6", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "supply_description", "name_de": "Leistungsbeschreibung", "name_en": "Description of goods/services", "legal_basis": "Art. 226 Nr. 6", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "TEXT"},
        {"feature_id": "supply_date", "name_de": "Lieferdatum", "name_en": "Date of supply", "legal_basis": "Art. 226 Nr. 7", "required_level": "REQUIRED", "extraction_type": "DATE", "category": "DATE"},
        {"feature_id": "taxable_amount", "name_de": "Bemessungsgrundlage", "name_en": "Taxable amount", "legal_basis": "Art. 226 Nr. 8", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"},
        {"feature_id": "vat_rate", "name_de": "Steuersatz", "name_en": "VAT rate", "legal_basis": "Art. 226 Nr. 10", "required_level": "REQUIRED", "extraction_type": "PERCENTAGE", "category": "TAX"},
        {"feature_id": "vat_amount", "name_de": "Steuerbetrag", "name_en": "VAT amount", "legal_basis": "Art. 226 Nr. 10", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "TAX"},
        {"feature_id": "reverse_charge_notice", "name_de": "Reverse-Charge-Hinweis", "name_en": "Reverse charge notice", "legal_basis": "Art. 226 Nr. 11a", "required_level": "CONDITIONAL", "extraction_type": "TEXTBLOCK", "category": "TAX"}
    ]'
),
(
    'UK_VAT',
    '1.0.0',
    'UK',
    'UK VAT (HMRC)',
    'UK VAT (HMRC)',
    '[{"law": "VAT Act 1994", "section": "Schedule 11", "description_en": "VAT invoice requirements"}, {"law": "HMRC VAT Notice 700", "section": "Section 16", "description_en": "VAT invoices"}]',
    '[
        {"feature_id": "supplier_name_address", "name_en": "Supplier name, address, VAT number", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "supplier_vat_number", "name_en": "Supplier VAT registration number", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "TAX"},
        {"feature_id": "invoice_number", "name_en": "Unique identifying number", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "STRING", "category": "IDENTITY"},
        {"feature_id": "invoice_date", "name_en": "Date of issue", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "DATE", "category": "DATE"},
        {"feature_id": "tax_point", "name_en": "Time of supply (tax point)", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "DATE", "category": "DATE"},
        {"feature_id": "customer_name_address", "name_en": "Customer name and address", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "IDENTITY"},
        {"feature_id": "supply_description", "name_en": "Description of goods/services", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "TEXTBLOCK", "category": "TEXT"},
        {"feature_id": "quantity", "name_en": "Quantity of goods", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "NUMBER", "category": "TEXT"},
        {"feature_id": "unit_price", "name_en": "Unit price (excl. VAT)", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"},
        {"feature_id": "vat_rate", "name_en": "Rate of VAT", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "PERCENTAGE", "category": "TAX"},
        {"feature_id": "total_excl_vat", "name_en": "Total excluding VAT", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"},
        {"feature_id": "total_vat", "name_en": "Total VAT charged", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "TAX"},
        {"feature_id": "total_incl_vat", "name_en": "Total amount payable", "legal_basis": "VAT Notice 700", "required_level": "REQUIRED", "extraction_type": "MONEY", "category": "AMOUNT"}
    ]'
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO flowaudit;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO flowaudit;
