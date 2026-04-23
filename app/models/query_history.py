from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class QueryHistory(SQLModel, table=True):
    __tablename__ = "query_history"

    # UUID como PK: independiente de la DB, seguro para exponer y fácil de
    # generar antes de insertar (útil para tracing y Celery task ids).
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Indexado porque casi todas las consultas de admin filtran por usuario.
    user_id: str = Field(index=True)

    # Pregunta original en NL — siempre obligatoria, es la fuente de verdad
    # de lo que el usuario pidió.
    original_query: str

    # Nullable: si los guardrails bloquean antes de llamar al LLM, no hay SQL.
    generated_sql: str | None = Field(default=None)

    # Default False: el caso normal es "pasó los guardrails".
    was_blocked: bool = Field(default=False)

    # Nullable: solo se llena cuando `was_blocked=True`.
    block_reason: str | None = Field(default=None)

    # Default False: recién creada, aún no se ejecutó contra la DB destino.
    executed: bool = Field(default=False)

    # UTC explícito: evitamos ambigüedad de timezone en auditoría.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Idioma detectado de `original_query` en formato ISO 639-1 ("en", "es").
    # Nullable: al crearse el registro, la detección aún no corrió. La capa
    # de servicio lo rellena antes de llamar al LLM para elegir el prompt
    # correspondiente y así responder en el idioma del usuario.
    detected_language: str | None = Field(default=None)
