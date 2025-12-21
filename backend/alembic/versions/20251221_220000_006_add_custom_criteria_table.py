"""Add custom_criteria table

Revision ID: 006
Revises: 005
Create Date: 2025-12-21 22:00:00.000000+00:00

Adds table for custom validation criteria.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create custom_criteria table
    op.create_table(
        "custom_criteria",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=False),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("ruleset_id", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, default="MEDIUM"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("logic_type", sa.String(30), nullable=False, default="SIMPLE_COMPARISON"),
        sa.Column("rule_config", JSONB, default=dict),
        sa.Column(
            "error_message_template",
            sa.Text(),
            default="Kriterium '{name}' nicht erfüllt.",
        ),
        sa.Column("priority", sa.Integer(), default=0),
        sa.Column(
            "created_by_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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


def downgrade() -> None:
    op.drop_table("custom_criteria")
