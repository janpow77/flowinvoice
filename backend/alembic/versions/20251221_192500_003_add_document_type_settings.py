"""Add document_type_settings table

Revision ID: 003
Revises: 002
Create Date: 2025-12-21 19:25:00.000000+00:00

Creates table for document type configurations with chunking settings.
Inserts default system document types.
"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# System document types to seed
SYSTEM_DOCUMENT_TYPES = [
    {
        "slug": "invoice",
        "name": "Rechnung",
        "description": "Standard-Rechnungen und Belege",
        "is_system": True,
        "chunk_size_tokens": 700,
        "chunk_overlap_tokens": 120,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "bank_statement",
        "name": "Kontoauszug",
        "description": "Bank- und Kontoauszüge",
        "is_system": True,
        "chunk_size_tokens": 900,
        "chunk_overlap_tokens": 150,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "procurement",
        "name": "Vergabeunterlagen",
        "description": "Ausschreibungen und Vergabedokumente",
        "is_system": True,
        "chunk_size_tokens": 1100,
        "chunk_overlap_tokens": 180,
        "max_chunks": 8,
        "chunk_strategy": "fixed",
    },
    {
        "slug": "other",
        "name": "Sonstiges",
        "description": "Andere Dokumenttypen",
        "is_system": True,
        "chunk_size_tokens": 900,
        "chunk_overlap_tokens": 150,
        "max_chunks": 6,
        "chunk_strategy": "fixed",
    },
]


def upgrade() -> None:
    # Create document_type_settings table
    op.create_table(
        "document_type_settings",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("chunk_size_tokens", sa.Integer(), nullable=False, server_default="700"),
        sa.Column("chunk_overlap_tokens", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("max_chunks", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("chunk_strategy", sa.String(20), nullable=False, server_default="fixed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Insert system document types
    document_type_settings = sa.table(
        "document_type_settings",
        sa.column("id", UUID(as_uuid=False)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_system", sa.Boolean),
        sa.column("chunk_size_tokens", sa.Integer),
        sa.column("chunk_overlap_tokens", sa.Integer),
        sa.column("max_chunks", sa.Integer),
        sa.column("chunk_strategy", sa.String),
    )

    op.bulk_insert(
        document_type_settings,
        [
            {
                "id": str(uuid4()),
                **doc_type,
            }
            for doc_type in SYSTEM_DOCUMENT_TYPES
        ],
    )


def downgrade() -> None:
    op.drop_table("document_type_settings")
