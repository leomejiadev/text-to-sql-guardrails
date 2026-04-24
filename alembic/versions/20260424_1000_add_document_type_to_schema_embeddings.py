"""Agrega columna document_type a schema_embeddings para distinguir schemas, joins y few-shots.

Revision ID: 20260424_1000
Revises: 20260420_1000
Create Date: 2026-04-24 10:00:00
"""
from alembic import op

revision = "20260424_1000"
down_revision = "20260420_1001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE schema_embeddings
        ADD COLUMN IF NOT EXISTS document_type VARCHAR(20) NOT NULL DEFAULT 'schema'
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE schema_embeddings DROP COLUMN IF EXISTS document_type")
