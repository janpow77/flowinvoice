"""Add project sharing and document type columns

Revision ID: 001
Revises: None
Create Date: 2025-12-21 19:00:00.000000+00:00

Adds columns for:
- Project sharing functionality (owner_id, is_shared_externally, share_token)
- Ruleset document type support (supported_document_types)
- Creates project_shares table for granular sharing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add project sharing columns to projects table
    op.add_column(
        "projects",
        sa.Column("owner_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("is_shared_externally", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "projects",
        sa.Column("share_token", sa.String(64), nullable=True, unique=True),
    )

    # Add foreign key for owner_id
    op.create_foreign_key(
        "fk_projects_owner_id",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create index for share_token lookups
    op.create_index("ix_projects_share_token", "projects", ["share_token"])

    # Add supported_document_types to rulesets table
    op.add_column(
        "rulesets",
        sa.Column(
            "supported_document_types",
            JSONB(),
            server_default="[]",
            nullable=False,
        ),
    )

    # Create project_shares table for granular sharing
    op.create_table(
        "project_shares",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("share_type", sa.String(20), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=True, unique=True),
        sa.Column("permissions", sa.String(20), server_default="read", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
        ),
    )

    # Create index for project_shares share_token
    op.create_index("ix_project_shares_share_token", "project_shares", ["share_token"])


def downgrade() -> None:
    # Drop project_shares table
    op.drop_index("ix_project_shares_share_token", table_name="project_shares")
    op.drop_table("project_shares")

    # Remove supported_document_types from rulesets
    op.drop_column("rulesets", "supported_document_types")

    # Remove project sharing columns
    op.drop_index("ix_projects_share_token", table_name="projects")
    op.drop_constraint("fk_projects_owner_id", "projects", type_="foreignkey")
    op.drop_column("projects", "share_token")
    op.drop_column("projects", "is_shared_externally")
    op.drop_column("projects", "owner_id")
