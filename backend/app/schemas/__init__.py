# Pfad: /backend/app/schemas/__init__.py
"""
FlowAudit Pydantic Schemas

Request/Response-Modelle für die API.
"""

from app.schemas.common import (
    BoundingBox,
    DateRange,
    Meta,
    Money,
    PaginatedResponse,
    ProblemDetail,
)
from app.schemas.document import (
    AnalysisResultResponse,
    DocumentCreate,
    DocumentResponse,
    DocumentUploadResponse,
    ParseRunResponse,
    PrecheckRunResponse,
)
from app.schemas.feedback import FeedbackCreate, FeedbackOverride, FeedbackResponse
from app.schemas.grant_purpose import (
    DimensionAssessment,
    GrantPurposeAuditRequest,
    GrantPurposeAuditResult,
    NegativeIndicator,
)
from app.schemas.llm import (
    LlmRunCreate,
    LlmRunLogResponse,
    LlmRunResponse,
    PreparePayloadResponse,
)
from app.schemas.project import (
    BeneficiarySchema,
    ImplementationSchema,
    ProjectCreate,
    ProjectResponse,
    ProjectSchema,
)
from app.schemas.rag import RagExampleResponse, RagRetrieveRequest, RagRetrieveResponse
from app.schemas.result import (
    AnalysisMetadata,
    FinalResultResponse,
    UnclearStatus,
)
from app.schemas.risk import (
    RiskAssessmentRequest,
    RiskAssessmentResult,
    RiskContext,
    RiskFinding,
)
from app.schemas.ruleset import FeatureSchema, RulesetResponse
from app.schemas.settings import (
    ApiKeyResponse,
    ApiKeySet,
    ProviderSettings,
    SettingsResponse,
    SettingsUpdate,
)
from app.schemas.stats import (
    FeedbackStatsResponse,
    GlobalStatsResponse,
    LlmStatsResponse,
    ProjectStatsResponse,
    RagStatsResponse,
    SystemStatsResponse,
)

__all__ = [
    # Common
    "Money",
    "DateRange",
    "BoundingBox",
    "Meta",
    "ProblemDetail",
    "PaginatedResponse",
    # Ruleset
    "RulesetResponse",
    "FeatureSchema",
    # Project
    "ProjectCreate",
    "ProjectResponse",
    "ProjectSchema",
    "BeneficiarySchema",
    "ImplementationSchema",
    # Document
    "AnalysisResultResponse",
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUploadResponse",
    "ParseRunResponse",
    "PrecheckRunResponse",
    # LLM
    "PreparePayloadResponse",
    "LlmRunCreate",
    "LlmRunResponse",
    "LlmRunLogResponse",
    # Result
    "FinalResultResponse",
    "AnalysisMetadata",
    "UnclearStatus",
    # Grant Purpose Audit
    "GrantPurposeAuditRequest",
    "GrantPurposeAuditResult",
    "DimensionAssessment",
    "NegativeIndicator",
    # Risk Assessment
    "RiskAssessmentRequest",
    "RiskAssessmentResult",
    "RiskContext",
    "RiskFinding",
    # Feedback
    "FeedbackCreate",
    "FeedbackResponse",
    "FeedbackOverride",
    # RAG
    "RagExampleResponse",
    "RagRetrieveRequest",
    "RagRetrieveResponse",
    # Settings
    "SettingsResponse",
    "SettingsUpdate",
    "ProviderSettings",
    "ApiKeySet",
    "ApiKeyResponse",
    # Stats
    "GlobalStatsResponse",
    "ProjectStatsResponse",
    "FeedbackStatsResponse",
    "LlmStatsResponse",
    "RagStatsResponse",
    "SystemStatsResponse",
]
