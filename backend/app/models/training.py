# Pfad: /backend/app/models/training.py
"""
FlowAudit Training Models

Training-Beispiele, Datasets, Training-Runs und Modell-Registry.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Provider

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.project import Project


class TrainingExample(Base):
    """
    Training-Beispiel (Goldstandard).

    Entsteht aus bestätigtem Feedback für lokales Fine-Tuning.
    """

    __tablename__ = "training_examples"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=True
    )

    # Modul (1=UStG, 2=Projektbezug, 3=Risiko)
    module: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Goldstandard-Labels
    label_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Quelle
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    # "manual" = manuell erfasst
    # "corrected_from_ai" = aus KI-Vorschlag korrigiert

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document | None"] = relationship("Document")
    project: Mapped["Project | None"] = relationship("Project")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<TrainingExample {self.id[:8]} Module {self.module}>"


class TrainingDataset(Base):
    """
    Training-Dataset (exportierte JSONL-Dateien).

    Sammlung von Training-Beispielen für Fine-Tuning.
    """

    __tablename__ = "training_datasets"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ruleset_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Statistik
    example_count: Mapped[int] = mapped_column(Integer, default=0)

    # Dateipfade
    train_file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    val_file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Manifest (Hashes, Seed, etc.)
    manifest: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    training_runs: Mapped[list["TrainingRun"]] = relationship(
        "TrainingRun", back_populates="dataset"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<TrainingDataset {self.name} ({self.example_count} examples)>"


class TrainingRun(Base):
    """
    Training-Run (Fine-Tuning-Durchlauf).

    Speichert Hyperparameter, Metriken und Artifacts.
    """

    __tablename__ = "training_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    dataset_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("training_datasets.id"), nullable=True
    )

    # Basis-Modell
    base_model: Mapped[str] = mapped_column(String(100), nullable=False)

    # Hyperparameter
    epochs: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_rate: Mapped[float] = mapped_column(Float, nullable=False)
    lora_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    # Metriken
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    """
    {
        "train_loss": 0.123,
        "eval_loss": 0.145,
        "f1_macro": 0.89
    }
    """

    # Artifacts
    artifacts_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    dataset: Mapped["TrainingDataset | None"] = relationship(
        "TrainingDataset", back_populates="training_runs"
    )

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<TrainingRun {self.id[:8]} [{self.base_model}]>"


class ModelRegistry(Base):
    """
    Modell-Registry.

    Registrierte Modelle (Basis + Fine-Tuned).
    """

    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Provider
    provider: Mapped[Provider] = mapped_column(Enum(Provider), nullable=False)

    # Basis-Modell (für Fine-Tuned)
    base_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Training-Run (falls Fine-Tuned)
    training_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("training_runs.id"), nullable=True
    )

    # Statistik
    trained_examples_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metriken
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Zeitstempel
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    training_run: Mapped["TrainingRun | None"] = relationship("TrainingRun")

    def __repr__(self) -> str:
        """String-Repräsentation."""
        return f"<ModelRegistry {self.model_name}>"
