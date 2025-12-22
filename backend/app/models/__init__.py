# Pfad: /backend/app/models/__init__.py
"""
FlowAudit SQLAlchemy Models

Alle Datenbankmodelle für das System.
"""

from app.models.audit import AuditEvent
from app.models.document import Document, ParseRun, PrecheckRun
from app.models.export import ExportJob, GeneratorJob
from app.models.feedback import Feedback, RagExample
from app.models.llm import LlmRun, LlmRunLog, PreparePayload
from app.models.project import Project
from app.models.project_share import ProjectShare
from app.models.result import AnalysisResult, FinalResult
from app.models.ruleset import Ruleset
from app.models.ruleset_checker import RulesetCheckerSettings
from app.models.ruleset_sample import RulesetSample
from app.models.settings import ApiKey, Setting
from app.models.solution import SolutionFile, SolutionMatch
from app.models.document_type import DocumentTypeSettings
from app.models.training import ModelRegistry, TrainingDataset, TrainingExample, TrainingRun
from app.models.user import User
from app.models.batch_job import BatchJob
from app.models.custom_criterion import CustomCriterion

__all__ = [
    # Core
    "Ruleset",
    "RulesetCheckerSettings",
    "RulesetSample",
    "Project",
    "ProjectShare",
    "Document",
    # Parsing
    "ParseRun",
    "PrecheckRun",
    # LLM
    "PreparePayload",
    "LlmRun",
    "LlmRunLog",
    # Results
    "AnalysisResult",
    "FinalResult",
    "Feedback",
    "RagExample",
    # Training
    "TrainingExample",
    "TrainingDataset",
    "TrainingRun",
    "ModelRegistry",
    # Settings
    "Setting",
    "ApiKey",
    "DocumentTypeSettings",
    # Export
    "ExportJob",
    "GeneratorJob",
    # Solution Files
    "SolutionFile",
    "SolutionMatch",
    # Audit
    "AuditEvent",
    # User
    "User",
    # Batch Jobs
    "BatchJob",
    # Custom Criteria
    "CustomCriterion",
]
