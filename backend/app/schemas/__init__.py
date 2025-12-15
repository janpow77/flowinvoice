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
    DocumentCreate,
    DocumentResponse,
    DocumentUploadResponse,
    ParseRunResponse,
    PrecheckRunResponse,
)
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackOverride
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
from app.schemas.result import FinalResultResponse
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
