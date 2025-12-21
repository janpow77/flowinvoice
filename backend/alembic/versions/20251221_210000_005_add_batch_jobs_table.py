"""Add batch_jobs table

Revision ID: 005
Revises: 004
Create Date: 2025-12-21 21:00:00.000000+00:00

Adds table for batch job management.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create batch_jobs table
    op.create_table(
        "batch_jobs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("job_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, index=True, default="PENDING"),
        sa.Column(
            "created_by_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("parameters", JSONB, default=dict),
        sa.Column("total_items", sa.Integer(), default=0),
        sa.Column("processed_items", sa.Integer(), default=0),
        sa.Column("successful_items", sa.Integer(), default=0),
        sa.Column("failed_items", sa.Integer(), default=0),
        sa.Column("skipped_items", sa.Integer(), default=0),
        sa.Column("progress_percent", sa.Float(), default=0.0),
        sa.Column("results", JSONB, default=dict),
        sa.Column("errors", JSONB, default=list),
        sa.Column("warnings", JSONB, default=list),
        sa.Column("status_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), default=False),
        sa.Column("schedule_cron", sa.String(100), nullable=True),
        sa.Column("priority", sa.Integer(), default=0),
        sa.Column("max_retries", sa.Integer(), default=3),
        sa.Column("retry_count", sa.Integer(), default=0),
    )


def downgrade() -> None:
    op.drop_table("batch_jobs")
