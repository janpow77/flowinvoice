"""Add legal_checker column to ruleset_checker_settings

Revision ID: 007
Revises: 006
Create Date: 2025-12-24 10:00:00.000000+00:00

Adds JSONB column for Legal Checker configuration (Legal Retrieval / Normenhierarchie).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default configuration for legal_checker
DEFAULT_LEGAL_CHECKER = {
    "enabled": False,
    "funding_period": "2021-2027",
    "max_results": 5,
    "min_relevance_score": 0.6,
    "use_hierarchy_weighting": True,
    "include_definitions": True,
}


def upgrade() -> None:
    # Add legal_checker column with default value
    default_json = '{"enabled": false, "funding_period": "2021-2027", "max_results": 5, "min_relevance_score": 0.6, "use_hierarchy_weighting": true, "include_definitions": true}'
    op.add_column(
        "ruleset_checker_settings",
        sa.Column(
            "legal_checker",
            JSONB(),
            nullable=False,
            server_default=sa.text(f"'{default_json}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("ruleset_checker_settings", "legal_checker")
