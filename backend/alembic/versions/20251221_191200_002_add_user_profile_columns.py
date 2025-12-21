"""Add user profile and access control columns

Revision ID: 002
Revises: 001
Create Date: 2025-12-21 19:12:00.000000+00:00

Adds columns for:
- User theme preference (theme)
- External user access control (assigned_project_id, access_expires_at, invited_by_id)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add theme preference column
    op.add_column(
        "users",
        sa.Column("theme", sa.String(20), server_default="system", nullable=False),
    )

    # Add external user access control columns
    op.add_column(
        "users",
        sa.Column("assigned_project_id", UUID(as_uuid=False), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("invited_by_id", sa.String(36), nullable=True),
    )

    # Add foreign keys
    op.create_foreign_key(
        "fk_users_assigned_project",
        "users",
        "projects",
        ["assigned_project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_invited_by",
        "users",
        "users",
        ["invited_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Remove foreign keys
    op.drop_constraint("fk_users_invited_by", "users", type_="foreignkey")
    op.drop_constraint("fk_users_assigned_project", "users", type_="foreignkey")

    # Remove columns
    op.drop_column("users", "invited_by_id")
    op.drop_column("users", "access_expires_at")
    op.drop_column("users", "assigned_project_id")
    op.drop_column("users", "theme")
