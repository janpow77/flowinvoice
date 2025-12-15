# FlowAudit – API Contracts (OpenAPI-orientiert, voll spezifiziert)
## Version: 0.1.0 (Contract-First)
## Basis-URL: /api
## Auth: Demo (optional). Rollen: user | admin (Header: X-Role)

---

## 0. Allgemeine Regeln

### 0.1 Content Types
- Requests: `application/json` (außer Upload)
- Upload: `multipart/form-data`
- Responses: `application/json`
- Fehler: `application/problem+json`

### 0.2 Standard-Header
- `X-Role`: `"user"` | `"admin"` (Demo; später durch echte Auth ersetzen)
- `X-Request-Id`: optional (Client erzeugt UUID)
- `Accept-Language`: `"de"` | `"en"` (UI Sprache; unabhängig vom Ruleset)

### 0.3 Standard-Response-Envelope (für Listen/Standardobjekte)
**Hinweis:** Für einfache GETs kann direkt das Objekt zurückgegeben werden. Für Konsistenz wird empfohlen:
```json
{
  "data": { },
  "meta": { "request_id": "..." }
}
````

### 0.4 Problem Details (RFC 7807)

```json
{
  "type": "https://flowaudit.local/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Field project_period_end must be after project_period_start",
  "instance": "/api/projects",
  "errors": [
    { "field": "project_period_end", "message": "must be after start" }
  ]
}
```

---

## 1. Globale Schemas (JSON-Schema-kompatibel)

### 1.1 Enum: Role

* `user`
* `admin`

### 1.2 Enum: RulesetId

* `DE_USTG`
* `EU_VAT`
* `UK_VAT`

### 1.3 Enum: UiLanguage

* `de`
* `en`

### 1.4 Enum: DocumentStatus

* `UPLOADED`
* `PARSING`
* `PARSED`
* `PRECHECKED`
* `PREPARED`
* `LLM_RUNNING`
* `LLM_DONE`
* `REVIEW_PENDING`
* `ACCEPTED`
* `REJECTED`
* `EXPORTED`
* `ERROR`

### 1.5 Enum: CheckStatus (Merkmalstatus)

* `PRESENT`
* `MISSING`
* `UNCLEAR`

### 1.6 Enum: RuleCheckStatus

* `OK`
* `WARN`
* `FAIL`
* `UNKNOWN`

### 1.7 Enum: TruthSource

* `RULE`
* `LLM`
* `USER`

### 1.8 Enum: Provider

* `LOCAL_OLLAMA`
* `OPENAI`
* `ANTHROPIC`
* `GEMINI`

### 1.9 Enum: FeedbackRating

* `CORRECT`
* `PARTIAL`
* `WRONG`

### 1.10 Enum: RelationLevel

* `YES`
* `PARTIAL`
* `UNCLEAR`
* `NO`

### 1.11 Schema: Money

```json
{
  "amount": "1234.56",
  "currency": "EUR"
}
```

### 1.12 Schema: DateRange

```json
{
  "start": "2025-01-01",
  "end": "2025-12-31"
}
```

### 1.13 Schema: BoundingBox (normalized)

```json
{
  "page": 1,
  "x0": 0.12,
  "y0": 0.33,
  "x1": 0.56,
  "y1": 0.38,
  "confidence": 0.94
}
```

---

## 2. Health & Meta

### 2.1 GET /api/health

**Response 200**

```json
{
  "status": "ok",
  "time_utc": "2025-12-15T12:00:00Z",
  "version": "0.1.0",
  "services": {
    "db": "ok",
    "ollama": "ok",
    "vectorstore": "ok"
  }
}
```

### 2.2 GET /api/meta

Liefert UI-Infos und Zähler.
**Response 200**

```json
{
  "active": {
    "ruleset_id": "DE_USTG",
    "ruleset_version": "1.0.0",
    "ui_language": "de",
    "provider": "LOCAL_OLLAMA",
    "model_name": "llama3.1:8b-instruct-q4"
  },
  "counters": {
    "projects_total": 12,
    "documents_total": 540,
    "documents_session": 6,
    "rag_examples_total": 84
  }
}
```

---

## 3. Settings (Provider/Model/Generator Pfade)

### 3.1 GET /api/settings

**Response 200**

```json
{
  "active_provider": "LOCAL_OLLAMA",
  "providers": {
    "LOCAL_OLLAMA": {
      "enabled": true,
      "base_url": "http://ollama:11434",
      "model_name": "llama3.1:8b-instruct-q4",
      "available_models": ["llama3.1:8b-instruct-q4", "mistral:7b", "qwen2:7b"]
    },
    "OPENAI": {
      "enabled": true,
      "api_key_is_set": true,
      "api_key_masked": "sk-****************************abcd",
      "model_name": "gpt-4o-mini",
      "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
    },
    "ANTHROPIC": {
      "enabled": true,
      "api_key_is_set": true,
      "api_key_masked": "sk-ant-************************1234",
      "model_name": "claude-sonnet-4-20250514",
      "available_models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"]
    },
    "GEMINI": {
      "enabled": false,
      "api_key_is_set": false,
      "api_key_masked": null,
      "model_name": "gemini-1.5-flash",
      "available_models": ["gemini-1.5-pro", "gemini-1.5-flash"]
    }
  },
  "inference": {
    "temperature": 0.2,
    "max_tokens": 2000,
    "timeout_sec": 120,
    "parallel_requests": 2,
    "retry_on_error": true,
    "max_retries": 3
  },
  "generator": {
    "output_dir": "/data/generated",
    "solutions_dir": "/data/generated",
    "enable_admin_menu": true
  },
  "rag": {
    "enabled": true,
    "top_k": 3,
    "similarity_threshold": 0.25
  },
  "logging": {
    "verbose": false
  }
}
```

### 3.2 PUT /api/settings

**Request** (partielle Updates erlaubt)

```json
{
  "active_provider": "ANTHROPIC",
  "providers": {
    "ANTHROPIC": {
      "model_name": "claude-sonnet-4-20250514"
    }
  },
  "inference": {
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

**Response 200**

* wie GET (vollständiges Settings-Objekt)

### 3.3 PUT /api/settings/providers/{provider_id}/api-key

Setzt oder aktualisiert API-Key für einen Provider.

**Request**

```json
{
  "api_key": "sk-ant-api03-..."
}
```

**Response 200**

```json
{
  "provider": "ANTHROPIC",
  "api_key_is_set": true,
  "api_key_masked": "sk-ant-************************wxyz"
}
```

### 3.4 DELETE /api/settings/providers/{provider_id}/api-key

Löscht API-Key für einen Provider.

**Response 200**

```json
{
  "provider": "ANTHROPIC",
  "api_key_is_set": false
}
```

### 3.5 POST /api/settings/providers/{provider_id}/test

Testet Verbindung und API-Key-Gültigkeit.

**Response 200**

```json
{
  "provider": "ANTHROPIC",
  "status": "ok",
  "model_accessible": true,
  "latency_ms": 450,
  "message": "Connection successful"
}
```

**Response 401** (ungültiger Key)

```json
{
  "provider": "ANTHROPIC",
  "status": "error",
  "message": "Invalid API key"
}
```

### 3.6 GET /api/settings/providers/LOCAL_OLLAMA/models

Listet verfügbare lokale Modelle von Ollama.

**Response 200**

```json
{
  "models": [
    {
      "name": "llama3.1:8b-instruct-q4",
      "size_gb": 4.7,
      "loaded": true,
      "modified_at": "2025-12-10T10:00:00Z"
    },
    {
      "name": "mistral:7b",
      "size_gb": 4.1,
      "loaded": false,
      "modified_at": "2025-12-01T08:00:00Z"
    }
  ]
}
```

### 3.7 POST /api/settings/providers/LOCAL_OLLAMA/models/pull

Lädt ein neues Modell herunter.

**Request**

```json
{
  "model_name": "qwen2:7b"
}
```

**Response 202**

```json
{
  "status": "pulling",
  "model_name": "qwen2:7b",
  "progress_url": "/api/settings/providers/LOCAL_OLLAMA/models/pull/status"
}
```

**Validations**

* `temperature` 0..1.5
* `max_tokens` 64..8192
* `timeout_sec` 30..300
* `parallel_requests` 1..10
* `output_dir` muss existieren oder vom System anlegbar sein

---

## 4. Rulesets (DE/EU/UK, Versioniert)

### 4.1 GET /api/rulesets

**Response 200**

```json
{
  "data": [
    { "ruleset_id": "DE_USTG", "version": "1.0.0", "title": "Deutschland §14 UStG", "language_support": ["de","en"] },
    { "ruleset_id": "EU_VAT", "version": "1.0.0", "title": "EU VAT Directive 2006/112/EC Art. 226", "language_support": ["de","en"] },
    { "ruleset_id": "UK_VAT", "version": "1.0.0", "title": "UK VAT Invoice (HMRC)", "language_support": ["de","en"] }
  ]
}
```

### 4.2 GET /api/rulesets/{ruleset_id}

**Response 200**

```json
{
  "ruleset_id": "DE_USTG",
  "version": "1.0.0",
  "legal_refs": [
    { "code": "UStG", "section": "§ 14 Abs. 4", "label_de": "Pflichtangaben", "label_en": "Mandatory invoice fields" }
  ],
  "features": [
    {
      "feature_id": "supplier_name_address",
      "name_de": "Name und Anschrift des leistenden Unternehmers",
      "name_en": "Supplier name and address",
      "legal_basis": "§ 14 Abs. 4 Nr. 1 UStG",
      "required_level": "REQUIRED",
      "extraction_type": "TEXTBLOCK",
      "validation_rules": { "regex": null, "min_len": 10 },
      "explanation_de": "…",
      "explanation_en": "…",
      "generator_rules": { "can_omit": true, "omit_probability_default": 0.0 }
    }
  ]
}
```

### 4.3 POST /api/rulesets (Admin)

Legt neue Version oder neues Ruleset an.
**Request**

* gleich wie GET ruleset payload
  **Response 201**

```json
{ "ruleset_id": "DE_USTG", "version": "1.1.0" }
```

### 4.4 PUT /api/rulesets/{ruleset_id}/{version} (Admin)

Update einer Version (optional; besser: immutable + new version).
**Response 200** updated payload.

---

## 5. Projects (Vorhaben)

### 5.1 Schema: ProjectCreate/Update

```json
{
  "ruleset_id_hint": "DE_USTG",
  "ui_language_hint": "de",
  "beneficiary": {
    "name": "Muster GmbH",
    "legal_form": "GMBH",
    "street": "Musterstraße 1",
    "zip": "12345",
    "city": "Musterstadt",
    "country": "DE",
    "vat_id": "DE123456789",
    "tax_number": "12/345/67890",
    "input_tax_deductible": true,
    "aliases": ["Muster GmbH", "Muster GmbH i.G."]
  },
  "project": {
    "project_title": "Baumaßnahme Aschaffenburg",
    "file_reference": "AZ-2025-0001",
    "project_description": "Umbau und Sanierung …",
    "implementation_location": "Aschaffenburg",
    "implementation_address": "Baustelle …",
    "total_budget": { "amount": "5000000.00", "currency": "EUR" },
    "funding_type": "PERCENT",
    "funding_rate_percent": 70.0,
    "funding_fixed_amount": null,
    "eligible_cost_categories": ["Bau", "Planung", "IT"],
    "project_period": { "start": "2025-01-01", "end": "2025-12-31" },
    "approval_date": "2024-12-20",
    "approving_authority": "Bewilligungsbehörde X"
  }
}
```

### 5.2 POST /api/projects

**Response 201**

```json
{ "project_id": "prj_9b3c...", "created_at": "2025-12-15T12:00:00Z" }
```

### 5.3 GET /api/projects

Query:

* `q=` search
* `limit`, `offset`
  **Response 200**

```json
{
  "data": [
    { "project_id": "prj_...", "project_title": "Baumaßnahme Aschaffenburg", "file_reference": "AZ-2025-0001", "ruleset_id_hint": "DE_USTG" }
  ],
  "meta": { "total": 1, "limit": 50, "offset": 0 }
}
```

### 5.4 GET /api/projects/{project_id}

**Response 200**

* full Project payload (as create schema) plus ids

### 5.5 PUT /api/projects/{project_id}

**Response 200**

* updated project

### 5.6 POST /api/projects/{project_id}/activate

Setzt aktives Projekt für Session (Demo).
**Response 200**

```json
{ "active_project_id": "prj_..." }
```

---

## 6. Documents (Upload, Parse, Analyse)

### 6.1 POST /api/projects/{project_id}/documents/upload

**Content-Type**: multipart/form-data
Fields:

* `files`: one or many
* optional: `client_tags` (json string)
  **Response 201**

```json
{
  "data": [
    {
      "document_id": "doc_123",
      "filename": "invoice_01.pdf",
      "sha256": "a8f3...",
      "status": "UPLOADED",
      "is_duplicate_in_project": false
    }
  ]
}
```

### 6.2 GET /api/projects/{project_id}/documents

Query:

* `status=` optional
* `limit`, `offset`
  **Response 200**

```json
{
  "data": [
    {
      "document_id": "doc_123",
      "filename": "invoice_01.pdf",
      "status": "PARSED",
      "ruleset_id": "DE_USTG",
      "created_at": "2025-12-15T12:00:00Z"
    }
  ],
  "meta": { "total": 1 }
}
```

### 6.3 GET /api/documents/{document_id}

**Response 200**

```json
{
  "document_id": "doc_123",
  "project_id": "prj_...",
  "filename": "invoice_01.pdf",
  "sha256": "a8f3...",
  "status": "LLM_DONE",
  "ruleset_id": "DE_USTG",
  "ui_language": "de",
  "created_at": "2025-12-15T12:00:00Z"
}
```

### 6.4 GET /api/documents/{document_id}/file

Returns original PDF (stream).
**Response 200**

* `application/pdf`

### 6.5 POST /api/documents/{document_id}/parse

Start parsing (sync or async).
**Response 202**

```json
{
  "document_id": "doc_123",
  "status": "PARSING",
  "parse_run_id": "parse_456"
}
```

### 6.6 GET /api/parse-runs/{parse_run_id}

**Response 200**

```json
{
  "parse_run_id": "parse_456",
  "document_id": "doc_123",
  "engine": "HYBRID",
  "status": "DONE",
  "timings_ms": { "total": 1830 },
  "outputs": {
    "raw_text_len": 5421,
    "pages": 2
  }
}
```

### 6.7 GET /api/documents/{document_id}/parsed

Returns parse output summary + tokens+bboxes pointer.
**Response 200**

```json
{
  "document_id": "doc_123",
  "engine": "HYBRID",
  "raw_text": "…",
  "pages": [
    {
      "page": 1,
      "tokens": [
        { "text": "Rechnung", "bbox": { "page": 1, "x0": 0.1, "y0": 0.1, "x1": 0.2, "y1": 0.12, "confidence": 0.98 } }
      ]
    }
  ]
}
```

---

## 7. Precheck (Regel-Engine)

### 7.1 POST /api/documents/{document_id}/precheck

**Response 202**

```json
{
  "precheck_run_id": "pre_789",
  "document_id": "doc_123",
  "status": "RUNNING"
}
```

### 7.2 GET /api/precheck-runs/{precheck_run_id}

**Response 200**

```json
{
  "precheck_run_id": "pre_789",
  "document_id": "doc_123",
  "status": "DONE",
  "checks": [
    {
      "check_id": "DATE_WITHIN_PROJECT",
      "status": "OK",
      "observed": { "invoice_date": "2025-03-01", "project_period": { "start": "2025-01-01", "end": "2025-12-31" } },
      "comment": "Invoice date within project period",
      "confidence": 0.95
    },
    {
      "check_id": "MATH_NET_VAT_GROSS",
      "status": "WARN",
      "observed": { "net": "100.00", "vat_rate": "0.19", "vat": "18.90", "gross": "119.00" },
      "comment": "Rounding difference 0.10",
      "confidence": 0.90
    }
  ]
}
```

---

## 8. Prepare Payload (Input-JSON an KI) – MUSS persistiert & UI-sichtbar sein

### 8.1 POST /api/documents/{document_id}/prepare

Creates `PreparePayload` (stored) and returns it.
**Response 201**

```json
{
  "payload_id": "pay_001",
  "document_id": "doc_123",
  "schema_version": "1.0",
  "ruleset": { "ruleset_id": "DE_USTG", "version": "1.0.0" },
  "ui_language": "de",
  "project_context": { "project_id": "prj_..." },
  "parsing_summary": { "engine": "HYBRID", "raw_text_len": 5421 },
  "deterministic_precheck_results": { "precheck_run_id": "pre_789" },
  "features": [
    { "feature_id": "invoice_number", "required_level": "REQUIRED" }
  ],
  "extracted_text": "…",
  "required_output_schema": { "type": "object", "properties": { "features": { "type": "array" } } },
  "rag_context": { "enabled": true, "examples": [] }
}
```

### 8.2 GET /api/payloads/{payload_id}

Returns persisted prepare payload.
**Response 200**

* same as above

### 8.3 GET /api/documents/{document_id}/payload

Convenience endpoint: latest payload for doc.
**Response 200**

* payload

---

## 9. LLM Run (lokal/extern)

### 9.1 POST /api/documents/{document_id}/run

Starts LLM inference using latest payload (or specify payload_id).
**Request**

```json
{
  "payload_id": "pay_001",
  "provider_override": null,
  "model_override": null
}
```

**Response 202**

```json
{
  "llm_run_id": "llm_001",
  "document_id": "doc_123",
  "status": "RUNNING"
}
```

### 9.2 GET /api/llm-runs/{llm_run_id}

**Response 200**

```json
{
  "llm_run_id": "llm_001",
  "document_id": "doc_123",
  "payload_id": "pay_001",
  "provider": "LOCAL_OLLAMA",
  "model_name": "llama3.1:8b-instruct-q4",
  "status": "DONE",
  "timings_ms": { "llm": 12800 },
  "token_usage": { "input": 2100, "output": 650 },
  "raw_response_text": "{...}",
  "structured_response": {
    "features": [
      {
        "feature_id": "invoice_number",
        "status": "PRESENT",
        "extracted_value": "2025-001",
        "confidence": 92,
        "rationale": "Found in header",
        "evidence": [{ "page": 1, "x0": 0.6, "y0": 0.12, "x1": 0.9, "y1": 0.14, "confidence": 0.95 }]
      }
    ],
    "semantic_project_fit": {
      "relation_level": "YES",
      "reasons": ["Construction services match project description"],
      "mapped_cost_category": "Bau",
      "time_plausible": true,
      "location_plausible": true,
      "beneficiary_plausible": true
    }
  }
}
```

### 9.3 GET /api/documents/{document_id}/llm

Latest llm run for doc.
**Response 200**

* same as above

### 9.4 GET /api/llm-runs/{llm_run_id}/logs

Returns log events (for LogView).
**Response 200**

```json
{
  "llm_run_id": "llm_001",
  "events": [
    { "ts": "2025-12-15T12:00:01Z", "level": "INFO", "msg": "payload loaded", "data": { "payload_id": "pay_001" } },
    { "ts": "2025-12-15T12:00:02Z", "level": "INFO", "msg": "provider request sent", "data": { "provider": "LOCAL_OLLAMA" } },
    { "ts": "2025-12-15T12:00:14Z", "level": "INFO", "msg": "response received", "data": { "tokens_out": 650 } }
  ]
}
```

---

## 10. Final Results (Konfliktlösung + berechnete Förderlogik)

### 10.1 POST /api/documents/{document_id}/finalize

Builds `final_results` based on rules+llm+user overrides (if any).
**Response 201**

```json
{
  "final_result_id": "fin_001",
  "document_id": "doc_123",
  "status": "REVIEW_PENDING",
  "computed": {
    "amounts": {
      "net": { "amount": "100.00", "currency": "EUR" },
      "vat": { "amount": "19.00", "currency": "EUR" },
      "gross": { "amount": "119.00", "currency": "EUR" },
      "eligible_amount": { "amount": "100.00", "currency": "EUR" },
      "funded_amount": { "amount": "70.00", "currency": "EUR" }
    }
  },
  "fields": [
    {
      "feature_id": "invoice_date",
      "rule_value": "2025-03-01",
      "llm_value": "2025-03-01",
      "user_value": null,
      "final_value": "2025-03-01",
      "source_of_truth": "RULE",
      "conflict_flag": false,
      "conflict_reason": null
    }
  ],
  "overall": {
    "traffic_light": "GREEN",
    "missing_required_features": [],
    "conflicts": []
  }
}
```

### 10.2 GET /api/final-results/{final_result_id}

Returns final result object.

### 10.3 GET /api/documents/{document_id}/final

Latest final result for doc.

---

## 11. Feedback (Human-in-the-loop)

### 11.1 POST /api/documents/{document_id}/feedback

**Request**

```json
{
  "final_result_id": "fin_001",
  "rating": "PARTIAL",
  "comment": "VAT amount rounding corrected; beneficiary spelling accepted.",
  "overrides": [
    { "feature_id": "vat_amount", "user_value": "19.00", "note": "OCR misread 18.90" },
    { "feature_id": "customer_name_address", "user_value": "Muster GmbH, Musterstraße 1, 12345 Musterstadt", "note": "Accepted alias" }
  ],
  "accept_result": true
}
```

**Response 201**

```json
{
  "feedback_id": "fb_001",
  "document_id": "doc_123",
  "stored_rag_example_id": "rag_001",
  "document_status": "ACCEPTED"
}
```

### 11.2 GET /api/documents/{document_id}/feedback

List feedback entries.
**Response 200**

```json
{
  "data": [
    { "feedback_id": "fb_001", "rating": "PARTIAL", "created_at": "2025-12-15T12:30:00Z" }
  ]
}
```

---

## 12. RAG (Vector Store)

### 12.1 GET /api/rag/examples

Query:

* ruleset_id
* limit/offset
  **Response 200**

```json
{
  "data": [
    { "rag_example_id": "rag_001", "ruleset_id": "DE_USTG", "created_at": "2025-12-15T12:30:00Z" }
  ],
  "meta": { "total": 84 }
}
```

### 12.2 GET /api/rag/examples/{rag_example_id}

Returns stored correction and minimal context (no secrets).

### 12.3 POST /api/rag/retrieve (debug)

Allows UI to show which examples would be used.
**Request**

```json
{ "payload_id": "pay_001", "top_k": 3 }
```

**Response 200**

```json
{
  "matches": [
    { "rag_example_id": "rag_001", "similarity": 0.83, "reason": "same supplier signature" }
  ]
}
```

---

## 13. Statistics

### 13.1 GET /api/projects/{project_id}/stats

**Response 200**

```json
{
  "project_id": "prj_...",
  "counters": {
    "documents_total": 50,
    "accepted": 40,
    "review_pending": 10,
    "rejected": 0,
    "rag_examples_used": 12
  },
  "timings": {
    "avg_parse_ms": 1200,
    "avg_llm_ms": 10500,
    "avg_total_ms": 12800
  },
  "tokens": {
    "avg_in": 2100,
    "avg_out": 650
  },
  "feature_error_rates": [
    { "feature_id": "supplier_tax_or_vat_id", "missing_rate": 0.12, "unclear_rate": 0.05 }
  ]
}
```

### 13.2 GET /api/stats/global

Aggregated statistics for dashboard.

---

## 14. Export (erst nach Feedback)

### 14.1 POST /api/projects/{project_id}/export

**Request**

```json
{
  "format": "XLSX",
  "only_status": ["ACCEPTED"],
  "include_payloads": false,
  "include_llm_responses": false
}
```

**Response 202**

```json
{ "export_job_id": "exp_001", "status": "RUNNING" }
```

### 14.2 GET /api/exports/{export_job_id}

**Response 200**

```json
{
  "export_job_id": "exp_001",
  "status": "DONE",
  "file_path": "/data/exports/project_prj_..._2025-12-15.xlsx",
  "download_url": "/api/exports/exp_001/file"
}
```

### 14.3 GET /api/exports/{export_job_id}/file

Streams file.

---

## 15. Generator (Admin-only)

### 15.1 GET /api/generator/templates

Returns template metadata + preview SVG/PNG refs.
**Response 200**

```json
{
  "data": [
    { "template_id": "T1_HANDWERK", "name": "Handwerker", "preview_url": "/api/generator/templates/T1_HANDWERK/preview" },
    { "template_id": "T2_SUPERMARKT", "name": "Supermarkt", "preview_url": "/api/generator/templates/T2_SUPERMARKT/preview" },
    { "template_id": "T3_CORPORATE", "name": "Konzern", "preview_url": "/api/generator/templates/T3_CORPORATE/preview" },
    { "template_id": "T4_FREELANCER", "name": "Freelancer", "preview_url": "/api/generator/templates/T4_FREELANCER/preview" },
    { "template_id": "T5_MINIMAL", "name": "Minimal", "preview_url": "/api/generator/templates/T5_MINIMAL/preview" }
  ]
}
```

### 15.2 POST /api/generator/run

**Request**

```json
{
  "project_id": "prj_...",
  "ruleset_id": "DE_USTG",
  "language": "de",
  "count": 20,
  "templates_enabled": ["T1_HANDWERK","T3_CORPORATE"],
  "error_rate_total": 5.0,
  "severity": 2,
  "per_feature_error_rates": {
    "supplier_tax_or_vat_id": 3.0,
    "invoice_number": 1.0,
    "supply_date_or_period": 2.0
  },
  "alias_noise_probability": 10.0,
  "date_format_profiles": ["DD.MM.YYYY", "RANGE_DD.MM.YYYY-DD.MM.YYYY", "MONTH_NAME_DE"],
  "output_dir_override": null
}
```

**Response 202**

```json
{
  "generator_job_id": "gen_001",
  "status": "RUNNING",
  "output_dir": "/data/generated/2025-12-15_120000",
  "solutions_file": "/data/generated/2025-12-15_120000/solutions.txt"
}
```

### 15.3 GET /api/generator/jobs/{generator_job_id}

**Response 200**

```json
{
  "generator_job_id": "gen_001",
  "status": "DONE",
  "generated_files": [
    { "filename": "INV_0001.pdf", "path": "/data/generated/.../INV_0001.pdf" }
  ],
  "solutions_file": "/data/generated/.../solutions.txt"
}
```

### 15.4 GET /api/generator/jobs/{generator_job_id}/solutions (Admin)

Returns parsed solutions (but never stored in DB).
**Response 200**

```json
{
  "solutions_file": "solutions.txt",
  "entries": [
    { "filename": "INV_0001.pdf", "wrong_features": ["supplier_tax_or_vat_id"] }
  ]
}
```

---

## 16. Logs & Audit

### 16.1 GET /api/audit/events

Query:

* entity_type/entity_id
* limit/offset
  **Response 200**

```json
{
  "data": [
    { "event_id": "evt_001", "event_type": "DOCUMENT_UPLOADED", "ts": "2025-12-15T12:00:00Z", "entity": { "type": "document", "id": "doc_123" } }
  ]
}
```

### 16.2 GET /api/documents/{document_id}/logstream (optional SSE)

Server-Sent Events for live UI logview.

---

## 17. Fehlercodes (Auswahl)

* 400 VALIDATION_ERROR
* 401 UNAUTHORIZED (wenn Auth später aktiv)
* 403 FORBIDDEN (admin-only endpoints)
* 404 NOT_FOUND
* 409 CONFLICT (duplicate doc hash)
* 422 UNPROCESSABLE (parse failed)
* 500 INTERNAL

---

## 18. Contract Invariants (MUSS)

1. `prepare_payloads` werden **persistiert** und via API abrufbar gemacht.
2. UI darf niemals „PreparePayload neu erzeugen“ ohne ihn zu speichern; `POST /prepare` ist der einzige Erzeugungspunkt.
3. `LLM run` darf nur gegen gespeicherten `payload_id` laufen.
4. `solutions` aus Generator werden **nie** in DB gespeichert; nur als File und via admin-only endpoint lesbar.
5. Export nur für `ACCEPTED` oder `REVIEWED` (oder admin override).

