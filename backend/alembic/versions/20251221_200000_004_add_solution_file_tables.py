"""Add solution_files and solution_matches tables

Revision ID: 004
Revises: 003
Create Date: 2025-12-21 20:00:00.000000+00:00

Adds tables for solution file import and matching.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create solution_files table
    op.create_table(
        "solution_files",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("generator_version", sa.String(50), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_count", sa.Integer(), default=0),
        sa.Column("valid_count", sa.Integer(), default=0),
        sa.Column("invalid_count", sa.Integer(), default=0),
        sa.Column("error_count", sa.Integer(), default=0),
        sa.Column("entries", JSONB, default=list),
        sa.Column("applied", sa.Boolean(), default=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "applied_by_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("applied_count", sa.Integer(), default=0),
        sa.Column("skipped_count", sa.Integer(), default=0),
        sa.Column("rag_examples_created", sa.Integer(), default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create solution_matches table
    op.create_table(
        "solution_matches",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "solution_file_id",
            UUID(as_uuid=False),
            sa.ForeignKey("solution_files.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            UUID(as_uuid=False),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("solution_position", sa.Integer(), nullable=False),
        sa.Column("solution_filename", sa.String(255), nullable=False),
        sa.Column("match_confidence", sa.Float(), default=1.0),
        sa.Column("match_reason", sa.String(255), nullable=True),
        sa.Column("strategy_used", sa.String(50), nullable=True),
        sa.Column("is_valid", sa.Boolean(), default=True),
        sa.Column("errors", JSONB, default=list),
        sa.Column("fields", JSONB, default=dict),
        sa.Column("applied", sa.Boolean(), default=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("errors_applied", sa.Integer(), default=0),
        sa.Column("fields_updated", sa.Integer(), default=0),
        sa.Column("rag_examples_created", sa.Integer(), default=0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create unique constraint to prevent duplicate matches
    op.create_unique_constraint(
        "uq_solution_match_document",
        "solution_matches",
        ["solution_file_id", "document_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_solution_match_document", "solution_matches", type_="unique")
    op.drop_table("solution_matches")
    op.drop_table("solution_files")
