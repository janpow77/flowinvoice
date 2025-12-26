"""Add OAuth columns to users table

Revision ID: 008
Revises: 007
Create Date: 2025-12-26 10:00:00.000000+00:00

Adds auth_provider and google_id columns for OAuth support.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auth_provider column (google, github, etc.) - null for local users
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(20), nullable=True),
    )
    # Add google_id column for Google OAuth
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(255), nullable=True),
    )
    # Create unique index on google_id
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_column("users", "google_id")
    op.drop_column("users", "auth_provider")
