"""Habilita pgvector y crea tabla schema_embeddings para indexar schemas de tablas.

Revision ID: 20260420_1000
Revises:
Create Date: 2026-04-20 10:00:00
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260420_1000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Habilitar extensión pgvector — idempotente, no falla si ya existe
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Crear tabla con raw SQL para usar el tipo nativo vector(3072) de pgvector
    # 3072 dims = dimensión real de models/gemini-embedding-001
    op.execute("""
        CREATE TABLE schema_embeddings (
            id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            table_name  VARCHAR      NOT NULL,
            schema_text TEXT         NOT NULL,
            embedding   vector(3072) NOT NULL,
            created_at  TIMESTAMP    NOT NULL DEFAULT now(),
            updated_at  TIMESTAMP    NOT NULL DEFAULT now()
        )
    """)

    # Índice único en table_name — el upsert en SchemaRepository depende de este constraint
    op.execute(
        "CREATE UNIQUE INDEX ix_schema_embeddings_table_name ON schema_embeddings (table_name)"
    )

    # HNSW omitido: pgvector lo limita a 2000 dims y gemini-embedding-001 produce 3072.
    # Sequential scan es suficiente para una tabla de schemas (decenas/cientos de filas).


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS schema_embeddings")
    # No eliminamos la extensión vector porque puede ser usada por otras tablas
