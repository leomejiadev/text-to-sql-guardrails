"""Crea tabla query_history para auditoría de queries NL→SQL.

Revision ID: 20260420_1001
Revises: 20260420_1000
Create Date: 2026-04-20 10:01:00
"""
from alembic import op

revision = "20260420_1001"
down_revision = "20260420_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE query_history (
            id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id           VARCHAR     NOT NULL,
            original_query    TEXT        NOT NULL,
            generated_sql     TEXT,
            was_blocked       BOOLEAN     NOT NULL DEFAULT FALSE,
            block_reason      TEXT,
            executed          BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at        TIMESTAMP   NOT NULL DEFAULT now(),
            detected_language VARCHAR
        )
    """)
    op.execute("CREATE INDEX ix_query_history_user_id ON query_history (user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS query_history")
